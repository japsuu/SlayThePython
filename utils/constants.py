import pygame

from data.cards import CardData
from utils.io import load_sound, get_sounds_in_directory

# Ensure pygame is initialized
pygame.init()

SAVE_GAME_FOLDER = "GameSaves"

PLAYER_STARTING_HEALTH = 100
PLAYER_STARTING_CARDS = CardData.load_starting_cards()

ENEMY_SPRITE_SCALING_FACTOR = 8

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
SYMBOLS_FONT = pygame.font.Font("Content/Fonts/GoddessSymbols.ttf", 20)
SYMBOLS_FONT_BG = pygame.font.Font("Content/Fonts/GoddessSymbols.ttf", 24)

# UI font constants
FONT_CARD_CHOOSE = FONT_UI_M
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
FONT_SPECIAL_ROOM_TITLE = FONT_UI_XXL
FONT_SPECIAL_ROOM_DESCRIPTION = FONT_UI_M

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
LAYER_CARD_CHOOSE_TITLE = DRAW_ORDER_OVERLAY_UI
LAYER_PLAYER_HAND = DRAW_ORDER_FOREGROUND
LAYER_PLAYER_UI_BACKGROUND = DRAW_ORDER_OVERLAY_UI
LAYER_PLAYER_UI_TEXT = DRAW_ORDER_OVERLAY_UI + 1
LAYER_UI_EFFECTS = LAYER_PLAYER_UI_TEXT + 50
LAYER_OVERRIDE_BG = 1000000
LAYER_OVERRIDE_FG = LAYER_OVERRIDE_BG + 1

# Animation priority constants
ANIM_PRIORITY_DEFAULT = 0
ANIM_PRIORITY_CARD_DRAW = ANIM_PRIORITY_DEFAULT + 500
ANIM_PRIORITY_CARD_REPOSITION = ANIM_PRIORITY_CARD_DRAW + 500
ANIM_PRIORITY_CARD_DISCARD = ANIM_PRIORITY_CARD_REPOSITION + 500

# AUDIO

# Ambient
AMBIENT_LOOP_SOUND = (load_sound("Content/Audio/Ambient/dungeon_loop.wav"), "ambient_loop")

# Spooks
SPOOK_SOUNDBANK = get_sounds_in_directory("Content/Audio/Spooks")

# Cards
shuffle_sound = (load_sound("Content/Audio/Cards/shuffle.wav"), "shuffle")
deal_hand_sound = (load_sound("Content/Audio/Cards/deal_hand.wav"), "deal_hand")
deal_one_soundbank = get_sounds_in_directory("Content/Audio/Cards/Deals")
play_card_sound = (load_sound("Content/Audio/Plays/play_card.wav"), "play_card")
card_move_1_sound = (load_sound("Content/Audio/Cards/card_move_1.wav"), "card_move_1")
card_move_2_sound = (load_sound("Content/Audio/Cards/card_move_2.wav"), "card_move_2")

# Plays
gain_block_sound = (load_sound("Content/Audio/Plays/gain_block.wav"), "gain_block")
gain_mana_sound = (load_sound("Content/Audio/Plays/gain_energy.wav"), "gain_energy")
exhaust_card_sound = (load_sound("Content/Audio/Plays/exhaust.wav"), "exhaust")
destroy_card_sound = (load_sound("Content/Audio/Plays/destroy.wav"), "destroy")
skip_sound = (load_sound("Content/Audio/Plays/skip.wav"), "skip")
end_turn_sound = (load_sound("Content/Audio/Plays/end_turn.wav"), "end_turn")

# UI
scene_change_sound = (load_sound("Content/Audio/UI/scene_change.wav"), "scene_change")
button_sound = (load_sound("Content/Audio/UI/button.wav"), "button")
show_rewards_sound = (load_sound("Content/Audio/UI/show_rewards.wav"), "show_rewards")
enter_room_sound = (load_sound("Content/Audio/UI/enter_room.wav"), "enter_room")

# Characters
damaged_sound = (load_sound("Content/Audio/Characters/damaged.wav"), "damaged")
blocked_sound = (load_sound("Content/Audio/Characters/blocked.wav"), "blocked")
killed_sound = (load_sound("Content/Audio/Characters/killed.wav"), "killed")
attacked_sound = (load_sound("Content/Audio/Characters/attacked.wav"), "attacked")
healed_sound = (load_sound("Content/Audio/Characters/healed.wav"), "healed")
open_backpack_sound = (load_sound("Content/Audio/Characters/open_backpack.wav"), "open_backpack")
