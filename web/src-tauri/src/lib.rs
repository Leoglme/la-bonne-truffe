//! Desktop shell of La Bonne Truffe: the dashboard in a window, kept in the notification area.
//!
//! Notifications are not delivered here: the iPhone and iPad receive them through Web Push.

mod tray;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let builder = tauri::Builder::default();
    // Release only: a dev build shares the installed app's identifier and would be blocked by it.
    // Single instance comes first, as its plugin requires: a second launch shows the running window.
    #[cfg(not(debug_assertions))]
    let builder = builder.plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
        tray::show_main_window(app);
    }));
    builder
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .on_window_event(tray::hide_main_window_on_close)
        .setup(|app| {
            tray::build_tray_icon(app)?;
            tray::show_main_window(app.handle());
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|_app_handle, _event| {
            // A click on the Dock icon brings back the window hidden by its close button.
            #[cfg(target_os = "macos")]
            if let tauri::RunEvent::Reopen { .. } = _event {
                tray::show_main_window(_app_handle);
            }
        });
}
