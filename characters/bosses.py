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
            "boss_key": self.key,
            "forecast_strength": self.strength + 13,
            "forecast_protection": self.protection + 6,
        }


BOSSES = {
    "sleeper_sanctum": Boss("sleeper_sanctum", "Echo Śniącego", 30, 1400, 80, 45, 3000, 500),
    "crawler_nest": Boss("crawler_nest", "Królowa pełzaczy", 5, 150, 20, 8, 300, 60),
    "swamp_den": Boss("swamp_den", "Prastary błotny wąż", 8, 220, 25, 10, 500, 100),
}


MECHANICS = {
    "crawler_nest": "Królowa przyzywa młode poniżej 65% zdrowia. Co trzecią rundę wykonuje zapowiedziany szarżujący atak. Ogień zadaje jej o 20% więcej obrażeń.",
    "swamp_den": "Poniżej połowy zdrowia wąż zanurza się co drugą rundę: zyskuje 6 pancerza. Przy wynurzeniu traci 6 pancerza. Co trzecią rundę następuje zapowiedziany atak ogonem.",
    "sleeper_sanctum": "Warta walczy z echem Śniącego i stabilizuje pieczęć. Przy 65% i 30% zdrowia osłona słabnie. Co trzecią rundę uderza zapowiedziana fala; magiczna ochrona zmniejsza jej obrażenia. Wymagane przygotowania sześciu rozdziałów.",
}


def encounter_round(monster, health, turn):
    """Deterministic rules shared by every participant; no client combat parameters."""
    key = monster.get("boss_key")
    stage = 1 + int(health * 100 <= monster["life"] * 65) + int(health * 100 <= monster["life"] * 30)
    protection = monster["weapon_prot"]
    strength = monster["strength"]
    kind = "weapon"
    messages = []
    if turn % 3 == 2:
        messages.append("Uwaga: przeciwnik przygotowuje silny atak na następną rundę.")
    if turn % 3 == 0:
        strength += 10
        messages.append("Zapowiedziany silny atak!")
    if key == "crawler_nest" and stage >= 2:
        strength += 3
        protection += 3
        messages.append("Młode pełzacze osłaniają królową; przebij się przez rój.")
    elif key == "swamp_den" and health * 2 <= monster["life"]:
        protection += 6 if turn % 2 else -6
        messages.append("Wąż zanurza się: pancerz +6." if turn % 2 else "Wąż wynurza się: pancerz -6.")
    elif key == "sleeper_sanctum":
        protection = max(0, protection - (stage-1)*15)
        if turn % 3 == 0:
            kind = "magic"
            messages.append("Fala echa uderza w magiczną ochronę warty.")
    return stage, max(0, protection), strength, kind, messages
