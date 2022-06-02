from files.__main__ import app, limiter
from files.helpers.wrappers import *
from files.helpers.alerts import *
from files.helpers.get import *
from files.helpers.const import *
from files.helpers.wrappers import *
from files.helpers.lottery import *
import requests

@app.post("/lottery/end")
@admin_level_required(3)
@lottery_required
def lottery_end(v):
    success, message = end_lottery_session()
    return {"message": message} if success else {"error": message}


@app.post("/lottery/start")
@admin_level_required(3)
@lottery_required
def lottery_start(v):
    start_new_lottery_session()
    return {"message": "Lottery started."}


@app.post("/lottery/buy")
@limiter.limit("3/second;100/minute;500/hour;1000/day")
@auth_required
@lottery_required
def lottery_buy(v):
    quantity = int(request.values.get("quantity"))
    success, message = purchase_lottery_tickets(v, quantity)
    lottery, participants = get_active_lottery_stats()


    if success:
        return {"message": message, "stats": {"user": v.lottery_stats, "lottery": lottery, "participants": participants}}
    else:
        return {"error": message, "stats": {"user": v.lottery_stats, "lottery": lottery, "participants": participants}}


@app.get("/lottery/active")
@limiter.limit("3/second;100/minute;500/hour;1000/day")
@auth_required
@lottery_required
def lottery_active(v):
    lottery, participants = get_active_lottery_stats()

    return {"message": "", "stats": {"user": v.lottery_stats, "lottery": lottery, "participants": participants}}

@app.get("/lottery")
@auth_required
@lottery_required
def lottery(v):
    lottery_stats, participant_stats = get_active_lottery_stats()
    return render_template("lottery.html", v=v, lottery_stats=lottery_stats, participant_stats=participant_stats)

@app.get("/admin/lottery/participants")
@admin_level_required(2)
@lottery_required
def lottery_admin(v):
    participants = get_users_participating_in_lottery()
    return render_template("admin/lottery.html", v=v, participants=participants)
