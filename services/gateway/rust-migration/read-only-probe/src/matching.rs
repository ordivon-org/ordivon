//! Pure lexical matching. No Owner transport, readiness caching, or authorization.
use icu_casemap::CaseMapper;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Metadata {
    capability: String,
    category: String,
    owner_id: String,
    description: String,
    tags: Vec<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(rename_all = "snake_case")]
enum MatchKind {
    Exact,
    Prefix,
    Token,
    Substring,
}

fn tokens(value: &str) -> BTreeSet<&str> {
    value
        .split(|c: char| !(c.is_ascii_lowercase() || c.is_ascii_digit()))
        .filter(|s| !s.is_empty())
        .collect()
}

pub fn fold(value: &str) -> String {
    CaseMapper::new().fold_string(value).into_owned()
}

struct CompiledMetadata {
    name: String,
    corpus: String,
    // Owned tokens allow reusable metadata without a self-referential struct.
    tokens: BTreeSet<String>,
}

impl CompiledMetadata {
    fn new(value: &Metadata) -> Self {
        let corpus = [
            &value.capability,
            &value.category,
            &value.owner_id,
            &value.description,
        ]
        .into_iter()
        .chain(value.tags.iter())
        .filter(|s| !s.is_empty())
        .map(|s| fold(s))
        .collect::<Vec<_>>()
        .join(" ");
        let tokens = tokens(&corpus).into_iter().map(str::to_owned).collect();
        Self {
            name: fold(&value.capability),
            corpus,
            tokens,
        }
    }

    fn rank(&self, query: &str, query_tokens: &BTreeSet<&str>) -> Option<MatchKind> {
        if query == self.name {
            Some(MatchKind::Exact)
        } else if self.name.starts_with(query) {
            Some(MatchKind::Prefix)
        } else if !query_tokens.is_empty()
            && query_tokens
                .iter()
                .all(|token| self.tokens.contains(*token))
        {
            Some(MatchKind::Token)
        } else if self.corpus.contains(query) {
            Some(MatchKind::Substring)
        } else {
            None
        }
    }
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SearchInput {
    query: String,
    category: Option<String>,
    owner_id: Option<String>,
    limit: usize,
    include_unavailable: bool,
    rows: Vec<SearchRow>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct SearchRow {
    metadata: Metadata,
    available: bool,
    observation_error: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct SearchResult {
    total_matches: usize,
    matches: Vec<Match>,
}

#[derive(Debug, Serialize)]
struct Match {
    capability: String,
    match_kind: MatchKind,
}

pub fn search(input: SearchInput) -> SearchResult {
    let query = fold(&input.query);
    let query_tokens = tokens(&query);
    let mut ranks: Vec<_> = input
        .rows
        .into_iter()
        .filter(|row| {
            let m = &row.metadata;
            input.category.as_ref().is_none_or(|c| c == &m.category)
                && input.owner_id.as_ref().is_none_or(|o| o == &m.owner_id)
                && (input.include_unavailable || row.available || row.observation_error.is_some())
        })
        .filter_map(|row| {
            let kind = CompiledMetadata::new(&row.metadata).rank(&query, &query_tokens)?;
            Some((kind, row.metadata.capability))
        })
        .collect();
    // Stable sorting preserves source order for equal ranks and names, as Python does.
    ranks.sort();
    SearchResult {
        total_matches: ranks.len(),
        matches: ranks
            .into_iter()
            .take(input.limit)
            .map(|(match_kind, capability)| Match {
                capability,
                match_kind,
            })
            .collect(),
    }
}

/// Fingerprint every Unicode scalar's full default case fold, including identity
/// mappings, using scalar UTF-8 + NUL + folded UTF-8 + NUL in scalar order.
/// The Python qualifier computes the same fingerprint independently. Surrogates
/// cannot be represented by Rust char and are not part of this proof.
pub fn scalar_fold_digest() -> String {
    let mapper = CaseMapper::new();
    let mut h = Sha256::new();
    for c in (0..=0x10ffff).filter_map(char::from_u32) {
        let mut buf = [0; 4];
        let src = c.encode_utf8(&mut buf);
        h.update(src.as_bytes());
        h.update([0]);
        h.update(mapper.fold_string(src).as_bytes());
        h.update([0]);
    }
    h.finalize()
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn full_fold_not_simple_lowercase() {
        assert_eq!(fold("Straße Σς K İ"), "strasse σσ k i\u{307}");
    }

    #[test]
    fn ascii_words_do_not_silently_expand_unicode_search_contract() {
        assert_eq!(
            tokens("foo中文bar ς a-b"),
            BTreeSet::from(["a", "b", "bar", "foo"])
        );
    }
}
