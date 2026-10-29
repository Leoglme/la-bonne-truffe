//! Reads the Centrale Canine pages the API asks for, from the computer's connection: with the curl of Windows,
//! or with the app's own browser when Cloudflare refuses curl (docs/02-sources.md).

pub mod browser;
pub mod curl;

use serde::Serialize;

/// Only the litters pages of the Centrale Canine may be read through these commands.
const CENTRALE_CANINE_PAGES_PREFIX: &str = "https://www.centrale-canine.fr/api/breed/";

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
