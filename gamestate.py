class Gamestate:
	def __init__(self, players, mission='test', json=''):
		if jsom:
			self.load_json(json)
			return
		else: # If no JSON, we load a new game from a mission.
			self.enemy_ships = []
			self.allied_ships = []
			self.asteroids = []
			self.wave = 0
			self.round = 0
			# Number of turns left before the next wave should come.
			self.time = 0
			# Rewards for each sent wave. The gamestate tracks this itself for restoration purposes.
			self.rewards = []
			self.players = []
			for player in players: self.players += Player(player)
			# The draw pointer is used to keep track of who will get the next card the players draw.
			self.draw_pointer = 0
			self.mission = Mission("missions/"+mission)
			self.draw_cards(self.mission.starting_cards)
			self.upkeep()
	def draw_cards(self, num):
		for i in range(num):
			self.players[self.draw_pointer].hand += draw_card()
			self.draw_pointer += 1
			if self.draw_pointer >= len(self.players): self.draw_pointer = 0
	def upkeep(self):
		for ship in self.allied_ships + self.enemy_ships:
			ship.already_moved = False
		self.time -= 1
		if self.time <= 0:
			wave, self.rewards[self.wave], self.time = self.mission.next()
			self.send_enemies(wave)
			self.nextwave += 1
	def send_enmeies(self, enemies):
		for enemy_type in enemies:
			for i in range(enemies[enemy_type]):
				if enemy_type == 'drone':
					pos = (random.randint(1, 15), random.randint(1, 15))
					rot = (0, 1)
					drone(self.window, pos, rot)

class Player:
	def __init__(self, name, cards=[]):
		self.name = name
		self.hand = cards

class Card:
	def __init__(self,name):
		self.name=name

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
	def next(self, wave):
		# The wave parameter is the number, since Gamestate tracks that and there's no point tracking it in two places.
		# This method will return a dict of enemy type:count, a reward for clearing it, a number of turns till the next wave.
		# Temp code:
		return {'drone':3}, None, 5

# The functions below initialize entity types.

def drone(pos, rot):
	weeapons = (Weapon('laser', 1, 1),)
	return Ship(pos, rot, 5, 0, (0,), weapons, 3, 1)
