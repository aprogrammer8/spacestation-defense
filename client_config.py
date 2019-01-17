import pygame

server = ("127.0.0.1", 1025)
SCREEN_SIZE = (1800, 1000)
LOBBY_RATE = 50
LOG_RECT = pygame.Rect(int(SCREEN_SIZE[0]/2)-50, int(SCREEN_SIZE[1]/2)-50, 100, 100) # The rect that messages like the username prompt appear in
NAME_ENTRY_RECT = pygame.Rect(int(SCREEN_SIZE[0]/2)-50, int(SCREEN_SIZE[1]/2)+60, 100, 20)
CHAT_RECT = pygame.Rect(5, 5, int(SCREEN_SIZE[0]/5), SCREEN_SIZE[1]-10)
CHAT_ENTRY_HEIGHT = 50
BGCOLOR = (0, 0, 0) # These colors are general purpose.
TEXTCOLOR = (255, 255, 255)
ACTIVE_INPUTBOX_COLOR = (0, 255, 0)
INACTIVE_INPUTBOX_COLOR = (255, 0, 0)
CHAT_BORDERCOLOR = (170, 170, 170)
CREATE_GAME_RECT = pygame.Rect(int(SCREEN_SIZE[0]/1.5)-50, int(SCREEN_SIZE[1]/2)-8, 100, 16)
LOBBYLIST_LABEL_RECT = pygame.Rect(CHAT_RECT.x+5, 5, 100, 16)
LOBBYLIST_RECT = pygame.Rect(CHAT_RECT.right+5, 5+LOBBYLIST_LABEL_RECT.bottom, 100, SCREEN_SIZE[1]-10-LOBBYLIST_LABEL_RECT.bottom)
START_GAME_RECT = CREATE_GAME_RECT
ACTIVE_STARTBUTTON_COLOR = (85, 255, 85)
INACTIVE_STARTBUTTON_COLOR = (0, 170, 0)
LOBBY_PLAYERLIST_RECT = pygame.Rect(CHAT_RECT.right+5, 5, 100, SCREEN_SIZE[1]-10)
PANEL_COLOR = (127, 127, 127)
PANEL_RECT = pygame.Rect(SCREEN_SIZE[0]-int(SCREEN_SIZE[0]/10), 0, int(SCREEN_SIZE[0]/10), SCREEN_SIZE[1])
GAME_WINDOW_RECT = pygame.Rect(CHAT_RECT.right, 0, SCREEN_SIZE[0]-CHAT_RECT.w-PANEL_RECT.w, SCREEN_SIZE[1])
GAME_PLAYERLIST_RECT = pygame.Rect(PANEL_RECT.x, 0, PANEL_RECT.w, PANEL_RECT.h)
GRID_COLOR = (255, 255, 255)
TILESIZE = (50, 50)

IMAGE_DICT = {
	"Drone": pygame.image.load("images/drone.png"),
	"Shield Generator": pygame.image.load("images/drone.png"),
}

for image_name in IMAGE_DICT:
	IMAGE_DICT[image_name].set_colorkey((255,255,255))
