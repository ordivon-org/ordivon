//! Pure Artifact inventory projection; no Owner RPC or completion authority.
use serde::Serialize;
use serde_json::Value;
use std::collections::HashSet;

#[derive(Debug, PartialEq, Eq, Serialize)]
pub(crate) struct Inventory<'a> {
    ids: Vec<&'a str>,
    qualified: bool,
    complete: Option<bool>,
}

pub(crate) fn project<'a>(payload: &'a Value, count: &Value) -> Inventory<'a> {
    let mut ids = Vec::new();
    let mut qualified = false;
    if let Some(rows) = payload.get("artifacts").and_then(Value::as_array) {
        qualified = true;
        for row in rows {
            match row.get("artifactId").and_then(Value::as_str) {
                Some(id)
                    if !id
                        .trim_matches(|c: char| {
                            c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c)
                        })
                        .is_empty() =>
                {
                    ids.push(id)
                }
                _ => qualified = false,
            }
        }
    }
    let complete = count.as_u64().map(|n| {
        qualified
            && ids.len() as u64 == n
            && ids.iter().copied().collect::<HashSet<_>>().len() as u64 == n
    });
    Inventory {
        ids,
        qualified,
        complete,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use serde_json::json;

    #[test]
    fn invalid_inventory_is_not_empty_and_unknown_count_is_not_false() {
        for raw in [
            json!(null),
            json!({}),
            json!([null]),
            json!([{"artifactId":" \u{1c}\u{1f}"}]),
        ] {
            let payload = json!({"artifacts":raw});
            assert_eq!(project(&payload, &json!(0)).complete, Some(false));
            assert_eq!(project(&payload, &json!(true)).complete, None);
        }
        let empty = json!({"artifacts":[]});
        assert_eq!(project(&empty, &json!(0)).complete, Some(true));
        for bad in [json!(null), json!(false), json!(-1), json!(0.0), json!("0")] {
            assert_eq!(project(&empty, &bad).complete, None);
        }
        let missing = json!({});
        assert_eq!(project(&missing, &json!(0)).complete, Some(false));
    }

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(512))]
        #[test]
        fn independent_cardinality_oracle(rows in prop::collection::vec(prop::option::of(0u8..16), 0..32), count in 0u64..35) {
            let payload=json!({"artifacts": rows.iter().map(|v| match v {
                Some(n)=>json!({"artifactId":format!("id-{n}")}),
                None=>json!({"artifactId":false})
            }).collect::<Vec<_>>()});
            let expected_ids=rows.iter().flatten().map(|n|format!("id-{n}")).collect::<Vec<_>>();
            let mut seen=[false;16];
            let mut unique=true;
            for n in rows.iter().flatten() {
                if seen[*n as usize] { unique=false; }
                seen[*n as usize]=true;
            }
            let qualified=rows.iter().all(Option::is_some);
            let result=project(&payload,&json!(count));
            prop_assert_eq!(result.ids, expected_ids.iter().map(String::as_str).collect::<Vec<_>>());
            prop_assert_eq!(result.qualified,qualified);
            prop_assert_eq!(result.complete,Some(qualified && unique && rows.len() as u64==count));
        }
    }
}
