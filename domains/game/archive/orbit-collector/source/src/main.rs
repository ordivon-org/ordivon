mod gameplay;
mod rules;

use bevy::prelude::*;
use gameplay::OrbitCollectorPlugin;

fn main() {
    App::new()
        .add_plugins(DefaultPlugins.set(WindowPlugin {
            primary_window: Some(Window {
                title: "Orbit Collector | Ordivon Game composition example".into(),
                resolution: (960, 540).into(),
                ..default()
            }),
            ..default()
        }))
        .add_plugins(OrbitCollectorPlugin)
        .run();
}
