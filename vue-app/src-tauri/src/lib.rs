use std::net::TcpStream;
use std::path::Path;
use std::sync::Mutex;
use std::time::Duration;

use tauri::Manager;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

struct BackendProcess(Mutex<Option<CommandChild>>);

fn api_running() -> bool {
    let address = match "127.0.0.1:8765".parse() {
        Ok(address) => address,
        Err(_) => return false,
    };
    TcpStream::connect_timeout(&address, Duration::from_millis(250)).is_ok()
}

fn repo_root() -> std::path::PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|path| path.parent())
        .map(Path::to_path_buf)
        .unwrap_or_else(|| Path::new(".").to_path_buf())
}

fn spawn_backend(app: &tauri::AppHandle) -> Result<(), String> {
    if api_running() {
        log::info!("backend already running on 127.0.0.1:8765");
        return Ok(());
    }

    let repo = repo_root();
    let env_file = repo.join(".env").to_string_lossy().to_string();
    let shell = app.shell();

    let python = repo.join(".venv").join("Scripts").join("python.exe");
    let command = if cfg!(debug_assertions) && python.is_file() {
        log::info!("starting backend from {:?}", python);
        shell
            .command(python.to_string_lossy().to_string())
            .args(["-m", "sc2analyzer.api"])
            .current_dir(repo.join("services").join("analyzer"))
            .env(
                "PYTHONPATH",
                repo.join("services").join("analyzer").to_string_lossy().to_string(),
            )
            .env("SC2_ENV_FILE", env_file)
            .env("SC2_API_HOST", "127.0.0.1")
            .env("SC2_API_PORT", "8765")
            .env("SC2_PARENT_PID", std::process::id().to_string())
    } else {
        log::info!("starting bundled backend sidecar");
        shell
            .sidecar("sc2analyzer-api")
            .map_err(|error| error.to_string())?
            .env("SC2_ENV_FILE", env_file)
            .env("SC2_API_HOST", "127.0.0.1")
            .env("SC2_API_PORT", "8765")
            .env("SC2_PARENT_PID", std::process::id().to_string())
    };

    let (mut events, child) = command.spawn().map_err(|error| error.to_string())?;

    tauri::async_runtime::spawn(async move {
        while let Some(event) = events.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    log::info!("[backend] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Stderr(line) => {
                    log::warn!("[backend] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Error(error) => {
                    log::error!("[backend] {}", error);
                }
                _ => {}
            }
        }
    });

    if let Some(state) = app.try_state::<BackendProcess>() {
        if let Ok(mut guard) = state.0.lock() {
            *guard = Some(child);
        }
    }

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .setup(|app| {
            app.manage(BackendProcess(Mutex::new(None)));

            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                if let Err(error) = spawn_backend(&handle) {
                    log::error!("failed to start backend: {}", error);
                }
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if window.label() == "main" {
                if let tauri::WindowEvent::CloseRequested { .. } = event {
                    if let Some(overlay) = window.app_handle().get_webview_window("overlay") {
                        let _ = overlay.close();
                    }
                    if let Some(state) = window.app_handle().try_state::<BackendProcess>() {
                        if let Ok(mut guard) = state.0.lock() {
                            if let Some(child) = guard.take() {
                                let _ = child.kill();
                            }
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
