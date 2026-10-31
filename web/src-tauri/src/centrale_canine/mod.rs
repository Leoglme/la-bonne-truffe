//! Reads the Centrale Canine pages the API asks for, from the computer's connection: with the curl of Windows,
//! or with the app's own browser when Cloudflare refuses curl (docs/02-sources.md).

pub mod browser;
pub mod curl;

use serde::Serialize;

/// Only pages of the Centrale Canine may be read through these commands: the API decides which ones (the
/// litters, the breeder directory, the club, the litter and dog pages, the breeders' sites).
const CENTRALE_CANINE_PAGE_PREFIXES: [&str; 1] = ["https://www.centrale-canine.fr/"];

/// Whether a page is one the API may ask the computer to read.
fn is_relayed_page_url(url: &str) -> bool {
    CENTRALE_CANINE_PAGE_PREFIXES
        .iter()
        .any(|prefix| url.starts_with(prefix))
}

/// A page as the computer read it, in the shape the API expects.
#[derive(Serialize)]
pub struct RelayedPageResponse {
    url: String,
    status_code: Option<u16>,
    body: String,
    cloudflare_mitigation: Option<String>,
    /// Why the page could not be read, by curl or the browser: the API knows the field by this name.
    curl_error: Option<String>,
}

impl RelayedPageResponse {
    /// A page the computer could not read, and why.
    fn failed(url: String, reading_error: String) -> Self {
        Self {
            url,
            status_code: None,
            body: String::new(),
            cloudflare_mitigation: None,
            curl_error: Some(reading_error),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_every_json_page_of_the_centrale_canine() {
        assert!(is_relayed_page_url(
            "https://www.centrale-canine.fr/api/breed/le-chien-de-race--cocker/chiots-de-la-race/0?_format=json"
        ));
        assert!(is_relayed_page_url(
            "https://www.centrale-canine.fr/api/breed/le-chien-de-race--cocker/eleveurs/0?department=t_41"
        ));
        assert!(is_relayed_page_url("https://www.centrale-canine.fr/api/litter/2834593?_format=json"));
        assert!(is_relayed_page_url("https://www.centrale-canine.fr/api/dog/7000001?_format=json"));
        assert!(is_relayed_page_url(
            "https://www.centrale-canine.fr/spaniel-club-francais/api/breeders/0?filter=1728&_format=json"
        ));
    }

    #[test]
    fn accepts_the_site_of_a_breeding() {
        assert!(is_relayed_page_url("https://www.centrale-canine.fr/elevage-123/api/homepage?_format=json"));
    }

    #[test]
    fn refuses_any_other_host_or_an_unsecured_address() {
        assert!(!is_relayed_page_url("https://example.com/api/dog/1"));
        assert!(!is_relayed_page_url("http://www.centrale-canine.fr/api/dog/1"));
        assert!(!is_relayed_page_url("https://www.centrale-canine.fr.example.com/api/dog/1"));
    }
}
