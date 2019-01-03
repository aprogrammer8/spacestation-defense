package main

import (
	"bytes"
	"log"
	"net"

	errors "github.com/pkg/errors"

	"io"
	"strings"
)

type client struct {
	Name     string
	InGame   bool
	Inbound  chan []byte
	Outbound chan []byte
}

// message is a transmission from a player to the lobby server. The username is added in by the multiplexer.
// If the Content is a chat message, it will start with "CHAT:". Otherwise, we interpret it as a control message.
type message struct {
	Username string
	Content  []byte
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
	listener, err := net.Listen("tcp4", "127.0.0.1:1025")
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
	var players []client
	msgMux := make(chan message)

	for {
		select {
		// Player joining.
		case player := <-entryChan:
			log.Println("Player joining:", player.Name)
			players = append(players, player)
			// Start a goroutine to multiplex the chat messages.
			go func(mux chan<- message, player client, exit chan<- string) {
				for msg := range player.Inbound {
					mux <- message{Username: player.Name, Content: msg}
				}
				exit <- player.Name
			}(msgMux, player, exitChan)
		// Player leaving.
		case username := <-exitChan:
			log.Println("Player leaving:", username)
			// We only got the name, so use it to find the player in order to delete them.
			for i := range players {
				if players[i].Name == username {
					players = append(players[:i], players[i+1:]...)
				}
			}
		// And player sending a message.
		case msg := <-msgMux:
			log.Println("Got message:", msg)
			msgStr := string(msg.Content)
			if strings.HasPrefix(msgStr, "CHAT:") {
				broadcast := msg.Username + ":" + strings.TrimPrefix(msgStr, "CHAT:")
				for _, player := range players {
					player.Outbound <- []byte(broadcast)
				}
			} else {
				switch msgStr {
				default:
					log.Println("Command not recognized:", msgStr)
				}
			}
		}
	}
}

// handleConnection is spawned in a goroutine for each player that connects. It listens for input from the player, as well as server messages back to them.
func handleConnection(conn net.Conn, entryChan chan<- client, exitChan chan<- string) {
	// When the player first connects, they're expected to choose a username.
	// TODO: handle the case of repeat names
	msg, err := readUntilDelim(conn, DELIM)
	if err != nil {
		log.Println(errors.Wrap(err, "When getting player's name"))
		return
	}
	// Send in the client to the lobby goroutine.
	player := client{
		Name:     string(msg),
		InGame:   false,
		Inbound:  make(chan []byte),
		Outbound: make(chan []byte),
	}
	defer close(player.Inbound)
	defer close(player.Outbound)
	entryChan <- player
	// Connect the outbound channel to the network socket.
	go func() {
		for msg := range player.Outbound {
			_, err := conn.Write(msg)
			if err != nil {
				log.Println(errors.Wrap(err, "When sending message to player"))
				return
			}
			//TODO remove them or just drop the message?
		}
	}()
	// Connect the network socket to the inbound channel.
	for {
		// Read the next message from chat.
		msg, err := readUntilDelim(conn, DELIM)
		if err != nil {
			log.Println(errors.Wrap(err, "When reading player message"))
			return
		}
		player.Inbound <- msg
	}
}

//func matchmaker() {
//
//}
