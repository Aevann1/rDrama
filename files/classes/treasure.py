import random


class Treasure:
    special_min = 100
    special_max = 1000
    standard_min = 10
    standard_max = 100

    def __init__(self, g):
        self.db = g.db

    def check_for_treasure(self, in_text, from_comment):
        has_gamble_command = '!slots' in in_text or '!blackjack' in in_text

        if not has_gamble_command:
            seed = random.randint(1, 1000)
            is_special = seed == 1000  # 0.1% chance
            is_standard = seed >= 990  # 1.0% chance
            amount = 0

            if is_special:
                amount = random.randint(self.special_min, self.special_max)
            elif is_standard:
                amount = random.randint(self.standard_min, self.standard_max)

                # Mimic: 25% chance
                if random.randint(1, 100) > 75:
                    amount = -amount

            if amount != 0:
                user = from_comment.author
                user.coins += amount

                if user.coins < 0:
                    user.coins = 0

                from_comment.treasure_amount = str(amount)

                self.db.add(user)
                self.db.add(from_comment)
                self.db.commit()
