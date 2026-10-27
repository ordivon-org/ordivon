use vstd::prelude::*;
verus! {
proof fn sum_commutes(x: int, y: int)
    ensures x + y == y + x
{}
}
fn main() {}
