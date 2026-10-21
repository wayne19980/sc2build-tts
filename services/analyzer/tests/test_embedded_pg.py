from pgserver import postgres_server

from sc2analyzer import embedded_pg


def test_pg_ctl_timeout_overrides_pgserver_default(monkeypatch):
    calls: list[float | None] = []

    def fake_pg_ctl(args, **kwargs):
        calls.append(kwargs.get("timeout"))
        return ""

    monkeypatch.setattr(postgres_server, "pg_ctl", fake_pg_ctl)
    embedded_pg._patch_pg_ctl_timeout()
    postgres_server.pg_ctl(["-w", "start"], timeout=10)
    postgres_server.pg_ctl(["-w", "stop"])

    assert calls == [embedded_pg._PG_CTL_TIMEOUT, embedded_pg._PG_CTL_TIMEOUT]
