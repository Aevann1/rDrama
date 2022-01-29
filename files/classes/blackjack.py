from functools import reduce
from json.encoder import INFINITY
import random
from math import floor

deck_count = 4
ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "X", "J", "Q", "K", "A"]
suits = ["♠️", "♥️", "♣️", "♦️"]


def shuffle(x):
    random.shuffle(x)
    return x


def get_shuffled_deck():
    return shuffle([rank + suit for rank in ranks for suit in suits for _ in range(deck_count)])


def deal_initial_cards():
    deck = get_shuffled_deck()
    p1, d1, p2, d2, *rest_of_deck = deck
    return [p1, p2], [d1, d2], rest_of_deck


def get_card_value(card):
    rank = card[0]
    return 0 if rank == "A" else min(ranks.index(rank) + 2, 10)


def get_hand_value(hand):
    without_aces = sum(map(get_card_value, hand))
    ace_count = sum("A" in c for c in hand)
    possibilities = []

    for i in range(ace_count + 1):
        value = without_aces + (ace_count - i) + i * 11
        possibilities.append(-1 if value > 21 else value)

    return max(possibilities)


def format_cards(hand):
    return map(lambda x: "".join(x), hand)


def format_all(player_hand, dealer_hand, deck, status, wager):
    formatted_player_hand = format_cards(player_hand)
    formatted_dealer_hand = format_cards(dealer_hand)
    formatted_deck = format_cards(deck)

    return f'{"/".join(formatted_player_hand)}_{"/".join(formatted_dealer_hand)}_{"/".join(formatted_deck)}_{status}_{wager}'


class Blackjack:
    command_word = "!blackjack"
    minimum_bet = 100
    maximum_bet = INFINITY

    def __init__(self, g):
        self.db = g.db

    def check_for_blackjack_command(self, in_text, from_user, from_comment):
        if self.command_word in in_text:
            for word in in_text.split():
                if self.command_word in word:
                    wager = word[len(self.command_word):]
                    wager_value = int(wager)

                    if (wager_value < self.minimum_bet):
                        break
                    elif (wager_value > self.maximum_bet):
                        break
                    elif (wager_value > from_user.coins):
                        break

                    from_user.coins -= wager_value

                    player_hand, dealer_hand, rest_of_deck = deal_initial_cards()
                    status = 'active'
                    player_value = get_hand_value(player_hand)
                    dealer_value = get_hand_value(dealer_hand)

                    if player_value == 21 and dealer_value == 21:
                        status = 'push'
                        self.apply_game_result(from_comment, wager, status)
                    elif player_value == 21:
                        status = 'blackjack'
                        self.apply_game_result(from_comment, wager, status)
                    elif dealer_value == 21:
                        status = 'lost'
                        self.apply_game_result(from_comment, wager, status)

                    from_comment.blackjack_result = format_all(
                        player_hand, dealer_hand, rest_of_deck, status, wager)

                    self.db.add(from_comment)
                    self.db.commit()

    def player_hit(self, from_comment):
        player_hand, dealer_hand, deck, status, wager = from_comment.blackjack_result.split(
            "_")
        player_hand = player_hand.split("/")
        dealer_hand = dealer_hand.split("/")
        deck = deck.split("/")
        player_hand.append(deck.pop(0))
        player_value = get_hand_value(player_hand)

        if player_value == -1:
            status = 'bust'
            self.apply_game_result(from_comment, wager, status)

        from_comment.blackjack_result = format_all(
            player_hand, dealer_hand, deck, status, wager)

        self.db.add(from_comment)
        self.db.commit()

        if (player_value == 21):
            self.player_stayed(from_comment)

    def player_stayed(self, from_comment):
        player_hand, dealer_hand, deck, status, wager = from_comment.blackjack_result.split(
            "_")
        player_hand = player_hand.split("/")
        player_value = get_hand_value(player_hand)
        dealer_hand = dealer_hand.split("/")
        dealer_value = get_hand_value(dealer_hand)
        deck = deck.split("/")

        while dealer_value < 17 and dealer_value != -1:
            next = deck.pop(0)
            dealer_hand.append(next)
            dealer_value = get_hand_value(dealer_hand)

        if player_value > dealer_value or dealer_value == -1:
            status = 'won'
        elif dealer_value > player_value:
            status = 'lost'
        else:
            status = 'push'

        from_comment.blackjack_result = format_all(
            player_hand, dealer_hand, deck, status, wager)

        self.db.add(from_comment)
        self.db.commit()

        self.apply_game_result(from_comment, wager, status)

    def apply_game_result(self, from_comment, wager, result):
        reward = 0

        if result == 'push':
            reward = int(wager)
        elif result == 'won':
            reward = int(wager) * 2
        elif result == 'blackjack':
            reward = int(wager) + floor(int(wager) * (3/2))

        if (reward > 0):
            user = from_comment.author
            user.coins += reward
            user.winnings += reward - int(wager)

            self.db.add(user)
            self.db.commit()