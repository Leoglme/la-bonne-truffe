//! Reads one Centrale Canine page in a hidden window of the app's own browser (WebView2), where Cloudflare runs
//! its check as in any browser. Nothing hides the automation: when the check asks for a person, the read fails.

use std::sync::atomic::{AtomicU32, Ordering};
use std::sync::{mpsc, Mutex};
use std::time::Duration;

use tauri::{AppHandle, Url, WebviewUrl, WebviewWindowBuilder};

use super::{RelayedPageResponse, CENTRALE_CANINE_PAGES_PREFIX};

/// Longest wait for the page, Cloudflare's check included.
const PAGE_TIMEOUT: Duration = Duration::from_secs(30);

/// Address the page script navigates to with the page text; the app catches the navigation and cancels it.
const DELIVERY_ADDRESS: &str = "https://relay.labonnetruffe.invalid/";

/// Query parameter of the delivery address that carries the page text.
const PAGE_TEXT_PARAMETER: &str = "page";

/// Script of the hidden window: once the page is the JSON and not Cloudflare's check, hand its text to the app.
const DELIVERY_SCRIPT: &str = r#"(() => {
  if (location.hostname !== 'www.centrale-canine.fr') {
    return;
  }
  const readPageText = async () => {
    const preformattedText = document.querySelector('pre')?.textContent ?? '';
    const bodyText = document.body?.innerText ?? '';
    for (const candidateText of [preformattedText, bodyText]) {
      try {
        JSON.parse(candidateText);
        return candidateText;
      } catch (error) {}
    }
    const response = await fetch(location.href, { credentials: 'include' });
    return response.text();
  };
  document.addEventListener('DOMContentLoaded', async () => {
    if (document.contentType !== 'application/json') {
      return;
    }
    const pageText = await readPageText();
    location.replace('__DELIVERY_ADDRESS__?__PAGE_TEXT_PARAMETER__=' + encodeURIComponent(pageText));
  });
})();"#;

/// Number of the next hidden window: each read gets its own.
static NEXT_READER_NUMBER: AtomicU32 = AtomicU32::new(1);

/// Read one Centrale Canine page in a hidden window of the app's browser.
#[tauri::command]
pub async fn read_centrale_canine_page_in_browser(
    app: AppHandle,
    url: String,
) -> Result<RelayedPageResponse, String> {
    if !url.starts_with(CENTRALE_CANINE_PAGES_PREFIX) {
        return Err(format!("Adresse refusée : {url}"));
    }
    let page_url: Url = url.parse().map_err(|error| format!("Adresse illisible : {error}"))?;
    let (page_text_sender, page_text_receiver) = mpsc::channel::<String>();
    let pending_page_text_sender = Mutex::new(Some(page_text_sender));
    let reader_label = format!("centrale-canine-reader-{}", NEXT_READER_NUMBER.fetch_add(1, Ordering::Relaxed));

    let reader_window = WebviewWindowBuilder::new(&app, reader_label, WebviewUrl::External(page_url))
        .visible(false)
        .initialization_script(delivery_script())
        .on_navigation(move |navigation_url| {
            let Some(page_text) = page_text_of_delivery(navigation_url) else {
                return true;
            };
            if let Some(sender) = pending_page_text_sender.lock().ok().and_then(|mut pending| pending.take()) {
                let _ = sender.send(page_text);
            }
            false
        })
        .build()
        .map_err(|error| format!("Navigateur de l'app indisponible : {error}"))?;

    let page_text = tauri::async_runtime::spawn_blocking(move || page_text_receiver.recv_timeout(PAGE_TIMEOUT))
        .await
        .map_err(|error| format!("Lecture interrompue : {error}"))?;
    let _ = reader_window.destroy();

    Ok(match page_text {
        Ok(page_text) => RelayedPageResponse {
            url,
            status_code: Some(200),
            body: page_text,
            cloudflare_mitigation: None,
            curl_error: None,
        },
        Err(_) => RelayedPageResponse::failed(
            url,
            "La vérification de Cloudflare n'a pas abouti dans le navigateur de l'app".to_string(),
        ),
    })
}

/// The script of the hidden window, with the delivery address the app watches.
fn delivery_script() -> String {
    DELIVERY_SCRIPT
        .replace("__DELIVERY_ADDRESS__", DELIVERY_ADDRESS)
        .replace("__PAGE_TEXT_PARAMETER__", PAGE_TEXT_PARAMETER)
}

/// The page text a delivery address carries; nothing for any other address.
fn page_text_of_delivery(navigation_url: &Url) -> Option<String> {
    if !navigation_url.as_str().starts_with(DELIVERY_ADDRESS) {
        return None;
    }
    navigation_url
        .query_pairs()
        .find(|(name, _)| name == PAGE_TEXT_PARAMETER)
        .map(|(_, page_text)| page_text.into_owned())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reads_the_page_text_a_delivery_address_carries() {
        let delivery_url: Url = format!("{DELIVERY_ADDRESS}?page=%7B%22litters%22%3A%7B%7D%7D").parse().unwrap();

        assert_eq!(page_text_of_delivery(&delivery_url).as_deref(), Some("{\"litters\":{}}"));
    }

    #[test]
    fn lets_any_other_navigation_go_on() {
        let challenge_url: Url = "https://www.centrale-canine.fr/cdn-cgi/challenge-platform/h/g".parse().unwrap();

        assert_eq!(page_text_of_delivery(&challenge_url), None);
    }

    #[test]
    fn hands_the_page_to_the_address_the_app_watches() {
        assert!(delivery_script().contains(&format!("'{DELIVERY_ADDRESS}?{PAGE_TEXT_PARAMETER}='")));
    }
}
