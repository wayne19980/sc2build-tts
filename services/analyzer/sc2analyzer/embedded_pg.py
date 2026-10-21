from __future__ import annotations

import atexit
import json
import os
from pathlib import Path

import pgserver
import pgserver.postgres_server as pg_server
import psutil
from platformdirs import user_data_dir

from . import config

_SERVER = None
_PG_CTL_TIMEOUT = float(os.environ.get("SC2_PG_CTL_TIMEOUT", "120"))
_BACKEND_PROCESS_NAMES = {"python.exe", "pythonw.exe", "sc2analyzer-api.exe"}
_POSTGRES_PROCESS_NAMES = {"postgres", "postgres.exe"}


def _patch_pg_ctl_timeout() -> None:
    """pgserver hard-codes a 10s pg_ctl timeout, too short for crash recovery."""
    original = pg_server.pg_ctl
    if getattr(original, "_sc2_timeout", None) == _PG_CTL_TIMEOUT:
        return

    def pg_ctl_with_timeout(args, **kwargs):
        kwargs["timeout"] = _PG_CTL_TIMEOUT
        return original(args, **kwargs)

    pg_ctl_with_timeout._sc2_timeout = _PG_CTL_TIMEOUT
    pg_server.pg_ctl = pg_ctl_with_timeout


def _process(pid: int) -> psutil.Process | None:
    try:
        process = psutil.Process(pid)
        if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
            return None
        return process
    except psutil.Error:
        return None


def _kill_process_tree(process: psutil.Process) -> None:
    try:
        children = process.children(recursive=True)
    except psutil.Error:
        children = []
    for child in children:
        try:
            child.terminate()
        except psutil.Error:
            pass
    try:
        process.terminate()
    except psutil.Error:
        pass
    _, alive = psutil.wait_procs(children + [process], timeout=3)
    for item in alive:
        try:
            item.kill()
        except psutil.Error:
            pass


def _prune_stale_handle_pids(pgdata: Path) -> None:
    """Drop dead backend PIDs left behind when a sidecar was force-killed.

    pgserver only stops PostgreSQL when the exiting process is the last handle.
    A stale PID makes every later instance skip the stop, leaking a server.
    """
    path = pgdata / ".handle_pids.json"
    if not path.exists():
        return

    try:
        pids = json.loads(path.read_text(encoding="utf-8") or "[]")
        alive: list[int] = []
        for raw in pids:
            pid = int(raw)
            if pid == os.getpid():
                continue
            process = _process(pid)
            if process is None:
                continue
            try:
                name = process.name().lower()
            except psutil.Error:
                continue
            if name in _BACKEND_PROCESS_NAMES:
                alive.append(pid)
    except (OSError, TypeError, ValueError):
        path.unlink(missing_ok=True)
        return

    if alive != pids:
        path.write_text(json.dumps(alive), encoding="utf-8")


def _stop_stale_postgres(pgdata: Path) -> None:
    """Stop leftover servers whose binaries were deleted with a temp directory.

    PyInstaller one-file builds run PostgreSQL from a temp dir that disappears
    when the sidecar dies. A surviving server then crash-loops on missing
    share files and keeps the log/data directory locked for the next launch.
    """
    pid_file = pgdata / "postmaster.pid"
    if not pid_file.exists():
        return

    try:
        pid = int(pid_file.read_text(encoding="utf-8").splitlines()[0].strip())
    except (OSError, ValueError, IndexError):
        pid_file.unlink(missing_ok=True)
        return

    process = _process(pid)
    if process is None:
        pid_file.unlink(missing_ok=True)
        return

    try:
        if process.name().lower() not in _POSTGRES_PROCESS_NAMES:
            pid_file.unlink(missing_ok=True)
            return
        executable = process.exe()
    except psutil.Error:
        pid_file.unlink(missing_ok=True)
        return

    if executable and Path(executable).is_file():
        return  # healthy server; pgserver will reuse it

    _kill_process_tree(process)
    pid_file.unlink(missing_ok=True)


def cleanup_database() -> None:
    global _SERVER
    if _SERVER is None:
        return
    try:
        _SERVER.cleanup()
    except Exception:
        pass
    _SERVER = None


atexit.register(cleanup_database)


def _data_root() -> Path:
    configured = os.environ.get("SC2_DATA_DIR", "").strip()
    if configured:
        return Path(configured)
    return Path(user_data_dir("sc2build-tts", appauthor=False))


def ensure_database() -> str:
    """Use an external DATABASE_URL, or start a bundled PostgreSQL server."""
    global _SERVER

    forced = os.environ.get("SC2_EMBEDDED_PG", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    if config.DATABASE_URL and not forced:
        return config.DATABASE_URL

    pgdata = _data_root() / "pgdata"
    pgdata.parent.mkdir(parents=True, exist_ok=True)
    pgdata.mkdir(parents=True, exist_ok=True)
    _prune_stale_handle_pids(pgdata)
    _stop_stale_postgres(pgdata)

    _patch_pg_ctl_timeout()
    _SERVER = pgserver.get_server(pgdata, cleanup_mode="stop")
    uri = _SERVER.get_uri()

    os.environ["DATABASE_URL"] = uri
    config.DATABASE_URL = uri
    return uri
