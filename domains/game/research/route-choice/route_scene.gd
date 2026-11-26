extends VBoxContainer

const RouteRules = preload("res://route_rules.gd")
var rules: Node
var status: Label
var map_label: Label
var encounter: Label
var forecast: Label
var buttons: Dictionary = {}
var witness := false

func _ready() -> void:
    witness = "--route-witness" in OS.get_cmdline_user_args()
    add_theme_constant_override("separation", 16)
    var title := label("ROUTE FORK | CHOOSE YOUR EXPEDITION", 32)
    title.modulate = Color(0.98, 0.80, 0.45)
    status = label("", 24)
    map_label = label("", 22)
    encounter = label("", 24)
    forecast = label("", 18)
    forecast.custom_minimum_size.y = 58
    label("Both routes contain eight foes. Direct has fewer rooms; gradual splits the encounters.", 18)
    var combat := HBoxContainer.new()
    add_child(combat)
    for pair in [["attack","A  Attack"],["guard","G  Guard"],["advance","N  Continue"],["restart","R  Restart"]]:
        button(combat,pair[0],pair[1])
    var fork := HBoxContainer.new()
    add_child(fork)
    button(fork,"direct","1  DIRECT  |  1 > 3 > 4")
    button(fork,"gradual","2  GRADUAL  |  1 > 2 > 2 > 3")
    label("Read the next strike. Every third blow can be perfectly parried.", 16)
    rules = RouteRules.new()
    add_child(rules)
    rules.state_changed.connect(render)
    rules.reset_run()

func label(content: String, size: int) -> Label:
    var out := Label.new()
    out.text = content
    out.add_theme_font_size_override("font_size", size)
    out.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    add_child(out)
    return out

func button(parent: Control, action: String, caption: String) -> void:
    var b := Button.new()
    b.text = caption
    b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    b.pressed.connect(func(): dispatch(action))
    parent.add_child(b)
    buttons[action] = b

func observe() -> Dictionary:
    var enabled := {}
    for action in buttons:
        enabled[action] = not buttons[action].disabled
    return {"state":rules.snapshot(),"route":rules.route_id(),
            "status":status.text,"map":map_label.text,"encounter":encounter.text,
            "enabled":enabled}

func dispatch(action: String) -> bool:
    var accepted := false
    match action:
        "attack": accepted = rules.attack()
        "guard": accepted = rules.guard()
        "advance": accepted = rules.advance()
        "restart": accepted = rules.restart_run()
        "direct", "gradual": accepted = rules.choose_route(action)
    if witness:
        print("ROUTE_EVENT=" + JSON.stringify({"action":action,"accepted":accepted,"after":observe()}))
    return accepted

func _input(event: InputEvent) -> void:
    if not event is InputEventKey or not event.pressed or event.echo:
        return
    if event.keycode == KEY_ESCAPE:
        get_tree().quit()
        get_viewport().set_input_as_handled()
        return
    var action: String = {KEY_A:"attack",KEY_G:"guard",KEY_N:"advance",KEY_R:"restart",
        KEY_1:"direct",KEY_2:"gradual"}.get(event.keycode,"")
    if not action.is_empty():
        dispatch(action)
        get_viewport().set_input_as_handled()

func render(s: Dictionary) -> void:
    var route: String = rules.route_id()
    status.text = "ROOM %d/%s   |   HP %d   |   STAMINA %d   |   TURN %d" % [
        s.room, "?" if route == "undecided" else str(s.total_rooms),s.player_health,s.stamina,s.turn]
    if route == "undecided":
        map_label.text = "START [1]  >  FORK  >  DIRECT [3,4]  /  GRADUAL [2,2,3]"
    else:
        map_label.text = route.to_upper() + " ROUTE   |   " + str(rules.route_rooms(route))
    match s.phase:
        "fighting": encounter.text = "ENCOUNTER: %d foes   |   Enemy HP %d" % [s.foes,s.enemy_health]
        "cleared": encounter.text = "CHOOSE YOUR ROUTE" if rules.can_choose() else "ROOM CLEARED — Continue"
        "won": encounter.text = "VICTORY — Expedition complete"
        "lost": encounter.text = "DEFEAT — Restart to try again"
    var f: Dictionary = s.get("forecast",{})
    forecast.text = ""
    if not f.is_empty():
        forecast.text = "NEXT HIT %d%s  |  Attack costs %d stamina, risks %d HP  |  Guard restores %d, risks %d HP" % [
            f.threat_damage," (CHARGED)" if f.charged else "", f.attack_cost,
            f.attack_health_loss,f.guard_stamina_gain,f.guard_health_loss]
    buttons.attack.disabled = s.phase != "fighting" or s.stamina < s.attack_cost
    buttons.guard.disabled = s.phase != "fighting"
    buttons.advance.disabled = s.phase != "cleared" or rules.can_choose()
    buttons.direct.disabled = not rules.can_choose()
    buttons.gradual.disabled = not rules.can_choose()
    buttons.restart.disabled = false
