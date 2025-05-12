from random import randint
from math import trunc, hypot
from transformers import pipeline
import json

# Load this once
text_gen = pipeline("text-generation", model="gpt2")


def roll(dice: str):
    """Roll dice in the form '1d20', '2d6', etc."""
    num, die = map(int, dice.lower().split('d'))
    return sum(randint(1, die) for _ in range(num))


class Character:
    def __init__(self, name, hp: int = 0, strength: int = 0,
                 dex: int = 0, cha: int = 0,
                 snk: int = 0, mnd: int = 0,
                 intl: int = 0, acc: int = 0,
                 spd: int = 0, rei: int = 0,
                 dmg_dice: str = "1d6", attack_range=1, max_attacks: int = 1, x=0, y=0):

        self.name = name
        self.hp = 100 + hp
        self.str = trunc(strength / 20)
        self.dex = trunc(dex / 40)
        self.cha = trunc(cha / 110)
        self.snk = trunc(snk / 80)
        self.mnd = trunc(mnd / 50)
        self.intl = trunc(intl / 50)
        self.acc = trunc(acc / 35)
        self.spd = trunc(spd / 80)
        self.bonus_rei_dice = trunc(rei / 500)
        self.hit_acc = trunc(acc / 75)
        self.ac = 10 + trunc(dex / 65)
        self.dmg_dice = dmg_dice  # base weapon damage
        self.range = attack_range  # in tiles
        self.speed = 5 + trunc(spd / 50)  # how many tiles they can move per turn
        self.speed_left = self.speed
        self.max_attacks = max_attacks
        self.attacks_left = self.max_attacks
        self.x = x
        self.y = y
        self.has_acted = False

    @staticmethod
    def from_json(file_path, x, y):
        with open(file_path) as f:
            data = json.load(f)
        return Character(x=x, y=y, **data)

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def distance_to(self, other):
        return hypot(self.x - other.x, self.y - other.y)

    def move(self, dx, dy):
        if self.speed_left != 0:
            self.x += dx
            self.y += dy
            self.speed_left -= 1
            return True
        else:
            return False


class Game:
    GRID_SIZE = 10

    def __init__(self):
        self.ai_mode = bool()
        self.players = [None, None]
        self.turn_index = 0
        self.log = []
        self.GRID_SIZE = 10

    @property
    def current_player(self):
        return self.players[self.turn_index]

    @property
    def other_player(self):
        return self.players[(self.turn_index + 1) % 2]

    def attack(self):
        attacker = self.current_player
        target = self.other_player
        dist = attacker.distance_to(target)

        if dist > attacker.range:
            self.log.append(f"{attacker.name} is out of range (distance {dist:.1f}, range {attacker.range})!")
            return

        if attacker.attacks_left <= 0:
            self.log.append(f"{attacker.name} has no attacks left this turn!")
            return

        attack_roll = roll("1d20") + attacker.hit_acc
        if attack_roll >= target.ac:
            dmg = roll(attacker.dmg_dice) + attacker.str
            target.take_damage(dmg)
            self.log.append(
                f"{attacker.name} rolls {attack_roll} and hits from {dist:.1f} tiles away! "
                f"Deals {dmg} damage."
            )
        else:
            self.log.append(
                f"{attacker.name} rolls {attack_roll} but misses {target.name} (AC {target.ac})."
            )
        attacker.attacks_left -= 1

    def end_turn(self):
        self.turn_index = (self.turn_index + 1) % 2
        if self.current_player.hp <= 0:
            self.log.append(f"The HP of {self.current_player.name} has been reduced to 0! "
                            f"They are forced to skip their turn!")
            exit()
        self.log.append(f"Turn passed to {self.current_player.name}")
        self.current_player.attacks_left = self.current_player.max_attacks
        self.current_player.speed_left = self.current_player.speed

    def move_current_player(self, dx, dy):
        moved = self.current_player.move(dx, dy)
        if moved:
            self.log.append(
                f"{self.current_player.name} moves to ({self.current_player.x}, {self.current_player.y})")
        else:
            self.log.append(
                f"{self.current_player.name} can't move that far (max {self.current_player.speed} tiles).")

    def ai_decide_and_play(self):
        if self.current_player != self.players[1]:
            return

        if self.ai_mode:
            self.log.append(f"The AI {self.current_player.name} is performing it's moves!")  # Inform user of AI opponent

            for i in range(self.current_player.max_attacks):
                prompt = (
                    f"{self.current_player.name} is at ({self.current_player.x}, {self.current_player.y}), "
                    f"HP: {self.current_player.hp}. "
                    f"Enemy is at ({self.other_player.x}, {self.other_player.y}), HP: {self.other_player.hp}. "
                    f"You have an attack range of {self.current_player.range} tiles and a movement range of {self.current_player.speed} tiles."
                    f"You cannot attack your opponent if their distance exceeds your attack range."
                    f"What should {self.current_player.name} do? Options: attack, move up, move down, move left, move right."
                )

                result = text_gen(prompt, max_new_tokens=10)[0]["generated_text"].lower()

                # Basic interpretation
                if "attack" in result:
                    self.attack()
                elif "up" in result:
                    self.move_current_player(0, -1)
                elif "down" in result:
                    self.move_current_player(0, 1)
                elif "left" in result:
                    self.move_current_player(-1, 0)
                elif "right" in result:
                    self.move_current_player(1, 0)
                else:
                    self.log.append("AI is confused and does nothing.")

                self.end_turn()
        else:
            return

    def get_winner(self):
        if self.players[0].is_alive() and not self.players[1].is_alive():
            return self.players[0]
        elif self.players[1].is_alive() and not self.players[0].is_alive():
            return self.players[1]
        return None