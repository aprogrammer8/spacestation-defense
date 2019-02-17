"""This module contains helper functions."""

import json
from rules import *

def rotate(pos, rot):
	if rot == 0: return pos
	if rot == 90: return [-pos[1], pos[0]]
	if rot == 180: return [-pos[0], -pos[1]]
	if rot == 270: return [pos[1], -pos[0]]
	print("Not a valid rotation:", rot)
	return pos

def spaces(main_pos, shape, rot):
	"""Takes an Entity's position, shape and rotation and returns all the positions it occupies."""
	spaces = [main_pos]
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

def interpret_assign(gamestate, cmd, display=None):
	"""Interprets a JSON-formatted ASSIGN command, sets the unit's actions, and updates the Display if necessary."""
	unit_pos = json.loads(cmd[:cmd.index(':')])
	unit = gamestate.occupied(unit_pos)
	unit.actions = json.loads(cmd[cmd.index(':')+1:])
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
