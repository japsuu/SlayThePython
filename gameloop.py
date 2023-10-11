import pygame

from utils.constants import LAYER_TARGETED_ENEMY_ICON, LAYER_CARD_REWARD_TEXT, LAYER_PLAYER_UI_BACKGROUND, LAYER_PLAYER_UI_TEXT, LAYER_OVERRIDE_BG, LAYER_OVERRIDE_FG, LAYER_UI_EFFECTS, \
    FONT_CARD_REWARD, FONT_DUNGEON_LEVEL, FONT_DUNGEON_LEVEL_HINT, FONT_CARD_PILE_COUNT, FONT_PLAYER_MANA, FONT_PLAYER_HEALTH, FONT_PLAYER_BLOCK, FONT_BUTTON_GENERIC
from game_objects import GameCard
from state_management import GameState
from utils.drawing import DrawCall
from utils.input import Inputs


def update(screen: pygame.Surface, game_state: GameState):
    game_state.update_game_objects()

    draw_damage_overlay(game_state)

    clean_up_finished_animations(game_state)

    if is_main_menu_button_pressed(game_state):
        game_state.exit_current_save()
        return

    if is_abandon_button_pressed(game_state):
        game_state.delete_current_save()
        return

    if game_state.is_player_choosing_rewards:
        player_choose_rewards(screen, game_state)
        return

    check_assigned_target(game_state)

    animate_target_icon(game_state)

    draw_player_stats(screen, game_state)

    if game_state.gameplay_pause_timer > 0:
        game_state.gameplay_pause_timer -= game_state.delta_time
        return  # Don't update the game if it's paused

    fight_state = game_state.get_fight_state()

    if fight_state == "PLAYER_WIN":
        if game_state.current_game_save.dungeon_room_index == game_state.game_data.boss_room_index:
            # The player has defeated the boss, delete the save game and return to the main menu
            game_state.delete_current_save()
            return
        for hand_card in game_state.current_hand_game_cards:
            hand_card.on_played()
            game_state.current_discard_pile.append(hand_card.card_data)
        game_state.current_hand_game_cards.clear()
        game_state.generate_reward_cards()
        game_state.is_player_choosing_rewards = True
    elif fight_state == "PLAYER_LOSE":
        # Player dies, delete the save game
        game_state.delete_current_save()  # TODO: Draw a game over screen with a button to return to main menu.
    elif fight_state == "IN_PROGRESS":
        if game_state.is_players_turn:
            # Display enemies' next round's intentions
            for enemy in game_state.current_alive_enemy_characters:
                enemy.current_round_index = game_state.current_round_index

            # Draw the player's hand
            for hand_card in game_state.current_hand_game_cards:
                # Color the card's mana cost red if the player can't afford it
                if can_play_card(game_state, hand_card):
                    hand_card.card_info_mana_text_color = (50, 50, 100)
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
                if (not hand_card.has_been_played) and hand_card.can_be_clicked:
                    # Create new rect that goes to bottom of the screen, so hit detection "feels" intuitive.
                    extended_rect = pygame.Rect(hand_card.rect.left, hand_card.rect.top, hand_card.rect.width, screen.get_height())
                    # If the card is hovered, move it up a bit
                    if (not is_some_card_hovered) and extended_rect.collidepoint(Inputs.get_mouse_position()):
                        is_some_card_hovered = True
                        if not hand_card.is_self_hovered:
                            target_pos = (hand_card.original_position[0], hand_card.original_position[1] + hovered_card_vertical_offset)
                            hand_card.create_animation(target_pos, card_move_up_duration, 255, 0.2)
                            hand_card.is_self_hovered = True
                            hand_card.is_other_card_hovered = False
                    else:
                        if hand_card.is_self_hovered:
                            hand_card.create_animation(hand_card.original_position, card_move_to_original_pos_duration, 255, 0.2)
                            hand_card.is_self_hovered = False

            # Update the player's hand cards (and check if the player clicked a card)
            # Use reverse iteration to get the top-most (actually visible and clicked) card
            card_played = False
            for hand_card in reversed(game_state.current_hand_game_cards):
                hand_card: GameCard
                if (not hand_card.has_been_played) and hand_card.can_be_clicked:
                    if can_play_card(game_state, hand_card):
                        # Check if the card was clicked
                        if (not card_played) and Inputs.is_mouse_button_pressed(1):
                            if hand_card.is_self_hovered and hand_card.rect.collidepoint(Inputs.get_mouse_position()):
                                play_card(game_state, hand_card)
                                card_played = True
                    if not hand_card.is_self_hovered:
                        # If some card is hovered, move other non-hovered cards down a bit
                        if is_some_card_hovered:
                            if not hand_card.is_other_card_hovered:
                                hand_card.is_other_card_hovered = True
                                target_pos = (hand_card.original_position[0], hand_card.original_position[1] + non_hovered_card_vertical_offset)
                                hand_card.create_animation(target_pos, non_hovered_card_duration, 100, 0.2)
                        # If no card is hovered, move all cards back to their original positions
                        else:
                            if hand_card.is_other_card_hovered:
                                hand_card.is_other_card_hovered = False
                                hand_card.create_animation(hand_card.original_position, card_move_to_original_pos_duration, 255, 0.2)

            # Check if the player clicked the end turn button
            if is_end_turn_button_pressed(game_state):
                game_state.is_players_turn = False
                for enemy in game_state.current_alive_enemy_characters:
                    enemy.remove_block(9999)
                    enemy.has_completed_turn = False

                for old_card in game_state.current_hand_game_cards:
                    old_card.on_played()
                    game_state.current_discard_pile.append(old_card.card_data)
                game_state.gameplay_pause_timer = 2
        else:
            # Apply enemy intentions
            for enemy in game_state.current_alive_enemy_characters:
                if enemy.has_completed_turn:
                    continue
                enemy.has_completed_turn = True
                enemy_intention = enemy.get_intention(game_state.current_round_index)
                if enemy_intention.gain_health_amount > 0:
                    enemy.gain_health(enemy_intention.gain_health_amount)
                if enemy_intention.gain_block_amount > 0:
                    enemy.gain_block(enemy_intention.gain_block_amount)
                if enemy_intention.deal_damage_amount > 0:
                    damage_player(game_state, enemy_intention.deal_damage_amount)
                enemy.play_turn_animation(enemy_intention)
                game_state.gameplay_pause_timer = 2
                return

            game_state.current_round_index += 1
            game_state.initialize_player_turn()
    else:
        raise Exception(f"Unknown fight state: {fight_state}. Guess I'll die :(")


def damage_player(game_state, amount):
    game_state: GameState
    # Reduce current block by the damage amount
    removed_block = game_state.current_player_block - max(0, game_state.current_player_block - amount)
    remaining_damage = amount - game_state.current_player_block
    if removed_block > 0:
        game_state.instantiate_damage_number(removed_block, True, (game_state.screen.get_rect().left + 100, game_state.screen.get_rect().bottom - 400), LAYER_UI_EFFECTS)
    game_state.remove_block(amount)

    # Reduce current health by the damage amount
    if remaining_damage > 0:
        game_state.current_game_save.player_health = max(game_state.current_game_save.player_health - remaining_damage, 0)
        game_state.play_player_damaged_animation()
        game_state.instantiate_damage_number(remaining_damage, False, (game_state.screen.get_rect().left + 100, game_state.screen.get_rect().bottom - 300), LAYER_UI_EFFECTS)


def clean_up_finished_animations(game_state: GameState):
    for hand_card in game_state.current_hand_game_cards:
        # If the card is marked for cleanup, delete it
        if hand_card.is_awaiting_destruction:
            game_state.current_hand_game_cards.remove(hand_card)


def draw_damage_overlay(game_state: GameState):
    if game_state.player_damaged_animation:
        game_state.player_damaged_animation.update(game_state.delta_time)
        if game_state.player_damaged_animation.is_finished:
            game_state.player_damaged_animation = None
    if game_state.player_damaged_animation:
        DrawCall(game_state.player_damaged_overlay, (0, 0), LAYER_OVERRIDE_BG).queue(game_state)


def check_assigned_target(game_state: GameState):
    # Assign a new target if the current target is dead or doesn't exist
    if not game_state.current_targeted_enemy_character:
        if len(game_state.current_alive_enemy_characters) > 0:
            game_state.current_targeted_enemy_character = game_state.current_alive_enemy_characters[0]
    else:
        for enemy in game_state.current_alive_enemy_characters:
            # If the player clicks the enemy, select it as the current target
            if Inputs.is_mouse_button_pressed(1) and (enemy != game_state.current_targeted_enemy_character):
                if enemy.rect.collidepoint(Inputs.get_mouse_position()):
                    game_state.current_targeted_enemy_character = enemy


def animate_target_icon(game_state: GameState):
    game_state.target_icon_alpha += game_state.target_icon_alpha_direction * game_state.delta_time * 255
    if game_state.target_icon_alpha > 255:
        game_state.target_icon_alpha = 255
        game_state.target_icon_alpha_direction = -1
    elif game_state.target_icon_alpha < 0:
        game_state.target_icon_alpha = 0
        game_state.target_icon_alpha_direction = 1
    if game_state.current_targeted_enemy_character:
        target_x = game_state.current_targeted_enemy_character.rect.centerx - game_state.game_data.image_library.icon_target.get_width() / 2
        target_y = game_state.current_targeted_enemy_character.rect.top - game_state.game_data.image_library.icon_target.get_width() / 2 - 100
        game_state.game_data.image_library.icon_target.set_alpha(game_state.target_icon_alpha)
        DrawCall(game_state.game_data.image_library.icon_target, (target_x, target_y), LAYER_TARGETED_ENEMY_ICON).queue(game_state)


def can_play_card(game_state: GameState, card: GameCard):
    return (not card.is_awaiting_destruction) and (card.card_data.card_cost <= game_state.current_player_mana)


def play_card(game_state: GameState, card: GameCard):
    game_state.current_player_mana -= card.card_data.card_cost
    damage_player(game_state, card.card_data.card_self_damage)
    game_state.current_player_block += card.card_data.card_self_block
    game_state.current_game_save.player_health += card.card_data.card_self_heal     # TODO: Use healing function instead
    game_state.current_player_mana += card.card_data.card_change_mana
    game_state.change_draw_limit(card.card_data.card_change_draw_limit)
    game_state.change_draw_limit_next_turn(card.card_data.card_change_draw_limit_next_turn)
    game_state.change_mana_limit(card.card_data.card_change_mana_limit)
    game_state.change_mana_next_turn(card.card_data.card_change_mana_next_turn)
    game_state.current_game_save.player_base_mana = max(0, game_state.current_game_save.player_base_mana + card.card_data.card_change_mana_limit_permanent)
    if card.card_data.card_target_remove_block > 0:
        if game_state.current_targeted_enemy_character:
            game_state.current_targeted_enemy_character.remove_block(card.card_data.card_target_remove_block)
    if card.card_data.card_target_damage > 0:
        game_state.current_targeted_enemy_character.take_damage(card.card_data.card_target_damage)
        if game_state.current_targeted_enemy_character.current_health <= 0:
            game_state.current_alive_enemy_characters.remove(game_state.current_targeted_enemy_character)
            if len(game_state.current_alive_enemy_characters) > 0:
                game_state.current_targeted_enemy_character = game_state.current_alive_enemy_characters[0]
    if card.card_data.delete:
        card.on_played(deleted=True)
    elif card.card_data.exhaust:
        game_state.current_exhaust_pile.append(card.card_data)
        card.on_played(exhausted=True)
    else:
        game_state.current_discard_pile.append(card.card_data)
        game_state.current_hand_game_cards.remove(card)
        card.on_played()


def player_choose_rewards(screen: pygame.Surface, game_state: GameState):
    text_color = (255, 255, 255)

    # Draw the info text
    text_surface = FONT_CARD_REWARD.render(f"Choose a new card to add to your deck:", True, text_color)
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
                game_state.load_next_room()
                game_state.save()


def draw_player_stats(screen: pygame.Surface, game_state: GameState):

    # Draw current level icon
    width = game_state.game_data.image_library.icon_level.get_width()
    height = game_state.game_data.image_library.icon_level.get_height()
    left = screen.get_rect().right - width - 10
    top = screen.get_rect().top + 60
    level_icon_rect = pygame.Rect(left, top, width, height)
    DrawCall(game_state.game_data.image_library.icon_level, level_icon_rect, LAYER_PLAYER_UI_BACKGROUND).queue(game_state)

    # Draw current level text
    level_text_surface = FONT_DUNGEON_LEVEL.render(f"{game_state.current_game_save.dungeon_room_index + 1} / {game_state.game_data.boss_room_index + 1}", True, (255, 255, 255))
    level_text_rect = level_text_surface.get_rect()
    level_text_rect.center = (level_icon_rect.centerx, level_icon_rect.centery)
    DrawCall(level_text_surface, level_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state)
    if game_state.current_game_save.dungeon_room_index == game_state.game_data.boss_room_index:
        boss_level_text_surface = FONT_DUNGEON_LEVEL_HINT.render("(boss room)", True, (255, 255, 255))
        boss_level_text_rect = boss_level_text_surface.get_rect()
        boss_level_text_rect.midtop = level_text_rect.midbottom
        DrawCall(boss_level_text_surface, boss_level_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state)

    # Draw pile icon
    width = game_state.game_data.image_library.icon_draw_pile.get_width()
    height = game_state.game_data.image_library.icon_draw_pile.get_height()
    left = screen.get_rect().left
    top = screen.get_rect().bottom - height
    draw_pile_icon_rect = pygame.Rect(left, top, width, height)
    DrawCall(game_state.game_data.image_library.icon_draw_pile, draw_pile_icon_rect, LAYER_PLAYER_UI_BACKGROUND).queue(game_state)

    # Draw pile text
    draw_pile_text_surface = FONT_CARD_PILE_COUNT.render(f"{len(game_state.current_draw_pile)}", True, (255, 255, 255))
    draw_pile_text_rect = draw_pile_text_surface.get_rect()
    draw_pile_text_rect.center = (draw_pile_icon_rect.centerx + 32, draw_pile_icon_rect.centery + 18)
    DrawCall(draw_pile_text_surface, draw_pile_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state)

    # Discard pile icon
    width = game_state.game_data.image_library.icon_discard_pile.get_width()
    height = game_state.game_data.image_library.icon_discard_pile.get_height()
    left = screen.get_rect().right - width
    top = screen.get_rect().bottom - height
    discard_pile_icon_rect = pygame.Rect(left, top, width, height)
    DrawCall(game_state.game_data.image_library.icon_discard_pile, discard_pile_icon_rect, LAYER_PLAYER_UI_BACKGROUND).queue(game_state)

    # Discard pile text
    discard_pile_text_surface = FONT_CARD_PILE_COUNT.render(f"{len(game_state.current_discard_pile)}", True, (255, 255, 255))
    discard_pile_text_rect = discard_pile_text_surface.get_rect()
    discard_pile_text_rect.center = (discard_pile_icon_rect.centerx - 32, discard_pile_icon_rect.centery + 18)
    DrawCall(discard_pile_text_surface, discard_pile_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state)

    # Mana icon
    left = screen.get_rect().left
    top = draw_pile_icon_rect.top - game_state.game_data.image_library.icon_mana.get_height()
    mana_icon_rect = pygame.Rect(left, top, game_state.game_data.image_library.icon_mana.get_width(), game_state.game_data.image_library.icon_mana.get_height())
    DrawCall(game_state.game_data.image_library.icon_mana, mana_icon_rect, LAYER_PLAYER_UI_BACKGROUND).queue(game_state)

    # Mana text
    mana_text_color = (0, 0, 0)
    if game_state.current_player_mana < 1:
        mana_text_color = (255, 60, 60)
    elif game_state.current_player_mana < 2:
        mana_text_color = (140, 0, 0)
    mana_text_surface = FONT_PLAYER_MANA.render(f"{game_state.current_player_mana} / 3", True, mana_text_color)
    mana_text_rect = mana_text_surface.get_rect()
    mana_text_rect.center = mana_icon_rect.center
    DrawCall(mana_text_surface, mana_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state)

    # Health icon
    health_icon_rect = pygame.Rect(0, 0, game_state.game_data.image_library.icon_health.get_width(), game_state.game_data.image_library.icon_health.get_height())
    health_icon_rect.midbottom = mana_icon_rect.midtop
    DrawCall(game_state.game_data.image_library.icon_health, health_icon_rect, LAYER_PLAYER_UI_BACKGROUND).queue(game_state)

    # Health text
    health_text_color = (0, 0, 0)
    if game_state.current_game_save.player_health < 20:
        health_text_color = (255, 60, 60)
    elif game_state.current_game_save.player_health < 50:
        health_text_color = (140, 0, 0)
    health_text_surface = FONT_PLAYER_HEALTH.render(f"{game_state.current_game_save.player_health}", True, health_text_color)
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
        shield_text_surface = FONT_PLAYER_BLOCK.render(f"{game_state.current_player_block}", True, shield_text_color)
        shield_text_rect = shield_text_surface.get_rect()
        shield_text_rect.center = shield_icon_rect.center
        DrawCall(shield_text_surface, shield_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state)


def is_end_turn_button_pressed(game_state: GameState):
    button_width = 120
    button_height = 40
    rect = pygame.Rect(game_state.screen.get_rect().right - button_width - 5, game_state.screen.get_rect().bottom - 200, button_width, button_height)
    if rect.collidepoint(Inputs.get_mouse_position()):
        button_color = (0, 128, 0)
    else:
        button_color = (0, 200, 0)
    text_color = (0, 50, 0)
    rect = __draw_button(game_state, "End Turn", rect, button_color, text_color)
    return __is_rect_clicked(rect)


def is_main_menu_button_pressed(game_state: GameState):
    button_width = 180
    button_height = 40
    rect = pygame.Rect(5, 5, button_width, button_height)
    if rect.collidepoint(Inputs.get_mouse_position()):
        button_color = (128, 0, 0)
    else:
        button_color = (200, 0, 0)
    text_color = (50, 0, 0)
    rect = __draw_button(game_state, "Main Menu", rect, button_color, text_color)
    return __is_rect_clicked(rect)


def is_abandon_button_pressed(game_state: GameState):
    button_width = 180
    button_height = 40
    rect = pygame.Rect(game_state.screen.get_rect().right - button_width - 5, 5, button_width, button_height)
    if rect.collidepoint(Inputs.get_mouse_position()):
        button_color = (128, 0, 0)
    else:
        button_color = (200, 0, 0)
    text_color = (50, 0, 0)
    rect = __draw_button(game_state, "Abandon run", rect, button_color, text_color)
    return __is_rect_clicked(rect)


def __draw_button(game_state: GameState, text: str, button_rect: pygame.Rect, button_color: tuple, text_color: tuple):
    # Create the button sprite
    button_surface = pygame.Surface((button_rect.width, button_rect.height))
    button_surface.fill(button_color)

    # Create the button text
    text_surface = FONT_BUTTON_GENERIC.render(text, True, text_color)

    # Calculate button and text positions
    text_rect = text_surface.get_rect()
    text_rect.center = button_rect.center

    DrawCall(button_surface, button_rect, LAYER_OVERRIDE_BG).queue(game_state)
    DrawCall(text_surface, text_rect, LAYER_OVERRIDE_FG).queue(game_state)
    return button_rect


def __is_rect_clicked(rect: pygame.Rect):
    if Inputs.is_mouse_button_pressed(1):
        if rect.collidepoint(Inputs.get_mouse_position()):
            return True
    return False
