import socket, random, sys, json
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
			# Find the player in the list and mark them as ready.
			for player in players:
				if player.name == player_name:
					player.done = True
					break
			# Check if all players are ready, and if so, move on.
			done = True
			for player in players:
				if not player.done:
					done = False
					break
			if done: return

def enemy_ai():
	for enemy in gamestate.ships:
		if enemy.team != 'enemy': continue
		command = assign_random_targets(gamestate, enemy)
		if command:
			interpret_assign(gamestate, command)
			sock.send(encode(command))
		# If there are still untargeted weapons after that, it's because the enemy wasn't in range, so if it can, it should move and try again.
		while enemy.untargeted() and enemy.moves_left():
			move_cmd = assign_random_move(gamestate, enemy)
			if not move_cmd:
				break
			interpret_assign(gamestate, move_cmd)
			sock.send(encode(move_cmd))
			command = assign_random_targets(gamestate, enemy)
			if command:
				interpret_assign(gamestate, command)
				sock.send(encode(command))

def asteroid_ai():
	for asteroid in gamestate.asteroids:
		if random.random() <= ASTEROID_MOVE_CHANCE:
			command = assign_random_move(gamestate, asteroid)
			interpret_assign(gamestate, command)
			sock.send(encode(command))

def process_actions():
	"""Takes an Entity with all its actions set, plays them out, and then encodes them as JSON and sends them so the clients can do the same."""
	# TEMP: Just play them out server-side; don't fill in accuracy or send them out or anything.
	for _ in gamestate.playout(): pass
	#sock.send(encode("ACTION:" + json.dumps(orig_pos) + ';' + json.dumps(entity.actions)))

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
		enemy_ai()
		asteroid_ai()
		process_actions()
		sock.send(encode("ROUND"))
		if abs(gamestate.station.thrust) >= gamestate.station.thrust_needed():
			gamestate.station.rotate()
		changes = gamestate.upkeep()
		if changes: sock.send(encode("SPAWN ENEMIES:" + json.dumps(changes)))
		# Dump gamestate to a file so it can be restored in case of a crash.
		#gamestate.encode()

if __name__ == '__main__': main()
