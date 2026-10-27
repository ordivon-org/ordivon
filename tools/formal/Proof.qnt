module Proof {
  var n: int
  action init = { n' = 0 }
  action step = { n' = n + 1 }
  val nonnegative = n >= 0
}
