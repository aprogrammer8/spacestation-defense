class Gamestate:
	def __init__(self, json='', mission='test'):
		if jsom:
			self.load_json(json)
			return
		else: # If no JSON, we load the starting state of the mission.
			self.mission = Mission("missions/"+mission)
			#self.enemy_ships = []
			#self.allied_ships = []
			#self.station = Station()
			self.wave = 0
			self.round = 0

# An Entity is anything with a position on the board.
class Entity:
	def __init__(self, window, pos, image, rot, hull, shield=0, shield_regen=(0,), weapons=()):
		self.window = window # Set to none on the server side.
		# Position on the grid. Window pixel position is calculated from this.
		self.pos = pos
		self.image = image
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
	def __init__(self, window, pos, image, rot, hull, shield, shield_regen, speed, salvage, wave=0, size=0):
		Entity.__init__(self, window=window, pos=pos, image=image, rot=rot, hull=hull, shield=shield, shield_regen=shield_regen)
		self.speed = speed
		# Enemy only fields.
		self.wave = wave
		# Ally only fields.
		self.size = size
		# This field is used for both, but means something different.
		self.salvage = salvage

# A Station Component.
class Component(Entity):
	def __init__(self, window, station, pos, image, rot, hull):
		Entity.__init__(self, window=window, pos=pos, image=image, rot=rot, hull=hull, shield=0, shield_regen=(0,))
	@property
	def shield(self):
		return 100 # calculate which shield generators are applying to it

class Composite:
	def __init__(self, components):
		self.compoments = components

class Station(Composite): pass

class Weapon():
	def __init__(self, type, power, tier=1):
		self.type = type
		self.tier = tier
		self.power = power

class Mission:
	def __init__(self, filename):
		# There should be a shitton of tunable parameters in here.
		pass
	def query(self, wave):
		# The wave parameter is the number, since Gamestate tracks that and there's no point tracking it in two places.
		# This method will return a list of enemies, a reward for clearing it, a number of turns till the next wave.
		# Temp code:
		return [stats.drone(), stats.drone(), stats.drone()], None, 5
