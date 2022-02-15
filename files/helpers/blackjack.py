from json.encoder import INFINITY
import random
from math import floor

deck_count = 4
ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "X", "J", "Q", "K", "A"]
suits = ["♠️", "♥️", "♣️", "♦️"]
coins_command_word = "!blackjack"
marseybucks_command_word = "!blackjackmb"
minimum_bet = 100
maximum_bet = INFINITY

def shuffle(x):
	random.shuffle(x)
	return x


def deal_initial_cards():
	deck = shuffle([rank + suit for rank in ranks for suit in suits for _ in range(deck_count)])
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


def format_all(player_hand, dealer_hand, deck, status, wager, kind):
	formatted_player_hand = format_cards(player_hand)
	formatted_dealer_hand = format_cards(dealer_hand)
	formatted_deck = format_cards(deck)

	return f'{"/".join(formatted_player_hand)}_{"/".join(formatted_dealer_hand)}_{"/".join(formatted_deck)}_{status}_{wager}_{kind}'


def check_for_blackjack_commands(in_text, from_user, from_comment):
	for command_word in (coins_command_word, marseybucks_command_word):
		currency_prop = "coins" if command_word == coins_command_word else "procoins"
		currency_value = getattr(from_user, currency_prop, 0)

		if command_word in in_text:
			for word in in_text.split():
				if command_word in word:
					try:
						wager = word[len(command_word):]
						wager_value = int(wager)
					except: break

					if (wager_value < minimum_bet): break
					elif (wager_value > maximum_bet): break
					elif (wager_value <= currency_value):

						setattr(from_user, currency_prop, currency_value - wager_value)

						player_hand, dealer_hand, rest_of_deck = deal_initial_cards()
						status = 'active'
						player_value = get_hand_value(player_hand)
						dealer_value = get_hand_value(dealer_hand)

						if player_value == 21 and dealer_value == 21:
							status = 'push'
							apply_game_result(from_comment, wager, status, currency_prop)
						elif player_value == 21:
							status = 'blackjack'
							apply_game_result(from_comment, wager, status, currency_prop)
						elif dealer_value == 21:
							status = 'lost'
							apply_game_result(from_comment, wager, status, currency_prop)

						from_comment.blackjack_result = format_all(player_hand, dealer_hand, rest_of_deck, status, wager, currency_prop)

def player_hit(from_comment):
	player_hand, dealer_hand, deck, status, wager, kind = from_comment.blackjack_result.split("_")
	player_hand = player_hand.split("/")
	dealer_hand = dealer_hand.split("/")
	deck = deck.split("/")
	player_hand.append(deck.pop(0))
	player_value = get_hand_value(player_hand)

	if player_value == -1:
		status = 'bust'
		apply_game_result(from_comment, wager, status, kind)

	from_comment.blackjack_result = format_all(player_hand, dealer_hand, deck, status, wager, kind)

	if (player_value == 21): player_stayed(from_comment)

def player_stayed(from_comment):
	player_hand, dealer_hand, deck, status, wager, kind = from_comment.blackjack_result.split("_")
	player_hand = player_hand.split("/")
	player_value = get_hand_value(player_hand)
	dealer_hand = dealer_hand.split("/")
	dealer_value = get_hand_value(dealer_hand)
	deck = deck.split("/")

	while dealer_value < 17 and dealer_value != -1:
		next = deck.pop(0)
		dealer_hand.append(next)
		dealer_value = get_hand_value(dealer_hand)

	if player_value > dealer_value or dealer_value == -1: status = 'won'
	elif dealer_value > player_value: status = 'lost'
	else: status = 'push'

	from_comment.blackjack_result = format_all(player_hand, dealer_hand, deck, status, wager, kind)

	apply_game_result(from_comment, wager, status, kind)

def apply_game_result(from_comment, wager, result, kind):
	wager_value = int(wager)
	user = from_comment.author
	reward = -1

	if result == 'push': reward = 0
	elif result == 'won': reward = wager_value
	elif result == 'blackjack': reward = floor(wager_value * 3/2)

	if (reward > -1):
		currency_value = int(getattr(user, kind, 0))

		setattr(user, kind, currency_value + wager_value + reward)

		user.winnings += reward