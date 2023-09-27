import pygame

from constants import LAYER_TARGETED_ENEMY_ICON, LAYER_CARD_REWARD_TEXT, LAYER_PLAYER_UI_BACKGROUND, LAYER_PLAYER_UI_TEXT, LAYER_OVERRIDE_BG, LAYER_OVERRIDE_FG
from game_objects import GameCard, VisualEffect
from state_management import GameState
from utils.drawing import DrawCall
from utils.input import Inputs


def update_gameloop(screen: pygame.Surface, game_state: GameState):
    game_state.update_game_objects()

    clean_up_finished_animations(game_state)

    if is_main_menu_button_pressed(game_state):
        game_state.save_and_exit_current_save()
        return

    if game_state.is_player_choosing_rewards:
        player_choose_rewards(screen, game_state)
        return

    check_assigned_target(game_state)

    draw_enemies(game_state)

    draw_player_stats(screen, game_state)

    fight_state = game_state.get_fight_state()

    if fight_state == "PLAYER_WIN":
        if game_state.current_game_save.dungeon_room_index == game_state.game_data.BOSS_ROOM_INDEX:
            # The player has defeated the boss, delete the save game and return to the main menu
            game_state.delete_current_save()
            return
        game_state.generate_reward_cards()
        game_state.is_player_choosing_rewards = True
    elif fight_state == "PLAYER_LOSE":
        # Player dies, delete the save game
        game_state.delete_current_save()  # TODO: Draw a game over screen with a button to return to main menu. Requires a player_alive flag in GameState
    elif fight_state == "IN_PROGRESS":
        if game_state.is_players_turn:
            # Display enemies' next round's intentions
            for enemy in game_state.current_alive_enemy_characters:
                # TODO: Move to EnemyCharacter.draw(), and manually update EnemyCharacter.current_round_index and EnemyCharacter.is_players_turn
                enemy.draw_intentions(screen, game_state.current_round_index)

            # Draw the player's hand
            for hand_card in game_state.current_hand_game_cards:
                # Color the card's mana cost red if the player can't afford it
                if can_use_card(game_state, hand_card):
                    hand_card.card_info_mana_text_color = (0, 0, 0)
                else:
                    hand_card.card_info_mana_text_color = (255, 0, 0)

            hovered_card_vertical_offset = -200
            non_hovered_card_vertical_offset = 150
            card_move_to_original_pos_duration = 0.3
            card_move_up_duration = 0.15
            non_hovered_card_duration = 0.1

            # Update the player's hand (Check if the player clicked a card)
            # If the mouse is over a card, move that card up a bit while moving the other cards down a bit
            # Use reverse iteration to get the top-most (actually visible and clicked) card
            is_some_card_hovered = False
            for index, hand_card in enumerate(reversed(game_state.current_hand_game_cards)):
                hand_card: GameCard
                if not hand_card.has_been_played:
                    # Create new rect that goes to bottom of the screen, so hit detection "feels" intuitive.
                    extended_rect = pygame.Rect(hand_card.rect.left, hand_card.rect.top, hand_card.rect.width, screen.get_height())
                    # If the card is hovered, move it up a bit
                    if (not is_some_card_hovered) and extended_rect.collidepoint(Inputs.get_mouse_position()):
                        is_some_card_hovered = True
                        if not hand_card.is_self_hovered:
                            target_pos = (hand_card.original_position[0], hand_card.original_position[1] + hovered_card_vertical_offset)
                            hand_card.move_to(target_pos, card_move_up_duration)
                            hand_card.is_self_hovered = True
                            hand_card.is_other_card_hovered = False
                    else:
                        if hand_card.is_self_hovered:
                            hand_card.move_to(hand_card.original_position, card_move_to_original_pos_duration)
                            hand_card.is_self_hovered = False

            # Update the player's hand cards (and check if the player clicked a card)
            # Use reverse iteration to get the top-most (actually visible and clicked) card
            card_played = False
            for hand_card in reversed(game_state.current_hand_game_cards):
                hand_card: GameCard
                if not hand_card.has_been_played:
                    if can_use_card(game_state, hand_card):
                        # Check if the card was clicked
                        if (not card_played) and Inputs.is_mouse_button_pressed(1):
                            if hand_card.is_self_hovered and hand_card.rect.collidepoint(Inputs.get_mouse_position()):
                                use_card(game_state, hand_card)
                                card_played = True
                    if not hand_card.is_self_hovered:
                        # If some card is hovered, move other non-hovered cards down a bit
                        if is_some_card_hovered:
                            if not hand_card.is_other_card_hovered:
                                hand_card.is_other_card_hovered = True
                                target_pos = (hand_card.original_position[0], hand_card.original_position[1] + non_hovered_card_vertical_offset)
                                hand_card.move_to(target_pos, non_hovered_card_duration)
                        # If no card is hovered, move all cards back to their original positions
                        else:
                            if hand_card.is_other_card_hovered:
                                hand_card.is_other_card_hovered = False
                                hand_card.move_to(hand_card.original_position, card_move_to_original_pos_duration)

            # Check if the player clicked the end turn button
            if is_end_turn_button_pressed(game_state):
                game_state.is_players_turn = False
        else:
            # TODO: Add a delay between enemy turns
            # TODO: Add a delay between enemy intentions
            # Apply enemy intentions
            for enemy in game_state.current_alive_enemy_characters:
                enemy_intention = enemy.get_intention(game_state.current_round_index)
                if enemy_intention.gain_health_amount > 0:
                    enemy.gain_health(enemy_intention.gain_health_amount)
                if enemy_intention.gain_block_amount > 0:
                    enemy.gain_block(enemy_intention.gain_block_amount)
                if enemy_intention.deal_damage_amount > 0:
                    damage_player(game_state, enemy_intention.deal_damage_amount)

            game_state.current_round_index += 1
            game_state.initialize_player_turn()
    else:
        raise Exception(f"Unknown fight state: {fight_state}. Guess I'll die :(")


def damage_player(game_state, amount):
    game_state: GameState
    # Reduce current block by the damage amount
    remaining_damage = amount - game_state.current_player_block
    game_state.remove_block(amount)

    # Reduce current health by the damage amount
    if remaining_damage > 0:
        game_state.current_game_save.player_health = max(game_state.current_game_save.player_health - remaining_damage, 0)
        effect_pos = (pygame.display.get_surface().get_width() // 2, pygame.display.get_surface().get_height() // 2)
        effect = VisualEffect(game_state.game_data.image_library.effect_damaged_self, effect_pos, 1000)
        effect.queue(game_state.game_object_collection)


def clean_up_finished_animations(game_state: GameState):
    # for hand_card in game_state.current_hand_game_cards:
    #     # If the card is marked for cleanup, delete it
    #     if hand_card.is_awaiting_destruction:           # WARN: Possibly not needed, as the card can be instantly removed from the hand when played. The GameObject system should handle this.
    #         game_state.current_hand_game_cards.remove(hand_card)
    print(f"Hand cards: {len(game_state.current_hand_game_cards)}")


def check_assigned_target(game_state: GameState):
    # Assign a new target if the current target is dead or doesn't exist
    if not game_state.current_targeted_enemy_character:
        if len(game_state.current_alive_enemy_characters) > 0:
            game_state.current_targeted_enemy_character = game_state.current_alive_enemy_characters[0]


def draw_enemies(game_state: GameState):
    for enemy in game_state.current_alive_enemy_characters:
        game_state.frame_buffer.add_drawable(enemy)
        # If the enemy has been selected as the current target, draw an icon above it
        if enemy == game_state.current_targeted_enemy_character:
            target_x = game_state.current_targeted_enemy_character.rect.centerx - game_state.game_data.image_library.icon_target.get_width() / 2
            target_y = game_state.current_targeted_enemy_character.rect.top - game_state.game_data.image_library.icon_target.get_width() / 2 - 100
            DrawCall(game_state.game_data.image_library.icon_target, (target_x, target_y), LAYER_TARGETED_ENEMY_ICON).queue(game_state)
        # If the player clicks the enemy, select it as the current target
        elif Inputs.is_mouse_button_pressed(1):
            if enemy.rect.collidepoint(Inputs.get_mouse_position()):
                game_state.current_targeted_enemy_character = enemy


def can_use_card(game_state: GameState, card: GameCard):
    return (not card.is_awaiting_destruction) and (card.card_data.card_cost <= game_state.current_player_mana)


def use_card(game_state: GameState, card: GameCard):
    card.on_played()

    game_state.current_player_mana -= card.card_data.card_cost
    game_state.current_player_block += card.card_data.card_block
    if card.card_data.card_damage > 0:
        if len(game_state.current_alive_enemy_characters) > 0:
            game_state.current_targeted_enemy_character.take_damage(card.card_data.card_damage)
            if game_state.current_targeted_enemy_character.current_health <= 0:
                game_state.current_alive_enemy_characters.remove(game_state.current_targeted_enemy_character)
                if len(game_state.current_alive_enemy_characters) > 0:
                    game_state.current_targeted_enemy_character = game_state.current_alive_enemy_characters[0]


def player_choose_rewards(screen: pygame.Surface, game_state: GameState):
    font = pygame.font.Font(None, 36)
    text_color = (255, 255, 255)

    # Draw the info text
    text_surface = font.render(f"Choose a card to add to your deck:", True, text_color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = screen.get_rect().midtop
    DrawCall(text_surface, text_rect, LAYER_CARD_REWARD_TEXT).queue(game_state)

    # Draw three cards to the center of the screen
    for card in game_state.current_reward_game_cards:
        if Inputs.is_mouse_button_pressed(1):
            if card.rect.collidepoint(Inputs.get_mouse_position()):
                # Card clicked, add it to the player's deck
                game_state.current_draw_pile.append(card.card_data)
                game_state.is_player_choosing_rewards = False
                for reward_card in game_state.current_reward_game_cards:
                    reward_card.destroy()
                game_state.load_next_room()
                game_state.save()


def draw_player_stats(screen: pygame.Surface, game_state: GameState):
    font = pygame.font.Font(None, 45)

    left = screen.get_rect().left
    top = screen.get_rect().bottom - game_state.game_data.image_library.icon_mana.get_height()
    mana_icon_rect = pygame.Rect(left, top, game_state.game_data.image_library.icon_mana.get_width(), game_state.game_data.image_library.icon_mana.get_height())
    DrawCall(game_state.game_data.image_library.icon_mana, mana_icon_rect, LAYER_PLAYER_UI_BACKGROUND).queue(game_state)

    mana_text_color = (0, 0, 0)
    if game_state.current_player_mana < 1:
        mana_text_color = (255, 60, 60)
    elif game_state.current_player_mana < 2:
        mana_text_color = (140, 0, 0)
    mana_text_surface = font.render(f"{game_state.current_player_mana} / 3", True, mana_text_color)
    mana_text_rect = mana_text_surface.get_rect()
    mana_text_rect.center = mana_icon_rect.center
    DrawCall(mana_text_surface, mana_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state)

    font = pygame.font.Font(None, 25)

    health_icon_rect = pygame.Rect(0, 0, game_state.game_data.image_library.icon_health.get_width(), game_state.game_data.image_library.icon_health.get_height())
    health_icon_rect.midbottom = mana_icon_rect.midtop
    DrawCall(game_state.game_data.image_library.icon_health, health_icon_rect, LAYER_PLAYER_UI_BACKGROUND).queue(game_state)

    health_text_color = (0, 0, 0)
    if game_state.current_game_save.player_health < 20:
        health_text_color = (255, 60, 60)
    elif game_state.current_game_save.player_health < 50:
        health_text_color = (140, 0, 0)
    health_text_surface = font.render(f"{game_state.current_game_save.player_health} / 100", True, health_text_color)
    health_text_rect = health_text_surface.get_rect()
    health_text_rect.center = health_icon_rect.center
    DrawCall(health_text_surface, health_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state)

    if game_state.current_player_block > 0:
        shield_icon_rect = pygame.Rect(0, 0, game_state.game_data.image_library.icon_block.get_width(), game_state.game_data.image_library.icon_block.get_height())
        shield_icon_rect.midbottom = health_icon_rect.midtop
        DrawCall(game_state.game_data.image_library.icon_block, shield_icon_rect, LAYER_PLAYER_UI_BACKGROUND).queue(game_state)

        shield_text_color = (0, 0, 0)
        if game_state.current_player_block < 3:
            shield_text_color = (255, 60, 60)
        shield_text_surface = font.render(f"{game_state.current_player_block}", True, shield_text_color)
        shield_text_rect = shield_text_surface.get_rect()
        shield_text_rect.center = shield_icon_rect.center
        DrawCall(shield_text_surface, shield_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state)


def is_end_turn_button_pressed(game_state: GameState):
    # Define button properties
    button_width = 120
    button_height = 40
    button_color = (0, 128, 0)  # Green color
    text_color = (255, 255, 255)  # White color
    font = pygame.font.Font(None, 36)  # You can adjust the card_info_font size

    # Create the button sprite
    button_surface = pygame.Surface((button_width, button_height))
    button_surface.fill(button_color)

    # Create the button text
    text_surface = font.render("End Turn", True, text_color)

    # Calculate button and text positions
    button_rect = button_surface.get_rect()
    text_rect = text_surface.get_rect()
    button_rect.bottomright = game_state.screen.get_rect().bottomright
    text_rect.center = button_rect.center

    DrawCall(button_surface, button_rect, LAYER_OVERRIDE_BG).queue(game_state)
    DrawCall(text_surface, text_rect, LAYER_OVERRIDE_FG).queue(game_state)

    if Inputs.is_mouse_button_pressed(1):
        if button_rect.collidepoint(Inputs.get_mouse_position()):
            return True

    return False


def is_main_menu_button_pressed(game_state: GameState):
    screen = pygame.display.get_surface()
    # Define button properties
    button_width = 180
    button_height = 40
    button_color = (128, 0, 0)
    text_color = (255, 255, 255)
    font = pygame.font.Font(None, 36)

    # Create the button sprite
    button_surface = pygame.Surface((button_width, button_height))
    button_surface.fill(button_color)

    # Create the button text
    text_surface = font.render("Main Menu", True, text_color)

    # Calculate button and text positions
    button_rect = button_surface.get_rect()
    text_rect = text_surface.get_rect()
    button_rect.topleft = screen.get_rect().topleft
    text_rect.center = button_rect.center

    DrawCall(button_surface, button_rect, LAYER_OVERRIDE_BG).queue(game_state)
    DrawCall(text_surface, text_rect, LAYER_OVERRIDE_FG).queue(game_state)

    if Inputs.is_mouse_button_pressed(1):
        if button_rect.collidepoint(Inputs.get_mouse_position()):
            return True

    return False
