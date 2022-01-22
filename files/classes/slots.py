from json.encoder import INFINITY
import random
from typing import NamedTuple
from .comment import *
from files.helpers.const import *

class Slots:
    commandWord = "!slots"
    minimumBet = 5
    maximumBet = INFINITY

    class Category(NamedTuple):
        symbols: list
        ratio: int
        payout: int

    categories = [
        Category("♦️ ♠️ ♥️ ♣️".split(), 4, 2),
        Category("⚧ 🔞 ⚛️ ☢️".split(), 3, 3),
        Category("✡️ ⚔️".split(), 2, 5),
        Category("🐱".split(), 1, 100),
    ]

    def __init__(self, g):
        self.db = g.db
        # Generate full set of symbols.
        symbols = []
        payouts = {}
        for c in self.categories:
            for s in c.symbols:
                symbols.extend([s] * c.ratio)
                payouts[s] = c.payout
        self.symbols = symbols
        self.payouts = payouts

    # Check for !slots<wager>
    def check_for_slots_command(self, in_text, from_user, from_comment):
        if self.commandWord in in_text:
            for word in in_text.split():
                if self.commandWord in word:
                    try:
                        wager = word[len(self.commandWord):]
                        wagerValue = int(wager, base=10)

                        if self.wager_is_valid(from_user, wagerValue):
                            result = self.pull_the_arm(from_user, wagerValue, from_comment)
                            return { 'pulled': True, 'result': result }

                    except: break
        return { 'pulled': False, 'result': '' }

    # Ensure user is capable of the wager
    def wager_is_valid(self, from_user, wager):
        if (wager < self.minimumBet):
            return False
        elif (wager > self.maximumBet):
            return False
        elif (wager > from_user.coins):
            return False
        else:
            return True

    # Actually make the relevant calls
    def pull_the_arm(self, from_user, amount, from_comment):
        # Determine the outcome
        s1 = random.choice(self.symbols)
        s2 = random.choice(self.symbols)
        s3 = random.choice(self.symbols)
        resultSymbols = [s1, s2, s3]

        if s1 == s2 == s3:
            # Pay out
            reward = amount * (self.payouts[s1] - 1) # withhold the bet
            self.credit_user(from_user, reward)
        elif s1 == s2 or s1 == s3 or s2 == s3 or "🐱" in resultSymbols:
            pass # Refund wager - do nothing
        else:
            self.charge_user(from_user, amount)

        return "".join(resultSymbols)

    # Credit the user's account
    def credit_user(self, from_user, amount):
        from_user.coins += amount
        self.db.add(from_user)

    # Charge the user's account
    def charge_user(self, from_user, amount):
        from_user.coins -= amount
        self.db.add(from_user)
