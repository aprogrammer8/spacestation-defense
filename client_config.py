import pygame

# Basics.
server = ("127.0.0.1", 1025)
SCREEN_SIZE = (1800, 1000)
LOBBY_RATE = 50
# Key repeat settings.
KEY_REPEAT_DELAY = 200
KEY_REPEAT_INTERVAL = 30
# This helps the sound delay. The 4th param defaults to 4096, which gives a huge delay.
pygame.mixer.pre_init(22050, -16, 2, 1024)
pygame.init()
FONT = pygame.font.Font(pygame.font.get_default_font(), 10)

# Abstract a few values that will be used in a ton of places.
LABEL_HEIGHT = 16
LABEL_SPACING = 4
BAR_HEIGHT = 20
BUTTON_HEIGHT = 20
ENTRY_HEIGHT = 20

# Login screen.
LOG_RECT = pygame.Rect(SCREEN_SIZE[0]//2-50, SCREEN_SIZE[1]//2-50, 100, 100)
NAME_ENTRY_RECT = pygame.Rect(SCREEN_SIZE[0]//2-50, SCREEN_SIZE[1]//2+60, 100, ENTRY_HEIGHT)

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
CREATE_GAME_RECT = pygame.Rect(SCREEN_SIZE[0]//1.5-50, SCREEN_SIZE[1]//2-8, 100, LABEL_HEIGHT)
LOBBYLIST_LABEL_RECT = pygame.Rect(CHAT_RECT.x+5, 5, 100, LABEL_HEIGHT)
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
# Panel colors.
PANEL_COLOR = (127, 127, 127)
ASSIGNING_TEXT_COLOR = (255, 0, 0)
HULL_COLOR = (255, 255, 0)
HULL_DAMAGE_COLOR = (127, 0, 0)
SHIELD_COLOR = (0, 0, 255)
SHIELD_DAMAGE_COLOR = (127, 0, 0)
CAPACITY_COLOR = (127, 63, 0)
CAPACITY_EMPTY_COLOR = (0, 0, 0)
POWER_COLOR = (255, 191, 0)
POWER_LOW_COLOR = (0, 0, 0)
SALVAGE_COLOR = (127, 63, 0)
SALVAGE_EMPTY_COLOR = (0, 0, 0)
THRUST_COLOR = (255, 255, 0)
THRUST_EMPTY_COLOR = (0, 0, 0)
# The top panel is the part that contains only the player list and the done button. It is not redrawn when the rest of the panel is.
TOP_PANEL_RECT = pygame.Rect(GAME_WINDOW_RECT.right, 0, SCREEN_SIZE[0]-GAME_WINDOW_RECT.right, SCREEN_SIZE[1]//8)
GAME_PLAYERLIST_RECT = pygame.Rect(TOP_PANEL_RECT.x, 0, TOP_PANEL_RECT.w, TOP_PANEL_RECT.h)
ACTIVE_DONE_BUTTON_COLOR = (255, 255, 0)
INACTIVE_DONE_BUTTON_COLOR = (170, 170, 0)
DONE_BUTTON_RECT = pygame.Rect(TOP_PANEL_RECT.x+TOP_PANEL_RECT.w//2, 2, TOP_PANEL_RECT.w//2, BUTTON_HEIGHT)
# The main panel rect.
PANEL_RECT = pygame.Rect(TOP_PANEL_RECT.x, TOP_PANEL_RECT.bottom, TOP_PANEL_RECT.w, SCREEN_SIZE[1]-TOP_PANEL_RECT.h)
# And a shortcut for the rare cases where you want a rect for both of them.
TOTAL_PANEL_RECT = pygame.Rect(TOP_PANEL_RECT.x, TOP_PANEL_RECT.y, TOP_PANEL_RECT.w, TOP_PANEL_RECT.h+PANEL_RECT.h)
# Selected entity info on panel.
PANEL_NAME_RECT = pygame.Rect(PANEL_RECT.left+2, PANEL_RECT.top+3, PANEL_RECT.w-3, LABEL_HEIGHT)
PANEL_ASSIGNING_RECT = pygame.Rect(PANEL_RECT.left+2, PANEL_NAME_RECT.bottom+2, PANEL_RECT.w-3, LABEL_HEIGHT)
PANEL_HULL_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_ASSIGNING_RECT.bottom+2, PANEL_RECT.w-2, LABEL_HEIGHT)
PANEL_HULL_BAR_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_HULL_RECT.bottom+2, PANEL_RECT.w-2, BAR_HEIGHT)
PANEL_SHIELD_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_HULL_BAR_RECT.bottom+20, PANEL_RECT.w-2, LABEL_HEIGHT)
PANEL_SHIELD_BAR_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_SHIELD_RECT.bottom+2, PANEL_RECT.w-2, BAR_HEIGHT)
PANEL_SPEED_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_SHIELD_BAR_RECT.bottom+2, PANEL_RECT.w-2, LABEL_HEIGHT)
PANEL_WEAPON_DESC_BEGIN = pygame.Rect(PANEL_RECT.left+1, PANEL_SPEED_RECT.bottom+20, PANEL_RECT.w-2, LABEL_HEIGHT + 4)
# Hangar launch buttons.
ACTIVE_HANGAR_BUTTON_COLOR = (255, 255, 0)
INACTIVE_HANGAR_BUTTON_COLOR = (170, 170, 0)
ACTIVE_LAUNCH_HANGAR_BUTTON_COLOR = (255, 255, 85)
INACTIVE_LAUNCH_HANGAR_BUTTON_COLOR = (170, 255, 0)
# Factory project buttons.
INACTIVE_FACTORY_PROJECT_BUTTON_COLOR = (127, 0, 255)
ACTIVE_FACTORY_PROJECT_BUTTON_COLOR = (170, 85, 255)
CONSTRUCTION_COLOR = (0, 255, 0)
CONSTRUCTION_EMPTY_COLOR = (0, 0, 0)
# Station-wide info starts at the bottom and grows upward.
PANEL_SALVAGE_BAR_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_RECT.bottom-22, PANEL_RECT.w-2, BAR_HEIGHT)
PANEL_STATION_SALVAGE_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_SALVAGE_BAR_RECT.top-20, PANEL_RECT.w-2, LABEL_HEIGHT)
PANEL_POWER_BAR_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_STATION_SALVAGE_RECT.top-32, PANEL_RECT.w-2, BAR_HEIGHT)
PANEL_POWER_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_POWER_BAR_RECT.top-20, PANEL_RECT.w-2, LABEL_HEIGHT)
PANEL_THRUST_BAR_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_POWER_RECT.top-32, PANEL_RECT.w-2, BAR_HEIGHT)
PANEL_THRUST_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_THRUST_BAR_RECT.top-20, PANEL_RECT.w-2, LABEL_HEIGHT)
# Salvage on space.
PANEL_SALVAGE_RECT = pygame.Rect(PANEL_RECT.left+1, PANEL_THRUST_RECT.top-40, PANEL_RECT.w-2, 20)

# Other colors.
MOVE_PROJECTION_COLOR = (255, 255, 0)
PLACEMENT_PROJECTION_COLOR = (0, 255, 0)

# Grid.
GRID_COLOR = (255, 255, 255)
TILESIZE = (25, 25)

IMAGE_DICT = {
	# Enemy ships.
	"Drone": "images/drone.png",
	"Kamikaze Drone": "images/kamikaze_drone.png",
	# Player ships.
	"Probe": "images/probe.png",
	# Station components.
	"Connector": "images/connector.png",
	"Shield Generator": "images/shield_generator.png",
	"Power Generator": "images/power_generator.png",
	"Laser Turret": "images/laser_turret.png",
	"Hangar": "images/hangar.png",
	"Factory": "images/factory.png",
	"Engine": "images/engine.png",
	# Asteroids.
	"Asteroid": "images/salvage1.png",
	# Misc.
	"salvage": "images/salvage1.png",
}

SFX_ERROR = pygame.mixer.Sound("sounds/error2.ogg")
