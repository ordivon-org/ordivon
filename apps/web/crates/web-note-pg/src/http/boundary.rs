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

/// Shared exact unsafe-origin guard. Missing Fetch Metadata is allowed for
/// non-browser clients, but Origin is mandatory.
pub(super) fn unsafe_origin(
    headers: &HeaderMap,
    origin: &str,
) -> Result<(), (StatusCode, &'static str)> {
    let mut origins = headers.get_all(header::ORIGIN).iter();
    if origins.next().and_then(|v| v.to_str().ok()) != Some(origin) || origins.next().is_some() {
        return Err((StatusCode::FORBIDDEN, "origin-rejected"));
    }
    let mut sites = headers.get_all("sec-fetch-site").iter();
    if sites.next().is_some_and(|v| v != "same-origin") || sites.next().is_some() {
        return Err((StatusCode::FORBIDDEN, "fetch-metadata-rejected"));
    }
    Ok(())
}
/// Exact configured HTTPS origin, not a URL with path/query or userinfo.
pub(super) fn valid_origin(origin: &str) -> bool {
    let Ok(uri) = origin.parse::<axum::http::Uri>() else {
        return false;
    };
    let Some(a) = uri.authority() else {
        return false;
    };
    uri.scheme_str() == Some("https")
        && !a.host().is_empty()
        && !a.as_str().contains('@')
        && origin == format!("https://{}", a.as_str())
}
