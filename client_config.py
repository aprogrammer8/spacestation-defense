import pygame
pygame.init()

# Basics.
server = ("127.0.0.1", 1025)
SCREEN_SIZE = (1800, 1000)
LOBBY_RATE = 50

# Login screen.
LOG_RECT = pygame.Rect(SCREEN_SIZE[0]//2-50, SCREEN_SIZE[1]//2-50, 100, 100)
NAME_ENTRY_RECT = pygame.Rect(SCREEN_SIZE[0]//2-50, SCREEN_SIZE[1]//2+60, 100, 20)

# Chat general.
CHAT_RECT = pygame.Rect(5, 5, SCREEN_SIZE[0]//5, SCREEN_SIZE[1]-10)
CHAT_ENTRY_HEIGHT = 50

# General-purpose colors.
BGCOLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
ACTIVE_INPUTBOX_COLOR = (0, 255, 0)
INACTIVE_INPUTBOX_COLOR = (255, 0, 0)
CHAT_BORDERCOLOR = (170, 170, 170)

# Global lobby.
CREATE_GAME_RECT = pygame.Rect(SCREEN_SIZE[0]//1.5-50, SCREEN_SIZE[1]//2-8, 100, 16)
LOBBYLIST_LABEL_RECT = pygame.Rect(CHAT_RECT.x+5, 5, 100, 16)
LOBBYLIST_RECT = pygame.Rect(CHAT_RECT.right+5, 5+LOBBYLIST_LABEL_RECT.bottom, 100, SCREEN_SIZE[1]-10-LOBBYLIST_LABEL_RECT.bottom)

# Local lobby.
START_GAME_RECT = CREATE_GAME_RECT
ACTIVE_STARTBUTTON_COLOR = (85, 255, 85)
INACTIVE_STARTBUTTON_COLOR = (0, 170, 0)
ACTIVE_LOBBYBUTTON_COLOR = (255, 255, 0)
INACTIVE_LOBBYBUTTON_COLOR = (170, 170, 0)
LOBBY_PLAYERLIST_RECT = pygame.Rect(CHAT_RECT.right+5, 5, 100, SCREEN_SIZE[1]-10)

# Gameplay.
GAME_WINDOW_RECT = pygame.Rect(CHAT_RECT.right, 0, SCREEN_SIZE[0]-CHAT_RECT.w-SCREEN_SIZE[0]//10, SCREEN_SIZE[1])
# Panel general.
PANEL_COLOR = (127, 127, 127)
# The top panel is the part that contains only the player list and the done button. It is not redrawn when the rest of the panel is.
TOP_PANEL_RECT = pygame.Rect(GAME_WINDOW_RECT.right, 0, SCREEN_SIZE[0]-GAME_WINDOW_RECT.right, SCREEN_SIZE[1]//8)
GAME_PLAYERLIST_RECT = pygame.Rect(TOP_PANEL_RECT.x, 0, TOP_PANEL_RECT.w, TOP_PANEL_RECT.h)
ACTIVE_DONE_BUTTON_COLOR = (255, 255, 0)
INACTIVE_DONE_BUTTON_COLOR = (170, 170, 0)
DONE_BUTTON_RECT = pygame.Rect(TOP_PANEL_RECT.x+TOP_PANEL_RECT.w//2, 2, TOP_PANEL_RECT.w//2, 20)
# THe main panel rect.
PANEL_RECT = pygame.Rect(TOP_PANEL_RECT.x, TOP_PANEL_RECT.bottom, TOP_PANEL_RECT.w, SCREEN_SIZE[1]-TOP_PANEL_RECT.h)
# Selected entity info on panel.
PANEL_NAME_RECT = pygame.Rect(PANEL_RECT.left+2, PANEL_RECT.top+3, PANEL_RECT.w-3, 16)
PANEL_HULL_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_NAME_RECT.bottom, PANEL_RECT.w-2, 16)
PANEL_HULL_BAR_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_HULL_RECT.bottom+2, PANEL_RECT.w-2, 20)
HULL_COLOR = (255, 255, 0)
HULL_DAMAGE_COLOR = (127, 0, 0)
PANEL_SHIELD_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_HULL_BAR_RECT.bottom+20, PANEL_RECT.w-2, 16)
PANEL_SHIELD_BAR_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_SHIELD_RECT.bottom+2, PANEL_RECT.w-2, 20)
SHIELD_COLOR = (0, 0, 255)
SHIELD_DAMAGE_COLOR = (127, 0, 0)
PANEL_WEAPON_DESC_BEGIN = pygame.Rect(PANEL_RECT.left+1, PANEL_SHIELD_BAR_RECT.bottom+20, PANEL_RECT.w-2, 20)
# Salvage / hangar capcity.
CAPACITY_COLOR = (127, 63, 0)
CAPACITY_EMPTY_COLOR = (0, 0, 0)
# Station-wide info starts at the bottom and grows upward.
PANEL_POWER_BAR_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_RECT.bottom-22, PANEL_RECT.w-2, 20)
PANEL_POWER_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_POWER_BAR_RECT.top-20, PANEL_RECT.w-2, 16)
POWER_COLOR = (255, 255, 0)
POWER_LOW_COLOR = (0, 0, 0)

# Grid.
GRID_COLOR = (255, 255, 255)
TILESIZE = (25, 25)

IMAGE_DICT = {
	# Enemy ships.
	"Drone": pygame.image.load("images/drone.png"),
	"Kamikaze Drone": pygame.image.load("images/kamikaze_drone.png"),
	# Player ships.
	"Probe": pygame.image.load("images/probe.png"),
	# Station components.
	"Connector": pygame.image.load("images/connector.png"),
	"Shield Generator": pygame.image.load("images/shield_generator.png"),
	"Power Generator": pygame.image.load("images/power_generator.png"),
	"Laser Turret": pygame.image.load("images/laser_turret.png"),
	"Factory": pygame.image.load("images/factory.png"),
	# Misc.
	"salvage": pygame.image.load("images/salvage1.png"),
}

# Handle transparency.
for image_name in IMAGE_DICT:
	IMAGE_DICT[image_name].set_colorkey((255,255,255))

SFX_ERROR = pygame.mixer.Sound("sounds/error.ogg")
