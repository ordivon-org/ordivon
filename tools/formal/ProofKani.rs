#[kani::proof]
fn no_wrap() {
 let a: u8 = kani::any();
 assert!((a as u16 + 1) > a as u16);
}
