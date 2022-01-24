from json.encoder import INFINITY
import random

def shuffle(stuff):
    random.shuffle(stuff)
    return stuff

class Slots:
    command_word = "!slots"
    minimum_bet = 5
    maximum_bet = INFINITY
    payout_to_symbols = {
        2: ["👣", "🍀", "🌈", "⭐️"],
        3: ["🍎", "🔞", "⚛️", "☢️"],
        5: ["✡️", "⚔️", "🍆", "🍒"],
        12: ["🐱"]
    }

    def __init__(self, g):
        self.db = g.db
            
    def check_for_slots_command(self, in_text, from_user, from_comment):
        if self.command_word in in_text:
            for word in in_text.split():
                if self.command_word in word:
                    try:
                        wager = word[len(self.command_word):]
                        wager_value = int(wager, base=10)

                        if self.wager_is_valid(from_user, wager_value):
                            from_user.coins -= wager_value

                            payout = self.determine_payout()
                            symbols = self.build_symbols(payout)
                            text = self.build_text(wager_value, payout)
                            reward = wager_value * payout

                            from_user.coins += reward
                            self.db.add(from_user)

                            from_comment.slots_result = symbols
                            from_comment.slots_text = text
                            self.db.add(from_comment)
                            
                            self.db.commit()
                    except: break

    def wager_is_valid(self, from_user, wager):
            if (wager < self.minimum_bet):
                return False
            elif (wager > self.maximum_bet):
                return False
            elif (wager > from_user.coins):
                return False
            else:
                return True

    def determine_payout(self):
        value = random.randint(0, 100)
        
        if value == 100:
            return 12
        elif value >= 96:
            return 5
        elif value >= 88:
            return 3
        elif value >= 72:
            return 2
        elif value >= 61:
            return 1
        else:
            return 0

    def build_symbols(self, for_payout):
        all_symbols = []
        
        for payout in self.payout_to_symbols:
            for symbol in self.payout_to_symbols[payout]:
                all_symbols.append(symbol)
                
        shuffle(all_symbols)
                
        if for_payout == 0:
            return "".join([all_symbols[0], all_symbols[1], all_symbols[2]])
        elif for_payout == 1:
            indices = shuffle([0, 1, 2])
            symbol_set = ["", "", ""]
            [match_a, match_b, nonmatch] = indices
            [matching_symbol, other_symbol] = all_symbols
            symbol_set[match_a] = matching_symbol
            symbol_set[match_b] = matching_symbol
            symbol_set[nonmatch] = other_symbol
            
            return "".join(symbol_set)
        else:
            relevantSymbols = shuffle(self.payout_to_symbols[for_payout])
            symbol = relevantSymbols[0]
            return "".join([symbol, symbol, symbol])
    
    def build_text(self, wager_value, result):
        if result == 0:
            return f'Lost {wager_value} Coins'
        elif result == 1:
            return 'Broke Even'
        elif result == 12:
            return f'Jackpot! Won {wager_value} Coins'
        else:
            return f'Won {wager_value} Coins'
        