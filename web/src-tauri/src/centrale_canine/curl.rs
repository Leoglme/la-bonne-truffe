//! Reads one Centrale Canine page with the curl of Windows, without opening any window.

use std::path::PathBuf;
use std::process::Command;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

use super::{RelayedPageResponse, CENTRALE_CANINE_PAGES_PREFIX};

/// Process creation flag that keeps curl from opening a console window.
#[cfg(target_os = "windows")]
const CREATE_NO_WINDOW: u32 = 0x0800_0000;

/// Written by curl after the body: the HTTP status, then the `cf-mitigated` header when Cloudflare sent one.
const STATUS_LINE_FORMAT: &str = "\n%{http_code} %header{cf-mitigated}";

/// Read one Centrale Canine page on a background thread, with the headers in the order the API gave them.
#[tauri::command]
pub async fn read_centrale_canine_page_with_curl(
    url: String,
    headers: Vec<(String, String)>,
) -> Result<RelayedPageResponse, String> {
    if !url.starts_with(CENTRALE_CANINE_PAGES_PREFIX) {
        return Err(format!("Adresse refusée : {url}"));
    }
    if !headers.iter().all(|(name, value)| is_safe_header(name, value)) {
        return Err("En-tête refusé".to_string());
    }
    tauri::async_runtime::spawn_blocking(move || read_with_curl(url, &headers))
        .await
        .map_err(|error| format!("Lecture interrompue : {error}"))
}

/// Run curl once and turn its output into the page it read.
fn read_with_curl(url: String, headers: &[(String, String)]) -> RelayedPageResponse {
    let mut command = Command::new(curl_path());
    command.args(["--silent", "--show-error", "--max-time", "30", "--write-out", STATUS_LINE_FORMAT]);
    for (name, value) in headers {
        command.arg("--header").arg(format!("{name}: {value}"));
    }
    command.arg(&url);
    #[cfg(target_os = "windows")]
    command.creation_flags(CREATE_NO_WINDOW);

    match command.output() {
        Ok(output) if output.status.success() => parse_curl_output(url, &output.stdout),
        Ok(output) => {
            let curl_error = String::from_utf8_lossy(&output.stderr).trim().to_string();
            RelayedPageResponse::failed(url, curl_error)
        }
        Err(error) => RelayedPageResponse::failed(url, format!("curl introuvable : {error}")),
    }
}

/// Split what curl printed into the body, then the status line written after it.
fn parse_curl_output(url: String, curl_output: &[u8]) -> RelayedPageResponse {
    let printed_text = String::from_utf8_lossy(curl_output);
    let Some((body, status_line)) = printed_text.rsplit_once('\n') else {
        return RelayedPageResponse::failed(url, "Réponse de curl illisible".to_string());
    };
    let mut status_line_parts = status_line.trim().splitn(2, ' ');
    let status_code = status_line_parts.next().and_then(|code| code.parse::<u16>().ok());
    let cloudflare_mitigation = status_line_parts
        .next()
        .map(str::trim)
        .filter(|mitigation| !mitigation.is_empty())
        .map(str::to_string);
    RelayedPageResponse {
        url,
        status_code,
        body: body.to_string(),
        cloudflare_mitigation,
        curl_error: None,
    }
}

/// Whether a header can go on the curl command line as it is: a plain name, a value on one line.
fn is_safe_header(name: &str, value: &str) -> bool {
    !name.is_empty()
        && name.chars().all(|character| character.is_ascii_alphanumeric() || character == '-')
        && !value.contains(['\r', '\n'])
}

/// The curl of Windows, by its full path: another curl on the PATH would be refused by Cloudflare.
#[cfg(target_os = "windows")]
fn curl_path() -> PathBuf {
    let windows_folder = std::env::var_os("SystemRoot").unwrap_or_else(|| "C:\\Windows".into());
    PathBuf::from(windows_folder).join("System32").join("curl.exe")
}

/// The curl of the system, outside Windows.
#[cfg(not(target_os = "windows"))]
fn curl_path() -> PathBuf {
    PathBuf::from("curl")
}

#[cfg(test)]
mod tests {
    use super::*;

    const PAGE_URL: &str = "https://www.centrale-canine.fr/api/breed/le-chien-de-race--cocker/chiots-de-la-race/0";

    #[test]
    fn reads_the_body_and_the_status_curl_wrote_after_it() {
        let response = parse_curl_output(PAGE_URL.to_string(), b"{\"litters\":{}}\n200 ");

        assert_eq!(response.status_code, Some(200));
        assert_eq!(response.body, "{\"litters\":{}}");
        assert_eq!(response.cloudflare_mitigation, None);
    }

    #[test]
    fn reads_the_refusal_of_cloudflare() {
        let response = parse_curl_output(PAGE_URL.to_string(), b"<html>Just a moment...</html>\n403 challenge");

        assert_eq!(response.status_code, Some(403));
        assert_eq!(response.cloudflare_mitigation.as_deref(), Some("challenge"));
    }

    #[test]
    fn refuses_a_header_that_would_add_a_line() {
        assert!(is_safe_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"));
        assert!(!is_safe_header("User-Agent", "Mozilla\r\nX-Injected: 1"));
        assert!(!is_safe_header("User Agent", "Mozilla"));
    }
}
