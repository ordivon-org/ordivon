use bevy::{prelude::*, window::WindowResolution};
use ordivon_room_action::{DashState, EnemyBehavior, LegoPalette, Phase, Run, compose_game};
use std::collections::HashSet;

const SPEED: f32 = 270.0;
const LEFT_EDGE: f32 = -440.0;
const RIGHT_EDGE: f32 = 435.0;
const BOTTOM_EDGE: f32 = -255.0;
const TOP_EDGE: f32 = 255.0;

#[derive(Resource)]
struct Session(Run);

#[derive(Resource, Default)]
struct FireDelay(f32);

#[derive(Resource, Default)]
struct TouchDelay(f32);

#[derive(Resource, Default)]
struct DashClock(DashState);

#[derive(Component)]
struct GameObject;

#[derive(Component)]
struct Hero;

#[derive(Component)]
struct Gate;

#[derive(Component)]
struct Foe {
    health: i32,
    speed: u16,
    behavior: EnemyBehavior,
}

#[derive(Component)]
struct Shot {
    speed: Vec2,
    ttl: f32,
    damage: i32,
    pierces_left: u8,
    hit_targets: Vec<Entity>,
}

/// Standard JSON interchange, same native Bevy consumer, no duplicate gameplay backend.
fn load_json<T: serde::de::DeserializeOwned>(path: &str) -> Result<T, String> {
    use std::io::Read;
    const MAX_RECIPE_BYTES: u64 = 1024 * 1024;
    let file = std::fs::File::open(path).map_err(|e| format!("cannot open {path}: {e}"))?;
    let mut bytes = Vec::new();
    file.take(MAX_RECIPE_BYTES + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| format!("cannot read {path}: {e}"))?;
    if bytes.len() as u64 > MAX_RECIPE_BYTES {
        return Err(format!("JSON input {path} exceeds 1 MiB"));
    }
    serde_json::from_slice(&bytes).map_err(|e| format!("invalid JSON in {path}: {e}"))
}

/// Parse a finite CLI into the existing validated Run. No window or engine
/// work is performed here, so agents can inspect and test the seam headlessly.
fn run_from_args(args: &[String]) -> Result<Run, String> {
    if args.is_empty() {
        return Ok(Run::default());
    }
    if !args.len().is_multiple_of(2) || args.len() > 6 {
        return Err("usage: [--seed N] [--rooms N] [--palette FILE] | --recipe FILE".into());
    }
    let mut seed = None;
    let mut room_count = None;
    let mut palette_path = None;
    let mut recipe_path = None;
    for pair in args.as_chunks::<2>().0 {
        match pair[0].as_str() {
            "--seed" if seed.is_none() => {
                seed = Some(
                    pair[1]
                        .parse::<u64>()
                        .map_err(|_| "invalid seed; expected unsigned integer".to_string())?,
                );
            }
            "--rooms" if room_count.is_none() => {
                room_count = Some(
                    pair[1]
                        .parse::<usize>()
                        .map_err(|_| "invalid room count".to_string())?,
                );
            }
            "--palette" if palette_path.is_none() => palette_path = Some(pair[1].as_str()),
            "--recipe" if recipe_path.is_none() => recipe_path = Some(pair[1].as_str()),
            _ => return Err(format!("invalid or duplicate flag: {}", pair[0])),
        }
    }
    if let Some(path) = recipe_path {
        if seed.is_some() || room_count.is_some() || palette_path.is_some() {
            return Err("--recipe cannot be combined with generation flags".into());
        }
        let config: ordivon_room_action::GameConfig = load_json(path)?;
        return Run::with_config(config).map_err(str::to_string);
    }
    if seed.is_none() {
        return Err("--rooms and --palette require --seed".into());
    }
    let palette = match palette_path {
        Some(path) => load_json(path)?,
        None => LegoPalette::default(),
    };
    let config =
        compose_game(seed.unwrap(), room_count.unwrap_or(4), &palette).map_err(str::to_string)?;
    Run::with_config(config).map_err(str::to_string)
}

fn main() {
    let mut args: Vec<String> = std::env::args().skip(1).collect();
    if args == ["--help"] {
        println!(
            "Room Action Kit (Bevy)\n  --seed N [--rooms 1..32] [--palette FILE] [--json]\n  --recipe FILE [--json]\n  --palette-json (print default catalog)\n  --json (print validated GameConfig without opening a window)\nNo flags: original two-room game"
        );
        return;
    }
    if args == ["--palette-json"] {
        let text = serde_json::to_string_pretty(&LegoPalette::default())
            .expect("built-in catalog is serializable");
        println!("{text}");
        return;
    }
    let json = if let Some(index) = args.iter().position(|arg| arg == "--json") {
        args.remove(index);
        true
    } else {
        false
    };
    let run = run_from_args(&args).unwrap_or_else(|error| {
        eprintln!("Invalid room-action recipe: {error}");
        std::process::exit(2);
    });
    if json {
        let text = serde_json::to_string_pretty(run.config())
            .expect("validated game recipe is serializable");
        println!("{text}");
        return;
    }
    App::new()
        .add_plugins(DefaultPlugins.set(WindowPlugin {
            primary_window: Some(Window {
                title: "Room Action Kit — WASD move / Mouse aim + LMB fire / R restart".into(),
                resolution: WindowResolution::new(960, 600),
                ..default()
            }),
            ..default()
        }))
        .insert_resource(ClearColor(Color::srgb(0.045, 0.055, 0.075)))
        .insert_resource(Session(run))
        .init_resource::<FireDelay>()
        .init_resource::<TouchDelay>()
        .init_resource::<DashClock>()
        .add_systems(Startup, setup)
        .add_systems(
            Update,
            (
                restart,
                move_player,
                move_enemies,
                tick_fire_delay,
                fire_shots,
                move_shots,
                resolve_hits,
                spawn_reinforcements,
                resolve_contact,
                traverse_gate,
                update_gate,
            )
                .chain(),
        )
        .run();
}

fn setup(mut commands: Commands, session: Res<Session>) {
    commands.spawn(Camera2d);
    for (position, size) in [
        (Vec2::new(0.0, -270.0), Vec2::new(920.0, 16.0)),
        (Vec2::new(0.0, 270.0), Vec2::new(920.0, 16.0)),
        (Vec2::new(-452.0, 0.0), Vec2::new(16.0, 556.0)),
        (Vec2::new(452.0, 0.0), Vec2::new(16.0, 556.0)),
    ] {
        commands.spawn((
            Sprite::from_color(Color::srgb(0.2, 0.23, 0.30), size),
            Transform::from_translation(position.extend(0.0)),
        ));
    }
    spawn_level(&mut commands, &session.0);
}

fn spawn_level(commands: &mut Commands, run: &Run) {
    commands.spawn((
        GameObject,
        Hero,
        Sprite::from_color(Color::srgb(0.25, 0.8, 1.0), Vec2::splat(28.0)),
        Transform::from_xyz(-340.0, 0.0, 1.0),
    ));
    commands.spawn((
        GameObject,
        Gate,
        Sprite::from_color(Color::srgb(0.9, 0.2, 0.2), Vec2::new(22.0, 108.0)),
        Transform::from_xyz(405.0, 0.0, 0.5),
    ));
    spawn_enemies(commands, run);
}

fn spawn_enemies(commands: &mut Commands, run: &Run) {
    for spec in run.current_wave_enemies() {
        commands.spawn((
            GameObject,
            Foe {
                health: spec.health,
                speed: spec.speed,
                behavior: spec.behavior,
            },
            Sprite::from_color(Color::srgb(1.0, 0.43, 0.24), Vec2::splat(30.0)),
            Transform::from_xyz(spec.x as f32, spec.y as f32, 1.0),
        ));
    }
}

fn restart(
    keys: Res<ButtonInput<KeyCode>>,
    mut commands: Commands,
    mut session: ResMut<Session>,
    objects: Query<Entity, With<GameObject>>,
    mut fire_delay: ResMut<FireDelay>,
    mut touch_delay: ResMut<TouchDelay>,
    mut dash: ResMut<DashClock>,
) {
    if !keys.just_pressed(KeyCode::KeyR)
        || !matches!(session.0.phase, Phase::Defeat | Phase::Victory)
    {
        return;
    }
    for entity in &objects {
        commands.entity(entity).despawn();
    }
    session.0.restart();
    fire_delay.0 = 0.0;
    touch_delay.0 = 0.0;
    dash.0 = DashState::default();
    spawn_level(&mut commands, &session.0);
}

fn move_player(
    keys: Res<ButtonInput<KeyCode>>,
    time: Res<Time>,
    session: Res<Session>,
    mut hero: Single<&mut Transform, With<Hero>>,
    mut dash: ResMut<DashClock>,
) {
    let elapsed_ms = (time.delta_secs() * 1000.0).round().max(0.0) as u32;
    dash.0.tick(elapsed_ms);
    if !session.0.can_act() {
        return;
    }
    let mut dir = Vec2::ZERO;
    if keys.pressed(KeyCode::KeyW) {
        dir.y += 1.0;
    }
    if keys.pressed(KeyCode::KeyS) {
        dir.y -= 1.0;
    }
    if keys.pressed(KeyCode::KeyA) {
        dir.x -= 1.0;
    }
    if keys.pressed(KeyCode::KeyD) {
        dir.x += 1.0;
    }
    if let Some(unit) = dir.try_normalize() {
        let mut speed = SPEED;
        if let Some(spec) = session.0.config().dash.as_ref() {
            if keys.just_pressed(KeyCode::Space) {
                dash.0.try_start(spec);
            }
            if dash.0.active() {
                speed = f32::from(spec.speed);
            }
        }
        hero.translation += (unit * speed * time.delta_secs()).extend(0.0);
    }
    hero.translation.x = hero.translation.x.clamp(LEFT_EDGE, RIGHT_EDGE);
    hero.translation.y = hero.translation.y.clamp(BOTTOM_EDGE, TOP_EDGE);
}

fn move_enemies(
    time: Res<Time>,
    session: Res<Session>,
    hero: Single<&Transform, With<Hero>>,
    mut foes: Query<(&Foe, &mut Transform), Without<Hero>>,
) {
    if !session.0.can_act() {
        return;
    }
    for (foe, mut transform) in &mut foes {
        let toward = hero.translation.xy() - transform.translation.xy();
        let sign = foe.behavior.movement_sign(toward.length());
        if sign == 0.0 {
            continue;
        }
        let unit = toward.try_normalize().unwrap_or(Vec2::NEG_X);
        transform.translation +=
            (unit * sign * f32::from(foe.speed) * time.delta_secs()).extend(0.0);
    }
}

fn tick_fire_delay(time: Res<Time>, mut delay: ResMut<FireDelay>) {
    delay.0 = (delay.0 - time.delta_secs()).max(0.0);
}

fn fire_shots(
    mut commands: Commands,
    session: Res<Session>,
    mouse: Res<ButtonInput<MouseButton>>,
    window: Single<&Window>,
    camera: Single<(&Camera, &GlobalTransform)>,
    hero: Single<&Transform, With<Hero>>,
    mut delay: ResMut<FireDelay>,
) {
    if !session.0.can_act() || !mouse.pressed(MouseButton::Left) || delay.0 > 0.0 {
        return;
    }
    let (camera, global) = *camera;
    let Some(cursor) = window.cursor_position() else {
        return;
    };
    let Ok(world) = camera.viewport_to_world_2d(global, cursor) else {
        return;
    };
    let Some(direction) = (world - hero.translation.xy()).try_normalize() else {
        return;
    };
    spawn_shot_pattern(&mut commands, hero.translation.xy(), direction, &session.0);
    delay.0 = f32::from(session.0.config().weapon.cooldown_ms) / 1000.0;
}

/// Native ECS adapter consuming one typed weapon recipe.
fn spawn_shot_pattern(commands: &mut Commands, origin: Vec2, aim: Vec2, run: &Run) {
    let spec = &run.config().weapon;
    let count = usize::from(spec.pellets);
    let step = if count > 1 {
        f32::from(spec.spread_degrees) / (count - 1) as f32
    } else {
        0.0
    };
    for index in 0..count {
        let degrees = if count == 1 {
            0.0
        } else {
            -f32::from(spec.spread_degrees) / 2.0 + index as f32 * step
        };
        let angle = degrees.to_radians();
        let direction = Vec2::new(
            aim.x * angle.cos() - aim.y * angle.sin(),
            aim.x * angle.sin() + aim.y * angle.cos(),
        );
        commands.spawn((
            GameObject,
            Shot {
                speed: direction * f32::from(spec.projectile_speed),
                ttl: 1.5,
                damage: run.weapon_damage(),
                pierces_left: spec.pierce,
                hit_targets: vec![],
            },
            Sprite::from_color(Color::srgb(0.4, 1.0, 0.9), Vec2::splat(10.0)),
            Transform::from_translation((origin + direction * 20.0).extend(2.0)),
        ));
    }
}

fn move_shots(
    mut commands: Commands,
    time: Res<Time>,
    mut shots: Query<(Entity, &mut Transform, &mut Shot)>,
) {
    for (entity, mut transform, mut shot) in &mut shots {
        transform.translation += (shot.speed * time.delta_secs()).extend(0.0);
        shot.ttl -= time.delta_secs();
        if shot.ttl <= 0.0 {
            commands.entity(entity).despawn();
        }
    }
}

fn resolve_hits(
    mut commands: Commands,
    mut session: ResMut<Session>,
    mut shots: Query<(Entity, &Transform, &mut Shot)>,
    mut foes: Query<(Entity, &Transform, &mut Foe), Without<Shot>>,
) {
    if !matches!(session.0.phase, Phase::Fighting | Phase::GateOpen) {
        return;
    }
    let living_before_hits = foes.iter_mut().count() as u32;
    let mut dead = HashSet::new();
    for (shot_entity, shot_transform, mut shot) in &mut shots {
        for (foe_entity, foe_transform, mut foe) in &mut foes {
            if dead.contains(&foe_entity) || shot.hit_targets.contains(&foe_entity) {
                continue;
            }
            if shot_transform
                .translation
                .xy()
                .distance_squared(foe_transform.translation.xy())
                > 20.0_f32.powi(2)
            {
                continue;
            }
            shot.hit_targets.push(foe_entity);
            foe.health = foe.health.saturating_sub(shot.damage);
            if foe.health <= 0 {
                dead.insert(foe_entity);
                commands.entity(foe_entity).despawn();
            }
            if shot.pierces_left == 0 {
                commands.entity(shot_entity).despawn();
                break;
            }
            shot.pierces_left -= 1;
        }
    }
    session
        .0
        .reconcile_living_enemies(living_before_hits.saturating_sub(dead.len() as u32));
}

/// Never open a room gate between waves; the last spawned foe is the authority.
fn spawn_reinforcements(mut commands: Commands, mut session: ResMut<Session>) {
    if session.0.advance_wave() {
        spawn_enemies(&mut commands, &session.0);
    }
}

fn resolve_contact(
    mut session: ResMut<Session>,
    time: Res<Time>,
    hero: Single<&Transform, With<Hero>>,
    foes: Query<&Transform, With<Foe>>,
    mut cooldown: ResMut<TouchDelay>,
) {
    let run = &mut session.0;
    cooldown.0 = (cooldown.0 - time.delta_secs()).max(0.0);
    if cooldown.0 > 0.0 || !run.can_act() {
        return;
    }
    if foes
        .iter()
        .any(|foe| foe.translation.xy().distance_squared(hero.translation.xy()) < 25.0_f32.powi(2))
    {
        run.take_hit();
        cooldown.0 = 0.75;
    }
}

fn traverse_gate(
    mut commands: Commands,
    mut session: ResMut<Session>,
    mut hero: Single<&mut Transform, With<Hero>>,
    foes: Query<Entity, With<Foe>>,
    shots: Query<Entity, With<Shot>>,
) {
    if session.0.phase != Phase::GateOpen || hero.translation.x < 370.0 {
        return;
    }
    for entity in &foes {
        commands.entity(entity).despawn();
    }
    for entity in &shots {
        commands.entity(entity).despawn();
    }
    session.0.enter_gate();
    hero.translation.x = -340.0;
    hero.translation.y = 0.0;
    if session.0.phase == Phase::Fighting {
        spawn_enemies(&mut commands, &session.0);
    }
}

fn update_gate(
    session: Res<Session>,
    mut gate: Single<&mut Sprite, With<Gate>>,
    mut hero: Single<&mut Sprite, (With<Hero>, Without<Gate>)>,
) {
    gate.color = match session.0.phase {
        Phase::Fighting => Color::srgb(0.9, 0.2, 0.2),
        Phase::GateOpen => Color::srgb(0.2, 0.95, 0.4),
        Phase::Victory => Color::srgb(0.3, 0.5, 1.0),
        Phase::Defeat => Color::srgb(0.5, 0.1, 0.1),
    };
    if session.0.phase == Phase::Defeat {
        hero.color = Color::srgb(0.4, 0.4, 0.4);
    }
}

#[cfg(test)]
mod consumer_tests {
    use super::*;

    fn headless_room() -> App {
        let mut app = App::new();
        app.insert_resource(Session(Run::default()))
            .add_systems(Update, (resolve_hits, traverse_gate).chain());
        app.world_mut()
            .spawn((Hero, Transform::from_xyz(-340.0, 0.0, 0.0)));
        for x in [80.0, 160.0] {
            app.world_mut().spawn((
                Foe {
                    health: 1,
                    speed: 78,
                    behavior: EnemyBehavior::Chase,
                },
                Transform::from_xyz(x, 0.0, 0.0),
            ));
        }
        app
    }

    fn shoot_at(app: &mut App, x: f32, y: f32) {
        let damage = app.world().resource::<Session>().0.weapon_damage();
        app.world_mut().spawn((
            Shot {
                speed: Vec2::ZERO,
                ttl: 1.0,
                damage,
                pierces_left: 0,
                hit_targets: vec![],
            },
            Transform::from_xyz(x, y, 0.0),
        ));
        app.update();
    }

    #[test]
    fn bevy_consumer_golden_path_shoot_clear_gate_reward_second_room_win() {
        let mut app = headless_room();
        assert_eq!(app.world().resource::<Session>().0.phase, Phase::Fighting);
        shoot_at(&mut app, 80.0, 0.0);
        assert_eq!(app.world().resource::<Session>().0.remaining, 1);
        shoot_at(&mut app, 160.0, 0.0);
        assert_eq!(app.world().resource::<Session>().0.phase, Phase::GateOpen);

        {
            let mut query = app
                .world_mut()
                .query_filtered::<&mut Transform, With<Hero>>();
            query.single_mut(app.world_mut()).unwrap().translation.x = 390.0;
        }
        app.update();
        let run = &app.world().resource::<Session>().0;
        assert_eq!((run.room, run.remaining, run.attack), (1, 3, 2));
        let enemies: usize = {
            let world = app.world_mut();
            let mut query = world.query::<&Foe>();
            query.iter(world).count()
        };
        assert_eq!(enemies, 3);

        // Room two's weapon upgrade must be consumed by the real ECS hit system.
        for (x, y) in [(115.0, 120.0), (180.0, -115.0), (20.0, -25.0)] {
            shoot_at(&mut app, x, y);
        }
        assert_eq!(app.world().resource::<Session>().0.phase, Phase::GateOpen);
        {
            let mut query = app
                .world_mut()
                .query_filtered::<&mut Transform, With<Hero>>();
            query.single_mut(app.world_mut()).unwrap().translation.x = 390.0;
        }
        app.update();
        assert_eq!(app.world().resource::<Session>().0.phase, Phase::Victory);
    }

    #[test]
    fn room_recipe_configures_real_bevy_entities_and_replaces_rewards() {
        use ordivon_room_action::{EnemySpec, GameConfig, Reward, RoomSpec};
        let config = GameConfig {
            max_health: 7,
            initial_attack: 4,
            weapon: ordivon_room_action::WeaponSpec::default(),
            dash: None,
            rooms: vec![
                RoomSpec {
                    reinforcement_waves: vec![],
                    enemies: vec![EnemySpec {
                        x: 91,
                        y: 42,
                        health: 4,

                        speed: 78,
                        behavior: EnemyBehavior::Chase,
                    }],
                    exit_reward: Reward {
                        attack: 3,
                        healing: 2,
                    },
                },
                RoomSpec {
                    reinforcement_waves: vec![],
                    enemies: vec![EnemySpec {
                        x: -50,
                        y: -60,
                        health: 6,

                        speed: 78,
                        behavior: EnemyBehavior::Chase,
                    }],
                    exit_reward: Reward::default(),
                },
            ],
        };
        let mut app = App::new();
        app.insert_resource(Session(Run::with_config(config).unwrap()))
            .add_systems(Startup, setup)
            .add_systems(Update, (resolve_hits, traverse_gate).chain());
        app.update();
        {
            let world = app.world_mut();
            let mut foes = world.query::<(&Foe, &Transform)>();
            let spawned: Vec<_> = foes
                .iter(world)
                .map(|(foe, at)| (foe.health, at.translation.xy()))
                .collect();
            assert_eq!(spawned, vec![(4, Vec2::new(91.0, 42.0))]);
        }
        shoot_at(&mut app, 91.0, 42.0);
        assert_eq!(app.world().resource::<Session>().0.phase, Phase::GateOpen);
        {
            let mut hero = app
                .world_mut()
                .query_filtered::<&mut Transform, With<Hero>>();
            hero.single_mut(app.world_mut()).unwrap().translation.x = 390.0;
        }
        app.update();
        assert_eq!(app.world().resource::<Session>().0.attack, 7);
        {
            let world = app.world_mut();
            let mut foes = world.query::<(&Foe, &Transform)>();
            let spawned: Vec<_> = foes
                .iter(world)
                .map(|(foe, at)| (foe.health, at.translation.xy()))
                .collect();
            assert_eq!(spawned, vec![(6, Vec2::new(-50.0, -60.0))]);
        }
    }

    #[test]
    fn weapon_recipe_pierce_reaches_actual_spawned_projectiles() {
        let mut config = ordivon_room_action::GameConfig::default();
        config.weapon.pierce = 2;
        let mut app = App::new();
        app.insert_resource(Session(Run::with_config(config).unwrap()))
            .add_systems(Update, |mut commands: Commands, session: Res<Session>| {
                spawn_shot_pattern(&mut commands, Vec2::ZERO, Vec2::X, &session.0);
            });
        app.update();
        let world = app.world_mut();
        let mut query = world.query::<&Shot>();
        let shots: Vec<_> = query.iter(world).collect();
        assert_eq!(shots.len(), 1);
        assert_eq!(shots[0].pierces_left, 2);
        assert!(shots[0].hit_targets.is_empty());
    }

    #[test]
    fn configured_piercing_shot_hits_two_foes_once_each_then_is_spent() {
        let mut app = headless_room();
        app.world_mut().spawn((
            Shot {
                speed: Vec2::ZERO,
                ttl: 1.0,
                damage: 1,
                pierces_left: 1,
                hit_targets: vec![],
            },
            Transform::from_xyz(80.0, 0.0, 0.0),
        ));
        // Put both foes at the exact same collision position.
        {
            let world = app.world_mut();
            let mut query = world.query_filtered::<&mut Transform, With<Foe>>();
            for mut foe in query.iter_mut(world) {
                foe.translation.x = 80.0;
            }
        }
        app.update();
        assert_eq!(app.world().resource::<Session>().0.phase, Phase::GateOpen);
        let world = app.world_mut();
        let mut q = world.query::<&Shot>();
        assert_eq!(q.iter(world).count(), 0, "shot exhausted after two targets");
    }

    #[test]
    fn piercing_projectile_does_not_hit_same_living_foe_again_next_frame() {
        let mut app = headless_room();
        {
            let world = app.world_mut();
            let mut q = world.query::<(&mut Foe, &mut Transform)>();
            for (mut foe, mut pos) in q.iter_mut(world) {
                if pos.translation.x == 80.0 {
                    foe.health = 5;
                } else {
                    pos.translation.x = 340.0;
                }
            }
        }
        app.world_mut().spawn((
            Shot {
                speed: Vec2::ZERO,
                ttl: 1.0,
                damage: 1,
                pierces_left: 2,
                hit_targets: vec![],
            },
            Transform::from_xyz(80.0, 0.0, 0.0),
        ));
        app.update();
        app.update();
        let world = app.world_mut();
        let mut q = world.query::<(&Foe, &Transform)>();
        let health = q
            .iter(world)
            .find(|(_, pos)| pos.translation.x == 80.0)
            .unwrap()
            .0
            .health;
        assert_eq!(
            health, 4,
            "one projectile must not apply damage twice to same enemy"
        );
    }

    #[test]
    fn concurrent_projectiles_can_kill_one_enemy_only_once() {
        let mut app = headless_room();
        for _ in 0..4 {
            app.world_mut().spawn((
                Shot {
                    speed: Vec2::ZERO,
                    ttl: 1.0,
                    damage: 1,
                    pierces_left: 0,
                    hit_targets: vec![],
                },
                Transform::from_xyz(80.0, 0.0, 0.0),
            ));
        }
        app.update();
        assert_eq!(app.world().resource::<Session>().0.remaining, 1);
        assert_eq!(app.world().resource::<Session>().0.phase, Phase::Fighting);
    }

    fn room_snapshot(app: &mut App) -> (Run, usize) {
        let state = app.world().resource::<Session>().0.clone();
        let world = app.world_mut();
        let mut foes = world.query::<&Foe>();
        (state, foes.iter(world).count())
    }

    fn scripted_room_trajectory() -> Vec<(Run, usize)> {
        let mut app = headless_room();
        let mut trace = vec![room_snapshot(&mut app)];
        shoot_at(&mut app, 80.0, 0.0);
        trace.push(room_snapshot(&mut app));
        shoot_at(&mut app, 160.0, 0.0);
        trace.push(room_snapshot(&mut app));
        {
            let mut query = app
                .world_mut()
                .query_filtered::<&mut Transform, With<Hero>>();
            query.single_mut(app.world_mut()).unwrap().translation.x = 390.0;
        }
        app.update();
        trace.push(room_snapshot(&mut app));
        for (x, y) in [(115.0, 120.0), (180.0, -115.0), (20.0, -25.0)] {
            shoot_at(&mut app, x, y);
            trace.push(room_snapshot(&mut app));
        }
        {
            let mut query = app
                .world_mut()
                .query_filtered::<&mut Transform, With<Hero>>();
            query.single_mut(app.world_mut()).unwrap().translation.x = 390.0;
        }
        app.update();
        trace.push(room_snapshot(&mut app));
        trace
    }

    #[test]
    fn scripted_ecs_trajectory_replays_to_identical_state_at_every_step() {
        let first = scripted_room_trajectory();
        let replay = scripted_room_trajectory();
        assert_eq!(first, replay);
        assert_eq!(first[0].0.phase, Phase::Fighting);
        assert_eq!(first[2].0.phase, Phase::GateOpen);
        assert_eq!(first[3].0.room, 1);
        assert_eq!(first[3].1, 3);
        assert_eq!(first.last().unwrap().0.phase, Phase::Victory);
        assert_eq!(first.last().unwrap().1, 0);
    }

    #[test]
    fn injected_additional_enemy_must_not_allow_premature_gate_clear() {
        let mut app = headless_room();
        // Fault injection: another legitimate enemy exists when the encounter ends.
        app.world_mut().spawn((
            Foe {
                health: 1,
                speed: 78,
                behavior: EnemyBehavior::Chase,
            },
            Transform::from_xyz(230.0, 0.0, 0.0),
        ));
        shoot_at(&mut app, 80.0, 0.0);
        shoot_at(&mut app, 160.0, 0.0);
        assert_eq!(
            app.world().resource::<Session>().0.phase,
            Phase::Fighting,
            "room must not open while a live enemy still exists"
        );
        shoot_at(&mut app, 230.0, 0.0);
        assert_eq!(app.world().resource::<Session>().0.phase, Phase::GateOpen);
    }
    #[test]
    fn weapon_recipe_spawns_real_bevy_three_pellet_spread_and_damage() {
        use ordivon_room_action::WeaponSpec;
        let config = ordivon_room_action::GameConfig {
            weapon: WeaponSpec {
                damage: 3,
                cooldown_ms: 120,
                projectile_speed: 420,
                pellets: 3,
                spread_degrees: 30,
                pierce: 0,
            },
            ..ordivon_room_action::GameConfig::default()
        };
        let mut app = App::new();
        app.insert_resource(Session(Run::with_config(config).unwrap()))
            .add_systems(Update, |mut commands: Commands, session: Res<Session>| {
                spawn_shot_pattern(&mut commands, Vec2::ZERO, Vec2::X, &session.0);
            });
        app.update();
        let world = app.world_mut();
        let mut q = world.query::<(&Shot, &Transform)>();
        let mut shots: Vec<_> = q
            .iter(world)
            .map(|(shot, tr)| (shot.speed, shot.damage, tr.translation.xy()))
            .collect();
        shots.sort_by(|a, b| a.0.y.total_cmp(&b.0.y));
        assert_eq!(shots.len(), 3);
        for shot in &shots {
            assert_eq!(shot.1, 3);
            assert!((shot.0.length() - 420.0).abs() < 0.001);
        }
        assert!(shots[0].0.y < -100.0);
        assert!(shots[1].0.y.abs() < 0.001);
        assert!(shots[2].0.y > 100.0);
    }

    #[test]
    fn chase_and_keep_distance_behaviors_move_oppositely_for_same_player() {
        use ordivon_room_action::EnemyBehavior;
        let mut app = App::new();
        let mut time = Time::<()>::default();
        time.advance_by(std::time::Duration::from_millis(100));
        app.insert_resource(time)
            .insert_resource(Session(Run::default()))
            .add_systems(Update, move_enemies);
        app.world_mut()
            .spawn((Hero, Transform::from_xyz(0.0, 0.0, 0.0)));
        app.world_mut().spawn((
            Foe {
                health: 2,
                speed: 100,
                behavior: EnemyBehavior::Chase,
            },
            Transform::from_xyz(20.0, 0.0, 0.0),
        ));
        app.world_mut().spawn((
            Foe {
                health: 2,
                speed: 100,
                behavior: EnemyBehavior::KeepDistance {
                    min_distance: 50,
                    max_distance: 100,
                },
            },
            Transform::from_xyz(20.0, 0.0, 0.0),
        ));
        app.update();
        let world = app.world_mut();
        let mut q = world.query::<(&Foe, &Transform)>();
        let xs: Vec<_> = q.iter(world).map(|(_, tr)| tr.translation.x).collect();
        assert_eq!(xs.len(), 2);
        assert!((xs[0] - 10.0).abs() < 0.001);
        assert!((xs[1] - 30.0).abs() < 0.001);
    }
    #[test]
    fn single_pellet_ignores_spread_angle_and_preserves_center_aim() {
        use ordivon_room_action::{GameConfig, WeaponSpec};
        let run = Run::with_config(GameConfig {
            weapon: WeaponSpec {
                spread_degrees: 90,
                pellets: 1,
                ..WeaponSpec::default()
            },
            ..GameConfig::default()
        })
        .unwrap();
        let mut app = App::new();
        app.insert_resource(Session(run)).add_systems(
            Update,
            |mut commands: Commands, session: Res<Session>| {
                spawn_shot_pattern(&mut commands, Vec2::ZERO, Vec2::X, &session.0);
            },
        );
        app.update();
        let world = app.world_mut();
        let mut q = world.query::<&Shot>();
        let shots: Vec<_> = q.iter(world).collect();
        assert_eq!(shots.len(), 1);
        assert!((shots[0].speed.x - 540.0).abs() < 0.001);
        assert!(shots[0].speed.y.abs() < 0.001);
    }

    #[test]
    fn overlap_with_kiting_enemy_does_not_trap_it_at_zero_vector() {
        let mut app = App::new();
        let mut time = Time::<()>::default();
        time.advance_by(std::time::Duration::from_millis(100));
        app.insert_resource(time)
            .insert_resource(Session(Run::default()))
            .add_systems(Update, move_enemies);
        app.world_mut().spawn((Hero, Transform::default()));
        app.world_mut().spawn((
            Foe {
                health: 2,
                speed: 100,
                behavior: EnemyBehavior::KeepDistance {
                    min_distance: 50,
                    max_distance: 100,
                },
            },
            Transform::default(),
        ));
        app.update();
        let world = app.world_mut();
        let mut q = world.query_filtered::<&Transform, With<Foe>>();
        let foe = q.single(world).unwrap();
        assert!(foe.translation.xy().length() > 0.001);
    }
    #[test]
    fn ecs_boss_reinforcement_blocks_gate_and_uses_same_enemy_lego() {
        use ordivon_room_action::{EnemySpec, GameConfig};
        let mut config = GameConfig::default();
        config.rooms[0].enemies = vec![EnemySpec {
            x: 80,
            y: 0,
            health: 1,
            speed: 78,
            behavior: EnemyBehavior::Chase,
        }];
        config.rooms[0].reinforcement_waves = vec![vec![EnemySpec {
            x: 160,
            y: 0,
            health: 5,
            speed: 40,
            behavior: EnemyBehavior::KeepDistance {
                min_distance: 50,
                max_distance: 100,
            },
        }]];
        let mut app = App::new();
        app.insert_resource(Session(Run::with_config(config).unwrap()))
            .add_systems(Startup, setup)
            .add_systems(
                Update,
                (resolve_hits, spawn_reinforcements, traverse_gate).chain(),
            );
        app.update();
        {
            let world = app.world_mut();
            let mut query = world.query_filtered::<&mut Transform, With<Hero>>();
            query.single_mut(world).unwrap().translation.x = 390.0;
        }
        shoot_at(&mut app, 80.0, 0.0);
        let state = &app.world().resource::<Session>().0;
        assert_eq!((state.room, state.wave, state.remaining), (0, 1, 1));
        assert_eq!(state.phase, Phase::Fighting, "boss wave blocks open gate");
        {
            let world = app.world_mut();
            let mut query = world.query::<(&Foe, &Transform)>();
            let live: Vec<_> = query
                .iter(world)
                .map(|(foe, at)| (foe.health, foe.behavior, at.translation.xy()))
                .collect();
            assert_eq!(live.len(), 1);
            assert_eq!(live[0].0, 5);
            assert_eq!(live[0].2, Vec2::new(160.0, 0.0));
        }
        for _ in 0..4 {
            shoot_at(&mut app, 160.0, 0.0);
            assert_eq!(app.world().resource::<Session>().0.room, 0);
        }
        shoot_at(&mut app, 160.0, 0.0);
        assert_eq!(app.world().resource::<Session>().0.room, 1);
        assert_eq!(app.world().resource::<Session>().0.wave, 0);
    }

    #[test]
    fn native_player_move_consumes_dash_speed_and_cooldown_state() {
        let mut app = App::new();
        let mut time = Time::<()>::default();
        time.advance_by(std::time::Duration::from_millis(100));
        let mut keys = ButtonInput::<KeyCode>::default();
        keys.press(KeyCode::KeyD);
        keys.press(KeyCode::Space);
        app.insert_resource(time)
            .insert_resource(keys)
            .insert_resource(DashClock::default())
            .insert_resource(Session(Run::default()))
            .add_systems(Update, move_player);
        app.world_mut().spawn((Hero, Transform::default()));
        app.update();
        let world = app.world_mut();
        let mut query = world.query_filtered::<&Transform, With<Hero>>();
        let moved = query.single(world).unwrap().translation.x;
        assert!((moved - 62.0).abs() < 0.001);
        assert!(world.resource::<DashClock>().0.active());
    }

    #[test]
    fn generated_room_templates_are_spawned_as_real_ecs_entities() {
        use ordivon_room_action::{GameConfig, rooms_from_seed};
        let templates = GameConfig::default().rooms;
        let rooms = rooms_from_seed(77, &templates, 4).unwrap();
        let expected = rooms[0].enemies.clone();
        let config = GameConfig {
            rooms,
            ..GameConfig::default()
        };
        let mut app = App::new();
        app.insert_resource(Session(Run::with_config(config).unwrap()))
            .add_systems(Startup, setup);
        app.update();
        let world = app.world_mut();
        let mut query = world.query::<(&Foe, &Transform)>();
        let actual: Vec<_> = query
            .iter(world)
            .map(|(foe, tr)| (foe.health, tr.translation.x as i32, tr.translation.y as i32))
            .collect();
        let expected: Vec<_> = expected.iter().map(|e| (e.health, e.x, e.y)).collect();
        assert_eq!(actual, expected);
    }

    #[test]
    fn agent_can_load_a_saved_recipe_and_reuse_the_existing_run_consumer() {
        let config =
            ordivon_room_action::compose_game(42, 3, &ordivon_room_action::LegoPalette::default())
                .unwrap();
        let path =
            std::env::temp_dir().join(format!("rak-recipe-{}-{}.json", std::process::id(), 42003));
        std::fs::write(&path, serde_json::to_vec_pretty(&config).unwrap()).unwrap();
        let args = vec!["--recipe".into(), path.display().to_string()];
        let loaded = run_from_args(&args).unwrap();
        assert_eq!(loaded.config(), &config);
        std::fs::remove_file(path).unwrap();
    }

    #[test]
    fn oversize_recipe_input_is_rejected_before_deserialization() {
        let path = std::env::temp_dir().join(format!(
            "rak-oversize-{}-{}.json",
            std::process::id(),
            51004
        ));
        std::fs::write(&path, vec![b' '; 1024 * 1024 + 1]).unwrap();
        let result = run_from_args(&["--recipe".into(), path.display().to_string()]);
        std::fs::remove_file(path).unwrap();
        assert!(result.unwrap_err().contains("exceeds 1 MiB"));
    }

    #[test]
    fn agent_palette_input_is_validated_before_starting_play() {
        let mut palette = ordivon_room_action::LegoPalette::default();
        palette.weapons.truncate(1);
        palette.enemies.truncate(1);
        palette.enemies[0].health = 8;
        let path =
            std::env::temp_dir().join(format!("rak-palette-{}-{}.json", std::process::id(), 42004));
        std::fs::write(&path, serde_json::to_vec(&palette).unwrap()).unwrap();
        let args = vec![
            "--seed".into(),
            "42".into(),
            "--rooms".into(),
            "3".into(),
            "--palette".into(),
            path.display().to_string(),
        ];
        let run = run_from_args(&args).unwrap();
        assert!(run.config().rooms.iter().all(|r| {
            r.enemies
                .iter()
                .chain(r.reinforcement_waves.iter().flatten())
                .all(|e| e.health == 8)
        }));
        palette.enemies[0].speed = 0;
        std::fs::write(&path, serde_json::to_vec(&palette).unwrap()).unwrap();
        assert!(run_from_args(&args).is_err());
        std::fs::remove_file(path).unwrap();
    }

    #[test]
    fn command_line_seed_builds_replayable_composed_game() {
        let a =
            run_from_args(&["--seed".into(), "42".into(), "--rooms".into(), "4".into()]).unwrap();
        let b =
            run_from_args(&["--seed".into(), "42".into(), "--rooms".into(), "4".into()]).unwrap();
        assert_eq!(a, b);
        assert_eq!(a.config().rooms.len(), 4);
        assert_eq!(run_from_args(&[]).unwrap(), Run::default());
        assert!(run_from_args(&["--rooms".into(), "5".into()]).is_err());
        assert!(run_from_args(&["--seed".into(), "oops".into()]).is_err());
        assert!(
            run_from_args(&["--seed".into(), "42".into(), "--rooms".into(), "99".into()]).is_err()
        );
    }

    #[test]
    fn seeded_game_spawns_actual_bevy_enemy_archetypes_from_palette() {
        use ordivon_room_action::{LegoPalette, compose_game};
        let palette = LegoPalette::default();
        let config = compose_game(42, 4, &palette).unwrap();
        let expected = config.rooms[0].enemies.clone();
        let mut app = App::new();
        app.insert_resource(Session(Run::with_config(config).unwrap()))
            .add_systems(Startup, setup);
        app.update();
        let world = app.world_mut();
        let mut query = world.query::<(&Foe, &Transform)>();
        let spawned: Vec<_> = query
            .iter(world)
            .map(|(foe, tr)| {
                (
                    tr.translation.x as i32,
                    tr.translation.y as i32,
                    foe.health,
                    foe.speed,
                    foe.behavior,
                )
            })
            .collect();
        assert_eq!(spawned.len(), expected.len());
        for entity in expected {
            assert!(spawned.contains(&(
                entity.x,
                entity.y,
                entity.health,
                entity.speed,
                entity.behavior
            )));
        }
    }
}
