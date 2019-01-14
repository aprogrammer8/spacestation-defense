import socket, selectors, random, sys
from gamestate import *
from sockets import *

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
#sock.setblocking(False)
selector = selectors.DefaultSelector()
selector.register(sock, selectors.EVENT_READ)
sock.connect(sys.argv[1])
# Receive the list of players
player_names = recv_message(sock).split(",")
print(players)
mission = recv_message(sock)
print(mission)
gamestate = Gamestate(players, mission)

while True:
	gamestate.upkeep()
	# Probably update the players now?
	collect_input()
	players_move()
	enemies_move()
	# Dump gamestate to a file so it can be restored in case of a crash.
	gamestate.encode()

	# Hm, gamestates are huge so the best way to send them out to each client will be by only sending the changes and letting the clients replay them themselves. That sounds doable. We'll have the gamestate log each change it makes internally and write them out.
