//! Bounded oracle for successful/factually rejected Note operations.
//! No database, production helpers, or scheduling assumptions.
use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Intent {
    pub note: u8,
    pub audit: u8,
    pub principal: bool,
    pub content: u8,
    pub time: i64,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Call {
    Execute(Intent),
    Observe(Intent),
    List(bool),
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Reply {
    Created(Intent),
    Collision,
    Exact,
    Unobserved,
    Mismatch,
    Listed(Vec<Intent>),
}
#[derive(Clone, Debug)]
pub struct Event {
    pub start: usize,
    pub end: usize,
    pub call: Call,
    pub reply: Reply,
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Facts {
    pub notes: BTreeMap<u8, Intent>,
    pub audits: BTreeMap<u8, Intent>,
}
impl Facts {
    pub fn step(&mut self, call: &Call) -> Reply {
        match call {
            Call::Execute(i) => {
                if self.notes.contains_key(&i.note) || self.audits.contains_key(&i.audit) {
                    Reply::Collision
                } else {
                    self.notes.insert(i.note, i.clone());
                    self.audits.insert(i.audit, i.clone());
                    Reply::Created(i.clone())
                }
            }
            Call::Observe(i) => {
                let note = self.notes.get(&i.note);
                let related: Vec<_> = self
                    .audits
                    .values()
                    .filter(|a| a.audit == i.audit || a.note == i.note)
                    .collect();
                if note.is_none() && related.is_empty() {
                    Reply::Unobserved
                } else if note == Some(i) && related == [i] {
                    Reply::Exact
                } else {
                    Reply::Mismatch
                }
            }
            Call::List(p) => {
                let mut v: Vec<_> = self
                    .notes
                    .values()
                    .filter(|i| i.principal == *p)
                    .cloned()
                    .collect();
                v.sort_by_key(|i| (std::cmp::Reverse(i.time), i.note));
                Reply::Listed(
                    v.into_iter()
                        .map(|mut i| {
                            i.audit = 0;
                            i
                        })
                        .collect(),
                )
            }
        }
    }
}
/// Tiny bounded exhaustive search, not a general-purpose linearizability engine.
/// Real-time precedence: a completed call must precede a later invocation.
/// Compare terminal independently observed facts as well as operation replies.
pub fn witness(history: &[Event], final_facts: &Facts) -> Option<Vec<usize>> {
    assert!(history.len() <= 8 && history.iter().all(|e| e.start < e.end));
    let mut stamps: Vec<_> = history.iter().flat_map(|e| [e.start, e.end]).collect();
    stamps.sort_unstable();
    stamps.dedup();
    assert_eq!(stamps.len(), history.len() * 2);
    fn search(
        h: &[Event],
        final_facts: &Facts,
        facts: Facts,
        chosen: u16,
        order: &mut Vec<usize>,
    ) -> bool {
        if order.len() == h.len() {
            return &facts == final_facts;
        }
        for (idx, e) in h.iter().enumerate() {
            let bit = 1u16 << idx;
            if chosen & bit != 0
                || h.iter()
                    .enumerate()
                    .any(|(j, p)| chosen & (1 << j) == 0 && p.end < e.start)
            {
                continue;
            }
            let mut next = facts.clone();
            if next.step(&e.call) != e.reply {
                continue;
            }
            order.push(idx);
            if search(h, final_facts, next, chosen | bit, order) {
                return true;
            }
            order.pop();
        }
        false
    }
    let mut order = Vec::new();
    search(history, final_facts, Facts::default(), 0, &mut order).then_some(order)
}
