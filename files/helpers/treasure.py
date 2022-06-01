from random import randint
from math import floor
from files.helpers.const import *
from files.helpers.lottery import *

special_min = 100
special_max = 200
standard_min = 12
standard_max = 100
lotterizer_rate = 33

def check_for_treasure(in_text, from_comment):
	user = from_comment.author

	if not user.can_gamble:
		return

	if '!slots' not in in_text and '!blackjack' not in in_text and '!wordle' not in in_text:
		seed = randint(1, 1000)
		is_special = seed == 1000
		is_standard = seed >= 990
		amount = 0

		if is_special:
			amount = randint(special_min, special_max)
		elif is_standard:
			amount = randint(standard_min, standard_max)
			if randint(1, 100) > 90:
				if amount > user.coins: amount = user.coins
				amount = -amount


		if amount != 0:
			if amount > 0:
				active_lottery = get_active_lottery()
				lottery_tickets_seed = randint(1, 100)
				lottery_tickets_instead = lottery_tickets_seed <= lotterizer_rate

				if active_lottery and lottery_tickets_instead:
					ticket_count = floor(amount / LOTTERY_TICKET_COST)
					grant_lottery_tickets_to_user(user, ticket_count)
					from_comment.treasure_amount = f'l{ticket_count}'
					return

			
			user.coins += amount
			from_comment.treasure_amount = str(amount)