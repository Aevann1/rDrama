from functools import reduce
import random

deck_count = 4
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'X', 'J', 'Q', 'K', 'A']
suits = ['♠️', '♥️', '♣️', '♦️']


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
    return 0 if rank == 'A' else min(ranks.index(rank) + 2, 10)


def get_hand_value(hand):
    without_aces = sum(map(get_card_value, hand))
    ace_count = sum('A' in c for c in hand)
    possibilities = []

    for i in range(ace_count + 1):
        value = without_aces + (ace_count - i) + i * 11
        possibilities.append(-1 if value > 21 else value)

    return max(possibilities)


def play_round():
    player, dealer, rest_of_deck = deal_initial_cards()
    player_stayed = False
    dealer_stayed = False

    print(f'Dealer is showing {dealer[0]}')

    while True:
        player_value, dealer_value = get_hand_value(
            player), get_hand_value(dealer)

        print(f'Player has {player} (value of {player_value})')

        if dealer_stayed:
            print(f'Dealer has {dealer} (value of {dealer_value})')

        if (player_value == 21 or dealer_value == -1):
            return 1
        elif (dealer_value == 21 or player_value == -1):
            return -1
        elif not player_stayed:
            choice = input('[H]it?').lower()

            if choice == 'h':
                player.append(rest_of_deck.pop(0))
            else:
                player_stayed = True
        elif not dealer_stayed:
            if dealer_value < 17:
                dealer.append(rest_of_deck.pop(0))
            else:
                dealer_stayed = True
        else:
            if player_value > dealer_value:
                return 1
            elif dealer_value > player_value:
                return -1
            else:
                return 0


result = play_round()

if (result == 1):
    print('Won!')
elif (result == -1):
    print('Lost...')
else:
    print('Pushed.')
