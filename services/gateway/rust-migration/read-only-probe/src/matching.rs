//! Pure lexical matching. No Owner transport, readiness caching, or authorization.
use icu_casemap::CaseMapper;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeSet, BinaryHeap};

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

#[derive(Debug, PartialEq, Eq, Serialize)]
pub struct SearchResult {
    total_matches: usize,
    matches: Vec<Match>,
}

#[derive(Debug, PartialEq, Eq, Serialize)]
struct Match {
    capability: String,
    match_kind: MatchKind,
}

/// Immutable compiled metadata, with request-local observations supplied by
/// the caller. The index cannot store an Owner's status or authorization.
struct SearchIndex {
    entries: Vec<(Metadata, CompiledMetadata)>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Observation {
    capability: String,
    available: bool,
    observation_error: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Query {
    query: String,
    category: Option<String>,
    owner_id: Option<String>,
    limit: usize,
    include_unavailable: bool,
    observations: Vec<Observation>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BatchInput {
    metadata: Vec<Metadata>,
    queries: Vec<Query>,
}

impl SearchIndex {
    fn new(metadata: Vec<Metadata>) -> Self {
        Self {
            entries: metadata
                .into_iter()
                .map(|m| {
                    let compiled = CompiledMetadata::new(&m);
                    (m, compiled)
                })
                .collect(),
        }
    }

    fn search(&self, input: &Query) -> Result<SearchResult, &'static str> {
        if input.observations.len() != self.entries.len()
            || self
                .entries
                .iter()
                .zip(&input.observations)
                .any(|((m, _), o)| m.capability != o.capability)
        {
            return Err("observation identity mismatch");
        }
        let query = fold(&input.query);
        let query_tokens = tokens(&query);
        // Retain only the worst of the best K at the heap root. Source index
        // breaks equal rank/name ties exactly as a stable full sort would.
        let mut top = BinaryHeap::new();
        let mut total_matches = 0;
        for (i, ((m, compiled), o)) in self.entries.iter().zip(&input.observations).enumerate() {
            if input.category.as_ref().is_some_and(|c| c != &m.category)
                || input.owner_id.as_ref().is_some_and(|id| id != &m.owner_id)
                || (!input.include_unavailable && !o.available && o.observation_error.is_none())
            {
                continue;
            }
            let Some(kind) = compiled.rank(&query, &query_tokens) else {
                continue;
            };
            total_matches += 1;
            if input.limit == 0 {
                continue;
            }
            let rank = (kind, m.capability.as_str(), i);
            if top.len() < input.limit {
                top.push(rank);
            } else if top.peek().is_some_and(|worst| rank < *worst) {
                *top.peek_mut().expect("nonempty heap") = rank;
            }
        }
        Ok(SearchResult {
            total_matches,
            matches: top
                .into_sorted_vec()
                .into_iter()
                .map(|(match_kind, name, _)| Match {
                    capability: name.to_owned(),
                    match_kind,
                })
                .collect(),
        })
    }
}

pub fn search_batch(input: BatchInput) -> Result<Vec<SearchResult>, &'static str> {
    let mut identities = BTreeSet::new();
    if input
        .metadata
        .iter()
        .any(|m| !identities.insert(&m.capability))
    {
        return Err("duplicate metadata identity");
    }
    let index = SearchIndex::new(input.metadata);
    input
        .queries
        .into_iter()
        .map(|query| index.search(&query))
        .collect()
}

pub fn search(input: SearchInput) -> SearchResult {
    let (metadata, observations) = input
        .rows
        .into_iter()
        .map(|row| {
            let obs = Observation {
                capability: row.metadata.capability.clone(),
                available: row.available,
                observation_error: row.observation_error,
            };
            (row.metadata, obs)
        })
        .unzip();
    SearchIndex::new(metadata)
        .search(&Query {
            query: input.query,
            category: input.category,
            owner_id: input.owner_id,
            limit: input.limit,
            include_unavailable: input.include_unavailable,
            observations,
        })
        .expect("constructed observations align with metadata")
}

/// Bounded qualification carrier for one actual Linux execution route. It
/// shares the compiled index but does not define another public MCP ABI.
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RuntimeSearchFixture {
    metadata: Metadata,
    query: String,
    limit: usize,
    include_unavailable: bool,
}

pub struct RuntimeSearchPlan {
    index: SearchIndex,
    query: Query,
}

impl RuntimeSearchPlan {
    pub fn new(input: RuntimeSearchFixture) -> Result<Self, &'static str> {
        let m = input.metadata;
        if m.capability != "execution.linux"
            || m.category != "execution"
            || m.owner_id != "runtime.linux"
        {
            return Err("unsupported fixture route");
        }
        let trim = |c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c);
        if input.query.is_empty()
            || input.query.trim_matches(trim) != input.query
            || input.query.chars().count() > 512
            || !(1..=50).contains(&input.limit)
        {
            return Err("invalid fixture query");
        }
        Ok(Self {
            index: SearchIndex::new(vec![m]),
            query: Query {
                query: input.query,
                category: None,
                owner_id: None,
                limit: input.limit,
                include_unavailable: input.include_unavailable,
                observations: Vec::new(),
            },
        })
    }

    pub fn requires_observation(&self) -> bool {
        let query = fold(&self.query.query);
        self.index.entries[0]
            .1
            .rank(&query, &tokens(&query))
            .is_some()
    }

    pub fn project(
        mut self,
        observation: Option<(bool, Option<String>)>,
    ) -> Result<SearchResult, &'static str> {
        match observation {
            None if !self.requires_observation() => Ok(SearchResult {
                total_matches: 0,
                matches: Vec::new(),
            }),
            Some((available, observation_error)) if self.requires_observation() => {
                self.query.observations.push(Observation {
                    capability: self.index.entries[0].0.capability.clone(),
                    available,
                    observation_error,
                });
                self.index.search(&self.query)
            }
            _ => Err("fixture observation does not match plan"),
        }
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

    fn original_full_sort(metadata: &[Metadata], input: &Query) -> SearchResult {
        let query = fold(&input.query);
        let query_tokens = tokens(&query);
        let mut ranks: Vec<_> = metadata
            .iter()
            .zip(&input.observations)
            .filter(|(m, o)| {
                input.category.as_ref().is_none_or(|c| c == &m.category)
                    && input.owner_id.as_ref().is_none_or(|id| id == &m.owner_id)
                    && (input.include_unavailable || o.available || o.observation_error.is_some())
            })
            .filter_map(|(m, _)| {
                Some((
                    CompiledMetadata::new(m).rank(&query, &query_tokens)?,
                    m.capability.as_str(),
                ))
            })
            .collect();
        ranks.sort();
        SearchResult {
            total_matches: ranks.len(),
            matches: ranks
                .into_iter()
                .take(input.limit)
                .map(|(match_kind, name)| Match {
                    capability: name.to_owned(),
                    match_kind,
                })
                .collect(),
        }
    }

    fn corpus(n: usize) -> Vec<Metadata> {
        (0..n)
            .rev()
            .map(|i| Metadata {
                capability: format!("runtime.fixture.{i:05}"),
                category: if i % 3 == 0 { "execution" } else { "research" }.to_owned(),
                owner_id: if i % 2 == 0 {
                    "runtime.linux"
                } else {
                    "runtime.windows"
                }
                .to_owned(),
                description: format!("Run read artifact Straße Σς test {}", i % 17),
                tags: vec!["candidate".to_owned(), "read-only".to_owned()],
            })
            .collect()
    }

    fn query_for(
        metadata: &[Metadata],
        query: &str,
        limit: usize,
        include: bool,
        phase: usize,
    ) -> Query {
        Query {
            query: query.to_owned(),
            category: None,
            owner_id: None,
            limit,
            include_unavailable: include,
            observations: metadata
                .iter()
                .enumerate()
                .map(|(i, m)| Observation {
                    capability: m.capability.clone(),
                    available: (i + phase).is_multiple_of(3),
                    observation_error: ((i + phase) % 3 == 1).then(|| "unobserved".to_owned()),
                })
                .collect(),
        }
    }

    #[test]
    fn bounded_heap_matches_original_sort_with_fresh_observations() {
        let metadata = corpus(257);
        let index = SearchIndex::new(metadata.clone());
        for q in [
            "runtime",
            "artifact",
            "strasse",
            "Σ",
            "runtime.fixture.00042",
            "none",
            "read-only",
        ] {
            for limit in [0, 1, 3, 50, 257, 999] {
                for include in [true, false] {
                    for phase in 0..3 {
                        let mut input = query_for(&metadata, q, limit, include, phase);
                        if phase == 1 {
                            input.category = Some("execution".to_owned());
                        }
                        if phase == 2 {
                            input.owner_id = Some("runtime.linux".to_owned());
                        }
                        assert_eq!(
                            index.search(&input).unwrap(),
                            original_full_sort(&metadata, &input)
                        );
                    }
                }
            }
        }
        let mut malformed = query_for(&metadata, "runtime", 10, false, 0);
        malformed.observations.swap(0, 1);
        assert_eq!(
            index.search(&malformed),
            Err("observation identity mismatch")
        );
        malformed.observations.pop();
        assert_eq!(
            index.search(&malformed),
            Err("observation identity mismatch")
        );
    }

    #[test]
    #[ignore = "explicit local CPU benchmark, not a timing gate"]
    fn benchmark_index_against_original_sort() {
        use std::{hint::black_box, time::Instant};
        for size in [19, 1900] {
            let metadata = corpus(size);
            let input = query_for(&metadata, "runtime", 10, false, 0);
            let start = Instant::now();
            let index = SearchIndex::new(metadata.clone());
            let compile_us = start.elapsed().as_secs_f64() * 1e6;
            assert_eq!(
                index.search(&input).unwrap(),
                original_full_sort(&metadata, &input)
            );
            let iterations = if size == 19 { 200 } else { 20 };
            let mut original = Vec::new();
            let mut compiled = Vec::new();
            for round in 0..7 {
                for old in if round % 2 == 0 {
                    [true, false]
                } else {
                    [false, true]
                } {
                    let start = Instant::now();
                    for _ in 0..iterations {
                        if old {
                            black_box(original_full_sort(black_box(&metadata), black_box(&input)));
                        } else {
                            black_box(index.search(black_box(&input)).unwrap());
                        }
                    }
                    let us = start.elapsed().as_secs_f64() * 1e6 / f64::from(iterations);
                    if old {
                        original.push(us);
                    } else {
                        compiled.push(us);
                    }
                }
            }
            original.sort_by(f64::total_cmp);
            compiled.sort_by(f64::total_cmp);
            println!(
                "NATIVE_SEARCH_BENCH rows={size} compile_us={compile_us:.3} old_median_us={:.3} new_median_us={:.3}",
                original[3], compiled[3]
            );
        }
    }

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
