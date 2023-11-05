from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List


class EnemyIntentionData:
    def __init__(self, gain_health_amount, gain_block_amount, deal_damage_amount):
        self.gain_health_amount = gain_health_amount
        self.gain_block_amount = gain_block_amount
        self.deal_damage_amount = deal_damage_amount

    def to_dict(self):
        return {
            "gain_health_amount": self.gain_health_amount,
            "gain_block_amount": self.gain_block_amount,
            "deal_damage_amount": self.deal_damage_amount,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["gain_health_amount"],
            data["gain_block_amount"],
            data["deal_damage_amount"],
        )

    def get_turn_sprite_path_prefix(self) -> str:
        if self.gain_health_amount > 0:
            return "_heal"
        if self.gain_health_amount < 0:
            return "_damaged"
        if self.gain_block_amount > 0:
            return "_block"
        if self.gain_block_amount < 0:
            return "_damaged"
        if self.deal_damage_amount > 0:
            return "_attack"
        return "_attack"

    def get_description(self) -> List[str]:
        description = ["Next turn:"]
        if self.gain_health_amount > 0:
            description.append(f"Will gain ? health.")
        if self.gain_health_amount < 0:
            description.append(f"Will lose ? health.")
        if self.gain_block_amount > 0:
            description.append(f"Will gain ? block.")
        if self.gain_block_amount < 0:
            description.append(f"Will lose ? block.")
        if self.deal_damage_amount > 0:
            description.append(f"Will deal {self.deal_damage_amount} damage.")
        if len(description) == 1:
            description.append("Will do nothing.")
        return description


class EnemySpawnData:
    def __init__(self, name, max_health_min, max_health_max, sprite_path, intention_pattern):
        self.name: str = name
        self.max_health_min: int = max_health_min
        self.max_health_max: int = max_health_max
        self.sprite_path: str = sprite_path
        self.intention_pattern: List[EnemyIntentionData] = [EnemyIntentionData.from_dict(data) for data in intention_pattern]

    def to_dict(self):
        return {
            "name": self.name,
            "max_health_min": self.max_health_min,
            "max_health_max": self.max_health_max,
            "sprite_path": self.sprite_path,
            "intention_pattern": self.intention_pattern
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["name"],
            data["max_health_min"],
            data["max_health_max"],
            data["sprite_path"],
            data["intention_pattern"]
        )
