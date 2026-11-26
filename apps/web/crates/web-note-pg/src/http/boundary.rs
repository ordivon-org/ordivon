//! Strict consumer of the existing __Host-session token representation.
//! Never parse arbitrary authorization headers, URL parameters or identity hints.
use axum::http::{HeaderMap, StatusCode, header};
pub(super) fn session_token(headers: &HeaderMap) -> Result<&str, (StatusCode, &'static str)> {
    let denied = (StatusCode::FORBIDDEN, "fetch-metadata-rejected");
    // More conservative than reference GET: reject cross-origin browser
    // fetches; no CORS headers and no cookie refresh on rejection.
    let sites = headers.get_all("sec-fetch-site").iter().collect::<Vec<_>>();
    if sites.len() > 1
        || sites
            .first()
            .is_some_and(|s| !matches!(s.to_str(), Ok("same-origin" | "none")))
    {
        return Err(denied);
    }
    let invalid = (StatusCode::UNAUTHORIZED, "session-missing");
    let mut token = None;
    for value in headers.get_all(header::COOKIE) {
        for field in value.to_str().map_err(|_| invalid)?.split(';') {
            if let Some((name, value)) = field.trim().split_once('=')
                && name == "__Host-session"
            {
                if token.is_some()
                    || value.len() != 43
                    || !value
                        .bytes()
                        .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
                {
                    return Err(invalid);
                }
                token = Some(value);
            }
        }
    }
    token.ok_or(invalid)
}
