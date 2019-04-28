"""This module contains helper functions."""

import json, random
from rules import *

def rotate(pos, rot):
	rot = rot % 360
	if rot == 0: return pos
	if rot == 90: return [-pos[1], pos[0]]
	if rot == 180: return [-pos[0], -pos[1]]
	if rot == 270: return [pos[1], -pos[0]]
	print("Not a valid rotation:", rot)
	return pos

def spaces(main_pos, shape, rot):
	"""Takes an Entity's position, shape and rotation and returns all the positions it occupies."""
	# Copy to avoid shared reference issues.
	spaces = [main_pos[:]]
	for pos in shape:
		pos = rotate(pos, rot)
		spaces.append([pos[0] + main_pos[0], pos[1] + main_pos[1]])
	return spaces

def rect(spaces):
	"""Takes a sequence of spaces and returns the inputs for a Rect containing them."""
	left = right = spaces[0][0]
	top = bottom = spaces[0][1]
	for space in spaces[1:]:
		if space[0] < left: left = space[0]
		if space[0] > right: right = space[0]
		if space[1] < top: top = space[1]
		if space[1] > bottom: bottom = space[1]
	return left, top, right-left+1, bottom-top+1

def adjacent(spaces1, spaces2):
	"""Returns whether two sequences of spaces are adjacent."""
	for space1 in spaces1:
		for space2 in spaces2:
			# For two spaces to be adjacent, one of their coordinates must be off by 1 and the other must match.
			if (abs(space1[0] - space2[0]) == 1 and space1[1] == space2[1]) or (space1[0] == space2[0] and abs(space1[1] - space2[1]) == 1):
				return True
	return False

def interpret_assign(gamestate, cmd, display=None):
	"""Interprets a JSON-formatted ASSIGN command, sets the unit's actions, and updates the Display if necessary."""
	# For conveience, don't force callers to strip the "ASSIGN:" prefix before coming here.
	if cmd.startswith("ASSIGN:"):
		cmd = cmd[7:]
	try:
		unit_pos = json.loads(cmd[:cmd.index(':')])
		unit = gamestate.occupied(unit_pos)
		unit.actions = json.loads(cmd[cmd.index(':')+1:])
	except Exception as e:
		print("Error interpreting command string:", cmd)
		raise e
	if display and display.selected == unit: display.select()

def shield_repr(entity):
	"""Returns a string suitable to label the shield bar on the panel."""
	string = str(entity.shield)+"/"+str(entity.maxshield)+"    + "+str(entity.shield_regen_amounts[entity.shield_regen_pointer])+" / "
	for amount in entity.shield_regen_amounts:
		string += str(amount) + "->"
	return string[:-2]

def power_repr(station):
	"""Returns a string suitable to label the power bar on a Station component."""
	string = str(station.power) + "(" + str(station.projected_power()) + ") / " + str(station.maxpower()) + "    + " + str(POWER_GEN_SPEED * len(station.power_generators()))
	return string

def thrust_repr(station):
	"""Returns a string suitable to label the thrust bar on a Station component."""
	string = str(abs(station.thrust)) + " / " + str(station.thrust_needed())
	if station.thrust > 0: string += " (clockwise)"
	elif station.thrust < 0: string += " (counterclockwise)"
	return string

def set_target(entity, index, pos):
	"""Generates an ASSIGN command string to target the Entity's weapon at the provided index at pos."""
	action_index = 0
	# Check if the requested weapon is already targeting something. If so, replace that target so the weapon isn't getting double-used.
	for action in entity.actions:
		if action['type'] == 'attack' and action['weapon'] == index:
			new_actions = entity.actions.copy()
			new_actions[action_index] = {'type': 'attack', 'weapon': index, 'target': pos}
			return "ASSIGN:" + json.dumps(entity.pos) + ":" + json.dumps(new_actions)
		action_index += 1
	return "ASSIGN:" + json.dumps(entity.pos) + ":" + json.dumps(entity.actions + [{'type': 'attack', 'weapon': index, 'target': pos}])

def assign_random_targets(gamestate, entity):
	"""Generates a list of ASSIGN command strings to target all an Entity's weapons at random Entities of the opposite side."""
	if entity.team == "enemy":
		targets = {ship for ship in gamestate.ships if ship.team == 'player'}.union(gamestate.station)
	else:
		targets = {ship for ship in gamestate.ships if ship.team == 'enemy'}.union(gamestate.asteroids)
	command = ""
	for i in entity.untargeted():
		# For now, we just pick out the first possible target.
		for target in targets:
			if gamestate.in_range(entity, entity.weapons[i], target):
				command = set_target(entity, i, target.pos)
				# We have to do this intermediate interpreting because we need the next call to set_target to see the Entity with the current target already set, so it doesn't overwrite it.
				interpret_assign(gamestate, command)
				break
	return command

def assign_random_move(gamestate, entity):
	"""Generates an ASSIGN command to assign a random move to the Entity. Returns None if no moves were legal."""
	valid_moves = []
	for move in ([0, 1], [0, -1], [1, 0], [-1, 0]):
		if not gamestate.invalid_move(entity, move): valid_moves.append(move)
	if valid_moves:
		move = random.choice(valid_moves)
		return "ASSIGN:" + json.dumps(entity.pos) + ":" + json.dumps(entity.actions + [{'type': 'move', 'move': move}])
