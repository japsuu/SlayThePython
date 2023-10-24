import pygame

from data.rooms import SpecialRoomAction
from utils.constants import LAYER_TARGETED_ENEMY_ICON, LAYER_CARD_CHOOSE_TITLE, LAYER_PLAYER_UI_BACKGROUND, LAYER_PLAYER_UI_TEXT, LAYER_OVERRIDE_BG, LAYER_OVERRIDE_FG, LAYER_UI_EFFECTS, \
    FONT_CARD_CHOOSE, FONT_DUNGEON_LEVEL, FONT_DUNGEON_LEVEL_HINT, FONT_CARD_PILE_COUNT, FONT_PLAYER_MANA, FONT_PLAYER_HEALTH, FONT_PLAYER_BLOCK, \
    FONT_SPECIAL_ROOM_TITLE, FONT_SPECIAL_ROOM_DESCRIPTION, FONT_HELP
from game_objects import GameCard
from state_management import GameState
from utils.drawing import DrawCall, draw_button, is_rect_clicked
from utils.input import Inputs


def update(screen: pygame.Surface, game_state: GameState):
    if is_player_dead(game_state):
        draw_game_over_screen(screen, game_state)
        return

    game_state.update_game_objects()

    if game_state.card_grid_layout:
        game_state.card_grid_layout.update(game_state.delta_time)

    draw_damage_overlay(game_state)
    clean_up_finished_animations(game_state)

    if is_game_paused(screen, game_state):
        return

    if game_state.is_player_choosing_reward_cards:
        draw_player_reward_cards(screen, game_state)
        return

    if game_state.is_player_removing_cards:
        player_remove_cards(screen, game_state)
        return

    if game_state.current_special_room_data:
        handle_special_room(game_state)
        return

    if Inputs.is_key_pressed(pygame.K_F12):
        if game_state.current_targeted_enemy_character:
            enemy = game_state.current_targeted_enemy_character
            enemy.take_damage(9999)
            game_state.current_alive_enemy_characters.remove(enemy)
            if len(game_state.current_alive_enemy_characters) > 0:
                game_state.current_targeted_enemy_character = game_state.current_alive_enemy_characters[0]

    check_assigned_target(game_state)

    animate_target_icon(game_state)

    draw_player_stats(screen, game_state)

    if len(game_state.current_alive_enemy_characters) == 0:  # Player win state
        if game_state.current_game_save.dungeon_room_index == game_state.game_data.boss_room_index:
            # The player has defeated the boss, delete the save game and return to the main menu
            game_state.delete_current_save()
            return
        for hand_card in game_state.current_hand:
            hand_card.on_played()
            game_state.current_discard_pile.append(hand_card.card_data)
        game_state.current_hand.clear()
        game_state.generate_reward_cards()
        game_state.is_player_choosing_reward_cards = True
    elif game_state.current_game_save.player_health <= 0:  # Player lose state
        return

    if game_state.gameplay_pause_timer > 0:
        game_state.gameplay_pause_timer -= game_state.delta_time
        return  # Don't update the game if it's paused

    update_characters_turns(screen, game_state)


def update_characters_turns(screen: pygame.Surface, game_state: GameState):
    if game_state.is_players_turn:
        # Display enemies' next round's intentions
        for enemy in game_state.current_alive_enemy_characters:
            enemy.current_round_index = game_state.current_round_index

        # Color cards' mana cost red if the player can't afford them
        for hand_card in game_state.current_hand:
            if can_play_card(game_state, hand_card):
                hand_card.card_info_mana_text_color = (50, 50, 100)
            else:
                hand_card.card_info_mana_text_color = (255, 0, 0)

        hovered_card_vertical_offset = -200
        non_hovered_card_vertical_offset = 150
        card_move_to_original_pos_duration = 0.3
        card_move_up_duration = 0.15
        non_hovered_card_duration = 0.1

        # Update the player's hand (Check if the player clicked a card).
        # If the mouse is over a card, move that card up a bit while moving the other cards down a bit.
        # Use reverse iteration to get the top-most (actually visible and clicked) card.
        is_some_card_hovered = False
        for index, hand_card in enumerate(reversed(game_state.current_hand)):
            hand_card: GameCard
            if (not hand_card.has_been_played) and hand_card.can_be_clicked:
                # Create a new rect that goes to the bottom of the screen, so hit detection "feels" intuitive.
                extended_rect = pygame.Rect(hand_card.rect.left, hand_card.rect.top, hand_card.rect.width, screen.get_height())
                # If the card is hovered, move it up a bit
                if (not is_some_card_hovered) and extended_rect.collidepoint(Inputs.get_mouse_position()):
                    is_some_card_hovered = True
                    if not hand_card.is_self_hovered:
                        target_pos = (hand_card.home_position[0], hand_card.home_position[1] + hovered_card_vertical_offset)
                        hand_card.create_and_queue_animation(target_pos, card_move_up_duration, 255, 0.2, name="hover")
                        hand_card.is_self_hovered = True
                        hand_card.is_other_card_hovered = False
                else:
                    if hand_card.is_self_hovered:
                        hand_card.create_and_queue_animation(hand_card.home_position, card_move_to_original_pos_duration, 255, 0.2, name="stop hover")
                        hand_card.is_self_hovered = False

        # Update the player's hand cards (and check if the player clicked a card)
        # Use reverse iteration to get the top-most (actually visible and clicked) card
        card_played = False
        for hand_card in reversed(game_state.current_hand):
            hand_card: GameCard
            if (not hand_card.has_been_played) and hand_card.can_be_clicked:
                if can_play_card(game_state, hand_card):
                    # Check if the card was clicked
                    if (not card_played) and Inputs.is_mouse_button_up(1):
                        if hand_card.is_self_hovered and hand_card.rect.collidepoint(Inputs.get_mouse_position()):
                            play_card(game_state, hand_card)
                            card_played = True
                if not hand_card.is_self_hovered:
                    # If some card is hovered, move other non-hovered cards down a bit
                    if is_some_card_hovered:
                        if not hand_card.is_other_card_hovered:
                            hand_card.is_other_card_hovered = True
                            target_pos = (hand_card.home_position[0], hand_card.home_position[1] + non_hovered_card_vertical_offset)
                            hand_card.create_and_queue_animation(target_pos, non_hovered_card_duration, 100, 0.2, name="other hover (move down)")
                    # If no card is hovered, move all cards back to their original positions
                    else:
                        if hand_card.is_other_card_hovered:
                            hand_card.is_other_card_hovered = False
                            hand_card.create_and_queue_animation(hand_card.home_position, card_move_to_original_pos_duration, 255, 0.2, name="other stop hover (move up)")

        # Check if the player clicked the end turn button
        if is_end_turn_button_pressed(game_state):
            game_state.is_players_turn = False
            for enemy in game_state.current_alive_enemy_characters:
                enemy.remove_block(9999)
                enemy.has_completed_turn = False

            for old_card in game_state.current_hand:
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
        game_state.player_draw_new_hand_cards()


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
    for hand_card in game_state.current_hand:
        # If the card is marked for cleanup, delete it
        if hand_card.is_awaiting_destruction:
            game_state.current_hand.remove(hand_card)


def is_player_dead(game_state):
    return game_state.current_game_save.player_health <= 0


def draw_game_over_screen(screen, game_state):
    # Draw a game-over text
    text_surface = FONT_DUNGEON_LEVEL.render("Game over!", True, (255, 0, 0))
    text_rect = text_surface.get_rect()
    text_rect.center = screen.get_rect().center
    screen.blit(text_surface, text_rect)

    # Draw a button to return to the main menu
    button_rect = pygame.Rect(0, 0, 300, 50)
    button_rect.midtop = (screen.get_rect().centerx, text_rect.bottom + 20)
    draw_button(game_state.frame_buffer, "Return to main menu", button_rect, (100, 100, 100), (255, 255, 255))
    if is_rect_clicked(button_rect):
        # Delete the save game
        game_state.delete_current_save()


def draw_damage_overlay(game_state: GameState):
    if game_state.player_damaged_animation:
        game_state.player_damaged_animation.update(game_state.delta_time)
        if game_state.player_damaged_animation.is_finished:
            game_state.player_damaged_animation = None
    if game_state.player_damaged_animation:
        screen_center = game_state.screen.get_rect().center
        DrawCall(game_state.player_damaged_overlay, screen_center, LAYER_OVERRIDE_BG).queue(game_state.frame_buffer)


def check_assigned_target(game_state: GameState):
    # Assign a new target if the current target is dead or doesn't exist
    if not game_state.current_targeted_enemy_character:
        if len(game_state.current_alive_enemy_characters) > 0:
            game_state.current_targeted_enemy_character = game_state.current_alive_enemy_characters[0]
    else:
        for enemy in game_state.current_alive_enemy_characters:
            # If the player clicks the enemy, select it as the current target
            if Inputs.is_mouse_button_up(1) and (enemy != game_state.current_targeted_enemy_character):
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
        target_x = game_state.current_targeted_enemy_character.rect.centerx
        target_y = game_state.current_targeted_enemy_character.rect.top - 100
        game_state.game_data.image_library.icon_target.set_alpha(game_state.target_icon_alpha)
        DrawCall(game_state.game_data.image_library.icon_target, (target_x, target_y), LAYER_TARGETED_ENEMY_ICON,
                 ["Currently targeted enemy.", "Click an enemy to set it as target."], False).queue(game_state.frame_buffer)


def can_play_card(game_state: GameState, card: GameCard):
    return (not card.is_awaiting_destruction) and (card.card_data.card_cost <= game_state.current_player_mana)


def play_card(game_state: GameState, card: GameCard):
    game_state.current_player_mana = max(0, game_state.current_player_mana - card.card_data.card_cost)
    damage_player(game_state, card.card_data.card_self_damage)
    game_state.current_player_block = max(0, game_state.current_player_block + card.card_data.card_self_block)
    game_state.current_game_save.player_health = min(game_state.current_game_save.player_health + card.card_data.card_self_heal, 100)
    game_state.current_player_mana = max(0, game_state.current_player_mana + card.card_data.card_change_mana)
    game_state.change_draw_limit(card.card_data.card_change_draw_limit)
    game_state.change_draw_limit_next_turn(card.card_data.card_change_draw_limit_next_turn)
    game_state.change_mana_limit_this_combat(card.card_data.card_change_mana_limit)
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
    game_state.current_hand.remove(card)
    if card.card_data.card_draw_additional_cards > 0:
        game_state.draw_hand_cards(card.card_data.card_draw_additional_cards)
    if card.card_data.delete:
        card.on_played(deleted=True)
    elif card.card_data.exhaust:
        game_state.current_exhaust_pile.append(card.card_data)
        card.on_played(exhausted=True)
    else:
        game_state.current_discard_pile.append(card.card_data)
        card.on_played()
    if card.card_data.card_draw_additional_cards <= 0:
        game_state.reposition_cards(game_state.current_hand)


def draw_player_reward_cards(screen: pygame.Surface, game_state: GameState):
    text_color = (255, 255, 255)

    # Draw the info text
    text_surface = FONT_CARD_CHOOSE.render(f"Choose a new card to add to your deck:", True, text_color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = screen.get_rect().midtop
    DrawCall(text_surface, text_rect, LAYER_CARD_CHOOSE_TITLE).queue(game_state.frame_buffer)

    # Draw the cards to the center of the screen
    is_some_card_hovered = False
    for card in game_state.current_reward_game_cards:
        if card.rect.collidepoint(Inputs.get_mouse_position()):
            if not card.is_self_hovered:
                card.create_and_queue_animation((card.home_position[0], card.home_position[1] - 50), 0.1, 255, 0.2, name="hover")
                card.is_self_hovered = True
                card.is_other_card_hovered = False
            is_some_card_hovered = True
            if Inputs.is_mouse_button_up(1):
                # Card clicked, add it to the player's deck
                game_state.current_draw_pile.append(card.card_data)
                game_state.is_player_choosing_reward_cards = False
                game_state.load_next_room()
                game_state.save()
    for card in game_state.current_reward_game_cards:
        if is_some_card_hovered and (not card.rect.collidepoint(Inputs.get_mouse_position())):
            if not card.is_other_card_hovered:
                card.create_and_queue_animation(card.home_position, 0.1, 100, 0.2, name="stop hover")
                card.is_other_card_hovered = True
        elif not is_some_card_hovered:
            if card.is_self_hovered or card.is_other_card_hovered:
                card.create_and_queue_animation(card.home_position, 0.1, 255, 0.2, name="stop hover")
                card.is_self_hovered = False
                card.is_other_card_hovered = False

    # Draw a button to skip choosing a card
    rect = draw_button(game_state.frame_buffer, "Skip", pygame.Rect(screen.get_rect().centerx - 60, screen.get_rect().bottom - 100, 120, 40),
                       (0, 200, 0), (0, 50, 0), ["Skip choosing a card."])
    if is_rect_clicked(rect):
        game_state.is_player_choosing_reward_cards = False
        game_state.load_next_room()
        game_state.save()


def player_remove_cards(screen: pygame.Surface, game_state: GameState):
    if game_state.player_can_remove_cards_count <= 0:
        for card in game_state.current_removal_game_cards:
            card.on_played()
        game_state.current_removal_game_cards.clear()
        game_state.card_grid_layout.clear()
        game_state.is_player_removing_cards = False
        return
    text_color = (255, 255, 255)

    # Draw the info text
    text_surface = FONT_CARD_CHOOSE.render(f"Choose {game_state.player_can_remove_cards_count} cards to remove from your deck:", True, text_color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (screen.get_rect().centerx, screen.get_rect().top + 20)
    DrawCall(text_surface, text_rect, LAYER_CARD_CHOOSE_TITLE).queue(game_state.frame_buffer)

    # Draw the cards to the center of the screen
    for card in game_state.current_removal_game_cards:
        if Inputs.is_mouse_button_up(1):
            if card.rect.collidepoint(Inputs.get_mouse_position()):
                # Card clicked, remove it from the player's deck
                game_state.current_removal_game_cards.remove(card)
                game_state.current_draw_pile.remove(card.card_data)
                # game_state.current_game_save.player_cards.remove(card.card_data)
                # print(f"Draw pile has {len(game_state.current_draw_pile)} cards.")
                # print(f"Exhaust pile has {len(game_state.current_exhaust_pile)} cards.")
                # print(f"Discard pile has {len(game_state.current_discard_pile)} cards.")
                # print(f"Save has {len(game_state.current_game_save.player_cards)} cards.")
                # print(f"Hand has {len(game_state.current_hand)} cards.")
                game_state.card_grid_layout.remove_item(card)
                card.on_played(exhausted=True)
                card.draw_order = LAYER_OVERRIDE_FG
                game_state.player_can_remove_cards_count -= 1

    # Draw a button to skip choosing a card
    if is_rect_clicked(draw_button(game_state.frame_buffer, "Skip", pygame.Rect(screen.get_rect().centerx - 60, screen.get_rect().bottom - 100, 120, 40),
                                   (0, 200, 0), (0, 50, 0), ["Skip choosing a card."])):
        for card in game_state.current_removal_game_cards:
            card.on_played()
        game_state.current_removal_game_cards.clear()
        game_state.card_grid_layout.clear()
        game_state.is_player_removing_cards = False


def handle_special_room(game_state: GameState):
    # Draw the room name
    text_surface = FONT_SPECIAL_ROOM_TITLE.render(game_state.current_special_room_data.room_name, True, (255, 255, 255))
    text_rect = text_surface.get_rect()
    text_rect.midtop = (game_state.screen.get_rect().centerx, game_state.screen.get_rect().top + 20)
    DrawCall(text_surface, text_rect, LAYER_CARD_CHOOSE_TITLE).queue(game_state.frame_buffer)

    # Draw the room description
    text_surface = FONT_SPECIAL_ROOM_DESCRIPTION.render(game_state.current_special_room_data.room_description, True, (255, 255, 255))
    desc_text_rect = text_surface.get_rect()
    desc_text_rect.midtop = (text_rect.midbottom[0], text_rect.midbottom[1] + 10)
    DrawCall(text_surface, desc_text_rect, LAYER_CARD_CHOOSE_TITLE).queue(game_state.frame_buffer)

    # Draw the player health
    draw_player_health(game_state, bottom_left_pos=(game_state.screen.get_rect().left + 10, game_state.screen.get_rect().bottom - 10))

    # Draw the available actions
    available_actions = game_state.current_special_room_data.room_available_actions
    for index, action in enumerate(available_actions):
        action: SpecialRoomAction
        # Draw a button for the action and check if it's pressed.
        pos_x = game_state.screen.get_rect().centerx - 200
        pos_y = game_state.screen.get_rect().centery - 200 + (index * 50)
        width = 200
        height = 40
        # if len(action.action_name) > 10:
        #     width = 300
        button_rect = draw_button(game_state.frame_buffer, action.action_name, pygame.Rect(pos_x - 100, pos_y, width, height),
                                  (0, 200, 0), (0, 50, 0), action.get_effects_text())
        if is_rect_clicked(button_rect):
            action.execute(game_state)
            game_state.current_special_room_data = None
            return
        # Draw the action description
        text_surface = FONT_SPECIAL_ROOM_DESCRIPTION.render(action.action_description, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        text_rect.midleft = (button_rect.right + 10, button_rect.centery)
        DrawCall(text_surface, text_rect, LAYER_CARD_CHOOSE_TITLE).queue(game_state.frame_buffer)


def draw_player_stats(screen: pygame.Surface, game_state: GameState):
    # TODO: Refactor this function. Split to DrawHealth, DrawMana, DrawBlock, DrawPiles, DrawLevel
    # Draw current level icon
    width = game_state.game_data.image_library.icon_level.get_width()
    height = game_state.game_data.image_library.icon_level.get_height()
    left = screen.get_rect().right - width - 10
    top = screen.get_rect().top + 60
    level_icon_rect = pygame.Rect(left, top, width, height)
    DrawCall(game_state.game_data.image_library.icon_level, level_icon_rect, LAYER_PLAYER_UI_BACKGROUND, ["Current room.", "The last room is a boss room."]).queue(game_state.frame_buffer)

    # Draw current level text
    level_text_surface = FONT_DUNGEON_LEVEL.render(f"{game_state.current_game_save.dungeon_room_index + 1} / {game_state.game_data.boss_room_index + 1}", True, (255, 255, 255))
    level_text_rect = level_text_surface.get_rect()
    level_text_rect.center = (level_icon_rect.centerx, level_icon_rect.centery)
    DrawCall(level_text_surface, level_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state.frame_buffer)
    if game_state.current_game_save.dungeon_room_index == game_state.game_data.boss_room_index:
        boss_level_text_surface = FONT_DUNGEON_LEVEL_HINT.render("(boss room)", True, (255, 255, 255))
        boss_level_text_rect = boss_level_text_surface.get_rect()
        boss_level_text_rect.midtop = level_text_rect.midbottom
        DrawCall(boss_level_text_surface, boss_level_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state.frame_buffer)

    # Draw pile icon
    width = game_state.game_data.image_library.icon_draw_pile.get_width()
    height = game_state.game_data.image_library.icon_draw_pile.get_height()
    left = screen.get_rect().left
    top = screen.get_rect().bottom - height
    draw_pile_icon_rect = pygame.Rect(left, top, width, height)
    DrawCall(game_state.game_data.image_library.icon_draw_pile, draw_pile_icon_rect, LAYER_PLAYER_UI_BACKGROUND,
             ["Your draw pile.", "When your draw pile is empty,", "the discard pile is shuffled", "into the draw pile."]).queue(game_state.frame_buffer)

    # Draw pile text
    draw_pile_text_surface = FONT_CARD_PILE_COUNT.render(f"{len(game_state.current_draw_pile)}", True, (255, 255, 255))
    draw_pile_text_rect = draw_pile_text_surface.get_rect()
    draw_pile_text_rect.center = (draw_pile_icon_rect.centerx + 32, draw_pile_icon_rect.centery + 18)
    DrawCall(draw_pile_text_surface, draw_pile_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state.frame_buffer)

    # Discard pile icon
    width = game_state.game_data.image_library.icon_discard_pile.get_width()
    height = game_state.game_data.image_library.icon_discard_pile.get_height()
    left = screen.get_rect().right - width
    top = screen.get_rect().bottom - height
    discard_pile_icon_rect = pygame.Rect(left, top, width, height)
    DrawCall(game_state.game_data.image_library.icon_discard_pile, discard_pile_icon_rect, LAYER_PLAYER_UI_BACKGROUND,
             ["Your discard pile.", "Your played cards end up here."]).queue(game_state.frame_buffer)

    # Discard pile text
    discard_pile_text_surface = FONT_CARD_PILE_COUNT.render(f"{len(game_state.current_discard_pile)}", True, (255, 255, 255))
    discard_pile_text_rect = discard_pile_text_surface.get_rect()
    discard_pile_text_rect.center = (discard_pile_icon_rect.centerx - 32, discard_pile_icon_rect.centery + 18)
    DrawCall(discard_pile_text_surface, discard_pile_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state.frame_buffer)

    # Mana icon
    left = screen.get_rect().left
    top = draw_pile_icon_rect.top - game_state.game_data.image_library.icon_mana.get_height()
    mana_icon_rect = pygame.Rect(left, top, game_state.game_data.image_library.icon_mana.get_width(), game_state.game_data.image_library.icon_mana.get_height())
    DrawCall(game_state.game_data.image_library.icon_mana, mana_icon_rect, LAYER_PLAYER_UI_BACKGROUND,
             ["Your current mana.", "Playing cards requires mana.", "Your mana is regenerated at", "the start of each turn."]).queue(game_state.frame_buffer)

    # Mana text
    mana_text_color = (0, 0, 0)
    if game_state.current_player_mana < 1:
        mana_text_color = (255, 60, 60)
    elif game_state.current_player_mana < 2:
        mana_text_color = (140, 0, 0)
    mana_text_surface = FONT_PLAYER_MANA.render(
        f"{game_state.current_player_mana} / {game_state.current_game_save.player_base_mana + game_state.player_base_mana_limit_addition_this_combat}", True, mana_text_color)
    mana_text_rect = mana_text_surface.get_rect()
    mana_text_rect.center = mana_icon_rect.center
    DrawCall(mana_text_surface, mana_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state.frame_buffer)

    health_icon_rect = draw_player_health(game_state, bottom_left_pos=(mana_icon_rect.left, mana_icon_rect.top))

    if game_state.current_player_block > 0:
        shield_icon_rect = pygame.Rect(0, 0, game_state.game_data.image_library.icon_block.get_width(), game_state.game_data.image_library.icon_block.get_height())
        shield_icon_rect.midbottom = health_icon_rect.midtop
        DrawCall(game_state.game_data.image_library.icon_block, shield_icon_rect, LAYER_PLAYER_UI_BACKGROUND,
                 ["Your current block.", "Block cancels incoming damage."]).queue(game_state.frame_buffer)

        shield_text_color = (0, 0, 0)
        if game_state.current_player_block < 3:
            shield_text_color = (255, 60, 60)
        shield_text_surface = FONT_PLAYER_BLOCK.render(f"{game_state.current_player_block}", True, shield_text_color)
        shield_text_rect = shield_text_surface.get_rect()
        shield_text_rect.center = shield_icon_rect.center
        DrawCall(shield_text_surface, shield_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state.frame_buffer)


def draw_player_health(game_state: GameState, top_left_pos=None, bottom_left_pos=None) -> pygame.Rect:
    # Health icon
    health_icon_rect = pygame.Rect(0, 0, game_state.game_data.image_library.icon_health.get_width(), game_state.game_data.image_library.icon_health.get_height())
    if bottom_left_pos:
        health_icon_rect.bottomleft = bottom_left_pos
    elif top_left_pos:
        health_icon_rect.topleft = top_left_pos
    DrawCall(game_state.game_data.image_library.icon_health, health_icon_rect, LAYER_PLAYER_UI_BACKGROUND,
             ["Your current health.", "Health does not regenerate,", "but some cards may have", "healing properties."]).queue(game_state.frame_buffer)

    # Health text
    health_text_color = (0, 0, 0)
    if game_state.current_game_save.player_health < 20:
        health_text_color = (255, 60, 60)
    elif game_state.current_game_save.player_health < 50:
        health_text_color = (140, 0, 0)
    health_text_surface = FONT_PLAYER_HEALTH.render(f"{game_state.current_game_save.player_health}", True, health_text_color)
    health_text_rect = health_text_surface.get_rect()
    health_text_rect.center = health_icon_rect.center
    DrawCall(health_text_surface, health_text_rect, LAYER_PLAYER_UI_TEXT).queue(game_state.frame_buffer)
    return health_icon_rect


def is_end_turn_button_pressed(game_state: GameState):
    button_width = 120
    button_height = 40
    rect = pygame.Rect(game_state.screen.get_rect().right - button_width - 5, game_state.screen.get_rect().bottom - 200, button_width, button_height)
    if rect.collidepoint(Inputs.get_mouse_position()):
        button_color = (0, 128, 0)
    else:
        button_color = (0, 200, 0)
    text_color = (0, 50, 0)
    rect = draw_button(game_state.frame_buffer, "End Turn", rect, button_color, text_color, ["End your turn and play the enemies' turns."])
    return is_rect_clicked(rect)


def is_main_menu_button_pressed(game_state: GameState, pause_background_rect: pygame.Rect):
    if not game_state.is_pause_menu_shown:
        return False
    button_width = 180
    button_height = 40
    rect = pygame.Rect(pause_background_rect.centerx - button_width / 2, pause_background_rect.centery, button_width, button_height)
    if rect.collidepoint(Inputs.get_mouse_position()):
        button_color = (128, 128, 0)
    else:
        button_color = (200, 200, 0)
    text_color = (50, 0, 0)
    rect = draw_button(game_state.frame_buffer, "Main Menu", rect, button_color, text_color, ["Return to the main menu.", "Game was last saved at the start of this room."])
    return is_rect_clicked(rect)


def is_abandon_button_pressed(game_state: GameState, pause_background_rect: pygame.Rect):
    if not game_state.is_pause_menu_shown:
        return False
    button_width = 180
    button_height = 40
    rect = pygame.Rect(pause_background_rect.centerx - button_width / 2, pause_background_rect.centery + 150, button_width, button_height)
    if rect.collidepoint(Inputs.get_mouse_position()):
        button_color = (128, 0, 0)
    else:
        button_color = (200, 0, 0)
    text_color = (50, 0, 0)
    rect = draw_button(game_state.frame_buffer, "Abandon run", rect, button_color, text_color, ["Abandon the current run and return to the main menu."])
    return is_rect_clicked(rect)


def is_help_button_pressed(game_state: GameState, pause_background_rect: pygame.Rect):
    if not game_state.is_pause_menu_shown:
        return False
    button_width = 180
    button_height = 40
    rect = pygame.Rect(pause_background_rect.centerx - button_width / 2, pause_background_rect.centery + 50, button_width, button_height)
    if rect.collidepoint(Inputs.get_mouse_position()):
        button_color = (128, 0, 128)
    else:
        button_color = (200, 0, 200)
    text_color = (50, 0, 0)
    rect = draw_button(game_state.frame_buffer, "Help", rect, button_color, text_color, ["This game is best played without help,", "but if you really need it, click here."])
    return is_rect_clicked(rect)


def is_game_paused(screen, game_state) -> bool:
    if not game_state.is_pause_menu_shown:
        help_text = FONT_HELP.render("Press 'Esc' to pause", True, (180, 180, 180))
        help_text_rect = help_text.get_rect()
        help_text_rect.topleft = (5, 5)
        screen.blit(help_text, help_text_rect)
        return False
    else:
        pause_background = pygame.Surface((1280, 720))
        pause_background.fill((0, 0, 0))
        pause_background.set_alpha(230)
        pause_background_rect = pause_background.get_rect()
        pause_background_rect.center = screen.get_rect().center
        DrawCall(pause_background, pause_background_rect, LAYER_OVERRIDE_BG, blocks_tooltips=True, mask_tooltip_surface=False).queue(game_state.frame_buffer)
        help_text = FONT_SPECIAL_ROOM_TITLE.render("Paused ('Esc' to close):", True, (180, 180, 180))
        help_text_rect = help_text.get_rect()
        help_text_rect.midtop = (pause_background_rect.midtop[0], 10)
        DrawCall(help_text, help_text_rect, LAYER_OVERRIDE_BG).queue(game_state.frame_buffer)

    if is_main_menu_button_pressed(game_state, pause_background_rect):
        game_state.exit_current_save()
        return True

    if is_abandon_button_pressed(game_state, pause_background_rect):
        game_state.delete_current_save()
        return True

    if is_help_button_pressed(game_state, pause_background_rect):
        game_state.is_help_shown = not game_state.is_help_shown

    if game_state.is_help_shown:
        # WARN: We are regenerating the pygame surface every frame here. This is not optimal.
        help_text_lines = [
            "",
            "#GENERAL",
            "-> The goal of the game is to defeat all enemies in each room.",
            "-> There's a boss at the end of each dungeon.",
            "-> Your stats are shown in the bottom left corner.",
            "-> Your stats are 'health', 'mana', and 'block'.",
            "",
            "#HEALTH",
            "-> Your health does not regenerate between rooms.",
            "-> Certain cards have healing properties.",
            "",
            "#MANA",
            "-> Your mana resets at the start of each turn.",
            "-> You can only play a card if you have the required mana.",
            "",
            "#BLOCK",
            "-> Your block resets at the start of each turn.",
            "-> Block negates the damage you take.",
            "",
            "#COMBAT",
            "-> Enemies' next round intentions are shown on top of them.",
            "-> Enemies can heal by casting a buff (blue fire icon).",
            "-> Click an enemy to set it as the target.",
            "",
            "#CARDS",
            "-> You can play cards by clicking on them.",
            "-> The mana cost of a card is shown in card's top left corner.",
            "",
            "#SAVING",
            "-> Game is automatically saved when you enter a new room.",
            "-> When a run is over, the save is deleted.",
        ]
        help_background = pygame.Surface((500, 700))
        help_background.fill((0, 0, 0))
        help_background.set_alpha(230)
        help_background_rect = help_background.get_rect()
        help_background_rect.midtop = (screen.get_width() / 2, 10)
        DrawCall(help_background, help_background_rect, LAYER_OVERRIDE_BG).queue(game_state.frame_buffer)
        help_text = FONT_HELP.render("Help ('Esc' to close):", True, (180, 180, 180))
        help_text_rect = help_text.get_rect()
        help_text_rect.midtop = (help_background_rect.midtop[0], 20)
        previous_rect = help_text_rect
        DrawCall(help_text, help_text_rect, LAYER_OVERRIDE_BG).queue(game_state.frame_buffer)
        for help_text_line in help_text_lines:
            if help_text_line.startswith("#"):
                help_text = FONT_HELP.render(help_text_line[1:], True, (255, 255, 255))
                help_text_rect = help_text.get_rect()
                help_text_rect.topleft = (help_background_rect.topleft[0] + 20, previous_rect.bottom + 10)
                previous_rect = help_text_rect
                DrawCall(help_text, help_text_rect, LAYER_OVERRIDE_BG).queue(game_state.frame_buffer)
            else:
                help_text = FONT_HELP.render(help_text_line, True, (180, 180, 180))
                help_text_rect = help_text.get_rect()
                help_text_rect.topleft = (help_background_rect.topleft[0] + 20, previous_rect.bottom)
                previous_rect = help_text_rect
                DrawCall(help_text, help_text_rect, LAYER_OVERRIDE_BG).queue(game_state.frame_buffer)
    return True
