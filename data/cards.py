import json


class CardData:
    def __init__(self, card_name, card_description, card_damage, card_block, card_cost, sprite_path):
        self.card_name: str = card_name
        self.card_description: str = card_description
        self.card_damage: int = card_damage
        self.card_block: int = card_block
        self.card_cost: int = card_cost
        self.sprite_path: str = sprite_path

    def to_dict(self):
        return {
            "card_name": self.card_name,
            "card_description": self.card_description,
            "card_damage": self.card_damage,
            "card_block": self.card_block,
            "card_cost": self.card_cost,
            "sprite_path": self.sprite_path
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["card_name"],
            data["card_description"],
            data["card_damage"],
            data["card_block"],
            data["card_cost"],
            data["sprite_path"]
        )

    @staticmethod
    def load_available_cards():
        card_data_list = []
        file_path = "Content/cards.json"
        with open(file_path, "r") as file:
            data = json.load(file)

            for enemy_data in data:
                card_data = CardData.from_dict(enemy_data)
                card_data_list.append(card_data)

        return card_data_list
