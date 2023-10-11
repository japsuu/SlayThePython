import pygame

from data.cards import CardData

# Ensure pygame is initialized
pygame.init()

SAVE_GAME_FOLDER = "GameSaves"

PLAYER_STARTING_HEALTH = 100
PLAYER_STARTING_CARDS = CardData.load_starting_cards()

# Fonts
BASE_FONT_PATH = "Content/Fonts/YoungSerif-Regular.ttf"
FONT_UI_XXS = pygame.font.Font(BASE_FONT_PATH, 5)
FONT_UI_XS = pygame.font.Font(BASE_FONT_PATH, 10)
FONT_UI_S = pygame.font.Font(BASE_FONT_PATH, 15)
FONT_UI_M = pygame.font.Font(BASE_FONT_PATH, 20)
FONT_UI_L = pygame.font.Font(BASE_FONT_PATH, 25)
FONT_UI_XL = pygame.font.Font(BASE_FONT_PATH, 35)
FONT_UI_XXL = pygame.font.Font(BASE_FONT_PATH, 45)
FONT_UI_XXXL = pygame.font.Font(BASE_FONT_PATH, 55)

# UI font constants
FONT_CARD_REWARD = FONT_UI_M
FONT_DUNGEON_LEVEL = FONT_UI_XL
FONT_DUNGEON_LEVEL_HINT = FONT_UI_S
FONT_CARD_PILE_COUNT = FONT_UI_L
FONT_PLAYER_MANA = pygame.font.Font(BASE_FONT_PATH, 30)
FONT_PLAYER_HEALTH = FONT_UI_L
FONT_PLAYER_BLOCK = FONT_UI_M
FONT_BUTTON_GENERIC = FONT_UI_M
FONT_HELP = pygame.font.Font(BASE_FONT_PATH, 13)
FONT_DAMAGE_EFFECT_GENERIC = FONT_UI_XXL
FONT_TOOLTIP_GENERIC = FONT_UI_S
FONT_SAVE_SELECTION = FONT_UI_L
FONT_SAVE_SELECTION_S = FONT_UI_M
FONT_DEBUG = pygame.font.Font(None, 15)
FONT_ENEMY_HEALTH = FONT_UI_L
FONT_ENEMY_ICON_HINT = FONT_UI_M
FONT_ENEMY_DAMAGE_EFFECT = FONT_UI_XXL
FONT_CARD_NAME = FONT_UI_M
FONT_CARD_DESCRIPTION = FONT_UI_S
FONT_CARD_MANA_COST = FONT_UI_XXL

# Layer draw order constants
DRAW_ORDER_BACKGROUND = -1000
DRAW_ORDER_MIDGROUND = 0
DRAW_ORDER_MIDGROUND_UI = 500
DRAW_ORDER_EFFECTS = 1000
DRAW_ORDER_FOREGROUND = 1500
DRAW_ORDER_FOREGROUND_UI = 2000
DRAW_ORDER_OVERLAY_UI = 2500

# Game object draw order constants
LAYER_DEFAULT = DRAW_ORDER_MIDGROUND
LAYER_ENEMY = DRAW_ORDER_MIDGROUND
LAYER_EFFECTS = LAYER_ENEMY + 50
LAYER_TARGETED_ENEMY_ICON = DRAW_ORDER_MIDGROUND_UI
LAYER_CARD_REWARD_TEXT = DRAW_ORDER_OVERLAY_UI
LAYER_CARD_REWARD = DRAW_ORDER_OVERLAY_UI
LAYER_PLAYER_HAND = DRAW_ORDER_FOREGROUND
LAYER_PLAYER_UI_BACKGROUND = DRAW_ORDER_OVERLAY_UI
LAYER_PLAYER_UI_TEXT = DRAW_ORDER_OVERLAY_UI + 1
LAYER_UI_EFFECTS = LAYER_PLAYER_UI_TEXT + 50
LAYER_OVERRIDE_BG = 1000000
LAYER_OVERRIDE_FG = LAYER_OVERRIDE_BG + 1

# Animation priority constants
ANIM_PRIORITY_DEFAULT = 0
ANIM_PRIORITY_CARD_DRAW = ANIM_PRIORITY_DEFAULT + 500
ANIM_PRIORITY_CARD_DISCARD = ANIM_PRIORITY_CARD_DRAW + 500