import pygame
import Constants

from Cards import GameCard
from Drawing import DrawCall
from Input import Inputs
from StateManagement import GameState


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
        game_state.is_player_choosing_rewards = True
    elif fight_state == "PLAYER_LOSE":
        # Player dies, delete the save game
        game_state.delete_current_save()  # TODO: Draw a game over screen with a button to return to main menu. Requires a player_alive flag in GameState
    elif fight_state == "IN_PROGRESS":
        if game_state.is_players_turn:
            # Display enemies' next round's intentions
            for enemy in game_state.current_alive_enemies:
                enemy.draw_intentions(screen, game_state, game_state.current_round_index)

            # Draw the player's hand
            for hand_card in game_state.current_hand:
                game_state.frame_buffer.add_drawable(hand_card, PLAYER_HAND_DRAW_ORDER)
                # Color the card's mana cost red if the player can't afford it
                if can_use_card(game_state, hand_card):
                    hand_card.mana_cost_text_color = (0, 0, 0)
                else:
                    hand_card.mana_cost_text_color = (255, 0, 0)

            hovered_card_vertical_offset = -200
            non_hovered_card_vertical_offset = 150
            card_return_duration = 1
            hovered_card_duration = 0.3
            non_hovered_card_duration = 3.8

            # Update the player's hand (Check if the player clicked a card)
            # If the mouse is over a card, move that card up a bit while moving the other cards down a bit
            # Use reverse iteration to get the top-most (actually visible and clicked) card
            hovered_card_index = -1
            for index, hand_card in enumerate(reversed(game_state.current_hand)):
                if not hand_card.marked_for_cleanup:
                    # Create new rect that goes to bottom of the screen, so hit detection "feels" intuitive.
                    full_screen_rect = pygame.Rect(hand_card.rect.left, hand_card.rect.top, hand_card.rect.width, screen.get_height())
                    # If the card is hovered, move it up a bit
                    if hovered_card_index < 0 and full_screen_rect.collidepoint(Inputs.get_mouse_position()):
                        hand_card.set_target_position_and_scale((hand_card.original_position[0], hand_card.original_position[1] + hovered_card_vertical_offset), 1, hovered_card_duration, 0.1)
                        hovered_card_index = index

            # Update the player's hand (Check if the player clicked a card)
            # Use reverse iteration to get the top-most (actually visible and clicked) card
            card_played = False
            for index, hand_card in enumerate(reversed(game_state.current_hand)):
                if can_use_card(game_state, hand_card):
                    if not hand_card.marked_for_cleanup:
                        # Check if the card was clicked
                        if (not card_played) and Inputs.is_mouse_button_pressed(1):
                            if index == hovered_card_index and hand_card.rect.collidepoint(Inputs.get_mouse_position()):
                                use_card(game_state, hand_card)
                                card_played = True
                        if hovered_card_index != index:
                            # If some card is hovered, move other non-hovered cards down a bit
                            if hovered_card_index >= 0:
                                hand_card.set_target_position_and_scale((hand_card.original_position[0], hand_card.original_position[1] + non_hovered_card_vertical_offset), 1, non_hovered_card_duration, 0.1)
                            # If no card is hovered, move all cards back to their original positions
                            else:
                                hand_card.set_target_position_and_scale(hand_card.original_position, 1, card_return_duration, 0.1)

            # Check if the player clicked the end turn button
            if is_end_turn_button_pressed(game_state):
                game_state.is_players_turn = False
        else:
            # TODO: Add a delay between enemy turns
            # TODO: Add a delay between enemy intentions
            # Apply enemy intentions
            for enemy in game_state.current_alive_enemies:
                enemy_intention = enemy.get_intentions(game_state.current_round_index)
                if enemy_intention.gain_health_amount > 0:
                    enemy.gain_health(enemy_intention.gain_health_amount)
                if enemy_intention.gain_block_amount > 0:
                    enemy.gain_block(enemy_intention.gain_block_amount)
                if enemy_intention.deal_damage_amount > 0:
                    game_state.damage_player(enemy_intention.deal_damage_amount)

            game_state.current_round_index += 1
            game_state.initialize_player_turn()
    else:
        raise Exception(f"Unknown fight state: {fight_state}. Guess I'll die :(")


def clean_up_finished_animations(game_state: GameState):    # TODO: Convert to GameObject implementation
    for hand_card in game_state.current_hand:
        # If the card is marked for cleanup, delete it
        if hand_card.should_delete():
            game_state.current_hand.remove(hand_card)


def check_assigned_target(game_state: GameState):
    # Assign a new target if the current target is dead or doesn't exist
    if not game_state.current_targeted_enemy:
        if len(game_state.current_alive_enemies) > 0:
            game_state.current_targeted_enemy = game_state.current_alive_enemies[0]


def draw_enemies(game_state: GameState):
    for enemy in game_state.current_alive_enemies:
        game_state.frame_buffer.add_drawable(enemy, ENEMY_DRAW_ORDER)
        # If the enemy has been selected as the current target, draw an icon above it
        if enemy == game_state.current_targeted_enemy:
            target_icon_pos = (game_state.current_targeted_enemy.rect.centerx - game_state.game_data.icon_target.get_width() / 2, game_state.current_targeted_enemy.rect.top - game_state.game_data.icon_target.get_width() / 2 - 100)
            DrawCall(game_state.game_data.icon_target, target_icon_pos, TARGETED_ENEMY_ICON_DRAW_ORDER).queue(game_state)
        # If the player clicks the enemy, select it as the current target
        elif Inputs.is_mouse_button_pressed(1):
            if enemy.rect.collidepoint(Inputs.get_mouse_position()):
                game_state.current_targeted_enemy = enemy


def can_use_card(game_state: GameState, card: GameCard):
    return card.card_data.card_cost <= game_state.current_player_mana


def use_card(game_state: GameState, card: GameCard):
    card.set_target_position_and_scale(game_state.screen.get_rect().center, 0.0)
    card.marked_for_cleanup = True

    game_state.current_player_mana -= card.card_data.card_cost
    game_state.current_player_block += card.card_data.card_block
    if card.card_data.card_damage > 0:
        if len(game_state.current_alive_enemies) > 0:
            game_state.current_targeted_enemy.take_damage(game_state, card.card_data.card_damage)
            if game_state.current_targeted_enemy.current_health <= 0:
                game_state.current_alive_enemies.remove(game_state.current_targeted_enemy)
                if len(game_state.current_alive_enemies) > 0:
                    game_state.current_targeted_enemy = game_state.current_alive_enemies[0]


# Let the player choose cards to add to their deck
def player_choose_rewards(screen: pygame.Surface, game_state: GameState):
    font = pygame.font.Font(None, 36)
    text_color = (255, 255, 255)

    # Draw the info text
    text_surface = font.render(f"Choose a card to add to your deck:", True, text_color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = screen.get_rect().midtop
    DrawCall(text_surface, text_rect, CARD_REWARD_TEXT_DRAW_ORDER).queue(game_state)

    # Draw three cards to the center of the screen
    for card in game_state.current_reward_cards:
        game_state.frame_buffer.add_drawable(card, CARD_REWARD_DRAW_ORDER)
        if Inputs.is_mouse_button_pressed(1):
            if card.rect.collidepoint(Inputs.get_mouse_position()):
                # Card clicked, add it to the player's deck
                game_state.current_draw_pile.append(card.card_data)
                game_state.is_player_choosing_rewards = False
                game_state.load_next_room()
                game_state.save()


def draw_player_stats(screen: pygame.Surface, game_state: GameState):
    font = pygame.font.Font(None, 45)

    mana_icon_rect = pygame.Rect(screen.get_rect().left, screen.get_rect().bottom - game_state.game_data.icon_mana.get_height(), game_state.game_data.icon_mana.get_width(), game_state.game_data.icon_mana.get_height())
    DrawCall(game_state.game_data.icon_mana, mana_icon_rect, PLAYER_UI_BACKGROUND_DRAW_ORDER).queue(game_state)

    mana_text_color = (0, 0, 0)
    if game_state.current_player_mana < 1:
        mana_text_color = (255, 60, 60)
    elif game_state.current_player_mana < 2:
        mana_text_color = (140, 0, 0)
    mana_text_surface = font.render(f"{game_state.current_player_mana} / 3", True, mana_text_color)
    mana_text_rect = mana_text_surface.get_rect()
    mana_text_rect.center = mana_icon_rect.center
    DrawCall(mana_text_surface, mana_text_rect, PLAYER_UI_TEXT_DRAW_ORDER).queue(game_state)

    font = pygame.font.Font(None, 25)

    health_icon_rect = pygame.Rect(0, 0, game_state.game_data.icon_health.get_width(), game_state.game_data.icon_health.get_height())
    health_icon_rect.midbottom = mana_icon_rect.midtop
    DrawCall(game_state.game_data.icon_health, health_icon_rect, PLAYER_UI_BACKGROUND_DRAW_ORDER).queue(game_state)

    health_text_color = (0, 0, 0)
    if game_state.current_game_save.player_health < 20:
        health_text_color = (255, 60, 60)
    elif game_state.current_game_save.player_health < 50:
        health_text_color = (140, 0, 0)
    health_text_surface = font.render(f"{game_state.current_game_save.player_health} / 100", True, health_text_color)
    health_text_rect = health_text_surface.get_rect()
    health_text_rect.center = health_icon_rect.center
    DrawCall(health_text_surface, health_text_rect, PLAYER_UI_TEXT_DRAW_ORDER).queue(game_state)

    if game_state.current_player_block > 0:
        shield_icon_rect = pygame.Rect(0, 0, game_state.game_data.icon_block.get_width(), game_state.game_data.icon_block.get_height())
        shield_icon_rect.midbottom = health_icon_rect.midtop
        DrawCall(game_state.game_data.icon_block, shield_icon_rect, PLAYER_UI_BACKGROUND_DRAW_ORDER).queue(game_state)

        shield_text_color = (0, 0, 0)
        if game_state.current_player_block < 3:
            shield_text_color = (255, 60, 60)
        shield_text_surface = font.render(f"{game_state.current_player_block}", True, shield_text_color)
        shield_text_rect = shield_text_surface.get_rect()
        shield_text_rect.center = shield_icon_rect.center
        DrawCall(shield_text_surface, shield_text_rect, PLAYER_UI_TEXT_DRAW_ORDER).queue(game_state)


def is_end_turn_button_pressed(game_state: GameState):
    # Define button properties
    button_width = 120
    button_height = 40
    button_color = (0, 128, 0)  # Green color
    text_color = (255, 255, 255)  # White color
    font = pygame.font.Font(None, 36)  # You can adjust the font size

    # Create the button drawn_surface
    button_surface = pygame.Surface((button_width, button_height))
    button_surface.fill(button_color)

    # Create the button text
    text_surface = font.render("End Turn", True, text_color)

    # Calculate button and text positions
    button_rect = button_surface.get_rect()
    text_rect = text_surface.get_rect()
    button_rect.bottomright = game_state.screen.get_rect().bottomright
    text_rect.center = button_rect.center

    DrawCall(button_surface, button_rect, OVERRIDE_DRAW_ORDER_BG).queue(game_state)
    DrawCall(text_surface, text_rect, OVERRIDE_DRAW_ORDER_FG).queue(game_state)

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

    # Create the button drawn_surface
    button_surface = pygame.Surface((button_width, button_height))
    button_surface.fill(button_color)

    # Create the button text
    text_surface = font.render("Main Menu", True, text_color)

    # Calculate button and text positions
    button_rect = button_surface.get_rect()
    text_rect = text_surface.get_rect()
    button_rect.topleft = screen.get_rect().topleft
    text_rect.center = button_rect.center

    DrawCall(button_surface, button_rect, OVERRIDE_DRAW_ORDER_BG).queue(game_state)
    DrawCall(text_surface, text_rect, OVERRIDE_DRAW_ORDER_FG).queue(game_state)

    if Inputs.is_mouse_button_pressed(1):
        if button_rect.collidepoint(Inputs.get_mouse_position()):
            return True

    return False
