import socket, selectors, random, sys, json
from gamestate import *
from sockets import *

class Player:
	def __init__(self, name):
		self.name = name
		# self.done is used during the collect_input phase.
		self.done = False


def collect_input():
	global sock, players, gamestate
	while True:
		msg = recv_message(sock)
		print(msg)
		player_name = msg[:msg.index(':')]
		msg = msg[msg.index(':')+1:]
		# Assigning an action to a ship or component.
		if msg.startswith("ASSIGN:"):
			sock.send(encode(msg))
			interpret_assign(gamestate, msg[msg.index(':')+1:])
		# Clear an assignment.
		if msg.startswith("UNASSIGN ALL:"):
			sock.send(encode(msg))
			interpret_unassign(gamestate, msg[msg.index(':')+1:])
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
	global sock, players, gamestate
	for component in gamestate.station: marshal_action(component)
	for ship in gamestate.allied_ships: marshal_action(ship)

def enemies_move():
	global sock, players, gamestate
	for enemy in gamestate.enemy_ships:
		for i in range(enemy.speed):
			# Stop as soon as we find a good spot to shoot from.
			if enemy.all_in_range(gamestate, enemy=True):
				enemy.random_targets(gamestate, enemy=True)
				break
			valid_moves = []
			for move in ([0, 1], [0, -1], [1, 0], [-1, 0]):
				# TOOD: Make this support multi-space ships.
				if not gamestate.occupied([enemy.pos[0]+move[0], enemy.pos[1]+move[1]]): valid_moves.append(move)
			if not valid_moves: break
			enemy.movement.append(random.choice(valid_moves))
		# Now make it all happen.
		marshal_action(enemy)

def marshal_action(entity):
	global sock, players, gamestate
	"""Takes an Entity with all its actions set, reflects them in the gamestate, and then encodes them as JSON so the clients can do the same."""
	# We build a JSON list of targets with indexes corresponding to weapon indexes.
	targets = []
	for weapon in entity.weapons:
		if weapon.target:
			if random.randint(1, 100) <= hit_chance(weapon.type, weapon.target):
				# The third value in here is whether it hit.
				targets.append(weapon.target.pos+[True])
				# Remember to reflect the gamestate change server-side as well.
				weapon.target.take_damage(weapon.power, weapon.type)
				# Remove dead targets.
				if weapon.target.hull <= 0: gamestate.remove(weapon.target)
			else:
				targets.append(weapon.target.pos+[False])
		else: targets.append(None)
	sock.send(encode("ACTION:" + json.dumps(entity.pos) + ':' + json.dumps(entity.movement) + ':' + json.dumps(targets)))
	# Finally, play out the movement on the server side.
	for move in entity.movement: entity.move(move)

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
		changes = gamestate.upkeep()
		if changes: sock.send(encode("SPAWN ENEMIES:" + json.dumps(changes)))
		collect_input()
		sock.send(encode("PLAYER INPUT COLLECTED"))
		players_move()
		enemies_move()
		sock.send(encode("ROUND"))
		# Dump gamestate to a file so it can be restored in case of a crash.
		#gamestate.encode()

if __name__ == '__main__': main()
