import socket, selectors, random, sys, json
from gamestate import *
from sockets import *

def collect_input():
	while True:
		msg = recv_message(sock)
		# Assigning an action to a ship or component. Complete actions only.
		if msg.startswith("ASSIGN:"):
			print(msg)
		# Playing a card.
		elif msg.startswith("PLAY:"):
			print(msg)



def main():
	global sock, players, gamestate
	sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	#sock.setblocking(False)
	#selector = selectors.DefaultSelector()
	#selector.register(sock, selectors.EVENT_READ)
	sock.connect(sys.argv[1])
	# Receive the list of players
	players = recv_message(sock).split(",")
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
		players_move()
		enemies_move()
		# Dump gamestate to a file so it can be restored in case of a crash.
		#gamestate.encode()

if __name__ == '__main__': main()
