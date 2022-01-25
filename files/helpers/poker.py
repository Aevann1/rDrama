from functools import reduce
import random

deck_count = 4
hand_size = 5
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'X', 'J', 'Q', 'K', 'A']
suits = ['♠', '♥', '♣', '♦']


def build_deck():
    deck = []

    for _ in range(0, deck_count):
        for rank in ranks:
            for suit in suits:
                deck.append(f'{rank}{suit}')

    random.shuffle(deck)

    return deck


def build_hands():
    deck = build_deck()
    player_hand = []
    dealer_hand = []

    for x in range(0, hand_size * 2):
        hand = player_hand if x % 2 == 0 else dealer_hand
        hand.append(deck[x])

    return player_hand, dealer_hand


def sort_hand(hand):
    def determine_card_value(card):
        rank = list(get_card_rank_suit(card))[0]
        return ranks.index(rank)

    return sorted(hand, key=determine_card_value)


def get_card_rank_suit(value):
    as_list = list(value)
    rank = as_list[0]
    suit = as_list[1]
    return rank, suit


def get_card_rank(value):
    rank = list(get_card_rank_suit(value))[0]
    return rank


def get_rank_value(rank):
    if rank == 'A':
        return 14
    elif rank == 'K':
        return 13
    elif rank == 'Q':
        return 12
    elif rank == 'J':
        return 11
    elif rank == 'X':
        return 10
    else:
        return int(rank, base=10)


def get_card_rank_value(card):
    rank = list(get_card_rank_suit(card))[0]
    return get_rank_value(rank)


def hand_is_straight(hand):
    converted_hand = list(map(get_card_rank_value, hand))
    converted_hand.reverse()
    is_straight = True
    prev = converted_hand.pop(0)

    for rank_value in converted_hand:
        if rank_value == prev - 1:
            prev = rank_value
        else:
            is_straight = False
            break

    return is_straight


def hand_is_flush(hand):
    _, first_suit = get_card_rank_suit(hand[0])
    suits_match = all(suit == first_suit for (_, suit)
                      in map(get_card_rank_suit, hand))
    return suits_match


def get_rank_counts(hand):
    hand_ranks = list(map(get_card_rank, hand))
    rank_counts = {}

    for rank in hand_ranks:
        if not rank_counts.get(rank):
            rank_counts[rank] = 0

        rank_counts[rank] += 1

    return rank_counts


def determine_hand_value(hand):
    sorted_hand = sort_hand(hand)
    hand_ranks = list(map(get_card_rank, sorted_hand))
    hand_rank_values = list(map(get_rank_value, hand_ranks))
    rank_counts = get_rank_counts(sorted_hand)
    is_flush = hand_is_flush(sorted_hand)
    is_straight = hand_is_straight(sorted_hand)
    high_card_value = hand_rank_values[-1]
    hand_value_total = reduce(lambda a, b: a + b, hand_rank_values)

    def _determine_hand_value():
        # 10. Royal Flush
        if (is_flush and hand_ranks == ['X', 'J', 'Q', 'K', 'A']):
            return 10

        # 9. Straight Flush
        if (is_flush and is_straight):
            return 9

        # 8. Four of a Kind
        for rank in rank_counts:
            if rank_counts[rank] == 4:
                return 8

        # 7. Full House
        fh3 = ''
        fh2 = ''
        fh2_2 = ''

        for rank in rank_counts:
            if rank_counts[rank] == 3:
                fh3 = rank
            elif rank_counts[rank] == 2:
                if fh2:
                    fh2_2 = rank
                else:
                    fh2 = rank

        if fh3 and fh2:
            return 7

        # 6. Flush
        if is_flush:
            return 6

        # 5. Straight
        if is_straight:
            return 5

        # 4. Three of a Kind
        if fh3:
            return 4

        # 3. Two Pair
        if fh2 and fh2_2:
            return 3

        # 2. Pair
        if fh2:
            return 2

        # 1. High Card
        return 1

    return (_determine_hand_value(), hand_value_total, high_card_value)


def compare_hands(player_hand, dealer_hand):
    (player_value, player_total, player_high_card) = determine_hand_value(player_hand)
    (dealer_value, dealer_total, dealer_high_card) = determine_hand_value(dealer_hand)

    if player_value == dealer_value:
        if player_total == dealer_total:
            if player_high_card == dealer_high_card:
                return 0
            elif dealer_high_card > player_high_card:
                return -1
            else:
                return 1
        elif dealer_total > player_total:
            return -1
        else:
            return 1
    elif dealer_value > player_value:
        return -1
    else:
        return 1


def play_a_hand():
    player_hand, dealer_hand = build_hands()
    result = compare_hands(player_hand, dealer_hand)
    return result, player_hand, dealer_hand

def format_hand(hand):
  return f'[{"][".join(hand)}]'

## Tests ##
def TEST_determine_hand_value():
    a, b, c = determine_hand_value(['X♠', 'J♠', 'Q♠', 'K♠', 'A♠'])
    print('Royal Flush?', a == 10, b == 60, c == 14)

    d, e, f = determine_hand_value(['2♠', '3♠', '4♠', '5♠', '6♠'])
    print('Straight Flush?', d == 9, e == 20, f == 6)

    g, h, i = determine_hand_value(['2♠', '2♣', '2♥', '2♦', '3♦'])
    print('Four of a Kind?', g == 8, h == 11, i == 3)

    j, k, l = determine_hand_value(['2♠', '2♣', '2♥', '3♥', '3♦'])
    print('Full House?', j == 7, k == 12, l == 3)

    m, n, o = determine_hand_value(['2♠', '3♠', '4♠', '5♠', '7♠'])
    print('Flush?', m == 6, n == 21, o == 7)

    p, q, r = determine_hand_value(['2♠', '3♥', '4♠', '5♠', '6♠'])
    print('Straight?', p == 5, q == 20, r == 6)

    s, t, u = determine_hand_value(['2♠', '2♣', '2♥', '5♦', '3♦'])
    print('Three of a Kind?', s == 4, t == 14, u == 5)

    v, w, x = determine_hand_value(['2♠', '2♣', '5♥', '5♦', '3♦'])
    print('Two Pair?', v == 3, w == 17, x == 5)

    y, z, aa = determine_hand_value(['2♠', '2♣', '8♥', '5♦', '3♦'])
    print('Pair?', y == 2, z == 20, aa == 8)

    bb, cc, dd = determine_hand_value(['2♠', '9♣', 'A♥', '5♦', '3♦'])
    print('High Card?', bb == 1, cc == 33, dd == 14)


def TEST_compare_hands():
    # Should be -1, a loss:
    a = ['2♠', '2♣', '2♥', '5♦', '3♦']  # 3 of a kind
    b = ['2♠', '2♣', '2♥', '3♥', '3♦']  # Full house

    print('Dealer wins', compare_hands(a, b) == -1)

    # Should be 0, a push:
    c = ['2♠', '2♣', '5♥', '5♦', '3♦']  # Two pair, 5 high
    d = ['2♠', '2♣', '5♥', '5♦', '3♥']  # Two pair, 5 high

    print('Push', compare_hands(c, d) == 0)

    # Should be 1, a win:
    e = ['2♠', '2♣', '2♥', '2♦', '3♦']  # 4 of a kind
    f = ['2♠', '2♣', '2♥', '3♥', '3♦']  # Full house

    print('Player wins', compare_hands(e, f) == 1)
##
