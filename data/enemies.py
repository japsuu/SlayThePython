from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List


class EnemyIntentionData:
    def __init__(self, gain_health_amount, gain_block_amount, deal_damage_amount, turn_sprite_path):
        self.gain_health_amount = gain_health_amount
        self.gain_block_amount = gain_block_amount
        self.deal_damage_amount = deal_damage_amount
        self.turn_sprite_path = turn_sprite_path

    def to_dict(self):
        return {
            "gain_health_amount": self.gain_health_amount,
            "gain_block_amount": self.gain_block_amount,
            "deal_damage_amount": self.deal_damage_amount,
            "turn_sprite_path": self.turn_sprite_path
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["gain_health_amount"],
            data["gain_block_amount"],
            data["deal_damage_amount"],
            data["turn_sprite_path"]
        )

    def get_description(self) -> List[str]:
        description = ["Next turn:"]
        if self.gain_health_amount > 0:
            description.append(f"Will gain ? health.")
        if self.gain_block_amount > 0:
            description.append(f"Will gain ? block.")
        if self.deal_damage_amount > 0:
            description.append(f"Will deal {self.deal_damage_amount} damage.")
        if len(description) == 1:
            description.append("Will do nothing.")
        return description


class EnemySpawnData:
    def __init__(self, name, max_health_min, max_health_max, sprite_path, damaged_sprite_path, intention_pattern):
        self.name: str = name
        self.max_health_min: int = max_health_min
        self.max_health_max: int = max_health_max
        self.sprite_path: str = sprite_path
        self.damaged_sprite_path: str = damaged_sprite_path
        self.intention_pattern: List[EnemyIntentionData] = [EnemyIntentionData.from_dict(data) for data in intention_pattern]

    def to_dict(self):
        return {
            "name": self.name,
            "max_health_min": self.max_health_min,
            "max_health_max": self.max_health_max,
            "sprite_path": self.sprite_path,
            "damaged_sprite_path": self.damaged_sprite_path,
            "intention_pattern": self.intention_pattern
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["name"],
            data["max_health_min"],
            data["max_health_max"],
            data["sprite_path"],
            data["damaged_sprite_path"],
            data["intention_pattern"]
        )
