//! UTF-8 byte cursor pagination that cannot return zero progress inside a character.
use super::{io, RuntimeError, RuntimeResult};

pub(super) fn artifact_utf8_window(
    text: &str,
    offset: u64,
    max_bytes: u64,
) -> RuntimeResult<(usize, usize)> {
    let begin = usize::try_from(offset).map_err(io)?;
    if begin > text.len() || !text.is_char_boundary(begin) {
        return Err(RuntimeError::invalid("invalid UTF-8 offset", "offset"));
    }
    let end = text.floor_char_boundary(begin.saturating_add(max_bytes as usize).min(text.len()));
    if end == begin && begin < text.len() {
        return Err(RuntimeError::invalid(
            "maxBytes is too small for the next UTF-8 character; use at least 4 bytes",
            "maxBytes",
        ));
    }
    Ok((begin, end))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn utf8_window_matches_independent_boundary_enumeration() {
        // All UTF-8 codepoint widths, including a zero byte, and a range of
        // invalid offsets/limits. The oracle enumerates starts and EOF.
        let alphabet = ['\0', 'a', 'é', '中', '🙂'];
        let mut texts = vec![String::new()];
        for _ in 0..4 {
            texts = texts
                .into_iter()
                .flat_map(|prefix| {
                    std::iter::once(prefix.clone()).chain(alphabet.into_iter().map(move |ch| {
                        let mut s = prefix.clone();
                        s.push(ch);
                        s
                    }))
                })
                .collect();
        }
        texts.sort();
        texts.dedup();
        let mut cases = 0;
        for text in texts {
            let boundaries: Vec<_> = text
                .char_indices()
                .map(|(i, _)| i)
                .chain(std::iter::once(text.len()))
                .collect();
            for offset in (0..=(text.len() as u64 + 1)).chain([u64::MAX]) {
                for limit in (0..=(text.len() as u64 + 1)).chain([u64::MAX]) {
                    let actual = artifact_utf8_window(&text, offset, limit);
                    if let Ok(begin) = usize::try_from(offset) {
                        if !boundaries.contains(&begin) {
                            assert_eq!(actual.unwrap_err().field.as_deref(), Some("offset"));
                        } else {
                            let cap = begin.saturating_add(limit as usize).min(text.len());
                            let end = *boundaries.iter().filter(|&&i| i <= cap).max().unwrap();
                            if end == begin && begin < text.len() {
                                assert_eq!(actual.unwrap_err().field.as_deref(), Some("maxBytes"));
                            } else {
                                assert_eq!(actual.unwrap(), (begin, end));
                            }
                        }
                    } else {
                        assert!(actual.is_err());
                    }
                    cases += 1;
                }
            }
        }
        println!("independent boundary cases: {cases}");
        assert!(cases > 50_000);
    }
}
