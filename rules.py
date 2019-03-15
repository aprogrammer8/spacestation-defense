"""This module contains game balance parameters."""

# Asteroids.
SALVAGE_START_TIME = 5
ASTEROID_MOVE_CHANCE = 1/2
ASTEROID_HULL = 50
ASTEROID_DROP = 0
# Probes.
PROBE_CAPACITY = 5
PROBE_DROP = 1
PROBE_HULL = 10
PROBE_SHIELD = 0
PROBE_SHIELD_REGEN = (0,)
PROBE_SPEED = 3
PROBE_SIZE = 1
PROBE_WEAPONS = ()
# Drones.
DRONE_DROP = 1
DRONE_HULL = 5
DRONE_SHIELD = 0
DRONE_SHIELD_REGEN = (0,)
DRONE_SPEED = 3
DRONE_WEAPONS = ({'type': 'laser', 'power': 1, 'tier': 1},)
# Kamikaze Drones.
KAMIKAZE_DRONE_DROP = 1
KAMIKAZE_DRONE_HULL = 10
KAMIKAZE_DRONE_SHIELD = 0
KAMIKAZE_DRONE_SHIELD_REGEN = (0,)
KAMIKAZE_DRONE_SPEED = 4
KAMIKAZE_DRONE_WEAPONS = ()

# Station general.
COMPONENT_HULL = 50
COMPONENT_POWER_USAGE = 2
COMPONENT_SALVAGE = 20
# Shield Generators.
SHIELD_GEN_CAP = 100
SHIELD_GEN_REGEN = (0, 1, 3, 8)
SHIELD_GEN_RANGE = 6
# Turrets.
LASER_TURRET_WEAPONS = (
	{'type': 'laser', 'power': 5, 'tier': 2},
	{'type': 'laser', 'power': 5, 'tier': 2},
	{'type': 'laser', 'power': 5, 'tier': 2},
)
# Power Generators.
POWER_GEN_SPEED = 5
POWER_GEN_CAP = 25
# Engines.
ENGINE_SPEED = 2
THRUST_PER_COMPONENT = 2
# Hangars.
HANGAR_CAPACITY = 20
# Factories.
FACTORY_SPEED = 2
FACTORY_CAP = 100
SHIP_CONSTRUCTION_COSTS = {"Probe": 5}
SHIP_DESCRIPTIONS = {
	"Probe":
		str(PROBE_HULL) + " hull, " +
		str(PROBE_SPEED) + " speed, " +
		str(PROBE_SIZE) + " size, can carry up to " +
		str(PROBE_CAPACITY) + " Salvage. " +
		str(SHIP_CONSTRUCTION_COSTS['Probe']) + " Salvage to build.",
}

# Careds.
CARD_PLANETARY_CANNON_DAMAGE = 200
CARD_DESCRIPTIONS = {
	"Power Surge":
		"Fill all Power Generators.",
	"Planetary Cannon":
		"Deal " + str(CARD_PLANETARY_CANNON_DAMAGE) + " damage to an enemy.",
}
