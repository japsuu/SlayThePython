# Global state manager

import pygame

from Cards import GameCard
from Input import Inputs
from StateManagement import GameState


# NOTE: A state machine would be better for this, but I'm too lazy to implement one for an otherwise small project :)
def gameloop_update(screen: pygame.Surface, game_state: GameState):
    clean_up_finished_animations(game_state)
    # Update and draw visual effects
    for effect in game_state.active_visual_effects:
        if effect.update():
            game_state.active_visual_effects.remove(effect)  # Remove expired effects
        else:
            effect.draw(screen)

    if is_main_menu_button_pressed():
        game_state.save_and_exit_current_save()
        return

    if game_state.is_player_choosing_rewards:
        player_choose_rewards(screen, game_state)
        return

    draw_enemies(screen, game_state)

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
                hand_card.draw(screen)
                # Color the card's mana cost red if the player can't afford it
                if can_use_card(game_state, hand_card):
                    hand_card.mana_cost_text_color = (0, 0, 0)
                else:
                    hand_card.mana_cost_text_color = (255, 0, 0)

            # If the mouse is over a card, move that card up a bit while moving the other cards down a bit
            hovered_card_index = -1
            for index, hand_card in enumerate(reversed(game_state.current_hand)):
                if not hand_card.marked_for_cleanup:
                    # Create new rect that goes to bottom of the screen, so hit detection "feels" intuitive.
                    full_screen_rect = pygame.Rect(hand_card.rect.left, hand_card.rect.top, hand_card.rect.width, screen.get_height())
                    if hovered_card_index < 0 and full_screen_rect.collidepoint(Inputs.get_mouse_position()):
                        hand_card.set_target_position_and_scale((hand_card.original_position[0], hand_card.original_position[1] - 200), 1, 0.1, 0.01)
                        hovered_card_index = index
                    else:
                        hand_card.set_target_position_and_scale(hand_card.original_position, 1, 0.3, 0.01)

            # Update the player's hand (Check if the player clicked a card)
            # Use reverse iteration to get the top-most (actually visible and clicked) card TODO: Merge with the loop above if possible.
            card_played = False
            for index, hand_card in enumerate(reversed(game_state.current_hand)):
                if can_use_card(game_state, hand_card):
                    if not hand_card.marked_for_cleanup:
                        if (not card_played) and Inputs.is_mouse_button_pressed(1):
                            if index == hovered_card_index and hand_card.rect.collidepoint(Inputs.get_mouse_position()):
                                use_card(game_state, hand_card)
                                card_played = True
                        if hovered_card_index >= 0 and hovered_card_index != index:
                            hand_card.set_target_position_and_scale((hand_card.original_position[0], hand_card.original_position[1] + 150), 1, 0.2, 0.01)

            # Check if the player clicked the end turn button
            if is_end_turn_button_pressed(screen):
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


def clean_up_finished_animations(game_state: GameState):
    for hand_card in game_state.current_hand:
        # If the card is marked for cleanup, delete it
        if hand_card.should_delete():
            game_state.current_hand.remove(hand_card)


def draw_enemies(screen: pygame.Surface, game_state: GameState):
    # Assign a new target if the current target is dead or doesn't exist
    if not game_state.current_targeted_enemy:
        if len(game_state.current_alive_enemies) > 0:
            game_state.current_targeted_enemy = game_state.current_alive_enemies[0]

    # Draw the enemies
    for enemy in game_state.current_alive_enemies:
        enemy.draw(screen, game_state)
        # If the enemy has been selected as the current target, draw an icon above it
        if enemy == game_state.current_targeted_enemy:
            target_icon_rect = (game_state.current_targeted_enemy.rect.centerx - game_state.game_data.icon_in_combat.get_width() / 2,
                                game_state.current_targeted_enemy.rect.top - game_state.game_data.icon_in_combat.get_width() / 2 - 60)
            screen.blit(game_state.game_data.icon_in_combat, target_icon_rect)
        # If the player clicks the enemy, select it as the current target
        elif Inputs.is_mouse_button_pressed(1):
            if enemy.rect.collidepoint(Inputs.get_mouse_position()):
                game_state.current_targeted_enemy = enemy


def can_use_card(game_state: GameState, card: GameCard):
    return card.card_data.card_cost <= game_state.current_player_mana


def use_card(game_state: GameState, card: GameCard):
    card.set_target_position_and_scale(pygame.display.get_surface().get_rect().center, 0.0)
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
    screen.blit(text_surface, text_rect)

    # Draw three cards to the center of the screen
    for card in game_state.current_reward_cards:
        card.draw(pygame.display.get_surface())
        if Inputs.is_mouse_button_pressed(1):
            if card.rect.collidepoint(Inputs.get_mouse_position()):
                # Card clicked, add it to the player's deck
                game_state.current_draw_pile.append(card.card_data)
                game_state.is_player_choosing_rewards = False
                game_state.load_next_room()
                game_state.save()


def draw_player_stats(screen: pygame.Surface, game_state: GameState):
    font = pygame.font.Font(None, 45)

    mana_icon_rect = pygame.Rect(screen.get_rect().left, screen.get_rect().bottom - game_state.game_data.icon_mana.get_height(), game_state.game_data.icon_mana.get_width(),
                                 game_state.game_data.icon_mana.get_height())
    pygame.display.get_surface().blit(game_state.game_data.icon_mana, mana_icon_rect)

    mana_text_color = (0, 0, 0)
    if game_state.current_player_mana < 1:
        mana_text_color = (255, 60, 60)
    elif game_state.current_player_mana < 2:
        mana_text_color = (140, 0, 0)
    mana_text_surface = font.render(f"{game_state.current_player_mana} / 3", True, mana_text_color)
    mana_text_rect = mana_text_surface.get_rect()
    mana_text_rect.center = mana_icon_rect.center
    screen.blit(mana_text_surface, mana_text_rect)

    font = pygame.font.Font(None, 25)

    health_icon_rect = pygame.Rect(0, 0, game_state.game_data.icon_health.get_width(), game_state.game_data.icon_health.get_height())
    health_icon_rect.midbottom = mana_icon_rect.midtop
    pygame.display.get_surface().blit(game_state.game_data.icon_health, health_icon_rect)

    health_text_color = (0, 0, 0)
    if game_state.current_game_save.player_health < 20:
        health_text_color = (255, 60, 60)
    elif game_state.current_game_save.player_health < 50:
        health_text_color = (140, 0, 0)
    health_text_surface = font.render(f"{game_state.current_game_save.player_health} / 100", True, health_text_color)
    health_text_rect = health_text_surface.get_rect()
    health_text_rect.center = health_icon_rect.center
    screen.blit(health_text_surface, health_text_rect)

    if game_state.current_player_block > 0:
        shield_icon_rect = pygame.Rect(0, 0, game_state.game_data.icon_block.get_width(), game_state.game_data.icon_block.get_height())
        shield_icon_rect.midbottom = health_icon_rect.midtop
        pygame.display.get_surface().blit(game_state.game_data.icon_block, shield_icon_rect)

        shield_text_color = (0, 0, 0)
        if game_state.current_player_block < 3:
            shield_text_color = (255, 60, 60)
        shield_text_surface = font.render(f"{game_state.current_player_block}", True, shield_text_color)
        shield_text_rect = shield_text_surface.get_rect()
        shield_text_rect.center = shield_icon_rect.center
        screen.blit(shield_text_surface, shield_text_rect)


def is_end_turn_button_pressed(screen: pygame.Surface):
    # Define button properties
    button_width = 120
    button_height = 40
    button_color = (0, 128, 0)  # Green color
    text_color = (255, 255, 255)  # White color
    font = pygame.font.Font(None, 36)  # You can adjust the font size

    # Create the button surface
    button_surface = pygame.Surface((button_width, button_height))
    button_surface.fill(button_color)

    # Create the button text
    text_surface = font.render("End Turn", True, text_color)

    # Calculate button and text positions
    button_rect = button_surface.get_rect()
    text_rect = text_surface.get_rect()
    button_rect.bottomright = screen.get_rect().bottomright
    text_rect.center = button_rect.center

    # Blit the button and text onto the screen
    screen.blit(button_surface, button_rect)
    screen.blit(text_surface, text_rect)

    if Inputs.is_mouse_button_pressed(1):
        if button_rect.collidepoint(Inputs.get_mouse_position()):
            return True

    return False


def is_main_menu_button_pressed():
    screen = pygame.display.get_surface()
    # Define button properties
    button_width = 180
    button_height = 40
    button_color = (128, 0, 0)
    text_color = (255, 255, 255)
    font = pygame.font.Font(None, 36)

    # Create the button surface
    button_surface = pygame.Surface((button_width, button_height))
    button_surface.fill(button_color)

    # Create the button text
    text_surface = font.render("Main Menu", True, text_color)

    # Calculate button and text positions
    button_rect = button_surface.get_rect()
    text_rect = text_surface.get_rect()
    button_rect.topleft = screen.get_rect().topleft
    text_rect.center = button_rect.center

    # Blit the button and text onto the screen
    screen.blit(button_surface, button_rect)
    screen.blit(text_surface, text_rect)

    if Inputs.is_mouse_button_pressed(1):
        if button_rect.collidepoint(Inputs.get_mouse_position()):
            return True

    return False
