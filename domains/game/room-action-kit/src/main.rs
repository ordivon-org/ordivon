//! A playable R2.1 LEGO: player action -> opponent reaction -> terminal result.
//! Bevy supplies ECS; position, rule and chase strategy stay replaceable.
use bevy::prelude::*;
use std::io::{self, Write};

#[derive(Component)]
struct Player;
#[derive(Component)]
struct Enemy;
#[derive(Component, Clone, Copy, PartialEq, Eq, Debug)]
struct Cell {
    x: i32,
    y: i32,
}
impl Cell {
    fn distance(self, other: Self) -> i32 {
        (self.x - other.x).abs() + (self.y - other.y).abs()
    }
}
#[derive(Component)]
struct Health(i32);
// These disjoint ECS query shapes are the engine-native actor boundaries,
// not additional gameplay registries or runtime abstractions.
type EnemyHitQuery<'w, 's> =
    Query<'w, 's, (&'static Cell, &'static mut Health), (With<Enemy>, Without<Player>)>;
type HeroHpQuery<'w, 's> =
    Query<'w, 's, (&'static Cell, &'static mut Health), (With<Player>, Without<Enemy>)>;
type EnemyMoveQuery<'w, 's> =
    Query<'w, 's, (&'static mut Cell, &'static Health), (With<Enemy>, Without<Player>)>;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Command {
    North,
    West,
    South,
    East,
    Strike,
}
#[derive(Resource, Default)]
struct Requested(Option<Command>);
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Phase {
    Playing,
    Won,
    Lost,
}
#[derive(Resource)]
struct Round {
    turns: u32,
    advanced: bool,
    phase: Phase,
    message: &'static str,
}
impl Default for Round {
    fn default() -> Self {
        Self {
            turns: 0,
            advanced: false,
            phase: Phase::Playing,
            message: "Defeat both foes to clear the room.",
        }
    }
}
#[derive(Resource)]
struct Room {
    width: i32,
    height: i32,
    obstacles: Vec<Cell>,
}
impl Default for Room {
    fn default() -> Self {
        Self {
            width: 7,
            height: 5,
            obstacles: vec![Cell { x: 3, y: 1 }, Cell { x: 3, y: 3 }],
        }
    }
}
impl Room {
    fn walkable(&self, p: Cell) -> bool {
        p.x >= 0
            && p.x < self.width
            && p.y >= 0
            && p.y < self.height
            && !self.obstacles.contains(&p)
    }
}
fn player_action(
    mut requested: ResMut<Requested>,
    mut round: ResMut<Round>,
    room: Res<Room>,
    mut player: Query<&mut Cell, (With<Player>, Without<Enemy>)>,
    mut foes: EnemyHitQuery<'_, '_>,
) {
    round.advanced = false;
    let Some(command) = requested.0.take() else {
        return;
    };
    if round.phase != Phase::Playing {
        return;
    }
    let Ok(mut pos) = player.single_mut() else {
        return;
    };
    match command {
        Command::Strike => {
            let mut hit = false;
            for (ep, mut hp) in &mut foes {
                if hp.0 > 0 && pos.distance(*ep) == 1 {
                    hp.0 -= 1;
                    hit = true;
                }
            }
            round.message = if hit { "Hit!" } else { "No adjacent target." };
        }
        dir => {
            let (dx, dy) = match dir {
                Command::North => (0, -1),
                Command::West => (-1, 0),
                Command::South => (0, 1),
                Command::East => (1, 0),
                Command::Strike => unreachable!(),
            };
            let next = Cell {
                x: pos.x + dx,
                y: pos.y + dy,
            };
            if room.walkable(next) && !foes.iter().any(|(ep, hp)| hp.0 > 0 && *ep == next) {
                *pos = next;
                round.message = "Moved.";
            } else {
                round.message = "Blocked.";
            }
        }
    }
    round.turns += 1;
    round.advanced = true;
}
// A replaceable thinking LEGO: Manhattan one-step chase, no custom planner.
fn enemy_turn(
    round: Res<Round>,
    room: Res<Room>,
    mut hero: HeroHpQuery<'_, '_>,
    mut foes: EnemyMoveQuery<'_, '_>,
) {
    if !round.advanced || round.phase != Phase::Playing {
        return;
    }
    let Ok((hero_pos, mut hero_hp)) = hero.single_mut() else {
        return;
    };
    let target = *hero_pos;
    let mut occupied: Vec<Cell> = foes
        .iter()
        .filter(|(_, hp)| hp.0 > 0)
        .map(|(p, _)| *p)
        .collect();
    for (mut pos, hp) in &mut foes {
        if hp.0 <= 0 || hero_hp.0 <= 0 {
            continue;
        }
        if pos.distance(target) == 1 {
            hero_hp.0 -= 1;
            continue;
        }
        let old = *pos;
        let dx = (target.x - old.x).signum();
        let dy = (target.y - old.y).signum();
        let moves = [
            Cell {
                x: old.x + dx,
                y: old.y,
            },
            Cell {
                x: old.x,
                y: old.y + dy,
            },
        ];
        for next in moves {
            if next != old && next != target && room.walkable(next) && !occupied.contains(&next) {
                if let Some(entry) = occupied.iter_mut().find(|p| **p == old) {
                    *entry = next;
                }
                *pos = next;
                break;
            }
        }
    }
}
fn decide_outcome(
    mut round: ResMut<Round>,
    hero: Query<&Health, With<Player>>,
    foes: Query<&Health, With<Enemy>>,
) {
    if round.phase != Phase::Playing || !round.advanced {
        return;
    }
    if hero.single().is_ok_and(|hp| hp.0 <= 0) {
        round.phase = Phase::Lost;
        round.message = "Defeated. r restarts.";
    } else if foes.iter().all(|hp| hp.0 <= 0) {
        round.phase = Phase::Won;
        round.message = "Room cleared! r replays.";
    }
}
fn new_game() -> App {
    let mut app = App::new();
    app.insert_resource(Room::default());
    app.init_resource::<Requested>();
    app.init_resource::<Round>();
    app.world_mut()
        .spawn((Player, Cell { x: 1, y: 2 }, Health(5)));
    app.world_mut()
        .spawn((Enemy, Cell { x: 5, y: 2 }, Health(1)));
    app.world_mut()
        .spawn((Enemy, Cell { x: 5, y: 3 }, Health(1)));
    app.add_systems(Update, (player_action, enemy_turn, decide_outcome).chain());
    app
}
fn advance(app: &mut App, command: Command) {
    app.world_mut().resource_mut::<Requested>().0 = Some(command);
    app.update();
}
fn snapshot(app: &mut App) -> String {
    let (width, height, obstacles) = {
        let room = app.world().resource::<Room>();
        (room.width, room.height, room.obstacles.clone())
    };
    let mut cells = vec![vec!['.'; width as usize]; height as usize];
    for p in obstacles {
        cells[p.y as usize][p.x as usize] = '#';
    }
    let mut heroes = app
        .world_mut()
        .query_filtered::<(&Cell, &Health), With<Player>>();
    let hp = heroes
        .iter(app.world())
        .map(|(p, hp)| {
            cells[p.y as usize][p.x as usize] = '@';
            hp.0
        })
        .next()
        .unwrap_or(0);
    let mut enemies = app
        .world_mut()
        .query_filtered::<(&Cell, &Health), With<Enemy>>();
    let mut alive = 0;
    for (p, hp) in enemies.iter(app.world()) {
        if hp.0 > 0 {
            cells[p.y as usize][p.x as usize] = 'e';
            alive += 1;
        }
    }
    let mut result = String::new();
    for row in cells {
        result.push_str(&row.iter().collect::<String>());
        result.push('\n');
    }
    let round = app.world().resource::<Round>();
    result.push_str(&format!(
        "Turn {} | HP {} | Enemies {} | {:?}\n{}\n",
        round.turns, hp, alive, round.phase, round.message
    ));
    result
}
fn parse_command(raw: &str) -> Option<Command> {
    match raw.trim().to_lowercase().as_str() {
        "w" => Some(Command::North),
        "a" => Some(Command::West),
        "s" => Some(Command::South),
        "d" => Some(Command::East),
        "f" => Some(Command::Strike),
        _ => None,
    }
}
fn main() {
    let demo = std::env::args().any(|arg| arg == "--demo");
    let mut app = new_game();
    println!("ROOM ACTION | Bevy ECS | @ player, e foe, # wall");
    println!("w/a/s/d move, f strike, r restart, q quit");
    println!("{}", snapshot(&mut app));
    if demo {
        for key in "ddfffdfff".chars() {
            let command = parse_command(&key.to_string()).unwrap();
            advance(&mut app, command);
            println!("> {}\n{}", key, snapshot(&mut app));
            if app.world().resource::<Round>().phase != Phase::Playing {
                break;
            }
        }
        return;
    }
    let mut line = String::new();
    loop {
        line.clear();
        print!("command> ");
        if io::stdout().flush().is_err() || io::stdin().read_line(&mut line).unwrap_or(0) == 0 {
            break;
        }
        match line.trim().to_lowercase().as_str() {
            "q" => break,
            "r" => app = new_game(),
            raw => {
                if let Some(cmd) = parse_command(raw) {
                    advance(&mut app, cmd);
                } else {
                    println!("Use w/a/s/d, f, r, q.");
                }
            }
        }
        println!("{}", snapshot(&mut app));
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    fn phase(app: &App) -> Phase {
        app.world().resource::<Round>().phase
    }
    #[test]
    fn unrequested_update_is_not_a_player_turn() {
        let mut app = new_game();
        app.update();
        assert_eq!(app.world().resource::<Round>().turns, 0);
    }
    #[test]
    fn movement_never_leaves_room() {
        let mut app = new_game();
        for _ in 0..10 {
            advance(&mut app, Command::West);
        }
        let mut q = app.world_mut().query_filtered::<&Cell, With<Player>>();
        assert_eq!(q.single(app.world()).unwrap().x, 0);
    }
    #[test]
    fn distant_attack_does_not_kill_enemy() {
        let mut app = new_game();
        advance(&mut app, Command::Strike);
        let mut q = app.world_mut().query_filtered::<&Health, With<Enemy>>();
        assert_eq!(q.iter(app.world()).filter(|hp| hp.0 > 0).count(), 2);
    }
    #[test]
    fn victory_and_defeat_are_both_reachable_and_terminal() {
        let mut won = new_game();
        for _ in 0..40 {
            advance(&mut won, Command::Strike);
            if phase(&won) != Phase::Playing {
                break;
            }
        }
        assert_eq!(phase(&won), Phase::Won);
        let won_turns = won.world().resource::<Round>().turns;
        advance(&mut won, Command::Strike);
        assert_eq!(won.world().resource::<Round>().turns, won_turns);
        let mut lost = new_game();
        for _ in 0..40 {
            advance(&mut lost, Command::West);
            if phase(&lost) != Phase::Playing {
                break;
            }
        }
        assert_eq!(phase(&lost), Phase::Lost);
        let lost_turns = lost.world().resource::<Round>().turns;
        advance(&mut lost, Command::East);
        assert_eq!(lost.world().resource::<Round>().turns, lost_turns);
    }
    #[test]
    fn input_has_five_commands_no_implicit_replay() {
        assert_eq!(
            ["w", "a", "s", "d", "f"]
                .iter()
                .filter(|c| parse_command(c).is_some())
                .count(),
            5
        );
        for text in ["q", "r", "z", "?"] {
            assert_eq!(parse_command(text), None);
        }
    }
    #[test]
    fn finite_four_turn_alphabet_never_violates_room_invariants() {
        // Exhaust all 1 + 5 + 25 + 125 + 625 = 781 typed action sequences.
        // This is bounded implementation testing, NOT a general Rust proof.
        let alphabet = [
            Command::North,
            Command::West,
            Command::South,
            Command::East,
            Command::Strike,
        ];
        let mut explored = 0;
        for length in 0..=4u32 {
            for mut index in 0..5usize.pow(length) {
                let mut app = new_game();
                explored += 1;
                for _ in 0..length {
                    let cmd = alphabet[index % alphabet.len()];
                    index /= alphabet.len();
                    advance(&mut app, cmd);
                    let mut hero = app
                        .world_mut()
                        .query_filtered::<(&Cell, &Health), With<Player>>();
                    let (hero_pos, hp) = {
                        let (pos, hp) = hero.single(app.world()).unwrap();
                        (*pos, hp.0)
                    };
                    assert!(app.world().resource::<Room>().walkable(hero_pos));
                    assert!(hp >= 0);
                    let mut enemy_query = app
                        .world_mut()
                        .query_filtered::<(&Cell, &Health), With<Enemy>>();
                    let living: Vec<Cell> = enemy_query
                        .iter(app.world())
                        .filter(|(_, hp)| hp.0 > 0)
                        .map(|(p, _)| *p)
                        .collect();
                    for pos in &living {
                        assert!(app.world().resource::<Room>().walkable(*pos));
                        assert_ne!(*pos, hero_pos);
                    }
                    for (i, first) in living.iter().enumerate() {
                        assert!(!living[i + 1..].contains(first));
                    }
                    let phase = app.world().resource::<Round>().phase;
                    if phase == Phase::Won {
                        assert!(living.is_empty());
                    }
                    if phase == Phase::Lost {
                        assert_eq!(hp, 0);
                    }
                }
            }
        }
        assert_eq!(explored, 781);
    }
}
