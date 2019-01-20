package main

import (
	"bytes"
	"io"
	"log"
	"net"
	"os"
	"os/exec"
	"strings"

	errors "github.com/pkg/errors"
)

type client struct {
	Name      string
	Lobby     string
	Inbound   chan []byte
	Outbound  chan string
	MatchChan chan message
}

// message is a transmission from a player to the lobby server. The username is added in by the multiplexer.
// If the Content is a chat message, it will start with "GLOBAL:" or "LOCAL:". Otherwise, we interpret it as a control message.
type message struct {
	// The reason this is a pointer is to allow changing the user through the message instead having to loop through the client list and find them.
	User    *client
	Content []byte
}

// update is a transmission from the game server to the lobby server, which will in turn get sent out to connected players.
type update struct {
	Game    string
	Content []byte
}

// Helper function to divide the byte stream of TCP into discrete messages.
func readUntilDelim(r io.Reader, delim byte) ([]byte, error) {
	var buf bytes.Buffer
	var b = []byte{0}
	for {
		_, err := r.Read(b)
		if b[0] == DELIM {
			return buf.Bytes(), nil
		}
		if err != nil {
			return buf.Bytes(), err
		}
		buf.Write(b)
	}
}

// DELIM is a global constant used to delimit messages.
var DELIM byte = 3

func main() {
	listener, err := net.Listen("tcp4", "0.0.0.0:1025")
	if err != nil {
		log.Fatal(errors.Wrap(err, "When listening on socket"))
	}
	defer listener.Close()
	entryChan := make(chan client)
	exitChan := make(chan string)
	go lobby(entryChan, exitChan)
	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Println(errors.Wrap(err, "When accepting connection"))
		}
		go handleConnection(conn, entryChan, exitChan)
	}

}

func lobby(entryChan <-chan client, exitChan chan string) {
	var players []*client
	var playerMux = make(chan message)
	var gameMux = make(chan update)
	for {
		select {
		// Player joining.
		case player := <-entryChan:
			log.Println("Player joining:", player.Name)
			players = append(players, &player)
			// Start a goroutine to multiplex the chat messages.
			go func(mux chan<- message, player *client, exit chan<- string) {
				for msg := range player.Inbound {
					mux <- message{User: player, Content: msg}
				}
				exit <- player.Name
			}(playerMux, &player, exitChan)
		// Playser leaving.
		case username := <-exitChan:
			log.Println("Player leaving:", username)
			// We only got the name, so use it to find the player in order to delete them.
			for i := range players {
				if players[i].Name == username {
					players = append(players[:i], players[i+1:]...)
					break
				}
			}
		// Player sending a message.
		case msg := <-playerMux:
			log.Println("Got message:", msg)
			var msgStr = string(msg.Content)
			if strings.HasPrefix(msgStr, "GLOBAL:") {
				for _, player := range players {
					player.Outbound <- msgStr
				}
			} else if strings.HasPrefix(msgStr, "LOCAL:") {
				for _, player := range players {
					// Local chat is only sent to other players in the same environment.
					if player.Lobby == msg.User.Lobby {
						player.Outbound <- msgStr
					}
				}
			} else if strings.HasPrefix(msgStr, "JOIN:") {
				var lobby = msgStr[5:]
				log.Println(msg.User.Name, "joining", lobby)
				// Iterate over players to find everyone else in the lobby.
				var lobbyPlayers []string
				for i := range players {
					if players[i].Lobby == lobby {
						lobbyPlayers = append(lobbyPlayers, players[i].Name)
						msg.User.Outbound <- "JOIN:" + players[i].Name
						players[i].Outbound <- "JOIN:" + msg.User.Name
					}
				}
				if len(lobbyPlayers) > 0 {
					msg.User.Lobby = lobby
				} else {
					log.Println("Join failed, we don't handle this yet")
				}
			} else {
				switch msgStr {
				case "CREATE":
					log.Println("New lobby:", msg.User.Name)
					msg.User.Lobby = msg.User.Name
					for i := range players {
						players[i].Outbound <- "+LOBBY:" + msg.User.Name
					}
				case "START":
					// Make sure the user owns the lobby.
					if msg.User.Lobby == msg.User.Name {
						log.Println("Game starting:", msg.User.Lobby)
						// The game server will need to know what players are connected.
						var participants []string
						for i := range players {
							if players[i].Lobby == msg.User.Lobby {
								participants = append(participants, players[i].Name)
							}
						}
						var matchChan = make(chan message)
						go handleMatch(gameMux, matchChan, msg.User.Lobby, participants)
						for _, player := range players {
							if player.Lobby == msg.User.Lobby {
								player.Outbound <- "START"
								player.MatchChan = matchChan
							} else {
								player.Outbound <- "-LOBBY:" + msg.User.Lobby
							}
						}
					} else {
						log.Println(msg.User.Name, "can't start game created by", msg.User.Lobby)
					}
				default:
					// Any unrecognized comamnds are sent to the match server, assuming it's an in-game thing. This way the lobby server doesn't have to know about changes in the game server interface.
					if msg.User.MatchChan != nil {
						msg.User.MatchChan <- msg
					} else {
						log.Println("Command not recognized as a lobbby control:", msgStr)
					}
				}
			}
		case msg := <-gameMux:
			for i := range players {
				// Match players who are in the game this update is from.
				if players[i].Lobby == msg.Game {
					players[i].Outbound <- string(msg.Content)
				}
			}
		}
	}
}

// handleConnection is spawned in a goroutine for each player that connects. It listens for input from the player, as well as server messages back to them.
func handleConnection(conn net.Conn, entryChan chan<- client, exitChan chan<- string) {
	// When the player first connects, they're expected to choose a username.
	// TODO: handle the case of repeat names
	var msg, err = readUntilDelim(conn, DELIM)
	if err != nil {
		log.Println(errors.Wrap(err, "When getting player's name"))
		return
	}
	// Send in the client to the lobby goroutine.
	player := client{
		Name:     string(msg),
		Lobby:    "",
		Inbound:  make(chan []byte),
		Outbound: make(chan string),
	}
	defer close(player.Inbound)
	defer close(player.Outbound)
	entryChan <- player
	// Connect the outbound channel to the network socket.
	go func() {
		for msg := range player.Outbound {
			_, err = conn.Write(append([]byte(msg), DELIM))
			if err != nil {
				log.Println(errors.Wrap(err, "When sending message to player"))
				return
			}
		}
	}()
	// Connect the network socket to the inbound channel.
	for {
		// Read the next message from chat.
		msg, err = readUntilDelim(conn, DELIM)
		if err != nil {
			log.Println(errors.Wrap(err, "When reading player message"))
			return
		}
		player.Inbound <- msg
	}
}

func handleMatch(updateChan chan<- update, inputChan <-chan message, lobby string, players []string) {
	var sockname = "/tmp/spacestation_defense_" + lobby + ".sock"
	// No point catching the error because if it doesn't exist, then that's what we wanted; if it can't be removed for another reason, we'll get the error on the next line anyway.
	os.Remove(sockname)
	var listener, err = net.Listen("unix", sockname)
	if err != nil {
		log.Println(errors.Wrap(err, "When opening socket"))
		return
	}
	var cmd = exec.Command("python3.6", "server.py", sockname)
	cmd.Stderr = os.Stderr
	// Connecting stdout is mostly for printing diagnostics.
	cmd.Stdout = os.Stdout
	err = cmd.Start()
	if err != nil {
		log.Println(errors.Wrap(err, "Failed to start server.py"))
		return
	}
	conn, err := listener.Accept()
	if err != nil {
		log.Println(errors.Wrap(err, "Could not establish connection with server.py"))
	}
	// Send the game server the list of players.
	_, err = conn.Write(append([]byte(strings.Join(players, ",")), DELIM))
	// Send it the mission name. For now, assume "test".
	_, err = conn.Write(append([]byte("test"), DELIM))
	// I/O loop.
	go func() {
		for input := range inputChan {
			_, err := conn.Write(append([]byte(input.User.Name+":"), append([]byte(input.Content), DELIM)...))
			if err != nil {
				log.Println(errors.Wrap(err, "When reading player input in-game"))
			}
		}
	}()
	for {
		var msg, err = readUntilDelim(conn, DELIM)
		if err != nil {
			log.Println(errors.Wrap(err, "When reading game server update"))
		}
		updateChan <- update{Game: lobby, Content: msg}
	}
}
