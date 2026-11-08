//! Real Bevy-native composition: ECS components + systems, input, Sprite, Text,
//! fixed scene recipe, and product-owned state transitions. No custom engine.

use crate::rules::{Phase, RunState};
use bevy::prelude::*;

const GOALS: [Vec2; 5] = [
    Vec2::new(-310.0, 160.0),
    Vec2::new(270.0, 155.0),
    Vec2::new(-260.0, -160.0),
    Vec2::new(310.0, -140.0),
    Vec2::new(0.0, 0.0),
];
const INITIAL_LIVES: u8 = 3;
const MOVE_SPEED: f32 = 240.0;
const PLAYER_RADIUS: f32 = 15.0;
const GOAL_RADIUS: f32 = 24.0;
const HAZARD_RADIUS: f32 = 28.0;
const ARENA_HALF_SIZE: Vec2 = Vec2::new(445.0, 225.0);
const HIT_COOLDOWN_SECS: f32 = 1.2;

#[derive(Component)]
struct Player;

#[derive(Component)]
struct Goal;

#[derive(Component)]
struct Hazard;

#[derive(Component)]
struct StatusText;

#[derive(Resource)]
struct GameRun {
    rules: RunState,
    last_hit_at: f32,
}

impl Default for GameRun {
    fn default() -> Self {
        Self {
            rules: RunState::new(GOALS.len(), INITIAL_LIVES),
            last_hit_at: f32::NEG_INFINITY,
        }
    }
}

pub struct OrbitCollectorPlugin;

impl Plugin for OrbitCollectorPlugin {
    fn build(&self, app: &mut App) {
        app.init_resource::<GameRun>()
            .add_systems(Startup, setup)
            .add_systems(
                Update,
                (
                    restart,
                    move_player,
                    collect_goals,
                    patrol_hazard,
                    resolve_hazard,
                    update_status,
                )
                    .chain(),
            );
    }
}

fn spawn_goals(commands: &mut Commands) {
    for position in GOALS {
        commands.spawn((
            Goal,
            Sprite::from_color(Color::srgb(0.98, 0.75, 0.18), Vec2::splat(23.0)),
            Transform::from_xyz(position.x, position.y, 1.0),
        ));
    }
}

fn setup(mut commands: Commands) {
    commands.spawn(Camera2d);
    commands.spawn((
        Player,
        Sprite::from_color(Color::srgb(0.20, 0.87, 0.87), Vec2::splat(30.0)),
        Transform::from_xyz(0.0, -95.0, 2.0),
    ));
    commands.spawn((
        Hazard,
        Sprite::from_color(Color::srgb(0.95, 0.29, 0.36), Vec2::splat(42.0)),
        Transform::from_xyz(0.0, 140.0, 1.0),
    ));
    spawn_goals(&mut commands);
    commands.spawn((
        StatusText,
        Text::new(""),
        TextFont {
            font_size: bevy::text::FontSize::Px(26.0),
            ..default()
        },
        TextColor(Color::srgb(0.94, 0.95, 1.0)),
        Node {
            position_type: PositionType::Absolute,
            left: px(18),
            top: px(12),
            ..default()
        },
    ));
}

fn restart(
    keys: Res<ButtonInput<KeyCode>>,
    mut commands: Commands,
    goals: Query<Entity, With<Goal>>,
    mut player: Query<&mut Transform, With<Player>>,
    mut run: ResMut<GameRun>,
) {
    if !keys.just_pressed(KeyCode::KeyR) {
        return;
    }
    for entity in &goals {
        commands.entity(entity).despawn();
    }
    spawn_goals(&mut commands);
    if let Ok(mut transform) = player.single_mut() {
        transform.translation = Vec3::new(0.0, -95.0, 2.0);
    }
    *run = GameRun::default();
}

fn move_player(
    keys: Res<ButtonInput<KeyCode>>,
    time: Res<Time>,
    mut players: Query<&mut Transform, With<Player>>,
    run: Res<GameRun>,
) {
    if run.rules.phase() != Phase::Playing {
        return;
    }
    let x = (keys.pressed(KeyCode::ArrowRight) || keys.pressed(KeyCode::KeyD)) as i32
        - (keys.pressed(KeyCode::ArrowLeft) || keys.pressed(KeyCode::KeyA)) as i32;
    let y = (keys.pressed(KeyCode::ArrowUp) || keys.pressed(KeyCode::KeyW)) as i32
        - (keys.pressed(KeyCode::ArrowDown) || keys.pressed(KeyCode::KeyS)) as i32;
    let movement = Vec2::new(x as f32, y as f32).normalize_or_zero();
    if let Ok(mut transform) = players.single_mut() {
        let mut next = transform.translation.truncate() + movement * MOVE_SPEED * time.delta_secs();
        next = next.clamp(-ARENA_HALF_SIZE, ARENA_HALF_SIZE);
        transform.translation.x = next.x;
        transform.translation.y = next.y;
    }
}

fn collect_goals(
    mut commands: Commands,
    players: Query<&Transform, With<Player>>,
    goals: Query<(Entity, &Transform), With<Goal>>,
    mut run: ResMut<GameRun>,
) {
    if run.rules.phase() != Phase::Playing {
        return;
    }
    let Ok(player) = players.single() else { return };
    for (entity, goal) in &goals {
        if player.translation.distance(goal.translation) < PLAYER_RADIUS + GOAL_RADIUS {
            commands.entity(entity).despawn();
            run.rules.collect();
        }
    }
}

fn patrol_hazard(time: Res<Time>, mut hazards: Query<&mut Transform, With<Hazard>>) {
    // The product-specific trajectory is intentionally not an engine abstraction.
    let t = time.elapsed_secs();
    for mut hazard in &mut hazards {
        hazard.translation.x = 250.0 * (t * 0.75).cos();
        hazard.translation.y = 120.0 * (t * 1.1).sin();
    }
}

fn resolve_hazard(
    time: Res<Time>,
    players: Query<&Transform, With<Player>>,
    hazards: Query<&Transform, With<Hazard>>,
    mut run: ResMut<GameRun>,
) {
    if run.rules.phase() != Phase::Playing
        || time.elapsed_secs() - run.last_hit_at < HIT_COOLDOWN_SECS
    {
        return;
    }
    let Ok(player) = players.single() else { return };
    for hazard in &hazards {
        if player.translation.distance(hazard.translation) < PLAYER_RADIUS + HAZARD_RADIUS {
            run.rules.take_hit();
            run.last_hit_at = time.elapsed_secs();
            break;
        }
    }
}

fn update_status(run: Res<GameRun>, mut labels: Query<&mut Text, With<StatusText>>) {
    let Ok(mut label) = labels.single_mut() else {
        return;
    };
    let outcome = match run.rules.phase() {
        Phase::Playing => "Collect the golden beacons. Avoid the red drone.",
        Phase::Won => "YOU WON! All beacons collected. Press R to replay.",
        Phase::Lost => "RUN ENDED! Press R to retry.",
    };
    **label = format!(
        "ORBIT COLLECTOR   {}/{}   Lives: {}\n{}\nWASD / arrows: move     R: restart",
        run.rules.collected(),
        run.rules.target(),
        run.rules.lives(),
        outcome
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn actual_bevy_plugin_assembles_game_components_and_rules() {
        let mut app = App::new();
        app.add_plugins(MinimalPlugins)
            .init_resource::<ButtonInput<KeyCode>>()
            .add_plugins(OrbitCollectorPlugin);
        app.update();

        let world = app.world_mut();
        let goal_count = world
            .query_filtered::<Entity, With<Goal>>()
            .iter(world)
            .count();
        let player_count = world
            .query_filtered::<Entity, With<Player>>()
            .iter(world)
            .count();
        let hud_count = world
            .query_filtered::<Entity, With<StatusText>>()
            .iter(world)
            .count();
        assert_eq!(goal_count, GOALS.len());
        assert_eq!(player_count, 1);
        assert_eq!(hud_count, 1);
        assert_eq!(world.resource::<GameRun>().rules.phase(), Phase::Playing);
    }

    #[test]
    fn native_ecs_collection_updates_goal_state_and_hud() {
        let mut app = App::new();
        app.add_plugins(MinimalPlugins)
            .init_resource::<ButtonInput<KeyCode>>()
            .add_plugins(OrbitCollectorPlugin);
        app.update();

        {
            let world = app.world_mut();
            let mut query = world.query_filtered::<&mut Transform, With<Player>>();
            let mut player = query.single_mut(world).expect("player spawned by plugin");
            player.translation = GOALS[0].extend(2.0);
        }
        app.update();

        assert_eq!(app.world().resource::<GameRun>().rules.collected(), 1);
        let world = app.world_mut();
        assert_eq!(
            world
                .query_filtered::<Entity, With<Goal>>()
                .iter(world)
                .count(),
            GOALS.len() - 1
        );
        let mut texts = world.query_filtered::<&Text, With<StatusText>>();
        let hud = texts.single(world).expect("HUD consumes game state");
        assert!(
            hud.0.contains("1/5"),
            "native Bevy Text must show updated score"
        );
    }

    #[test]
    fn recipe_goal_count_matches_state_goal() {
        let run = GameRun::default();
        assert_eq!(run.rules.target(), GOALS.len());
        assert_eq!(run.rules.lives(), INITIAL_LIVES);
        assert!(
            GOALS
                .iter()
                .all(|pos| pos.abs().cmple(ARENA_HALF_SIZE).all())
        );
    }
}
