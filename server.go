package main

import (
	errors "github.com/pkg/errors"
	"log"
	"net"
	"time"
)

type Player struct {
	Name     string
	InGame   bool
	Inbound  chan []byte
	Outbound chan []byte
}

type Msg struct {
	Username string
	Content  []byte
}

func main() {
	listener, err := net.Listen("tcp4", "127.0.0.1:1025")
	if err != nil {
		log.Fatal(errors.Wrap(err, "When listening on socket"))
	}
	defer listener.Close()
	entryChan = make(chan Player)
	exitChan = make(chan string)
	go lobby(entryChan, exitChan)
	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Println(errors.Wrap(err, "When accepting connection"))
		}
		go handleConnection(conn, entryChan, exitChan)
	}

}

func lobby(entryChan <-chan Player, exitChan <-chan string) {
	var players []Player
	msgMux := make(chan Msg)

	for {
		select {
		case player := <-entryChan:
			players = append(players, player)
			// Start a goroutine to multiplex the chat messages.
			go func(mux chan<- Msg, player Player, exit chan<- string) {
				for msg := range player.Inbound {
					mux <- Msg{Username: player.Name, Content: msg}
				}
				exit <- player.Name
			}(msgMux, player, exitChan)
		case username := <-exitChan:
			// We only got the name, so use it to find the player in order to delete them.
			for i := range players {
				if players[i].Name == username {
					players = append(players[:i], layers[i+1:])
				}
			}
		//case msg := <-msgMux:
			// For now, we send everything as a chat message
			//What should the outbound messages be? Should they still be []byte? They need to have the username.
		}
	}
}

// handleConnection is spawned in a goroutine for each player that connects. It listens for input from the player, as well as server messages back to them.
func handleConnection(conn net.Conn, entryChan chan<- Player, exitChan chan<- string) {
	// When the player first connects, they're expected to choose a username.
	// TODO: handle the case of repeat names
	var msg []byte
	_, err := conn.Read(&msg)
	if err != nil {
		log.Println(errors.Wrap(err, "When getting player's name"))
		return
	}
	// Send in the Player to the lobby goroutine.
	player = Player{
		Name:     msg,
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
			}
			//TODO remove them or just drop the message?
		}
	}()
	// Connect the network socket to the inbound channel.
	for {
		// Read the next message from chat.
		_, err := conn.Read(&msg)
		if err != nil {
			log.Println(errors.Wrap(err, "When reading player message"))
			//return
		}
		player.Inbound <- msg
	}
}

//func matchmaker() {
//
//}
