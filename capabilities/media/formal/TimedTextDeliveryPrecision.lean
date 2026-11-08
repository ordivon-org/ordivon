-- WebVTT and SRT use millisecond delivery precision, while Media source
-- time remains integer ticks. This is a pure model, not a Python proof.
namespace OrdivonMedia

def roundedMillis (tick ticksPerSecond : Nat) : Nat :=
  let numerator := tick * 1000
  let quotient := numerator / ticksPerSecond
  let remainder := numerator % ticksPerSecond
  if remainder * 2 < ticksPerSecond then quotient
  else if ticksPerSecond < remainder * 2 then quotient + 1
  else if quotient % 2 = 0 then quotient else quotient + 1

def renderable (startTick endTick ticksPerSecond : Nat) : Prop :=
  And (ticksPerSecond > 0)
    (roundedMillis startTick ticksPerSecond <
     roundedMillis endTick ticksPerSecond)

theorem renderable_requires_positive_output (startTick endTick base : Nat)
    (h : renderable startTick endTick base) :
    roundedMillis startTick base < roundedMillis endTick base := by
  exact h.2

theorem collapsed_delivery_rejected (startTick endTick base : Nat)
    (collapsed : Not (roundedMillis startTick base < roundedMillis endTick base)) :
    Not (renderable startTick endTick base) := by
  intro admitted
  exact collapsed admitted.2

theorem zero_tick_base_rejected (startTick endTick : Nat) :
    Not (renderable startTick endTick 0) := by
  simp [renderable]

-- A source whose timebase is exactly 1000 ticks/sec suffers no rounding drift.
theorem exact_millisecond_source_ticks (tick : Nat) :
    roundedMillis tick 1000 = tick := by
  simp [roundedMillis]

-- Concrete model-level witnesses: a source interval can collapse in WebVTT.
example : Not (renderable 1 2 10000) := by simp [renderable, roundedMillis]
-- The same timebase can express ordinary millisecond boundaries exactly.
example : renderable 10 20 10000 := by simp [renderable, roundedMillis]
-- Nearest-integer rounding preserves the existing ties-to-even policy.
example : roundedMillis 1 2000 = 0 := by decide
example : roundedMillis 3 2000 = 2 := by decide

end OrdivonMedia
