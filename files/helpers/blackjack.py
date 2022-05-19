from json.encoder import INFINITY
import random
from math import floor

deck_count = 4
ranks = ("2", "3", "4", "5", "6", "7", "8", "9", "X", "J", "Q", "K", "A")
suits = ("♠️", "♥️", "♣️", "♦️")
coins_command_word = "!blackjack"
marseybux_command_word = "!blackjackmb"
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


def format_all(player_hand, dealer_hand, deck, status, wager, kind, is_insured=0):
	formatted_player_hand = format_cards(player_hand)
	formatted_dealer_hand = format_cards(dealer_hand)
	formatted_deck = format_cards(deck)

	return f'{"/".join(formatted_player_hand)}_{"/".join(formatted_dealer_hand)}_{"/".join(formatted_deck)}_{status}_{wager}_{kind}_{str(is_insured)}'


def check_for_blackjack_commands(in_text, from_user, from_comment):
	for command_word in (coins_command_word, marseybux_command_word):
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

						from_comment.blackjack_result = format_all(player_hand, dealer_hand, rest_of_deck, status, wager, currency_prop, 0)

def player_hit(from_comment, did_double_down=False):
	player_hand, dealer_hand, deck, status, wager, kind, is_insured = from_comment.blackjack_result.split("_")
	player_hand = player_hand.split("/")
	dealer_hand = dealer_hand.split("/")
	deck = deck.split("/")
	player_hand.append(deck.pop(0))
	player_value = get_hand_value(player_hand)

	if player_value == -1:
		status = 'bust'
		apply_game_result(from_comment, wager, status, kind)

	from_comment.blackjack_result = format_all(player_hand, dealer_hand, deck, status, wager, kind, int(is_insured))

	if (did_double_down or player_value == 21): player_stayed(from_comment)

def player_stayed(from_comment):
	player_hand, dealer_hand, deck, status, wager, kind, is_insured = from_comment.blackjack_result.split("_")
	player_hand = player_hand.split("/")
	player_value = get_hand_value(player_hand)
	dealer_hand = dealer_hand.split("/")
	dealer_value = get_hand_value(dealer_hand)
	deck = deck.split("/")

	if dealer_value == 21 and is_insured == "1":
		currency_value = getattr(from_comment.author, kind, 0)
		setattr(from_comment.author, kind, currency_value + int(wager))
	else:
		while dealer_value < 17 and dealer_value != -1:
			next = deck.pop(0)
			dealer_hand.append(next)
			dealer_value = get_hand_value(dealer_hand)

	if player_value > dealer_value or dealer_value == -1: status = 'won'
	elif dealer_value > player_value: status = 'lost'
	else: status = 'push'

	from_comment.blackjack_result = format_all(player_hand, dealer_hand, deck, status, wager, kind, int(is_insured))

	apply_game_result(from_comment, wager, status, kind)

def player_doubled_down(from_comment): 
	# When doubling down, the player receives one additional card (a "hit") and their initial bet is doubled.
	player_hand, dealer_hand, deck, status, wager, kind, is_insured = from_comment.blackjack_result.split("_")
	wager_value = int(wager)
	currency_value = getattr(from_comment.author, kind, 0)

	# Gotsta have enough coins
	if (currency_value < wager_value): return

	# Double the initial wager
	setattr(from_comment.author, kind, currency_value - wager_value)
	wager_value *= 2

	# Apply the changes to the stored hand.
	player_hand = player_hand.split("/")
	dealer_hand = dealer_hand.split("/")
	deck = deck.split("/")
	from_comment.blackjack_result = format_all(player_hand, dealer_hand, deck, status, str(wager_value), kind, int(is_insured))

	player_hit(from_comment, True)

def player_bought_insurance(from_comment):
	# When buying insurance, the player pays a side bet equal to 1/2 the original bet.
	# In the event the dealer actually had a blackjack, they receive a 2:1 payout limiting the negative effect.
	player_hand, dealer_hand, deck, status, wager, kind, is_insured = from_comment.blackjack_result.split("_")
	wager_value = int(wager)
	insurance_cost = wager_value / 2
	currency_value = getattr(from_comment.author, kind, 0)

	# Gotsta have enough coins
	if (currency_value < insurance_cost): return

	# Charge for (and grant) insurance
	setattr(from_comment.author, kind, currency_value - insurance_cost)
	is_insured = 1

	# Apply the changes to the stored hand.
	player_hand = player_hand.split("/")
	dealer_hand = dealer_hand.split("/")
	deck = deck.split("/")
	from_comment.blackjack_result = format_all(player_hand, dealer_hand, deck, status, str(wager_value), kind, int(is_insured))

def apply_game_result(from_comment, wager, result, kind):
	wager_value = int(wager)
	user = from_comment.author

	if result == 'push': reward = 0
	elif result == 'won': reward = wager_value
	elif result == 'blackjack': reward = floor(wager_value * 3/2)
	else: reward = -wager_value

	user.winnings += reward

	if (reward > -1):
		currency_value = int(getattr(user, kind, 0))
		setattr(user, kind, currency_value + wager_value + reward)