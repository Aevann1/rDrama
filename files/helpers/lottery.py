import time
from random import choice
from sqlalchemy import *
from files.helpers.alerts import *
from files.helpers.wrappers import *
from flask import g
from .const import *


def get_active_lottery():
    return g.db.query(Lottery).order_by(Lottery.id.desc()).filter(Lottery.is_active).one_or_none()


def get_users_participating_in_lottery():
    return g.db.query(User).filter(User.currently_held_lottery_tickets > 0).all()


def get_active_lottery_stats():
    active_lottery = get_active_lottery()
    participating_users = get_users_participating_in_lottery()

    return None if active_lottery is None else active_lottery.stats,  len(participating_users)


def end_lottery_session():
    active_lottery = get_active_lottery()

    if (active_lottery is None):
        return False, "There is no active lottery."

    participating_users = get_users_participating_in_lottery()
    raffle = []
    for user in participating_users:
        for _ in range(user.currently_held_lottery_tickets):
            raffle.append(user.id)

    winner = choice(raffle)
    active_lottery.winner_id = winner
    winning_user = next(filter(lambda x: x.id == winner, participating_users))
    winning_user.coins += active_lottery.prize
    winning_user.total_lottery_winnings += active_lottery.prize

    for user in participating_users:
        chance_to_win = user.currently_held_lottery_tickets / len(raffle) * 100
        notification_text = f'You won {active_lottery.prize} dramacoins in the lottery! Congratulations!\nOdds of winning: {chance_to_win}%' if user.id == winner else "You did not win the lottery. Better luck next time!\nOdds of winning: {chance_to_win}%"
        send_repeatable_notification(user.id, notification_text)
        user.currently_held_lottery_tickets = 0

    active_lottery.is_active = False

    manager = g.db.query(User).get(LOTTERY_MANAGER_ACCOUNT_ID)

    if manager:
        manager.coins -= active_lottery.prize

    g.db.commit()

    return True, f'{winning_user.username} won {active_lottery.prize} dramacoins!'


def start_new_lottery_session():
    end_lottery_session()

    lottery = Lottery()
    epoch_time = int(time.time())
    one_week_from_now = epoch_time + 60 * 60 * 24 * 7
    lottery.ends_at = one_week_from_now
    lottery.is_active = True

    g.db.add(lottery)
    g.db.commit()


def purchase_lottery_ticket(v):
    if (v.coins < LOTTERY_TICKET_COST):
        return False, f'Lottery tickets cost {LOTTERY_TICKET_COST} dramacoins each.'

    most_recent_lottery = get_active_lottery()
    if (most_recent_lottery is None):
        return False, "There is no active lottery."

    v.coins -= LOTTERY_TICKET_COST
    v.currently_held_lottery_tickets += 1
    v.total_held_lottery_tickets += 1

    net_ticket_value = LOTTERY_TICKET_COST - LOTTERY_SINK_RATE - LOTTERY_ROYALTY_RATE
    most_recent_lottery.prize += net_ticket_value
    most_recent_lottery.tickets_sold += 1

    grant_lottery_proceeds_to_manager(net_ticket_value)

    beneficiary = g.db.query(User).get(LOTTERY_ROYALTY_ACCOUNT_ID)
    
    if beneficiary:
        beneficiary.coins += LOTTERY_ROYALTY_RATE

    g.db.commit()

    return True, 'Successfully purchased a lottery ticket!'

def grant_lottery_proceeds_to_manager(amount):
    manager = g.db.query(User).get(LOTTERY_MANAGER_ACCOUNT_ID)
    
    if manager:
        manager.coins += amount

def grant_lottery_tickets_to_user(v, amount):
    active_lottery = get_active_lottery()
    prize_value = amount * LOTTERY_TICKET_COST

    if active_lottery:
        v.currently_held_lottery_tickets += amount
        v.total_held_lottery_tickets += amount

        active_lottery.prize += prize_value
        active_lottery.tickets_sold += amount

        grant_lottery_proceeds_to_manager(amount)

        g.db.commit()