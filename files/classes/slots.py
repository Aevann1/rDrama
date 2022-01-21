from json.encoder import INFINITY
import random
from .comment import *
from files.helpers.const import *

class Slots:
    commandWord = "!slots"
    minimumBet = 5
    maximumBet = INFINITY
    symbols = {"♦️", "♠️", "♥️", "♣️", "⚧", "🔞", "⚛️", "☢️", "✡️", "⚔️", "🐱"}

    # Common...
    commonRatio = 4
    commonPayout = 2

    # Uncommon.
    uncommonIndex = 4
    uncommonRatio = 3
    uncommonPayout = 3

    # Rare~
    rareIndex = 8
    rareRatio = 2
    rarePayout = 5

    # Jackpot!
    jackpotIndex = 10
    jackpotRatio = 1
    jackpotPayout = 100

    def __init__(self, g):
        self.db = g.db

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

                    except ValueError:
                        break
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

    # Generate full set of symbols.
    def count_out_symbols(self):
        countedSymbols = []
        payoutLookup = {}
        index = 0

        for item in self.symbols:
            count = 0

            if index == self.jackpotIndex:
                count = self.jackpotRatio
                payoutLookup[item] = self.jackpotPayout
            elif index >= self.rareIndex:
                count = self.rareRatio
                payoutLookup[item] = self.rarePayout
            elif index >= self.uncommonIndex:
                count = self.uncommonRatio
                payoutLookup[item] = self.uncommonPayout
            else:
                count = self.commonRatio
                payoutLookup[item] = self.commonPayout

            while count > 0:
                countedSymbols.append(item)
                count -= 1
            
            index += 1
            
        random.shuffle(countedSymbols)
            
        return { 'symbols': countedSymbols, 'payout': payoutLookup }

    # Consolation prizes return the user's wager.
    def check_for_consolation(self, symbols):
        # 1. Any 2 matching.
        if symbols[0] == symbols[1] or symbols[0] == symbols[2] or symbols[1] == symbols[2]:
            return True
        # 2. Any instance of jackpot.
        for symbol in symbols:
            if symbol == "🐱":
                return True
        
        return False

    # Actually make the relevant calls
    def pull_the_arm(self, from_user, amount, from_comment):
        # Charge user for the bet
        self.charge_user(from_user, amount)

        # Determine the outcome
        result1 = self.count_out_symbols()
        result2 = self.count_out_symbols()
        result3 = self.count_out_symbols()
        symbol1 = result1['symbols'][0]
        symbol2 = result2['symbols'][0]
        symbol3 = result3['symbols'][0]
        payout = result1['payout'][symbol1]
        isMatch = symbol1 == symbol2 and symbol2 == symbol3
        resultSymbols = [symbol1, symbol2, symbol3]
        isConsolation = self.check_for_consolation(resultSymbols)

        if isMatch:
            # Pay out
            reward = amount * payout
            self.credit_user(from_user, reward)
        elif isConsolation:
            # Refund wager
            self.credit_user(from_user, amount)

        return "".join(resultSymbols)

    # Credit the user's account
    def credit_user(self, from_user, amount):
        from_user.coins += amount

        self.db.add(from_user)
        self.db.commit()

    # Charge the user's account
    def charge_user(self, from_user, amount):
        from_user.coins -= amount

        self.db.add(from_user)
        self.db.commit()
