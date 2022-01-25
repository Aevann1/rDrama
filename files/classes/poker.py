from json.encoder import INFINITY
from files.helpers.poker import play_a_hand, format_hand


class Poker:
    command_word = "!poker"
    minimum_bet = 5
    maximum_bet = INFINITY

    def __init__(self, g):
        self.db = g.db

    def check_for_poker_command(self, in_text, from_user, from_comment):
        if self.command_word in in_text:
            for word in in_text.split():
                if self.command_word in word:
                    try:
                        wager = word[len(self.command_word):]
                        wager_value = int(wager, base=10)

                        if self.wager_is_valid(from_user, wager_value):
                            from_user.coins -= wager_value
                            result, player_hand, dealer_hand = play_a_hand()

                            if result == 0:
                                from_user.coins += wager_value
                            elif result == 1:
                                from_user.coins += wager_value * 2

                            from_comment.poker_result = self.build_text(
                                wager_value, result, player_hand, dealer_hand)

                            self.db.add(from_user)
                            self.db.add(from_comment)
                            self.db.commit()
                    except:
                        break

    def wager_is_valid(self, from_user, wager):
        if (wager < self.minimum_bet):
            return False
        elif (wager > self.maximum_bet):
            return False
        elif (wager > from_user.coins):
            return False
        else:
            return True

    def build_text(self, wager_value, comparison, player_hand, dealer_hand):
        player_cards = format_hand(player_hand)
        dealer_cards = format_hand(dealer_hand)
        card_result = f'{player_cards} vs. {dealer_cards} |'

        if comparison == 0:
            return f'{card_result} Broke Even'
        elif comparison == 1:
            return f'{card_result} Won {wager_value} Coins'
        else:
            return f'{card_result} Lost {wager_value} Coins'
