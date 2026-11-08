extends Resource
class_name RelayPlan

# Game-specific native content only, not a generic factory schema.
@export var pickup_sites: PackedVector2Array = PackedVector2Array([
    Vector2(105, 205), Vector2(375, 230), Vector2(92, 580), Vector2(380, 570),
])
@export var depot: Vector2 = Vector2(240, 448)
@export var initial_enemy_interval: float = 0.95
