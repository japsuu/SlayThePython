import json


class CardData:
    def __init__(self, card_info_name,
                 card_info_description,
                 card_damage_all,
                 card_target_damage,
                 card_target_remove_block,
                 card_self_damage,
                 card_self_block,
                 card_self_heal,
                 card_draw_additional_cards,
                 card_change_draw_limit,
                 card_change_draw_limit_next_turn,
                 card_change_mana_limit,
                 card_change_mana_limit_permanent,
                 card_change_mana,
                 card_change_mana_next_turn,
                 card_cost,
                 exhaust,
                 delete,
                 sprite_path):
        self.card_info_name: str = card_info_name
        self.card_info_description: str = card_info_description
        self.card_damage_all: int = card_damage_all
        self.card_target_damage: int = card_target_damage
        self.card_target_remove_block: int = card_target_remove_block
        self.card_self_damage: int = card_self_damage
        self.card_self_block: int = card_self_block
        self.card_self_heal: int = card_self_heal
        self.card_draw_additional_cards: int = card_draw_additional_cards
        self.card_change_draw_limit: int = card_change_draw_limit
        self.card_change_draw_limit_next_turn: int = card_change_draw_limit_next_turn
        self.card_change_mana_limit: int = card_change_mana_limit
        self.card_change_mana_limit_permanent: int = card_change_mana_limit_permanent
        self.card_change_mana: int = card_change_mana
        self.card_change_mana_next_turn: int = card_change_mana_next_turn
        self.card_cost: int = card_cost
        self.exhaust: bool = exhaust
        self.delete: bool = delete
        self.sprite_path: str = sprite_path

    def to_dict(self):
        return {
            "card_info_name": self.card_info_name,
            "card_damage_all": self.card_damage_all,
            "card_target_damage": self.card_target_damage,
            "card_target_remove_block": self.card_target_remove_block,
            "card_self_damage": self.card_self_damage,
            "card_self_block": self.card_self_block,
            "card_self_heal": self.card_self_heal,
            "card_draw_additional_cards": self.card_draw_additional_cards,
            "card_change_draw_limit": self.card_change_draw_limit,
            "card_change_draw_limit_next_turn": self.card_change_draw_limit_next_turn,
            "card_change_mana_limit": self.card_change_mana_limit,
            "card_change_mana_limit_permanent": self.card_change_mana_limit_permanent,
            "card_change_mana": self.card_change_mana,
            "card_change_mana_next_turn": self.card_change_mana_next_turn,
            "card_cost": self.card_cost,
            "exhaust": self.exhaust,
            "delete": self.delete,
            "sprite_path": self.sprite_path
        }

    def copy(self):
        return CardData(
            self.card_info_name,
            self.card_info_description,
            self.card_damage_all,
            self.card_target_damage,
            self.card_target_remove_block,
            self.card_self_damage,
            self.card_self_block,
            self.card_self_heal,
            self.card_draw_additional_cards,
            self.card_change_draw_limit,
            self.card_change_draw_limit_next_turn,
            self.card_change_mana_limit,
            self.card_change_mana_limit_permanent,
            self.card_change_mana,
            self.card_change_mana_next_turn,
            self.card_cost,
            self.exhaust,
            self.delete,
            self.sprite_path
        )

    @classmethod
    def from_dict(cls, data):
        # Assign all the properties to temporary variables
        # so that we can use them to generate the description:
        name = data["card_info_name"]
        description = ""
        damage_all = data["card_damage_all"]
        target_damage = data["card_target_damage"]
        target_remove_block = data["card_target_remove_block"]
        self_damage = data["card_self_damage"]
        self_block = data["card_self_block"]
        self_heal = data["card_self_heal"]
        draw_additional_cards = data["card_draw_additional_cards"]
        change_draw_limit = data["card_change_draw_limit"]
        change_draw_limit_next_turn = data["card_change_draw_limit_next_turn"]
        change_mana_limit = data["card_change_mana_limit"]
        change_mana_limit_permanent = data["card_change_mana_limit_permanent"]
        change_mana = data["card_change_mana"]
        change_mana_next_turn = data["card_change_mana_next_turn"]
        exhaust = data["exhaust"]
        delete = data["delete"]

        # AutoGenerate the card description
        if damage_all != 0:
            description += f"Deal {damage_all} damage to ALL enemies.\n\n"
        if target_damage != 0:
            description += f"Deal {target_damage} damage.\n\n"
        if target_remove_block != 0:
            description += f"Remove {target_remove_block} block from target.\n\n"
        if self_damage != 0:
            description += f"Lose {self_damage} HP.\n\n"
        if self_block != 0:
            description += f"Gain {self_block} block.\n\n"
        if self_heal != 0:
            description += f"Heal {self_heal} HP.\n\n"
        if draw_additional_cards != 0:
            description += f"Draw {draw_additional_cards} cards.\n\n"
        if change_draw_limit != 0:
            if change_draw_limit > 0:
                description += f"Increase your draw limit by {change_draw_limit}\nfor the rest of this combat.\n\n"
            else:
                description += f"Decrease your draw limit by {change_draw_limit}\nfor the rest of this combat.\n\n"
        if change_draw_limit_next_turn != 0:
            if change_draw_limit_next_turn > 0:
                description += f"Increase your draw limit by {change_draw_limit_next_turn}\nfor the next turn.\n\n"
            else:
                description += f"Decrease your draw limit by {change_draw_limit_next_turn}\nfor the next turn.\n\n"
        if change_mana_limit != 0:
            if change_mana_limit > 0:
                description += f"Increase your mana limit by {change_mana_limit}\nfor the rest of this combat.\n\n"
            else:
                description += f"Decrease your mana limit by {change_mana_limit}\nfor the rest of this combat.\n\n"
        if change_mana_limit_permanent != 0:
            if change_mana_limit_permanent > 0:
                description += f"Increase your mana limit by {change_mana_limit_permanent} permanently.\n\n"
            else:
                description += f"Decrease your mana limit by {change_mana_limit_permanent} permanently.\n\n"
        if change_mana != 0:
            if change_mana > 0:
                description += f"Gain {change_mana} mana.\n\n"
            else:
                description += f"Lose {change_mana} mana.\n\n"
        if change_mana_next_turn != 0:
            if change_mana_next_turn > 0:
                description += f"Gain {change_mana_next_turn} mana next turn.\n\n"
            else:
                description += f"Lose {change_mana_next_turn} mana next turn.\n\n"
        if description == "":
            description = "This card does nothing.\n\n"
        if exhaust:
            description += "Exhaust.\n\n"
        if delete:
            description += "Delete.\n\n"

        description = description.strip()

        return cls(
            name,
            description,
            damage_all,
            target_damage,
            target_remove_block,
            self_damage,
            self_block,
            self_heal,
            draw_additional_cards,
            change_draw_limit,
            change_draw_limit_next_turn,
            change_mana_limit,
            change_mana_limit_permanent,
            change_mana,
            change_mana_next_turn,
            data["card_cost"],
            exhaust,
            delete,
            data["sprite_path"]
        )

    @staticmethod
    def load_available_cards():
        card_data_list = []
        file_path = "Content/cards.json"
        with open(file_path, "r") as file:
            json_data = json.load(file)

            for data in json_data:
                card_data = CardData.from_dict(data)
                card_data_list.append(card_data)

        return card_data_list

    @staticmethod
    def load_starting_cards():
        card_data_list = []
        file_path = "Content/cards_start.json"
        with open(file_path, "r") as file:
            json_data = json.load(file)

            for data in json_data:
                card_data = CardData.from_dict(data)
                card_data_list.append(card_data)

        return card_data_list
