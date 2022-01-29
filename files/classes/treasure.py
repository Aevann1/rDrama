import random


class Treasure:
    special_min = 100
    special_max = 1000
    standard_min = 10
    standard_max = 100

    def __init__(self, g):
        self.db = g.db

    def check_for_treasure(self, from_comment):
        seed = random.randint(1, 1000)
        is_special = seed == 1000  # 0.1% chance
        is_standard = seed >= 990  # 1.0% chance
        amount = 0

        if is_special:
            amount = random.randint(self.special_min, self.special_max)
        elif is_standard:
            amount = random.randint(self.standard_min, self.standard_max)

        if amount > 0:
            user = from_comment.author
            user.coins += amount
            from_comment.treasure_amount = str(amount)

            self.db.add(user)
            self.db.add(from_comment)
            self.db.commit()
