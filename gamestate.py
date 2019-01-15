import random

class Gamestate:
	def __init__(self, players, mission='test', json=''):
		if json:
			self.load_json(json)
			return
		else: # If no JSON, we load a new game from a mission.
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
	#def encode(self):
	#	"""Encodes the Gamestate into a JSON object that can be sent over the network."""
	def draw_cards(self, num): # Redo this func to return the updates necessary
		draws = []
		for i in range(num):
			draws += {'player':self.players[self.draw_pointer], 'card':draw_card()}
			self.draw_pointer += 1
			if self.draw_pointer >= len(self.players): self.draw_pointer = 0
	def upkeep(self):
		for ship in self.allied_ships + self.enemy_ships:
			ship.already_moved = False
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
				inserts.append({'type':enemy_type, 'pos':self.find_open_pos()})
		print(inserts)
		return inserts
	def find_open_pos(self, size=(1,1)):
		"""Searches through all game objects and find an unoccupied position to put the enemy on."""
		# Placeholder.
		return (random.randint(1,15), random.randint(1,15))
	def insert_enemies(self, enemies):
		"""Inserts the given enemies into the gamestate. Takes a tuple of dicts with enemy type names as keys and their board positions as values."""
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
	def __init__(self, pos, rot, hull, shield=0, shield_regen=(0,), weapons=()):
		# Position on the grid. Window pixel position is calculated from this.
		self.pos = pos
		# Rotation is stored as as 2-element tuple, like (0, -1) for up.
		self.rot = rot
		self.maxhull = self.hull = hull
		self.maxshield = self.shield = shield
		self.shield_regen_amounts = shield_regen_amounts
		self.shield_regen_pointer = 0
		self.already_moved = False
		self.stored_action = None
	def move(self, change):
		self.pos[0] += change[0]
		self.pos[1] += change[1]
		if self.window:pass # TODO: animation of moving


class Ship(Entity):
	def __init__(self, pos, rot, hull, shield, shield_regen, weapons, speed, salvage, wave=0, size=0):
		Entity.__init__(self, pos=pos, rot=rot, hull=hull, shield=shield, shield_regen=shield_regen, weapons=weapons)
		self.speed = speed
		# Enemy only fields.
		self.wave = wave
		# Ally only fields.
		self.size = size
		# This field is used for both, but means something different.
		self.salvage = salvage

# A Station Component.
class Component(Entity):
	def __init__(self, station, pos, rot, hull):
		Entity.__init__(self, pos=pos, rot=rot, hull=hull, shield=0, shield_regen=(0,))
	@property
	def shield(self):
		return 100 # calculate which shield generators are applying to it

class Composite:
	def __init__(self, components):
		self.compoments = components

class Station(Composite): pass

class Weapon:
	def __init__(self, type, power, tier=1):
		self.type = type
		self.tier = tier
		self.power = power

class Mission:
	def __init__(self, filename):
		# There should be a shitton of tunable parameters in here. For now, just give them all placeholder values.
		self.starting_cards = 4
	def wave(self, num):
		"""This method acccepts a wave number and returns a dict of enemy type:count, a reward for clearing it, and a number of turns until the next wave arrives."""
		# Temp code:
		return {'Drone':3}, None, 5

# The functions below initialize entity types.

def drone(pos, rot):
	weeapons = (Weapon('laser', 1, 1),)
	return Ship(pos, rot, 5, 0, (0,), weapons, 3, 1)
