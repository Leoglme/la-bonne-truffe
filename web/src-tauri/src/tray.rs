//! Keeps the app in the notification area (tray), as in DevLeadHunter.
//!
//! Closing the window only hides it; the tray icon brings it back or quits the app for good.
//! The app starts with Windows, hidden: in the background, it reads the Centrale Canine for the API.

use tauri::menu::{Menu, MenuItem};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{App, AppHandle, Manager, Window, WindowEvent};

/// Argument of the Windows startup entry: the app then starts hidden in the tray.
pub const LAUNCHED_AT_LOGIN_ARG: &str = "--minimized";

/// Label of the only window, declared in `tauri.conf.json`.
const MAIN_WINDOW_LABEL: &str = "main";

/// Show the main window, even when it is minimized or hidden in the tray.
pub fn show_main_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window(MAIN_WINDOW_LABEL) {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
    }
}

/// Show the window at launch, unless Windows started the app at login.
pub fn show_main_window_unless_launched_at_login(app: &AppHandle) {
    if !std::env::args().any(|arg| arg == LAUNCHED_AT_LOGIN_ARG) {
        show_main_window(app);
    }
}

/// Turn the launch at Windows startup on once, at the first launch.
///
/// Enabling it at every launch would override a user who switched it off in the Task Manager;
/// a marker file in the app data folder remembers it was done.
#[cfg(not(debug_assertions))]
pub fn enable_autostart_on_first_launch(app: &App) {
    use tauri_plugin_autostart::ManagerExt;

    let Ok(data_dir) = app.path().app_data_dir() else {
        return;
    };
    let marker = data_dir.join("autostart-enabled-once");
    if marker.exists() {
        return;
    }
    match app.autolaunch().enable() {
        Ok(()) => {
            let _ = std::fs::create_dir_all(&data_dir);
            let _ = std::fs::write(&marker, b"");
        }
        Err(error) => log::error!("launch at Windows startup not enabled: {error}"),
    }
}

/// Hide the main window instead of closing it.
pub fn hide_main_window_on_close(window: &Window, event: &WindowEvent) {
    if let WindowEvent::CloseRequested { api, .. } = event {
        if window.label() == MAIN_WINDOW_LABEL {
            api.prevent_close();
            let _ = window.hide();
        }
    }
}

/// Add the tray icon: a left click opens the window, its menu opens or quits the app.
pub fn build_tray_icon(app: &App) -> tauri::Result<()> {
    let open_item = MenuItem::with_id(app, "open", "Ouvrir La Bonne Truffe", true, None::<&str>)?;
    let quit_item = MenuItem::with_id(app, "quit", "Quitter La Bonne Truffe", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&open_item, &quit_item])?;
    let mut tray = TrayIconBuilder::with_id("main")
        .tooltip("La Bonne Truffe")
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(|app, event| match event.id().as_ref() {
            "open" => show_main_window(app),
            "quit" => app.exit(0),
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                show_main_window(tray.app_handle());
            }
        });
    if let Some(icon) = app.default_window_icon() {
        tray = tray.icon(icon.clone());
    }
    tray.build(app)?;
    Ok(())
}
