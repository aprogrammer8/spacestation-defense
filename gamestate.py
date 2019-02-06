import random, json

class Gamestate:
	def __init__(self, players, mission='test', json=''):
		if json:
			self.load_json(json)
			return
		else: # If no JSON, we load a new game from a mission.
			self.station = Station()
			self.enemy_ships = []
			self.allied_ships = [probe([0, 5])]
			self.asteroids = []
			self.salvages = {}
			self.nextwave = 0
			self.round = 0
			# Number of turns left before the next wave should come.
			self.time = 0
			# Rewards for each sent wave. The gamestate tracks this itself for restoration purposes.
			self.rewards = {}
			self.players = []
			for player in players: self.players.append(Player(player))
			# The draw pointer is used to keep track of who will get the next card the players draw.
			self.draw_pointer = 0
			self.mission = Mission("missions/"+mission)
	def init_station(self, data):
		for pos in data: self.station.append(Component(list(pos), self.station, data[pos], 0, COMPONENT_HULL))
	#def encode(self):
	#	"""Encodes the Gamestate into a JSON object that can be sent over the network."""
	def draw_cards(self, num):
		draws = []
		for i in range(num):
			draws += {'player':self.players[self.draw_pointer], 'card':draw_card()}
			self.draw_pointer += 1
			if self.draw_pointer >= len(self.players): self.draw_pointer = 0
		return draws
	def clear(self):
		"""Clears the stored actions and moves of all gamestate objects."""
		for ship in self.allied_ships: ship.actions = []
		for ship in self.enemy_ships: ship.actions = []
		for component in self.station: component.actions = []
		for asteroid in self.asteroids: asteroid.actions = []
	def upkeep(self, clientside=False):
		self.clear()
		# Regen everyone's shields.
		for ship in self.allied_ships: ship.shield_regen()
		for ship in self.enemy_ships: ship.shield_regen()
		self.station.shield_regen()
		self.station.power_regen()
		# Salvage decay. We make a new dict to avoid messings things up by changing the size during iteration.
		new_salvages = {}
		for pos in self.salvages:
			salvage = self.salvages[tuple(pos)]
			salvage.decay()
			if salvage.amount > 0: new_salvages[tuple(pos)] = salvage
		self.salvages = new_salvages
		if not clientside:
			# Advance the mission track.
			self.time -= 1
			if self.time <= 0:
				wave, self.rewards[self.nextwave], self.time = self.mission.wave(self.nextwave)
				self.nextwave += 1
				return self.send_enemies(wave)
	def send_enemies(self, enemies):
		"Accepts enemies to send as passed by the mission's wave method and returns the changes that must be made to the gamestate."
		inserts = []
		for enemy_type in enemies:
			for i in range(enemies[enemy_type]):
				# The rot value of 0 is a placeholder.
				inserts.append({'type':enemy_type, 'pos':self.find_open_pos(), 'rot':0})
				self.insert_enemies((inserts[-1],))
		return inserts
	def insert_enemies(self, enemies):
		"""Inserts the given enemies into the Gamestate. Takes a sequence of dicts with enemy type names as keys and their board positions as values."""
		for enemy in enemies:
			if enemy['type'] == "Drone": self.enemy_ships.append(drone(enemy['pos'], enemy['rot']))
			elif enemy['type'] == "Kamikaze Drone": self.enemy_ships.append(kamikaze_drone(enemy['pos'], enemy['rot']))
			else: print("Unrecognized enemy type:", enemy)
	def add_salvage(self, pos, salvage):
		# Salvage positions have to be tuples, because they're keys in a dict. It's not a problem because they never move anyway.
		if type(pos) != tuple: pos = tuple(pos)
		if pos not in self.salvages:
			# Easy case, we just add it.
			self.salvages[pos] = salvage
		else:
			# If there's already one, it stacks.
			self.salvages[pos].amount += salvage.amount
			self.salvages[pos].time = max(self.salvages[pos].time, salvage.time)
	def occupied(self, pos):
		"""Checks if a gameboard space is occupied."""
		for entity in self.station:
			if pos in entity.spaces(): return entity
		for entity in self.allied_ships:
			if pos in entity.spaces(): return entity
		for entity in self.enemy_ships:
			if pos in entity.spaces(): return entity
		for entity in self.asteroids:
			if pos in entity.spaces(): return entity
	def occupied_area(self, spaces, exclude=None):
		"""Checks if any of a sequence of spaces is occupied."""
		for space in spaces:
			entity = self.occupied(space)
			if entity and entity != exclude: return entity
	def find_open_pos(self, size=(1,1)):
		"""Searches through all game objects and find an unoccupied position to put the enemy on."""
		while True:
			pos = [random.randint(-5,5), random.randint(5,7)]
			if not self.occupied(pos): return pos
	def invalid_move(self, entity, move):
		"""Helper function that takes an Entity and a proposed move, and checks all destination spaces."""
		# Found the bug: it's projecting from the already projected space.
		for space in entity.projected_spaces():
			occupied = self.occupied([space[0]+move[0], space[1]+move[1]])
			# Have to also check for equality, because big ships will overlap themselves when they move.
			if occupied and occupied != entity: return occupied
		return False
	def in_range(self, source, type, target):
		"""Determines whether a source is in range of a target. type is the type of attack - some might have range limits."""
		# Try all source spaces to all target spaces.
		for source_space in source.projected_spaces():
			for target_space in target.spaces():
				if self.path(source, source_space, type, target_space): return True
		return False
	def path(self, source_entity, source, type, target):
		dist = [abs(target[0] - source[0]), abs(target[1] - source[1])]
		total_dist = dist[0] + dist[1]
		# It's ugly, but it finds the distance with magnitude reduced to 1 or -1.
		dir = ({True: 1, False: -1}[target[0]>source[0]], {True: 1, False: -1}[target[1]>source[1]])
		probe = [source[0], source[1]]
		step_x, step_y = dist[0]/total_dist, dist[1]/total_dist
		counter = [0, 0]
		while probe != target:
			if probe[0] > 100 or probe[1] > 100: print("probe crashed, at ", probe, "from", source, "aimed at", target, "; stepx=", step_x, "; step_y=", step_y, "; total_dist=", total_dist, "; dir=", dir)
			if probe != source:
				block = self.occupied(probe)
				# Make sure we don't fail if we run over another space of the same entity.
				if block and block != source_entity: break
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
	def remove(self, entity):
		for e in self.station:
			if e == entity:
				self.station.remove(e)
				return
		for e in self.allied_ships:
			if e == entity:
				self.allied_ships.remove(e)
				return
		for e in self.enemy_ships:
			if e == entity:
				self.enemy_ships.remove(e)
				return
		for e in self.asteroids:
			if e == entity:
				self.asteroids.remove(e)
				return


def slope(p1, p2):
	"""Returns the slope between two points, handling division by zero with a high value if the numerator is not also zero, or 1 if it is."""
	dist = (abs(p2[0] - p1[0]), abs(p2[1] - p1[1]))
	if dist[0] == 0:
		if dist[1] == 0: return 1
		return 100
	return dist[1]/dist[0]


class Player:
	def __init__(self, name, cards=[]):
		self.name = name
		self.hand = cards

class Card:
	def __init__(self,name):
		self.name = name

def draw_card():
	return Card("Repair")

# An Entity is anything with a position on the board.
class Entity:
	def __init__(self, pos, shape, rot, salvage, hull, shield=0, shield_regen=(0,), weapons=(), speed=0):
		self.pos = pos
		# self.shape is a tuple of other positions expressed as offsets from the main pos (when rot == 0), that the Entity also occupies (used for Entities bigger than 1x1).
		self.shape = shape
		# Rotation is stored as a number of degrees, to help with displaying.
		self.rot = rot
		self.maxhull = self.hull = hull
		# Components can't have their shield property set, because it's not really theirs.
		if type(self) != Component: self.maxshield = self.shield = shield
		self.shield_regen_amounts = shield_regen
		self.shield_regen_pointer = 0
		self.weapons = weapons
		self.speed = speed
		# This field refers to salvage dropped when the ship is destroyed.
		self.salvage = salvage
		# The sequence of actions the Entity plans to make.
		self.actions = []
	def move(self, change):
		self.pos[0] += change[0]
		self.pos[1] += change[1]
	def spaces(self):
		"""Returns all spaces the Entity occupies."""
		return spaces(self.pos, self.shape, self.rot)
	def projected_spaces(self):
		final_pos = self.pos
		for move in filter(lambda x: len(x)==2, self.actions):
			final_pos = [final_pos[0] + move[0], final_pos[1] + move[1]]
		return spaces(final_pos, self.shape, self.rot)
	def rect(self):
		"""Returns the top-left space of the Entity and the bottom right."""
		return rect(self.spaces())
	def move_rect(self):
		"""Like Entity.rect, but encompasses both current position and projected position."""
		return rect(self.spaces()+self.projected_spaces())
	def take_damage(self, dmg, type):
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
		if self.shield_regen_pointer < len(self.shield_regen_amounts) - 1: self.shield_regen_pointer += 1
	def moves_left(self):
		moves = self.speed
		for action in self.actions:
			# Moves are always length 2.
			if len(action) == 2: moves -= 1
		return moves
	def target(self, index, pos):
		action_index = 0
		for action in self.actions:
			if len(action) > 2 and action[0] == index:
				self.actions[action_index] = [index, *pos]
				return
			action_index += 1
		self.actions.append([index, *pos])
	def desc_target(self, weapon, gamestate):
		"""Takes a weapon and returns a string describing what it's targeting, if anything."""
		index = self.weapons.index(weapon)
		for action in self.actions:
			if len(action) > 2 and action[0] == index:
				target = gamestate.occupied(action[1:3])
				if target: return ", targeting " + target.type + " at " + str(target.pos)
		return ""
	def untargeted(self):
		"""Returns all weapons with no target."""
		# First, construct a list of indexes of weapons.
		weapons = []
		i = 0
		for w in self.weapons:
			weapons.append(i)
			i += 1
		# Now filter out the ones that have targets.
		for action in self.actions:
			if len(action) > 2: weapons.remove(action[0])
		return weapons
	def all_in_range(self, gamestate, enemy):
		"""Returns all weapons that can hit something from the opposing team from our current position. enemy is a bool saying which team this Entity is on."""
		weapons = []
		if enemy: targets = gamestate.allied_ships + gamestate.station
		else: targets = gamestate.enemy_ships + gamestate.asteroids
		for weapon in self.weapons:
			for target in target:
				if gamestate.in_range(self, weapon.type, target):
					weapons.append(self.index[weapon])
					break
		return weapons
	def random_targets(self, gamestate, enemy):
		"""Randomly target all weapons at random enemies."""
		if enemy: targets = gamestate.allied_ships + gamestate.station
		else: targets = gamestate.enemy_ships + gamestate.asteroids
		i = 0
		for weapon in self.untargeted():
			# For now, we just pick out the first possible target.
			for target in targets:
				if gamestate.in_range(self, self.weapons[weapon], target):
					self.actions.append([i, *target.pos])
					break

class Ship(Entity):
	def __init__(self, type, team, pos, shape, rot, salvage, hull, shield, shield_regen, weapons, speed, wave=0, size=0):
		Entity.__init__(self, pos=pos, shape=shape, rot=rot, salvage=salvage, hull=hull, shield=shield, shield_regen=shield_regen, weapons=weapons, speed=speed)
		self.type = type
		self.team = team
		# Enemy only fields.
		self.wave = wave
		# Ally only fields.
		self.size = size
		# Probes can carry salvage.
		if self.type == "Probe": self.load = 0
	def collect(self, salvage):
		"""The Ship picks up a piece of salvage. Only Probes can do this."""
		if self.type != "Probe":
			print("Something is wrong, this ship cannot pick up salvage:", self.type, self.pos)
			return
		collected = min(salvage.amount, PROBE_CAPACITY-self.load)
		self.load += collected
		salvage.amount -= collected

# A Station Component.
class Component(Entity):
	def __init__(self, pos, station, type, rot, hull):
		Entity.__init__(self, pos, shape=((1,0),(0,1),(1,1)), rot=rot, salvage=COMPONENT_SALVAGE, hull=hull, shield=0, shield_regen=(0,))
		if type not in COMPONENT_TYPES: raise TypeException("Not a valid station component type: " + type)
		self.station = station
		self.type = type
		if type == "Shield Generator":
			self.__shield = self.__maxshield = SHIELD_GEN_CAP
			self.shield_regen_amounts = SHIELD_GEN_REGEN
		if type == "Laser Turret":
			self.weapons = (
				Weapon('laser', 5, 2),
				Weapon('laser', 5, 2),
				Weapon('laser', 5, 2)
			)
		if type == "Power Generator":
			# For now, the rule for starting power is half the max power.
			self.station.power += POWER_GEN_CAP // 2
		if type == "Hangar":
			self.contents = []
	def shield_generators(self):
		"""Find all Shield Generators covering this Component."""
		gens = []
		for comp in self.station:
			if comp.type != "Shield Generator": continue
			if abs(comp.pos[0] - self.pos[0]) + abs(comp.pos[1] - self.pos[1]) < 6:
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
		while diff>0:
			# Spread out the damage over all in-range generators.
			for gen in gens:
				if gen.shield>0:
					gen.__shield -= 1
					gen.shield_regen_pointer = 0
					diff -= 1
	def powered(self):
		"""Returns whether the Component is currently using power."""
		if self.type == "Shield Generator": return True
		if self.type == "Laser Turret": return bool(self.actions)
		return False

class Composite:
	def __init__(self, components):
		self.compoments = components

class Station(list):
	def __init__(self, li=[]):
		list.__init__(self, li)
		self.power = 0
	def shield_regen(self):
		for comp in self:
			if comp.type == "Shield Generator": comp.shield_regen()
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

class Weapon:
	def __init__(self, type, power, tier=1):
		self.type = type
		self.tier = tier
		self.power = power
	def __str__(self):
		return self.type + ": " + str(self.power)

class Salvage:
	def __init__(self, amount):
		self.amount = amount
		self.time = SALVAGE_START_TIME
	def decay(self):
		self.time -= 1
		if self.time < 0: self.amount -= 1
	def __str__(self):
		if self.time > 0: return str(self.amount) + " salvage, " + str(self.time) + " turns until decay"
		return str(self.amount) + " salvage, decaying"

class Mission:
	def __init__(self, filename):
		# There should be a shitton of tunable parameters in here. For now, just give them all placeholder values.
		self.starting_station = {
			(2,0): "Shield Generator",
			(0,-2): "Power Generator",
			(-2,0): "Laser Turret",
			(0,0): "Connector",
			(0,2): "Hangar",
		}
		self.starting_cards = 4
	def wave(self, num):
		"""This method acccepts a wave number and returns a dict of enemy type:count, a reward for clearing it, and a number of turns until the next wave arrives."""
		# Temp code:
		return {'Drone':6}, None, 5

def rotate(pos, rot):
	if rot == 0: return pos
	if rot == 90: return [-pos[1], pos[0]]
	if rot == 180: return [-pos[0], -pos[1]]
	if rot == 270: return [pos[1], -pos[0]]
	print("Not a valid rotation:", rot)
	return pos

def spaces(main_pos, shape, rot):
	"""Takes an Entity's position, shape and rotation and returns all the positions it occupies."""
	print("in spaces for", main_pos)
	spaces = [main_pos]
	for pos in shape:
		print("spaces: in loop on", pos)
		pos = rotate(pos, rot)
		spaces.append([pos[0] + main_pos[0], pos[1] + main_pos[1]])
	return spaces

def rect(spaces):
	"""Takes a sequence of spaces and returns the inputs for a Rect containing them."""
	left = right = spaces[0][0]
	top = bottom = spaces[0][1]
	for space in spaces[1:]:
		if space[0] < left: left = space[0]
		if space[0] > right: right = space[0]
		if space[1] < top: top = space[1]
		if space[1] > bottom: bottom = space[1]
	return left, top, right-left+1, bottom-top+1

def hit_chance(attack, target):
	"""Calculates the hit rate of a given attack type against the target ship."""
	# Station components can never be missed by anything.
	if type(target) == Component: return 100
	if target.type in ('Probe', 'Drone', 'Kamikaze Drone'): return {'laser':75, 'missile':25}[attack]
	# Error message that should never get triggered.
	print("Did not have a hit chance for", attack, "against a", target.type)

# The functions below initialize entity types.

def drone(pos, rot=0):
	weapons = (Weapon('laser', 1, 1),)
	return Ship("Drone", team='enemy', pos=pos, shape=(), rot=rot, salvage=1, hull=5, shield=0, shield_regen=(0,), weapons=weapons, speed=3)

def kamikaze_drone(pos, rot=0):
	return Ship("Kamikaze Drone", team='enemy', pos=pos, shape=(), rot=rot, salvage=1, hull=10, shield=0, shield_regen=(0,), weapons=(), speed=5)

# Player ships.

def probe(pos, rot=0):
	return Ship("Probe", team='player', pos=pos, shape=(), rot=rot, salvage=1, hull=10, shield=0, shield_regen=(0,), weapons=(), speed=3, size=1)

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

# Game rule constants.
COMPONENT_HULL = 50
COMPONENT_SALVAGE = 20
SHIELD_GEN_CAP = 100
SHIELD_GEN_REGEN = (0, 1, 3, 8)
POWER_GEN_SPEED = 5
POWER_GEN_CAP = 25
COMPONENT_POWER_USAGE = 2
ENGINE_SPEED = 2
SALVAGE_START_TIME = 5
PROBE_CAPACITY = 5
HANGAR_CAPACITY = 20

def interpret_assign(gamestate, cmd):
	unit_pos = json.loads(cmd[:cmd.index(':')])
	unit = gamestate.occupied(unit_pos)
	unit.actions = json.loads(cmd[cmd.index(':')+1:])

# Unassign commands clear all actions for a ship, both movement and targeting.
def interpret_unassign(gamestate, cmd):
	unit_pos = json.loads(cmd)
	unit = gamestate.occupied(unit_pos)
	unit.actions = []
