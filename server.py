import socket, selectors, random, sys, json
from gamestate import *
from sockets import *

class Player:
	def __init__(self, name):
		self.name = name
		# self.done is used during the collect_input phase.
		self.done = False


def collect_input():
	while True:
		msg = recv_message(sock)
		print(msg)
		player_name = msg[:msg.index(':')]
		msg = msg[msg.index(':')+1:]
		# Assigning an action to a ship or component.
		if msg.startswith("ASSIGN:"):
			sock.send(encode(msg))
			interpret_assign(gamestate, msg[msg.index(':')+1:])
		# Playing a card.
		elif msg.startswith("PLAY:"):
			pass
		# When a player is ready to proceed.
		elif msg == "DONE":
			for player in players:
				if player.name == player_name:
					player.done = True
					break
			done = True
			for player in players:
				if not player.done:
					done = False
					break
			if done: break


def players_move():
	# This one is very simple since no AI is necessary.
	for component in gamestate.station: process_actions(component)
	for ship in gamestate.allied_ships: process_actions(ship)


def enemies_move():
	for enemy in gamestate.enemy_ships:
		enemy.random_targets(gamestate, enemy=True)
		while enemy.untargeted() and enemy.moves_left():
			valid_moves = []
			for move in ([0, 1], [0, -1], [1, 0], [-1, 0]):
				if not gamestate.invalid_move(enemy, move): valid_moves.append(move)
			if not valid_moves: break
			enemy.actions.append({'type': 'move', 'move': random.choice(valid_moves)})
			enemy.random_targets(gamestate, enemy=True)
		# Now make it happen.
		process_actions(enemy)

def process_actions(entity):
	"""Takes an Entity with all its actions set, plays them out, and then encodes them as JSON and sends them so the clients can do the same."""
	skip = False
	# Subtract power for used components (except Hangars).
	if type(entity) == Component and entity.type != "Hangar":
		if not entity.powered() or not gamestate.station.use_power():
			skip = True
	# We'll need the original at the end if the Entity moved.
	orig_pos = entity.pos[:]
	if not skip:
		entity.shield_regen()
		playout_actions(entity)
	sock.send(encode("ACTION:" + json.dumps(orig_pos) + ';' + json.dumps(entity.actions)))

def playout_actions(entity):
	"""Takes an Entity and plays out its actions, reflecting the changes in the gamestate."""
	for action in entity.actions:
		# Turning off power to auto-running components.
		if action['type'] == 'off':
			# Nothing we need to do here.
			continue
		# Engines.
		if action['type'] == 'boost':
			gamestate.station.thrust += ENGINE_SPEED * action['dir']
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
			if not gamestate.hangar_launch(entity, action['index'], action['pos'], action['rot']):
				# If the launch is illegal, we need to not send it back out to the clients.
				return
		# Moves.
		elif action['type'] == 'move':
			# Don't process remaining actions if the ship lands in a Hangar.
			if gamestate.move(entity, action['move']) == "LANDED": break
		# Attacks.
		elif action['type'] == 'attack':
			weapon = entity.weapons[action['weapon']]
			target = gamestate.occupied(action['target'])
			# This should happen if we killed the target in a previous attack.
			if not target: continue
			# Determine whether the attack hits.
			action['hit'] = random.randint(1, 100) <= hit_chance(weapon.type, target)
			# Nothing is changed in the gamestate if the attack misses.
			if not action['hit']: continue
			target.take_damage(weapon.power, weapon.type)
			# Remove dead targets.
			if target.hull <= 0:
				gamestate.remove(target)
				# Spawn salvage pile.
				gamestate.add_salvage(Salvage(target.pos, target.salvage))

		else: print(action, "is an invalid action")

	# The legality checks are handled inside the method.
	if entity.type == "Factory": entity.work()

def main():
	global sock, players, gamestate
	sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	sock.connect(sys.argv[1])
	# Receive the list of players.
	player_names = recv_message(sock).split(",")
	players = []
	for name in player_names: players.append(Player(name))
	mission = recv_message(sock)
	gamestate = Gamestate(players, mission)
	changes = gamestate.draw_cards(gamestate.mission.starting_cards)
	if changes: sock.send(encode(json.dumps(changes)))
	gamestate.init_station(gamestate.mission.starting_station)
	# The clients will initialize the station on their own, at least for now.
	#sock.send(encode("SPAWN COMPONENTS:" + json.dumps(changes)))
	while True:
		collect_input()
		sock.send(encode("DONE"))
		players_move()
		enemies_move()
		sock.send(encode("ROUND"))
		if abs(gamestate.station.thrust) >= gamestate.station.thrust_needed():
			gamestate.station.rotate()
		changes = gamestate.upkeep()
		if changes: sock.send(encode("SPAWN ENEMIES:" + json.dumps(changes)))
		# Dump gamestate to a file so it can be restored in case of a crash.
		#gamestate.encode()

if __name__ == '__main__': main()
