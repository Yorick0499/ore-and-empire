"""Provisional solo encounter balance; rewards never come from client input."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Boss:
    key: str
    name: str
    level: int
    life: int
    strength: int
    protection: int
    experience: int
    ore: int
    cooldown_minutes: int = 30
    energy_cost: int = 25

    @property
    def monster(self):
        return {
            "nazwa": self.name,
            "life": self.life,
            "strength": self.strength,
            "weapon_prot": self.protection,
        }


BOSSES = {
    "crawler_nest": Boss("crawler_nest", "Królowa pełzaczy", 5, 150, 20, 8, 300, 60),
    "swamp_den": Boss("swamp_den", "Prastary błotny wąż", 8, 220, 25, 10, 500, 100),
}
