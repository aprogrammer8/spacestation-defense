class Gamestate:
	def __init__(self, filename='', mission=''):
		if filename:
			self.load(filename)
			return
		self.enemy_ships = []
		self.allied_ships = []
		self.station = Station()
		self.wave = 0
		self.mission = # Some kind of read_mission fumc? I need a mission class too