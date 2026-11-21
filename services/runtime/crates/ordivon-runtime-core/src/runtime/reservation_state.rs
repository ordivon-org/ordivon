//! Storage-neutral reservation capacity and terminal Attempt evidence contracts.
//! No new reservation state, separate database, or policy authority.
pub(crate) struct ReservationContract;

mod capacity;
mod terminal;

#[cfg(kani)]
mod kani_reservation_contract_proofs;
#[cfg(test)]
mod tests;
