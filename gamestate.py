import random

class Gamestate:
	def __init__(self, players, mission='test', json=''):
		if json:
			self.load_json(json)
			return
		else: # If no JSON, we load a new game from a mission.
			self.station = []
			self.enemy_ships = []
			self.allied_ships = []
			self.asteroids = []
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
		for pos in data: self.station.append(Component(list(pos), self.station, data[pos], 0, 50))
	#def encode(self):
	#	"""Encodes the Gamestate into a JSON object that can be sent over the network."""
	def draw_cards(self, num): # Redo this func to return the updates necessary
		draws = []
		for i in range(num):
			draws += {'player':self.players[self.draw_pointer], 'card':draw_card()}
			self.draw_pointer += 1
			if self.draw_pointer >= len(self.players): self.draw_pointer = 0
	def upkeep(self):
		for ship in self.allied_ships: ship.already_moved = False
		for ship in self.enemy_ships: ship.already_moved = False
		for component in self.station: component.already_moved = False
		for asteroid in self.asteroids: asteroid.already_moved = False
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
		return inserts
	def occupied(self, pos):
		"""Checks if a gameboard space is occupied."""
		for entity in self.station:
			if entity.occupies(pos): return entity
		for entity in self.allied_ships:
			if entity.occupies(pos): return entity
		for entity in self.enemy_ships:
			if entity.occupies(pos): return entity
		for entity in self.asteroids:
			if entity.occupies(pos): return entity
	def find_open_pos(self, size=(1,1)):
		"""Searches through all game objects and find an unoccupied position to put the enemy on."""
		while True:
			pos = [random.randint(1,15), random.randint(1,15)]
			if not self.occupied(pos): return pos
	def insert_enemies(self, enemies):
		"""Inserts the given enemies into the gamestate. Takes a sequence of dicts with enemy type names as keys and their board positions as values."""
		for enemy in enemies:
			if enemy['type'] == "Drone": self.enemy_ships.append(drone(enemy['pos'], enemy['rot']))

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
	def __init__(self, pos, shape, rot, hull, shield=0, shield_regen=(0,), weapons=()):
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
		self.already_moved = False
		self.stored_action = None
	def move(self, change):
		self.pos[0] += change[0]
		self.pos[1] += change[1]
	def occupies(self, space):
		"""Returns whether the Entity is on a space."""
		if self.pos == space: return True
		for pos in self.shape:
			pos = rotate(pos, self.rot)
			if pos[0] + self.pos[0] == space[0] and pos[1] + self.pos[1] == space[1]: return True
		return False

class Ship(Entity):
	def __init__(self, type, pos, shape, rot, hull, shield, shield_regen, weapons, speed, salvage, wave=0, size=0):
		Entity.__init__(self, pos, shape, rot=rot, hull=hull, shield=shield, shield_regen=shield_regen, weapons=weapons)
		self.type = type
		self.speed = speed
		# Enemy only fields.
		self.wave = wave
		# Ally only fields.
		self.size = size
		# This field is used for both, but means something different.
		self.salvage = salvage

# A Station Component.
class Component(Entity):
	def __init__(self, pos, station, type, rot, hull):
		Entity.__init__(self, pos, shape=((1,0),(0,1),(1,1)), rot=rot, hull=hull, shield=0, shield_regen=(0,))
		if type not in COMPONENT_TYPES: raise TypeException("Not a valid station component type: " + type)
		self.station = station
		self.type = type
	@property
	def shield(self):
		return 100 # calculate which shield generators are applying to it
	@property
	def maxshield(self):
		return 100

class Composite:
	def __init__(self, components):
		self.compoments = components

class Weapon:
	def __init__(self, type, power, tier=1):
		self.type = type
		self.tier = tier
		self.power = power

class Mission:
	def __init__(self, filename):
		# There should be a shitton of tunable parameters in here. For now, just give them all placeholder values.
		self.starting_station = {
			(7,7): "Shield Generator"
		}
		self.starting_cards = 4
	def wave(self, num):
		"""This method acccepts a wave number and returns a dict of enemy type:count, a reward for clearing it, and a number of turns until the next wave arrives."""
		# Temp code:
		return {'Drone':3}, None, 5

def rotate(pos, rot):
	if rot == 0: return pos
	if rot == 90: return [-pos[1], pos[0]]
	if rot == 180: return [-pos[0], -pos[1]]
	if rot == 270: return [pos[1], -pos[0]]
	print("Not a valid rotation:", rot)
	return pos


# The functions below initialize entity types.

def drone(pos, rot=0):
	weapons = (Weapon('laser', 1, 1),)
	return Ship("Drone", pos, (), rot, 5, 0, (0,), weapons, 3, 1)

COMPONENT_TYPES = ('Shield Generator')
