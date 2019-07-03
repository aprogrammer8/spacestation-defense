Spacestation Defense was a project I originall envisioned when I was about 15, and tried to make with my amateur coding skills and poor knowledge of Pygame. I gave up. 5 years later, I picked the project back up thinking I'd make it for real and it would be my first real game I'd release.
The game would be network-enabled and have global and lobby chat.

That was the same year where most of my beliefs about game design were formed. In a bittersweet conclusion, I abandoned the project for good after realizing that that the game was simply a bad idea at its heart. I didn't want to make a game I couldn't in good conscience recommend to other people.

The game would work like this: a group of players command a space station to defend it against waves of enemy ships. Each round, the players would assign actions to each station component and defending ship they controlled. After all players were ready they would lock in their decisions and they would all play out followed by the enemies taking their turn.

Destroyed units would drop salvage, which would be collected by Probes and brought to the station's onbaord Factory by dropping it off at a Hangar. The Factory could build more ships with it including Fighters, Bombers, and more Probes. But the Probes themselves were delicate.

There were two main types of weapons (although I was considering others for the future): lasers and missles. Lasers were guaranteed hits against most things while missiles did lots more damage but would usually miss small targets.

The Station also had to manage power. Most components consumed 2 to do their thing and the Power Generator component could make 5 per turn, so you would sometimes have to weigh the usefulness of activating a component against saving power so you could activate it later in a situation where it would do more good.

I was also going to have cards. Defeating the last enemy of a wave would usually award some number of cards to be distributed among the players, which would be powerful one-time abilities that you'd want to save until a good opportunity for them (like waiting for enough medium-strength enemies to clump together to play a Bomb, or until the Missile Turret-heavy side
of the station was swarmed by Fighters to play Manual Targeting and wipe them out).

The core design problem that disillusioned me was that it wasn't a good competitive game because there was too much randomness and not enough room for skill, and it wasn't a good casual game because it was too complicated and too much of a slog.
Too much time spent assigning actions to each of possibly dozens of units for such incremental and unimpressive results. Not to mention that the average match would probably go on for at least two hundred rounds.

I still don't consider the project a complete waste because I learned a ton about programming from it the second time around. I came to appreciate the value of abstraction when I found myself with a 300-line play() function in client.py and decided to separate out all the graphical frontend
details to client_display.py, where client.py now mostly contains logic for communicating between the Display and the server (I left the graphical details of the lobby screen and other non-gameplay screens in client.py because they were simple enough and there were more urgent things to work on).

Moving back to Python for this project after working as an intern in Go was also what taught me to really appreciate Go as a language. When I started learning Go I actually hated it; I resented how hard it could be just to make a simple test edit when it refuses to compile because you have an unused import.
And I still think that's stupid. But moving back to Python made me appreciate static typing and having a compiler to check it soooo much. I still really like Python in a lot of ways but it's miserable to want to test a feature that takes a minute to get to from game start only to have the first five
attempts crash because of a mispelled variable name or function args being passed in the wrong order or some crap.

This project taught me that inheritance is a lot less useful in practice than it sounds. Every time I try to write a class that ought to be a subtype of another class, I subclass it and think, "what methods can we inherit"? And almost always the answer is "none, this type requires slightly
different behavior for all of them so they all have to be completely separate". And of course that means you have to copy the whole massive argument list into the new constructor and use that ugly syntax for calling the parent constructor and pass the entire huge argument list again.
It's disgusting. Composition really is better. I'm sure the gamestate.py module and the whole mess of classes would have come out a lot better if I had written it Go.

The project gave me the following belief about object-oriented design altogether: data and code are different things and shouldn't be bundled this way. For the most part it's better to use structs and functions than objects and methods. I believe that the only reason for a function to be a
method of a data structure is if it only deals with that data structure, such as a take_damage() method, but not a shoot() method that takes a target and calls its take_damage(). I find it's much clearer most of the time to keep execution in a central place and not modify an object from
within another object's method. I ended up moving more and more Entity methods into the Gamestate later on, since I thought they could be thought of as part of the Gamestate.

The code is probably a little light on comments since I didn't expect anyone else to ever read this. That's also why the lines are so long - I write in a terminal with 381 columns :O

server.go is the lobby server. client.py connects to it and enters the lobby; when a group of players in a match lobby agree to start a game server.go starts a process running server.py which is the match server.
The game is playable in its current state; you can run the server locally, connect to to it, chat, open a lobby, start a game and shoot the endless Drones and Asteroids.

On the Mission class:
	The plan here was to eventually make mission files that the Gamestate would read an initialize a Mission object from them.

The catalog file has some old thoughts about what cards and ships I wanted to include eventually. Most of it was written years ago.
