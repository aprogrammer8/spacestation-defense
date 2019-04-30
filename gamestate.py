import random, json
from rules import *
from util import *

class Gamestate:
	def __init__(self, players, mission='test', json=''):
		if json:
			self.load_json(json)
			return
		else: # If no JSON, we load a new game from a mission.
			self.station = Station()
			self.ships = set()
			self.asteroids = set()
			self.salvages = set()
			self.nextwave = 0
			self.round = 0
			self.ships.add(Probe(-1, [0, 5]))
			# Number of turns left before the next wave should come.
			self.time = 0
			# Rewards for each sent wave. The gamestate tracks this itself for restoration purposes.
			self.rewards = {}
			self.players = []
			for player in players: self.players.append(Player(player))
			for player in self.players: player.hand += [Card("Power Surge"), Card("Planetary Cannon")]
			# The draw pointer is used to keep track of who will get the next card the players draw.
			self.draw_pointer = 0
			self.mission = Mission("missions/"+mission)
			# Every entity will need an internal ID so we don't lose track if it moves or something.
			self.next_id = 0

	# Non-mutating methods.

	def occupied(self, pos):
		"""Returns the Entity occupying a gameboard space."""
		for entity in self.station:
			if pos in entity.spaces(): return entity
		for entity in self.ships:
			if pos in entity.spaces(): return entity
		for entity in self.asteroids:
			if pos in entity.spaces(): return entity

	def occupied_area(self, spaces, exclude=None):
		"""Returns an Entity occupying any of a sequence of spaces."""
		for space in spaces:
			entity = self.occupied(space)
			if entity and entity != exclude: return entity

	def find_open_pos(self, size=(1,1)):
		"""Searches through all game objects and finds an unoccupied position to put the enemy on."""
		while True:
			pos = [random.randint(-5,5), random.randint(5,7)]
			if not self.occupied(pos): return pos

	def invalid_move(self, entity, move):
		"""Takes an Entity and a proposed move, and checks all destination spaces for obstructions."""
		for space in entity.projected_spaces():
			occupied = self.occupied([space[0] + move[0], space[1] + move[1]])
			# Have to also check for equality, because big ships will overlap themselves when they move.
			if occupied and occupied != entity: return occupied
		return False

	def path(self, source_entity, source, type, target):
		"""Attempts to find a path for an attack to get from one space to a target space. The source_entity is needed so we don't count it as an obstacle."""
		dist = [abs(target[0] - source[0]), abs(target[1] - source[1])]
		total_dist = dist[0] + dist[1]
		# It's ugly, but it finds the distance with magnitude reduced to 1 or -1.
		dir = ({True: 1, False: -1}[target[0] > source[0]], {True: 1, False: -1}[target[1] > source[1]])
		probe = [source[0], source[1]]
		step_x, step_y = dist[0] / total_dist, dist[1] / total_dist
		counter = [0, 0]
		while probe != target:
			if probe != source:
				block = self.occupied(probe)
				# Make sure we don't fail if we run over another space of the same entity.
				if block and block != source_entity: break
			# Only increment the counter if neither one is already above 1.
			if not (counter[0] > 1 or counter[1] > 1):
				counter[0] += step_x
				counter[1] += step_y
			if counter[0] < 1 and counter[1] < 1: continue
			# If only x has advanced enough.
			if counter[0] >= 1 and counter[1] < 1:
				counter[0] -= 1
				probe[0] += dir[0]
				dist[0] -= 1
			# If only y has advanced enough.
			elif counter[1] >= 1 and counter[0] < 1:
				counter[1] -= 1
				probe[1] += dir[1]
				dist[1] -= 1
			# They've both advanced, so we need to check which one is higher.
			else:
				if counter[0] > counter[1]:
					counter[0] -= 1
					probe[0] += dir[0]
					dist[0] -= 1
				else:
					counter[1] -= 1
					probe[1] += dir[1]
					dist[1] -= 1
		if probe == target: return True
		return False

	def in_range(self, source, type, target):
		"""Determines whether a source is in range of a target. type is the type of attack - some might have range limits."""
		# Try all source spaces to all target spaces.
		for source_space in source.projected_spaces():
			for target_space in target.spaces():
				if self.path(source, source_space, type, target_space): return True
		return False

	def get_id(self):
		"""Increment an return the current Entity id. This should be called whenever a new Entity needs to be created."""
		self.next_id += 1
		return self.next_id

	def get_entity_from_id(self, id):
		"""Returns the Entity object with the specified id."""
		for entity in self.station.union(self.ships, self.asteroids):
			if entity.id == id: return entity

	# Basic mutating methods.

	def resolve_rng(self):
		"""Fills in randomly generated accuracy wherever necessary, and acts as a generator for the commands needed to propagate this."""
		# Order doesn't matter here since it's just assigning.
		for entity in self.station.union(self.ships, self.asteroids):
			# We need to update if and only if at least one action was changed, but we don't want to send out a bunch of updates for the same Entity if it had multiple attacks.
			update_needed = False
			for action in entity.actions:
				if action['type'] == 'attack':
					target = self.occupied(action['target'])
					# This should only happen if they targeted a space that doesn't have an Entity anymore.
					if not target:
						continue
					action['hit'] = random.randint(1, 100) <= hit_chance(entity.weapons[action['weapon']].type, target)
					update_needed = True
			if update_needed:
				yield "ASSIGN:" + json.dumps(entity.pos) + ":" + json.dumps(entity.actions)

	def playout(self):
		"""Plays out all Entities actions."""
		# We sort Entities in a top-left to bottom-right order for determinism.
		entities_to_act = sorted(self.station.union(self.ships, self.asteroids),
			# This lambda ensures (because False gets sorted before True) that player stuff goes first, then enemy stuff, then asteroids; and within that, it goes by position.
			key = lambda e: (e.team != 'player', e.team != 'enemy', e.pos))
		for entity in entities_to_act:
			if isinstance(entity, Component):
				if entity.powered() and not self.station.use_power():
					continue
			else:
				# Non-Components have independent shield regeneration.
				entity.shield_regen()
			# We yield each time the client needs to play an animation to reflect the action. The server will just do nothing with them when it calls this.
			animation = self.playout_entity(entity)
			if animation: yield animation

	def playout_entity(self, entity):
		"""Plays out the given Entity's actions."""
		for action in entity.actions:
			# Turning off power to auto-running components.
			if action['type'] == 'off':
				# Nothing we need to do here; the power was already not consumed.
				continue
			# Engines.
			if action['type'] == 'boost':
				self.station.thrust += ENGINE_SPEED * action['dir']
			# Shield Generators hiding their shields.
			elif action['type'] == 'hide':
				# Nothing we need to do here.
				continue
			# Factory assignments.
			elif action['type'] == 'build':
				entity.project = action['ship']
				entity.hangar = action['hangar']
			# Hangar launches.
			elif action['type'] == 'launch':
				self.hangar_launch(entity, action['index'], action['pos'], action['rot'])
				# TODO There should be an animation for this, but for now there isn't.
			# Moves.
			elif action['type'] == 'move':
				# Don't process remaining actions if the ship lands in a Hangar.
				if self.move(entity, action['move']) == "LANDED": break
			# Attacks.
			elif action['type'] == 'attack':
				# Nothing is changed in the gamestate if the attack misses.
				if not action['hit']: continue
				target = self.occupied(action['target'])
				# This should happen if we killed the target in a previous attack.
				if not target: continue
				weapon = entity.weapons[action['weapon']]
				target.take_damage(weapon.power, weapon.type)
				# Remove dead targets.
				if target.hull <= 0:
					self.remove(target)
					# Spawn salvage pile.
					self.add_salvage(Salvage(target.pos, target.salvage))

			else: print(action, "is an invalid action")

		# The legality checks are handled inside the method.
		if entity.type == "Factory": self.factory_work(entity)


	def init_station(self, data):
		for pos in data: self.station.add(Component(self.get_id(), list(pos), self.station, data[pos], 0, COMPONENT_HULL))

	#def encode(self):
	#	"""Encodes the Gamestate into a JSON object that can be sent over the network."""

	def draw_cards(self, num):
		draws = []
		for i in range(num):
			draws += {'player': self.players[self.draw_pointer], 'card': draw_card()}
			self.draw_pointer += 1
			if self.draw_pointer >= len(self.players): self.draw_pointer = 0
		return draws

	def clear(self):
		"""Clears the stored actions and moves of all gamestate objects."""
		for ship in self.ships: ship.actions = []
		for component in self.station: component.actions = []
		for asteroid in self.asteroids: asteroid.actions = []

	def upkeep(self, clientside=False):
		"""Do every-round tasks, like regenerating power and salvage decay and stuff."""
		self.clear()
		self.station.power_regen()
		# Salvage decay. We make a new set to avoid messings things up by changing the size during iteration.
		new_salvages = set()
		for salvage in self.salvages:
			salvage.decay()
			if salvage.amount > 0: new_salvages.add(salvage)
		self.salvages = new_salvages
		if not clientside:
			# Advance the mission track.
			self.time -= 1
			if self.time <= 0:
				wave, self.rewards[self.nextwave], self.time = self.mission.wave(self.nextwave)
				self.nextwave += 1
				return self.send_enemies(wave, self.nextwave - 1)

	def send_enemies(self, enemies, wavenum):
		"Accepts enemies to send as passed by the mission's wave method, calls insert_enemies, but also returns the data that insert_enemies needs to be called with, so that it can be sent out to clients."
		inserts = []
		for enemy_type in enemies:
			for _ in range(enemies[enemy_type]):
				# The rot value of 0 is a placeholder.
				inserts.append({'type': enemy_type, 'pos': self.find_open_pos(), 'rot': 0, 'wave': wavenum})
				self.insert_enemies((inserts[-1],))
		return inserts

	def insert_enemies(self, enemies):
		"""Inserts the given enemies into the Gamestate. Takes a sequence of dicts with enemy type names as keys and their board positions as values."""
		for enemy in enemies:
			# Asteroids aren't technically enemies, but they're handled by the same function.
			if enemy['type'] == "Asteroid":
				self.asteroids.add(Asteroid(self.get_id(), enemy['pos'], enemy['rot']))
			elif enemy['type'] == "Drone":
				self.ships.add(Drone(self.get_id(), enemy['pos'], enemy['rot'], enemy['wave']))
			elif enemy['type'] == "Kamikaze Drone":
				self.ships.add(Kamikaze_Drone(self.get_id(), enemy['pos'], enemy['rot'], enemy['wave']))
			else:
				print("Unrecognized enemy type:", enemy)

	def add_salvage(self, salvage):
		# If there's already one on the space, it stacks for simplicity.
		for s in self.salvages:
			if s.pos == salvage.pos:
				s.amount += salvage.amount
				s.time = max(s.time, salvage.time)
				return
		# Otherwise, we just add it.
		self.salvages.add(salvage)

	def jump(self, entity, pos, rot=-1):
		"""Jump an Entity to a position. A rot value of -1 means to not change it. Salvage on the destination space will be automatically picked up if possible."""
		entity.pos = pos
		if rot != -1: entity.rot = rot
		# The landing in Hangars is encapsulated in here, so client and server don't have to copy as much code.
		if entity.team == 'player':
			obstacle = self.occupied_area(entity.spaces(), exclude=entity)
			# If there's an obstacle other than a Hangar, then the server sent an invalid move and that's not the client's responsibility.
			if obstacle:
				# Land it: remove it from the list of visible ships, and add it to the hangar's contents.
				self.ships.remove(entity)
				obstacle.contents.append(entity)
				# Dump any salvage the ship was carrying.
				if hasattr(entity, 'load'): self.station.receive_salvage(entity)
				# These return signals are so the client can know whether to play a sound.
				return "LANDED"
			# Pick up Salvage.
			if isinstance(entity, SalvageCollector):
				for salvage in self.salvages:
					if salvage.pos == entity.pos:
						entity.collect(salvage)
						if salvage.amount <= 0: self.salvages.remove(salvage)
						return "COLLECTED"

	def move(self, entity, change):
		"""A wrapper around Gamestate.jump that takes a tuple of (x, y) as a move to be made from the Entity's current position, and calculates the position to jump it to."""
		return self.jump(entity, [entity.pos[0] + change[0], entity.pos[1] + change[1]])

	def remove(self, entity):
		"""Remove an Entity."""
		for e in self.station:
			if e == entity:
				self.station.remove(e)
				return
		for e in self.ships:
			if e == entity:
				self.ships.remove(e)
				return
		for e in self.asteroids:
			if e == entity:
				self.asteroids.remove(e)
				return

	# Type-specific mutating methods.

	def hangar_launch(self, hangar, index, pos, rot, test=False):
		"""Launch a ship from a Hangar. Returns True if the launch is legal. If test is True, it will return the legality of the launch but won't do it."""
		try: ship = hangar.contents[index]
		except IndexError:
			print("Hangar at", hangar.pos, "could not launch due to IndexError, contents:", hangar.contents)
			return False
		launch_spaces = spaces(pos, ship.shape, rot)
		if self.occupied_area(launch_spaces): return False
		# The ship can only be launched to a space adjacent to the Hangar.
		if not adjacent(launch_spaces, hangar.spaces()): return False
		# The launch is legal.
		if not test:
			del hangar.contents[index]
			# Clear actions so the ship won't come out with moves.
			ship.actions = []
			self.ships.add(ship)
			self.jump(ship, pos, rot)
		return True

	def factory_work(self, factory):
		"""Progresses construction of a Factory, and places the ship if it finishes."""
		if not factory.project or factory.actions == [{'type': 'off'}]: return
		progress = min(FACTORY_SPEED, SHIP_CONSTRUCTION_COSTS[factory.project] - factory.progress, factory.station.salvage)
		factory.progress += progress
		factory.station.salvage -= progress
		if factory.progress >= SHIP_CONSTRUCTION_COSTS[factory.project]:
			# First, make sure the Hangar is still alive.
			for comp in factory.station:
				if comp.type == "Hangar" and comp.pos == factory.hangar:
					# Position and rotation don't matter for ships spawning in a Hangar. They'll be set when the ship launches.
					if factory.project == "Probe":
						comp.contents.append(Probe(self.get_id(), [0,0], 0))
					factory.progress = 0
					factory.project = None
					factory.hangar = None
					return


def slope(p1, p2):
	"""Returns the slope between two points, handling division by zero with a high value if the numerator is not also zero, or 1 if it is."""
	dist = (abs(p2[0] - p1[0]), abs(p2[1] - p1[1]))
	if dist[0] == 0:
		if dist[1] == 0: return 1
		return 100
	return dist[1]/dist[0]


class Player:
	def __init__(self, name, cards=None):
		self.name = name
		if cards is None: cards = []
		self.hand = cards

class Card:
	def __init__(self,name):
		self.name = name

def draw_card():
	return Card("Repair")

class Entity:
	"""An Entity is anything that has a position on the board, cannot be overlapped by another Entity, and can be targeted."""
	def __init__(self, id, type, team, pos, shape, rot, salvage, hull, shield=0, shield_regen=(0,), weapons=(), speed=0, wave=0, size=0):
		self.id = id
		self.type = type
		self.team = team
		self.pos = pos
		# self.shape is a tuple of other positions expressed as offsets from the main pos (when rot == 0), that the Entity also occupies (used for Entities bigger than 1x1).
		self.shape = shape
		# Rotation is stored as a number of degrees, to help with displaying.
		self.rot = rot
		self.maxhull = self.hull = hull
		# Components can't have their shield property set, because it's not really theirs.
		if not isinstance(self, Component): self.maxshield = self.shield = shield
		self.shield_regen_amounts = shield_regen
		self.shield_regen_pointer = 0
		self.speed = speed
		# Weapons are a little more complicated to initialize, since we need to pass the dicts of params to the Weapon constructor.
		self.weapons = []
		for w in weapons:
			self.weapons.append(Weapon(**w))
		# This field refers to salvage dropped when the Entity is destroyed.
		self.salvage = salvage
		# The sequence of actions the Entity plans to make.
		self.actions = []
		# Enemy only fields.
		self.wave = wave
		# Ally only fields.
		self.size = size

	def spaces(self):
		"""Returns all spaces the Entity occupies."""
		return spaces(self.pos, self.shape, self.rot)

	def projected_spaces(self):
		"""Like Entity.spaces, but uses the projected final position."""
		final_pos = self.pos
		for move in self.moves_planned():
			final_pos = [final_pos[0] + move[0], final_pos[1] + move[1]]
		return spaces(final_pos, self.shape, self.rot)

	def rect(self):
		"""Returns the top-left space of the Entity and the bottom right."""
		return rect(self.spaces())

	def move_rect(self):
		"""Like Entity.rect, but encompasses the projected spaces from all planned moves too."""
		pos = self.pos[:]
		total_spaces = self.spaces()
		for move in self.moves_planned():
			pos[0] += move[0]
			pos[1] += move[1]
			total_spaces += spaces(pos, self.shape, self.rot)
		return rect(total_spaces)

	def take_damage(self, dmg, type):
		"""This method internally accounts for switching from shields to hull, resetting the shield regen pointer, etc."""
		# For now, we ignore type.
		dealt = min(dmg, self.shield)
		# Taking shield damage always resets the regen pointer.
		if dealt > 0: self.shield_regen_pointer = 0
		self.shield -= dealt
		dmg -= dealt
		if dmg == 0: return
		# Now it goes through to hull.
		self.hull -= dmg

	def shield_regen(self):
		self.shield += self.shield_regen_amounts[self.shield_regen_pointer]
		# Update pointer.
		if self.shield_regen_pointer < len(self.shield_regen_amounts) - 1:
			self.shield_regen_pointer += 1
		return True

	def moves_left(self):
		moves = self.speed
		for action in self.actions:
			# Moves are always length 2.
			if len(action) == 2: moves -= 1
		return moves

	def target(self, index, pos):
		"""Targets the Entity's weapon at the provided index at the Entity at pos."""
		action_index = 0
		# Check if the requested weapon is already targeting something. If so, replace that target so the weapon isn't getting double-used.
		for action in self.actions:
			if action['type'] == 'attack' and action['weapon'] == index:
				self.actions[action_index] = {'type': 'attack', 'weapon': index, 'target': pos}
				return
			action_index += 1
		self.actions.append({'type': 'attack', 'weapon': index, 'target': pos})

	def desc_target(self, weapon, gamestate):
		"""Takes a weapon index and returns a string describing what it's targeting, if anything."""
		index = self.weapons.index(weapon)
		for action in self.actions:
			if action['type'] == 'attack' and action['weapon'] == index:
				target = gamestate.occupied(action['target'])
				if target: return ", targeting " + target.type + " at " + str(target.pos)
		return ""

	def moves_planned(self):
		"""Filters the list of planned actions and returns only the moves."""
		return [move['move'] for move in self.actions if move['type'] == 'move']

	def untargeted(self):
		"""Returns all weapons with no target."""
		# First, construct a list of indexes of weapons.
		weapons = list(range(len(self.weapons)))
		# Now filter out the ones that have targets.
		for action in self.actions:
			if action['type'] == 'attack': weapons.remove(action['weapon'])
		return weapons

	def hangar_describe(self):
		"""Returns a string suitable for describing the Ship when it's in a Hangar."""
		string = self.type + "; hull = " + str(self.hull) + "/" + str(self.maxhull) + ", shield = " + str(self.shield) + "/" + str(self.maxshield) + " (+" + str(self.shield_regen_amounts[self.shield_regen_pointer]) + ")"
		# I know it's kind of wrong design to have a method check what type the object is, but I decided it was better than just copying the method.
		if isinstance(self, SalvageCollector):
			string += "; carrying " + str(self.load) + " salvage"
		return string


class SalvageCollector:
	def __init__(self):
		self.load = 0
	def collect(self, salvage):
		"""The Ship picks up a piece of salvage. Only Probes can do this."""
		collected = min(salvage.amount, PROBE_CAPACITY-self.load)
		self.load += collected
		salvage.amount -= collected


class Component(Entity):
	"""A Station Component."""
	def __init__(self, id, pos, station, type, rot, hull):
		Entity.__init__(self, id, type, "player", pos, shape=((1,0), (0,1), (1,1)), rot=rot, salvage=COMPONENT_SALVAGE, hull=hull, shield=0, shield_regen=(0,))
		if type not in COMPONENT_TYPES: raise TypeError("Not a valid station component type: " + type)
		self.station = station
		if type == "Shield Generator":
			self.__shield = self.__maxshield = SHIELD_GEN_CAP
			self.shield_regen_amounts = SHIELD_GEN_REGEN
		if type == "Laser Turret":
			for w in LASER_TURRET_WEAPONS:
				self.weapons.append(Weapon(**w))
		if type == "Power Generator":
			# For now, the rule for starting power is half the max power.
			self.station.power += POWER_GEN_CAP // 2
		if type == "Hangar":
			self.contents = []
		if type == "Factory":
			# The ship it's currently building.
			self.project = None
			# How much progress toward making the ship.
			self.progress = 0
			# The Hangar the ship will spawn in.
			self.hangar = None

	def shield_generators(self):
		"""Find all Shield Generators covering this Component."""
		gens = []
		for comp in self.station:
			if comp.type != "Shield Generator": continue
			# We check "not comp.actions" instead of comp.powered() because Shield Generators in hide mode shouldn't count here.
			if abs(comp.pos[0] - self.pos[0]) + abs(comp.pos[1] - self.pos[1]) < SHIELD_GEN_RANGE and not comp.actions:
				gens.append(comp)
		return gens

	@property
	def shield(self):
		# Calculate which shield generators are applying to it, and use their underlying fields.
		shield = 0
		for comp in self.shield_generators(): shield += comp.__shield
		return shield

	@property
	def maxshield(self):
		shield = 0
		for comp in self.shield_generators(): shield += comp.__maxshield
		return shield

	@shield.setter
	def shield(self, new):
		diff = self.shield - new
		# If we're regenerating. We can assume that we're a Shield Generator because this method wouldn't get called in this way on anything else.
		if diff < 0:
			self.__shield = min(self.__shield - diff, self.__maxshield)
			return
		# Calling this ahead of time so it doesn't incur an overhead calling it every time we loop for large amounts of damage.
		gens = self.shield_generators()
		while diff > 0:
			# Spread out the damage over all in-range generators.
			for gen in gens:
				if gen.shield > 0 and diff > 0:
					gen.__shield -= 1
					gen.shield_regen_pointer = 0
					diff -= 1

	def powered(self):
		"""Returns whether the Component is currently using power."""
		if self.type == "Shield Generator": return self.actions != [{'type': 'off'}]
		if self.type == "Laser Turret": return bool(self.actions)
		if self.type == "Factory": return self.actions != [{'type': 'off'}] and (self.project or self.actions) and self.station.salvage > 0
		if self.type == "Engine": return bool(self.actions)
		# Hangars don't cost power to land or launch.
		return False

	def current_fill(self):
		if self.type != "Hangar":
			print("Error: current_fill should not have been called on the component at", self.pos, "which is a", self.type)
		fill = 0
		for ship in self.contents: fill += ship.size
		return fill

	def summarize_contents(self):
		"""Return a string suitable for describing the Hangar's contents on the panel."""
		if self.type != "Hangar":
			print("Error: summarize_contents should not have been called on the component at", self.pos, "which is a", self.type)
		# First, make a dictionary of ship types to counts.
		ship_dict = {}
		for ship in self.contents:
			if ship.type not in ship_dict: ship_dict[ship.type] = 1
			else: ship_dict[ship.type] += 1
		# Now format it to a (relatively) pretty string.
		string = ''
		for type in ship_dict:
			if string == '': string = type + " x " + str(ship_dict[type])
			else: string += ", " + type + " x " + str(ship_dict[type])
		return string


class Composite:
	def __init__(self, components):
		self.compoments = components

class Station(set):
	"""Station is an extension of a list, and its methods basically just propagate the calls down to each Component."""
	def __init__(self, items=None):
		if items is None: items = set()
		set.__init__(self, items)
		self.power = 0
		self.salvage = 6
		self.thrust = 0

	def power_regen(self):
		for comp in self.power_generators(): self.power += POWER_GEN_SPEED
		self.power = min(self.power, self.maxpower())

	def power_generators(self):
		gens = []
		for comp in self:
			if comp.type == "Power Generator": gens.append(comp)
		return gens

	def maxpower(self):
		cap = 0
		for comp in self.power_generators(): cap += POWER_GEN_CAP
		return cap

	def projected_power(self):
		used = 0
		for comp in self:
			if comp.powered(): used += COMPONENT_POWER_USAGE
		return self.power - used

	def use_power(self):
		"""Called when a Component needs to use power. If it can, this will subtract the power and return True. If there isn't enough, this will not subtract it and return False."""
		if self.power >= COMPONENT_POWER_USAGE:
			self.power -= COMPONENT_POWER_USAGE
			return True
		return False

	def max_salvage(self):
		cap = 0
		for comp in self:
			if comp.type == "Factory": cap += FACTORY_CAP
		return cap

	def receive_salvage(self, entity):
		"""Used when a ship docks in a Hangar to pick up the Salvage from the ship."""
		transfer = min(entity.load, self.max_salvage() - self.salvage)
		self.salvage += transfer
		entity.load -= transfer

	def thrust_needed(self):
		return THRUST_PER_COMPONENT * len(self)

	def rotate(self):
		if self.thrust > 0:
			self.thrust -= self.thrust_needed()
			rot = 90
		else:
			self.thrust += self.thrust_needed()
			rot = -90
		for comp in self:
			comp.pos = rotate(comp.pos, rot)


class Weapon:
	def __init__(self, type, power, tier=1):
		self.type = type
		self.tier = tier
		self.power = power

	def __str__(self):
		return self.type + ": " + str(self.power)


class Salvage:
	def __init__(self, pos, amount):
		self.pos = pos
		self.amount = amount
		self.time = SALVAGE_START_TIME

	def decay(self):
		self.time -= 1
		if self.time < 0: self.amount -= 1

	def rect(self):
		return rect((self.pos,))

	def __str__(self):
		if self.time > 0: return str(self.amount) + " salvage, " + str(self.time) + " turns until decay"
		return str(self.amount) + " salvage, decaying"


class Mission:
	def __init__(self, filename):
		# There should be a shitton of tunable parameters in here. For now, just give them all placeholder values.
		self.starting_station = {
			(0, 0): "Connector",
			(-2, 0): "Connector",
			(2, 0): "Connector",
			(2, -2): "Shield Generator",
			(0, -2): "Power Generator",
			(0, 2): "Laser Turret",
			(-4, 0): "Hangar",
			(-2, -2): "Factory",
			(4, 0): "Engine",
		}
		self.starting_cards = 4

	def wave(self, num):
		"""This method acccepts a wave number and returns a dict of enemy type:count, a reward for clearing it, and a number of turns until the next wave arrives."""
		# TEMP
		return {'Drone': 6, 'Asteroid': 5}, None, 5


def hit_chance(attack, target):
	"""Calculates the hit rate of a given attack type against the target ship."""
	# Station components can never be missed by anything.
	if isinstance(target, Component) or target.type == "Asteroid": return 100
	if target.type in ('Probe', 'Drone', 'Kamikaze Drone'): return {'laser':75, 'missile':25}[attack]
	# Error message that should never get triggered.
	print("Did not have a hit chance for", attack, "against a", target.type)

COMPONENT_TYPES = (
	"Connector",
	'Shield Generator',
	'Power Generator',
	"Laser Turret",
	"Missile Turret",
	"Engine",
	"Hangar",
	"Factory",
)

# Entity types.

class Drone(Entity):
	def __init__(self, id, pos, rot=0, wave=0):
		Entity.__init__(self, id, "Drone", team='enemy', pos=pos, shape=(), rot=rot, salvage=DRONE_DROP, hull=DRONE_HULL, shield=DRONE_SHIELD, shield_regen=DRONE_SHIELD_REGEN, weapons=DRONE_WEAPONS, speed=DRONE_SPEED, wave=wave)

class Kamikaze_Drone(Entity):
	def __init__(self, id, pos, rot=0, wave=0):
		Entity.__init__(self, id, "Kamikaze Drone", team='enemy', pos=pos, shape=(), rot=rot, salvage=KAMIKAZE_DRONE_DROP, hull=KAMIKAZE_DRONE_HULL, shield=KAMIKAZE_DRONE_SHIELD, shield_regen=KAMIKAZE_DRONE_SHIELD_REGEN, weapons=KAMIKAZE_DRONE_WEAPONS, speed=KAMIKAZE_DRONE_SPEED, wave=wave)

# Player ships.

class Probe(Entity, SalvageCollector):
	def __init__(self, id, pos, rot=0):
		Entity.__init__(self, id, "Probe", team='player', pos=pos, shape=(), rot=rot, salvage=PROBE_DROP, hull=PROBE_HULL, shield=PROBE_SHIELD, shield_regen=PROBE_SHIELD_REGEN, weapons=PROBE_WEAPONS, speed=PROBE_SPEED, size=PROBE_SIZE)
		SalvageCollector.__init__(self)

class Asteroid(Entity):
	def __init__(self, id, pos, rot=0):
		Entity.__init__(self, id, "Asteroid", team=None, pos=pos, shape=(), rot=rot, salvage=ASTEROID_DROP, hull=ASTEROID_HULL, shield=0, shield_regen=(0,), weapons=(), speed=1)
