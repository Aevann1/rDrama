import qrcode
import io
import time
import math
from files.classes.views import ViewerRelationship
from files.helpers.alerts import *
from files.helpers.sanitize import *
from files.helpers.const import *
from files.mail import *
from flask import *
from files.__main__ import app, limiter, db_session
from pusher_push_notifications import PushNotifications
from collections import Counter
import gevent
from sys import stdout
import os

if PUSHER_ID != 'blahblahblah':
	beams_client = PushNotifications(instance_id=PUSHER_ID, secret_key=PUSHER_KEY)

def pusher_thread2(interests, notifbody, username):
	beams_client.publish_to_interests(
		interests=[interests],
		publish_body={
			'web': {
				'notification': {
					'title': f'New message from @{username}',
					'body': notifbody,
					'deep_link': f'{SITE_FULL}/notifications?messages=true',
					'icon': f'{SITE_FULL}/assets/images/{SITE_NAME}/icon.webp?v=1015',
				}
			},
			'fcm': {
				'notification': {
					'title': f'New message from @{username}',
					'body': notifbody,
				},
				'data': {
					'url': '/notifications?messages=true',
				}
			}
		},
	)
	stdout.flush()

def leaderboard_thread():
	global users9, users9_25, users13, users13_25

	db = db_session()

	votes1 = db.query(Submission.author_id, func.count(Submission.author_id)).join(Vote, Vote.submission_id==Submission.id).filter(Vote.vote_type==-1).group_by(Submission.author_id).order_by(func.count(Submission.author_id).desc()).all()
	votes2 = db.query(Comment.author_id, func.count(Comment.author_id)).join(CommentVote, CommentVote.comment_id==Comment.id).filter(CommentVote.vote_type==-1).group_by(Comment.author_id).order_by(func.count(Comment.author_id).desc()).all()
	votes3 = Counter(dict(votes1)) + Counter(dict(votes2))
	users8 = db.query(User).filter(User.id.in_(votes3.keys())).all()
	users9 = []
	for user in users8: users9.append((user, votes3[user.id]))
	users9 = sorted(users9, key=lambda x: x[1], reverse=True)
	users9_25 = users9[:25]

	votes1 = db.query(Vote.user_id, func.count(Vote.user_id)).filter(Vote.vote_type==1).group_by(Vote.user_id).order_by(func.count(Vote.user_id).desc()).all()
	votes2 = db.query(CommentVote.user_id, func.count(CommentVote.user_id)).filter(CommentVote.vote_type==1).group_by(CommentVote.user_id).order_by(func.count(CommentVote.user_id).desc()).all()
	votes3 = Counter(dict(votes1)) + Counter(dict(votes2))
	users14 = db.query(User).filter(User.id.in_(votes3.keys())).all()
	users13 = []
	for user in users14:
		users13.append((user, votes3[user.id]-user.post_count-user.comment_count))
	users13 = sorted(users13, key=lambda x: x[1], reverse=True)
	users13_25 = users13[:25]

	db.close()
	stdout.flush()

gevent.spawn(leaderboard_thread())











@app.get("/@<username>/upvoters/<uid>/posts")
@auth_required
def upvoters_posts(v, username, uid):
	u = get_user(username)
	if u.is_private and (not v or (v.id != u.id and v.admin_level < 2 and not v.eye)): abort(403)
	id = u.id
	uid = int(uid)

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(Submission).join(Vote, Vote.submission_id==Submission.id).filter(Submission.ghost == False, Submission.is_banned == False, Submission.deleted_utc == 0, Vote.vote_type==1, Submission.author_id==id, Vote.user_id==uid).order_by(Submission.created_utc.desc()).offset(25 * (page - 1)).limit(26).all()

	listing = [p.id for p in listing]
	next_exists = len(listing) > 25
	listing = listing[:25]

	listing = get_posts(listing, v=v)

	return render_template("voted_posts.html", next_exists=next_exists, listing=listing, page=page, v=v)


@app.get("/@<username>/upvoters/<uid>/comments")
@auth_required
def upvoters_comments(v, username, uid):
	u = get_user(username)
	if u.is_private and (not v or (v.id != u.id and v.admin_level < 2 and not v.eye)): abort(403)
	id = u.id
	uid = int(uid)

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(Comment).join(CommentVote, CommentVote.comment_id==Comment.id).filter(Comment.ghost == False, Comment.is_banned == False, Comment.deleted_utc == 0, CommentVote.vote_type==1, Comment.author_id==id, CommentVote.user_id==uid).order_by(Comment.created_utc.desc()).offset(25 * (page - 1)).limit(26).all()

	listing = [c.id for c in listing]
	next_exists = len(listing) > 25
	listing = listing[:25]

	listing = get_comments(listing, v=v)

	return render_template("voted_comments.html", next_exists=next_exists, listing=listing, page=page, v=v, standalone=True)


@app.get("/@<username>/downvoters/<uid>/posts")
@auth_required
def downvoters_posts(v, username, uid):
	u = get_user(username)
	if u.is_private and (not v or (v.id != u.id and v.admin_level < 2 and not v.eye)): abort(403)
	id = u.id
	uid = int(uid)

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(Submission).join(Vote, Vote.submission_id==Submission.id).filter(Submission.ghost == False, Submission.is_banned == False, Submission.deleted_utc == 0, Vote.vote_type==-1, Submission.author_id==id, Vote.user_id==uid).order_by(Submission.created_utc.desc()).offset(25 * (page - 1)).limit(26).all()

	listing = [p.id for p in listing]
	next_exists = len(listing) > 25
	listing = listing[:25]

	listing = get_posts(listing, v=v)

	return render_template("voted_posts.html", next_exists=next_exists, listing=listing, page=page, v=v)


@app.get("/@<username>/downvoters/<uid>/comments")
@auth_required
def downvoters_comments(v, username, uid):
	u = get_user(username)
	if u.is_private and (not v or (v.id != u.id and v.admin_level < 2 and not v.eye)): abort(403)
	id = u.id
	uid = int(uid)

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(Comment).join(CommentVote, CommentVote.comment_id==Comment.id).filter(Comment.ghost == False, Comment.is_banned == False, Comment.deleted_utc == 0, CommentVote.vote_type==-1, Comment.author_id==id, CommentVote.user_id==uid).order_by(Comment.created_utc.desc()).offset(25 * (page - 1)).limit(26).all()

	listing = [c.id for c in listing]
	next_exists = len(listing) > 25
	listing = listing[:25]

	listing = get_comments(listing, v=v)

	return render_template("voted_comments.html", next_exists=next_exists, listing=listing, page=page, v=v, standalone=True)





@app.get("/@<username>/upvoting/<uid>/posts")
@auth_required
def upvoting_posts(v, username, uid):
	u = get_user(username)
	if u.is_private and (not v or (v.id != u.id and v.admin_level < 2 and not v.eye)): abort(403)
	id = u.id
	uid = int(uid)

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(Submission).join(Vote, Vote.submission_id==Submission.id).filter(Submission.ghost == False, Submission.is_banned == False, Submission.deleted_utc == 0, Vote.vote_type==1, Vote.user_id==id, Submission.author_id==uid).order_by(Submission.created_utc.desc()).offset(25 * (page - 1)).limit(26).all()

	listing = [p.id for p in listing]
	next_exists = len(listing) > 25
	listing = listing[:25]

	listing = get_posts(listing, v=v)

	return render_template("voted_posts.html", next_exists=next_exists, listing=listing, page=page, v=v)


@app.get("/@<username>/upvoting/<uid>/comments")
@auth_required
def upvoting_comments(v, username, uid):
	u = get_user(username)
	if u.is_private and (not v or (v.id != u.id and v.admin_level < 2 and not v.eye)): abort(403)
	id = u.id
	uid = int(uid)

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(Comment).join(CommentVote, CommentVote.comment_id==Comment.id).filter(Comment.ghost == False, Comment.is_banned == False, Comment.deleted_utc == 0, CommentVote.vote_type==1, CommentVote.user_id==id, Comment.author_id==uid).order_by(Comment.created_utc.desc()).offset(25 * (page - 1)).limit(26).all()

	listing = [c.id for c in listing]
	next_exists = len(listing) > 25
	listing = listing[:25]

	listing = get_comments(listing, v=v)

	return render_template("voted_comments.html", next_exists=next_exists, listing=listing, page=page, v=v, standalone=True)


@app.get("/@<username>/downvoting/<uid>/posts")
@auth_required
def downvoting_posts(v, username, uid):
	u = get_user(username)
	if u.is_private and (not v or (v.id != u.id and v.admin_level < 2 and not v.eye)): abort(403)
	id = u.id
	uid = int(uid)

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(Submission).join(Vote, Vote.submission_id==Submission.id).filter(Submission.ghost == False, Submission.is_banned == False, Submission.deleted_utc == 0, Vote.vote_type==-1, Vote.user_id==id, Submission.author_id==uid).order_by(Submission.created_utc.desc()).offset(25 * (page - 1)).limit(26).all()

	listing = [p.id for p in listing]
	next_exists = len(listing) > 25
	listing = listing[:25]

	listing = get_posts(listing, v=v)

	return render_template("voted_posts.html", next_exists=next_exists, listing=listing, page=page, v=v)


@app.get("/@<username>/downvoting/<uid>/comments")
@auth_required
def downvoting_comments(v, username, uid):
	u = get_user(username)
	if u.is_private and (not v or (v.id != u.id and v.admin_level < 2 and not v.eye)): abort(403)
	id = u.id
	uid = int(uid)

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(Comment).join(CommentVote, CommentVote.comment_id==Comment.id).filter(Comment.ghost == False, Comment.is_banned == False, Comment.deleted_utc == 0, CommentVote.vote_type==-1, CommentVote.user_id==id, Comment.author_id==uid).order_by(Comment.created_utc.desc()).offset(25 * (page - 1)).limit(26).all()

	listing = [c.id for c in listing]
	next_exists = len(listing) > 25
	listing = listing[:25]

	listing = get_comments(listing, v=v)

	return render_template("voted_comments.html", next_exists=next_exists, listing=listing, page=page, v=v, standalone=True)





@app.get("/grassed")
@auth_required
def grassed(v):
	users = g.db.query(User).filter(User.ban_reason.like('grass award used by @%')).all()

	return render_template("grassed.html", v=v, users=users)

@app.get("/agendaposters")
@auth_required
def agendaposters(v):
	users = [x for x in g.db.query(User).filter(User.agendaposter > 0).order_by(User.username).all()]
	return render_template("agendaposters.html", v=v, users=users)


@app.get("/@<username>/upvoters")
@auth_required
def upvoters(v, username):
	id = get_user(username).id

	votes = g.db.query(Vote.user_id, func.count(Vote.user_id)).join(Submission, Vote.submission_id==Submission.id).filter(Submission.ghost == False, Submission.is_banned == False, Submission.deleted_utc == 0, Vote.vote_type==1, Submission.author_id==id).group_by(Vote.user_id).order_by(func.count(Vote.user_id).desc()).all()

	votes2 = g.db.query(CommentVote.user_id, func.count(CommentVote.user_id)).join(Comment, CommentVote.comment_id==Comment.id).filter(Comment.ghost == False, Comment.is_banned == False, Comment.deleted_utc == 0, CommentVote.vote_type==1, Comment.author_id==id).group_by(CommentVote.user_id).order_by(func.count(CommentVote.user_id).desc()).all()

	votes = Counter(dict(votes)) + Counter(dict(votes2))

	users = g.db.query(User).filter(User.id.in_(votes.keys())).all()
	users2 = []
	for user in users: users2.append((user, votes[user.id]))

	users = sorted(users2, key=lambda x: x[1], reverse=True)
	
	try:
		pos = [x[0].id for x in users].index(v.id)
		pos = (pos+1, users[pos][1])
	except: pos = (len(users)+1, 0)

	return render_template("voters.html", v=v, users=users[:25], pos=pos, name='Up', name2=f'@{username} biggest simps')



@app.get("/@<username>/downvoters")
@auth_required
def downvoters(v, username):
	id = get_user(username).id

	votes = g.db.query(Vote.user_id, func.count(Vote.user_id)).join(Submission, Vote.submission_id==Submission.id).filter(Submission.ghost == False, Submission.is_banned == False, Submission.deleted_utc == 0, Vote.vote_type==-1, Submission.author_id==id).group_by(Vote.user_id).order_by(func.count(Vote.user_id).desc()).all()

	votes2 = g.db.query(CommentVote.user_id, func.count(CommentVote.user_id)).join(Comment, CommentVote.comment_id==Comment.id).filter(Comment.ghost == False, Comment.is_banned == False, Comment.deleted_utc == 0, CommentVote.vote_type==-1, Comment.author_id==id).group_by(CommentVote.user_id).order_by(func.count(CommentVote.user_id).desc()).all()

	votes = Counter(dict(votes)) + Counter(dict(votes2))

	users = g.db.query(User).filter(User.id.in_(votes.keys())).all()
	users2 = []
	for user in users: users2.append((user, votes[user.id]))

	users = sorted(users2, key=lambda x: x[1], reverse=True)
	
	try:
		pos = [x[0].id for x in users].index(v.id)
		pos = (pos+1, users[pos][1])
	except: pos = (len(users)+1, 0)

	return render_template("voters.html", v=v, users=users[:25], pos=pos, name='Down', name2=f'@{username} biggest haters')

@app.get("/@<username>/upvoting")
@auth_required
def upvoting(v, username):
	id = get_user(username).id

	votes = g.db.query(Submission.author_id, func.count(Submission.author_id)).join(Vote, Vote.submission_id==Submission.id).filter(Submission.ghost == False, Submission.is_banned == False, Submission.deleted_utc == 0, Vote.vote_type==1, Vote.user_id==id).group_by(Submission.author_id).order_by(func.count(Submission.author_id).desc()).all()

	votes2 = g.db.query(Comment.author_id, func.count(Comment.author_id)).join(CommentVote, CommentVote.comment_id==Comment.id).filter(Comment.ghost == False, Comment.is_banned == False, Comment.deleted_utc == 0, CommentVote.vote_type==1, CommentVote.user_id==id).group_by(Comment.author_id).order_by(func.count(Comment.author_id).desc()).all()

	votes = Counter(dict(votes)) + Counter(dict(votes2))

	users = g.db.query(User).filter(User.id.in_(votes.keys())).all()
	users2 = []
	for user in users: users2.append((user, votes[user.id]))

	users = sorted(users2, key=lambda x: x[1], reverse=True)
	
	try:
		pos = [x[0].id for x in users].index(v.id)
		pos = (pos+1, users[pos][1])
	except: pos = (len(users)+1, 0)

	return render_template("voters.html", v=v, users=users[:25], pos=pos, name='Up', name2=f'Who @{username} simps for')

@app.get("/@<username>/downvoting")
@auth_required
def downvoting(v, username):
	id = get_user(username).id

	votes = g.db.query(Submission.author_id, func.count(Submission.author_id)).join(Vote, Vote.submission_id==Submission.id).filter(Submission.ghost == False, Submission.is_banned == False, Submission.deleted_utc == 0, Vote.vote_type==-1, Vote.user_id==id).group_by(Submission.author_id).order_by(func.count(Submission.author_id).desc()).all()

	votes2 = g.db.query(Comment.author_id, func.count(Comment.author_id)).join(CommentVote, CommentVote.comment_id==Comment.id).filter(Comment.ghost == False, Comment.is_banned == False, Comment.deleted_utc == 0, CommentVote.vote_type==-1, CommentVote.user_id==id).group_by(Comment.author_id).order_by(func.count(Comment.author_id).desc()).all()

	votes = Counter(dict(votes)) + Counter(dict(votes2))

	users = g.db.query(User).filter(User.id.in_(votes.keys())).all()
	users2 = []
	for user in users: users2.append((user, votes[user.id]))

	users = sorted(users2, key=lambda x: x[1], reverse=True)
	
	try:
		pos = [x[0].id for x in users].index(v.id)
		pos = (pos+1, users[pos][1])
	except: pos = (len(users)+1, 0)

	return render_template("voters.html", v=v, users=users[:25], pos=pos, name='Down', name2=f'Who @{username} hates')



@app.post("/@<username>/suicide")
@limiter.limit("1/second;5/day")
@limiter.limit("1/second;5/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def suicide(v, username):
	user = get_user(username)
	suicide = f"Hi there,\n\nA [concerned user](/id/{v.id}) reached out to us about you.\n\nWhen you're in the middle of something painful, it may feel like you don't have a lot of options. But whatever you're going through, you deserve help and there are people who are here for you.\n\nThere are resources available in your area that are free, confidential, and available 24/7:\n\n- Call, Text, or Chat with Canada's [Crisis Services Canada](https://www.crisisservicescanada.ca/en/)\n- Call, Email, or Visit the UK's [Samaritans](https://www.samaritans.org/)\n- Text CHAT to America's [Crisis Text Line](https://www.crisistextline.org/) at 741741.\nIf you don't see a resource in your area above, the moderators keep a comprehensive list of resources and hotlines for people organized by location. Find Someone Now\n\nIf you think you may be depressed or struggling in another way, don't ignore it or brush it aside. Take yourself and your feelings seriously, and reach out to someone.\n\nIt may not feel like it, but you have options. There are people available to listen to you, and ways to move forward.\n\nYour fellow users care about you and there are people who want to help."
	send_notification(user.id, suicide)
	g.db.commit()
	return {"message": "Help message sent!"}


@app.get("/@<username>/coins")
@auth_required
def get_coins(v, username):
	user = get_user(username)
	if user != None: return {"coins": user.coins}, 200
	else: return {"error": "invalid_user"}, 404

@app.post("/@<username>/transfer_coins")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@is_not_permabanned
def transfer_coins(v, username):
	receiver = g.db.query(User).filter_by(username=username).one_or_none()

	if receiver is None: return {"error": "That user doesn't exist."}, 404

	if receiver.id != v.id:
		amount = request.values.get("amount", "").strip()
		amount = int(amount) if amount.isdigit() else None

		if amount is None or amount <= 0: return {"error": "Invalid amount of coins."}, 400
		if v.coins < amount: return {"error": "You don't have enough coins."}, 400
		if amount < 100: return {"error": "You have to gift at least 100 coins."}, 400

		if not v.patron and not receiver.patron and not v.alts_patron and not receiver.alts_patron: tax = math.ceil(amount*0.03)
		else: tax = 0

		log_message = f"@{v.username} has transferred {amount} coins to @{receiver.username}"
		send_repeatable_notification(GIFT_NOTIF_ID, log_message)

		receiver.coins += amount-tax
		v.coins -= amount
		send_repeatable_notification(receiver.id, f":marseycapitalistmanlet: @{v.username} has gifted you {amount-tax} coins!")
		g.db.add(receiver)
		g.db.add(v)

		g.db.commit()
		return {"message": f"{amount-tax} coins transferred!"}, 200

	return {"message": "You can't transfer coins to yourself!"}, 400


@app.post("/@<username>/transfer_bux")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@is_not_permabanned
def transfer_bux(v, username):
	receiver = g.db.query(User).filter_by(username=username).one_or_none()

	if not receiver: return {"error": "That user doesn't exist."}, 404

	if receiver.id != v.id:
		amount = request.values.get("amount", "").strip()
		amount = int(amount) if amount.isdigit() else None

		if not amount or amount < 0: return {"error": "Invalid amount of marseybux."}, 400
		if v.procoins < amount: return {"error": "You don't have enough marseybux"}, 400
		if amount < 100: return {"error": "You have to gift at least 100 marseybux."}, 400

		log_message = f"@{v.username} has transferred {amount} Marseybux to @{receiver.username}"
		send_repeatable_notification(GIFT_NOTIF_ID, log_message)

		receiver.procoins += amount
		v.procoins -= amount
		send_repeatable_notification(receiver.id, f":marseycapitalistmanlet: @{v.username} has gifted you {amount} marseybux!")
		g.db.add(receiver)
		g.db.add(v)

		g.db.commit()
		return {"message": f"{amount} marseybux transferred!"}, 200

	return {"message": "You can't transfer marseybux to yourself!"}, 400


@app.get("/leaderboard")
@auth_required
def leaderboard(v):

	users = g.db.query(User)

	users1 = users.order_by(User.coins.desc()).limit(25).all()
	sq = g.db.query(User.id, func.rank().over(order_by=User.coins.desc()).label("rank")).subquery()
	pos1 = g.db.query(sq.c.id, sq.c.rank).filter(sq.c.id == v.id).limit(1).one()[1]

	users2 = users.order_by(User.stored_subscriber_count.desc()).limit(25).all()
	sq = g.db.query(User.id, func.rank().over(order_by=User.stored_subscriber_count.desc()).label("rank")).subquery()
	pos2 = g.db.query(sq.c.id, sq.c.rank).filter(sq.c.id == v.id).limit(1).one()[1]

	users3 = users.order_by(User.post_count.desc()).limit(25).all()
	sq = g.db.query(User.id, func.rank().over(order_by=User.post_count.desc()).label("rank")).subquery()
	pos3 = g.db.query(sq.c.id, sq.c.rank).filter(sq.c.id == v.id).limit(1).one()[1]

	users4 = users.order_by(User.comment_count.desc()).limit(25).all()
	sq = g.db.query(User.id, func.rank().over(order_by=User.comment_count.desc()).label("rank")).subquery()
	pos4 = g.db.query(sq.c.id, sq.c.rank).filter(sq.c.id == v.id).limit(1).one()[1]

	users5 = users.order_by(User.received_award_count.desc()).limit(25).all()
	sq = g.db.query(User.id, func.rank().over(order_by=User.received_award_count.desc()).label("rank")).subquery()
	pos5 = g.db.query(sq.c.id, sq.c.rank).filter(sq.c.id == v.id).limit(1).one()[1]

	if request.host == 'pcmemes.net':
		users6 = users.order_by(User.basedcount.desc()).limit(25).all()
		sq = g.db.query(User.id, func.rank().over(order_by=User.basedcount.desc()).label("rank")).subquery()
		pos6 = g.db.query(sq.c.id, sq.c.rank).filter(sq.c.id == v.id).limit(1).one()[1]
	else:
		users6 = None
		pos6 = None

	users7 = users.order_by(User.coins_spent.desc()).limit(25).all()
	sq = g.db.query(User.id, func.rank().over(order_by=User.coins_spent.desc()).label("rank")).subquery()
	pos7 = g.db.query(sq.c.id, sq.c.rank).filter(sq.c.id == v.id).limit(1).one()[1]

	try:
		pos9 = [x[0].id for x in users9].index(v.id)
		pos9 = (pos9+1, users9[pos9][1])
	except: pos9 = (len(users9)+1, 0)

	users10 = users.order_by(User.truecoins.desc()).limit(25).all()
	sq = g.db.query(User.id, func.rank().over(order_by=User.truecoins.desc()).label("rank")).subquery()
	pos10 = g.db.query(sq.c.id, sq.c.rank).filter(sq.c.id == v.id).limit(1).one()[1]

	sq = g.db.query(Badge.user_id, func.count(Badge.user_id).label("count"), func.rank().over(order_by=func.count(Badge.user_id).desc()).label("rank")).group_by(Badge.user_id).subquery()
	users11 = g.db.query(User, sq.c.count).join(sq, User.id==sq.c.user_id).order_by(sq.c.count.desc())
	pos11 = g.db.query(User.id, sq.c.rank, sq.c.count).join(sq, User.id==sq.c.user_id).filter(User.id == v.id).one_or_none()
	if pos11: pos11 = (pos11[1],pos11[2])
	else: pos11 = (users11.count()+1, 0)
	users11 = users11.limit(25).all()

	if pos11[1] < 25 and v not in (x[0] for x in users11):
		pos11 = (26, pos11[1])

	if SITE_NAME == 'rDrama':
		sq = g.db.query(Marsey.author_id, func.count(Marsey.author_id).label("count"), func.rank().over(order_by=func.count(Marsey.author_id).desc()).label("rank")).group_by(Marsey.author_id).subquery()
		users12 = g.db.query(User, sq.c.count).join(sq, User.id==sq.c.author_id).order_by(sq.c.count.desc())
		pos12 = g.db.query(User.id, sq.c.rank, sq.c.count).join(sq, User.id==sq.c.author_id).filter(User.id == v.id).one_or_none()
		if pos12: pos12 = (pos12[1],pos12[2])
		else: pos12 = (users12.count()+1, 0)
		users12 = users12.limit(25).all()
	else:
		users12 = None
		pos12 = None

	try:
		pos13 = [x[0].id for x in users13].index(v.id)
		pos13 = (pos13+1, users13[pos13][1])
	except: pos13 = (len(users13)+1, 0)

	users14 = users.order_by(User.winnings.desc()).limit(25).all()
	sq = g.db.query(User.id, func.rank().over(order_by=User.winnings.desc()).label("rank")).subquery()
	pos14 = g.db.query(sq.c.id, sq.c.rank).filter(sq.c.id == v.id).limit(1).one()[1]

	users15 = users.order_by(User.winnings).limit(25).all()
	sq = g.db.query(User.id, func.rank().over(order_by=User.winnings).label("rank")).subquery()
	pos15 = g.db.query(sq.c.id, sq.c.rank).filter(sq.c.id == v.id).limit(1).one()[1]

	return render_template("leaderboard.html", v=v, users1=users1, pos1=pos1, users2=users2, pos2=pos2, users3=users3, pos3=pos3, users4=users4, pos4=pos4, users5=users5, pos5=pos5, users6=users6, pos6=pos6, users7=users7, pos7=pos7, users9=users9_25, pos9=pos9, users10=users10, pos10=pos10, users11=users11, pos11=pos11, users12=users12, pos12=pos12, users13=users13_25, pos13=pos13, users14=users14, pos14=pos14, users15=users15, pos15=pos15)

@app.get("/@<username>/css")
def get_css(username):
	user = get_user(username)
	resp = make_response(user.css or "")
	resp.headers["Content-Type"] = "text/css"
	resp.headers["Referrer-Policy"] = "no-referrer"
	return resp

@app.get("/@<username>/profilecss")
def get_profilecss(username):
	user = get_user(username)
	if user.profilecss: profilecss = user.profilecss
	else: profilecss = ""
	resp = make_response(profilecss)
	resp.headers["Content-Type"] = "text/css"
	resp.headers["Referrer-Policy"] = "no-referrer"
	return resp

@app.get("/id/<id>/profilecss")
def get_profilecss_id(id):
	user = get_account(id)
	if user.profilecss: profilecss = user.profilecss
	else: profilecss = ""
	resp = make_response(profilecss)
	resp.headers["Content-Type"] = "text/css"
	resp.headers["Referrer-Policy"] = "no-referrer"
	return resp

@app.get("/@<username>/song")
def usersong(username):
	user = get_user(username)
	if user.song: return redirect(f"/song/{user.song}.mp3")
	else: abort(404)

@app.get("/song/<song>")
@app.get("/static/song/<song>")
def song(song):
	resp = make_response(send_from_directory('/songs', song))
	resp.headers.remove("Cache-Control")
	resp.headers.add("Cache-Control", "public, max-age=3153600")
	return resp

@app.post("/subscribe/<post_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def subscribe(v, post_id):
	new_sub = Subscription(user_id=v.id, submission_id=post_id)
	g.db.add(new_sub)
	g.db.commit()
	return {"message": "Post subscribed!"}
	
@app.post("/unsubscribe/<post_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def unsubscribe(v, post_id):
	sub=g.db.query(Subscription).filter_by(user_id=v.id, submission_id=post_id).one_or_none()
	if sub:
		g.db.delete(sub)
		g.db.commit()
	return {"message": "Post unsubscribed!"}

@app.get("/report_bugs")
@auth_required
def reportbugs(v):
	return redirect(f'/post/{BUG_THREAD}')

@app.post("/@<username>/message")
@limiter.limit("1/second;10/minute;20/hour;50/day")
@limiter.limit("1/second;10/minute;20/hour;50/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@is_not_permabanned
def message2(v, username):

	user = get_user(username, v=v)
	if hasattr(user, 'is_blocking') and user.is_blocking: return {"error": "You're blocking this user."}, 403

	if v.admin_level <= 1 and hasattr(user, 'is_blocked') and user.is_blocked:
		return {"error": "This user is blocking you."}, 403

	message = request.values.get("message", "").strip()[:10000].strip()

	if not message: return {"error": "Message is empty!"}

	if 'linkedin.com' in message: return {"error": "This domain 'linkedin.com' is banned."}, 403

	body_html = sanitize(message)

	existing = g.db.query(Comment.id).filter(Comment.author_id == v.id,
															Comment.sentto == user.id,
															Comment.body_html == body_html,
															).one_or_none()

	if existing: return {"error": "Message already exists."}, 403

	c = Comment(author_id=v.id,
						  parent_submission=None,
						  level=1,
						  sentto=user.id,
						  body_html=body_html
						  )
	g.db.add(c)

	g.db.flush()

	if blackjack and any(i in c.body_html.lower() for i in blackjack.split()):
		v.shadowbanned = 'AutoJanny'
		g.db.add(v)
		notif = g.db.query(Notification).filter_by(comment_id=c.id, user_id=CARP_ID).one_or_none()
		if not notif:
			notif = Notification(comment_id=c.id, user_id=CARP_ID)
			g.db.add(notif)
			g.db.flush()

	c.top_comment_id = c.id

	notif = g.db.query(Notification).filter_by(comment_id=c.id, user_id=user.id).one_or_none()
	if not notif:
		notif = Notification(comment_id=c.id, user_id=user.id)
		g.db.add(notif)

	g.db.commit()

	if PUSHER_ID != 'blahblahblah' and not v.shadowbanned:
		if len(message) > 500: notifbody = message[:500] + '...'
		else: notifbody = message

		try: gevent.spawn(pusher_thread2, f'{request.host}{user.id}', notifbody, v.username)
		except: pass

	return {"message": "Message sent!"}


@app.post("/reply")
@limiter.limit("1/second;6/minute;50/hour;200/day")
@limiter.limit("1/second;6/minute;50/hour;200/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def messagereply(v):

	message = request.values.get("body", "").strip()[:10000].strip()

	if not message and not request.files.get("file"): return {"error": "Message is empty!"}

	if 'linkedin.com' in message: return {"error": "this domain 'linkedin.com' is banned"}

	id = int(request.values.get("parent_id"))
	parent = get_comment(id, v=v)
	user_id = parent.author.id

	if parent.sentto == 2: user_id = None
	elif v.id == user_id: user_id = parent.sentto

	body_html = sanitize(message)

	if parent.sentto == 2 and request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
		file=request.files["file"]
		if file.content_type.startswith('image/'):
			name = f'/images/{time.time()}'.replace('.','') + '.webp'
			file.save(name)
			url = process_image(v.patron, name)
			body_html += f'<img data-bs-target="#expandImageModal" data-bs-toggle="modal" onclick="expandDesktopImage(this.src)" class="img" src="{url}" loading="lazy">'
		elif file.content_type.startswith('video/'):
			if file.content_type == 'video/webm':
				file.save("video.mp4")
			else:
				file.save("unsanitized.mp4")
				os.system(f'ffmpeg -y -loglevel warning -i unsanitized.mp4 -map_metadata -1 -c:v copy -c:a copy video.mp4')
			with open("video.mp4", 'rb') as f:
				try: req = requests.request("POST", "https://pomf2.lain.la/upload.php", files={'files[]': f}, timeout=5).json()
				except requests.exceptions.ConnectionError: return {"error": "Video upload timed out, please try again!"}
				try: url = req['files'][0]['url']
				except: return {"error": req['description']}, 400
			body_html += f"<p>{url}</p>"
		else: return {"error": "Image/Video files only"}, 400


	c = Comment(author_id=v.id,
							parent_submission=None,
							parent_comment_id=id,
							top_comment_id=parent.top_comment_id,
							level=parent.level + 1,
							sentto=user_id,
							body_html=body_html,
							)
	g.db.add(c)
	g.db.flush()

	if blackjack and any(i in c.body_html.lower() for i in blackjack.split()):
		v.shadowbanned = 'AutoJanny'
		g.db.add(v)
		notif = g.db.query(Notification).filter_by(comment_id=c.id, user_id=CARP_ID).one_or_none()
		if not notif:
			notif = Notification(comment_id=c.id, user_id=CARP_ID)
			g.db.add(notif)
			g.db.flush()

	if user_id and user_id != v.id and user_id != 2:
		notif = g.db.query(Notification).filter_by(comment_id=c.id, user_id=user_id).one_or_none()
		if not notif:
			notif = Notification(comment_id=c.id, user_id=user_id)
			g.db.add(notif)
			ids = [c.top_comment.id] + [x.id for x in c.top_comment.replies]
			notifications = g.db.query(Notification).filter(Notification.comment_id.in_(ids), Notification.user_id == user_id)
			for n in notifications:
				g.db.delete(n)

		if PUSHER_ID != 'blahblahblah' and not v.shadowbanned:
			if len(message) > 500: notifbody = message[:500] + '...'
			else: notifbody = message
			
			beams_client.publish_to_interests(
				interests=[f'{request.host}{user_id}'],
				publish_body={
					'web': {
						'notification': {
							'title': f'New message from @{v.username}',
							'body': notifbody,
							'deep_link': f'{SITE_FULL}/notifications?messages=true',
							'icon': f'{SITE_FULL}/assets/images/{SITE_NAME}/icon.webp"a=1015',
						}
					},
					'fcm': {
						'notification': {
							'title': f'New message from @{v.username}',
							'body': notifbody,
						},
						'data': {
							'url': '/notifications?messages=true',
						}
					}
				},
			)


	if c.top_comment.sentto == 2:
		admins = g.db.query(User).filter(User.admin_level > 2, User.id != v.id).all()
		for admin in admins:
			notif = Notification(comment_id=c.id, user_id=admin.id)
			g.db.add(notif)

		ids = [c.top_comment.id] + [x.id for x in c.top_comment.replies]
		uids = [x.id for x in admins]
		notifications = g.db.query(Notification).filter(Notification.comment_id.in_(ids), Notification.user_id.in_(uids))
		for n in notifications:
			g.db.delete(n)

	g.db.commit()

	return {"comment": render_template("comments.html", v=v, comments=[c], ajax=True)}

@app.get("/2faqr/<secret>")
@auth_required
def mfa_qr(secret, v):
	x = pyotp.TOTP(secret)
	qr = qrcode.QRCode(
		error_correction=qrcode.constants.ERROR_CORRECT_L
	)
	qr.add_data(x.provisioning_uri(v.username, issuer_name=app.config["SITE_NAME"]))
	img = qr.make_image(fill_color="#000000", back_color="white")

	mem = io.BytesIO()

	img.save(mem, format="PNG")
	mem.seek(0, 0)

	try: f = send_file(mem, mimetype="image/png", as_attachment=False)
	except:
		print('/2faqr/<secret>', flush=True)
		abort(404)
	return f


@app.get("/is_available/<name>")
def api_is_available(name):

	name=name.strip()

	if len(name)<3 or len(name)>25:
		return {name:False}
		
	name2 = name.replace('\\', '').replace('_','\_').replace('%','')

	x= g.db.query(User).filter(
		or_(
			User.username.ilike(name2),
			User.original_username.ilike(name2)
			)
		).one_or_none()

	if x:
		return {name: False}
	else:
		return {name: True}

@app.get("/id/<id>")
@auth_required
def user_id(id, v):
	user = get_account(id)
	return redirect(user.url)
		
@app.get("/u/<username>")
@auth_required
def redditor_moment_redirect(username, v):
	return redirect(f"/@{username}")

@app.get("/@<username>/followers")
@auth_required
def followers(username, v):
	u = get_user(username, v=v)
	users = g.db.query(User).join(Follow, Follow.target_id == u.id).filter(Follow.user_id == User.id).order_by(Follow.created_utc).all()
	return render_template("followers.html", v=v, u=u, users=users)

@app.get("/@<username>/following")
@auth_required
def following(username, v):
	u = get_user(username, v=v)
	users = g.db.query(User).join(Follow, Follow.user_id == u.id).filter(Follow.target_id == User.id).order_by(Follow.created_utc).all()
	return render_template("following.html", v=v, u=u, users=users)

@app.get("/views")
@auth_required
def visitors(v):
	if v.admin_level < 2 and not v.patron: return render_template("errors/patron.html", v=v)
	viewers=sorted(v.viewers, key = lambda x: x.last_view_utc, reverse=True)
	return render_template("viewers.html", v=v, viewers=viewers)


@app.get("/@<username>")
@app.get("/logged_out/@<username>")
@auth_desired
def u_username(username, v=None):

	if not v and not request.path.startswith('/logged_out'): return redirect(f"/logged_out{request.full_path}")
	if v and request.path.startswith('/logged_out'): return redirect(request.full_path.replace('/logged_out',''))

	u = get_user(username, v=v)


	if username != u.username:
		return redirect(SITE_FULL + request.full_path.replace(username, u.username)[:-1])

	if u.reserved:
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": f"That username is reserved for: {u.reserved}"}
		return render_template("userpage_reserved.html", u=u, v=v)

	if v and v.id not in (u.id,DAD_ID) and (u.patron or u.admin_level > 1):
		view = g.db.query(ViewerRelationship).filter_by(viewer_id=v.id, user_id=u.id).one_or_none()

		if view: view.last_view_utc = int(time.time())
		else: view = ViewerRelationship(viewer_id=v.id, user_id=u.id)

		g.db.add(view)
		g.db.commit()

		
	if u.is_private and (not v or (v.id != u.id and v.admin_level < 2 and not v.eye)):
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": "That userpage is private"}
		return render_template("userpage_private.html", u=u, v=v)

	
	if v and hasattr(u, 'is_blocking') and u.is_blocking:
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": f"You are blocking @{u.username}."}
		return render_template("userpage_blocking.html", u=u, v=v)


	if v and v.admin_level < 2 and hasattr(u, 'is_blocked') and u.is_blocked:
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": "This person is blocking you."}
		return render_template("userpage_blocked.html", u=u, v=v)


	sort = request.values.get("sort", "new")
	t = request.values.get("t", "all")
	try: page = max(int(request.values.get("page", 1)), 1)
	except: page = 1

	ids = u.userpagelisting(site=SITE, v=v, page=page, sort=sort, t=t)

	next_exists = (len(ids) > 25)
	ids = ids[:25]

	if page == 1:
		sticky = []
		sticky = g.db.query(Submission).filter_by(is_pinned=True, author_id=u.id).all()
		if sticky:
			for p in sticky:
				ids = [p.id] + ids

	listing = get_posts(ids, v=v)

	if u.unban_utc:
		if request.headers.get("Authorization"): {"data": [x.json for x in listing]}
		return render_template("userpage.html",
												unban=u.unban_string,
												u=u,
												v=v,
												listing=listing,
												page=page,
												sort=sort,
												t=t,
												next_exists=next_exists,
												is_following=(v and u.has_follower(v)))



	if request.headers.get("Authorization"): return {"data": [x.json for x in listing]}
	return render_template("userpage.html",
									u=u,
									v=v,
									listing=listing,
									page=page,
									sort=sort,
									t=t,
									next_exists=next_exists,
									is_following=(v and u.has_follower(v)))


@app.get("/@<username>/comments")
@app.get("/logged_out/@<username>/comments")
@auth_desired
def u_username_comments(username, v=None):

	if not v and not request.path.startswith('/logged_out'): return redirect(f"/logged_out{request.full_path}")
	if v and request.path.startswith('/logged_out'): return redirect(request.full_path.replace('/logged_out',''))

	user = get_user(username, v=v)

	if username != user.username: return redirect(f'/@{user.username}/comments')

	u = user

	if u.reserved:
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": f"That username is reserved for: {u.reserved}"}
		return render_template("userpage_reserved.html",
												u=u,
												v=v)


	if u.is_private and (not v or (v.id != u.id and v.admin_level < 2 and not v.eye)):
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": "That userpage is private"}
		return render_template("userpage_private.html", u=u, v=v)

	if v and hasattr(u, 'is_blocking') and u.is_blocking:
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": f"You are blocking @{u.username}."}
		return render_template("userpage_blocking.html", u=u, v=v)

	if v and v.admin_level < 2 and hasattr(u, 'is_blocked') and u.is_blocked:
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": "This person is blocking you."}
		return render_template("userpage_blocked.html", u=u, v=v)


	try: page = max(int(request.values.get("page", "1")), 1)
	except: page = 1
	
	sort=request.values.get("sort","new")
	t=request.values.get("t","all")


	comments = g.db.query(Comment.id).filter(Comment.author_id == u.id, Comment.parent_submission != None)

	if not v or (v.id != u.id and v.admin_level < 2):
		comments = comments.filter(Comment.deleted_utc == 0, Comment.is_banned == False, Comment.ghost == False)

	now = int(time.time())
	if t == 'hour':
		cutoff = now - 3600
	elif t == 'day':
		cutoff = now - 86400
	elif t == 'week':
		cutoff = now - 604800
	elif t == 'month':
		cutoff = now - 2592000
	elif t == 'year':
		cutoff = now - 31536000
	else:
		cutoff = 0
	comments = comments.filter(Comment.created_utc >= cutoff)

	if sort == "new":
		comments = comments.order_by(Comment.created_utc.desc())
	elif sort == "old":
		comments = comments.order_by(Comment.created_utc)
	elif sort == "controversial":
		comments = comments.order_by((Comment.upvotes+1)/(Comment.downvotes+1) + (Comment.downvotes+1)/(Comment.upvotes+1), Comment.downvotes.desc())
	elif sort == "top":
		comments = comments.order_by(Comment.downvotes - Comment.upvotes)
	elif sort == "bottom":
		comments = comments.order_by(Comment.upvotes - Comment.downvotes)

	comments = comments.offset(25 * (page - 1)).limit(26).all()
	ids = [x.id for x in comments]

	next_exists = (len(ids) > 25)
	ids = ids[:25]

	listing = get_comments(ids, v=v)

	is_following = (v and user.has_follower(v))

	if request.headers.get("Authorization"): return {"data": [c.json for c in listing]}
	return render_template("userpage_comments.html", u=user, v=v, listing=listing, page=page, sort=sort, t=t,next_exists=next_exists, is_following=is_following, standalone=True)


@app.get("/@<username>/info")
@auth_required
def u_username_info(username, v=None):

	user=get_user(username, v=v)

	if hasattr(user, 'is_blocking') and user.is_blocking:
		return {"error": "You're blocking this user."}, 401
	elif hasattr(user, 'is_blocked') and user.is_blocked:
		return {"error": "This user is blocking you."}, 403

	return user.json

@app.get("/<id>/info")
@auth_required
def u_user_id_info(id, v=None):

	user=get_account(id, v=v)

	if hasattr(user, 'is_blocking') and user.is_blocking:
		return {"error": "You're blocking this user."}, 401
	elif hasattr(user, 'is_blocked') and user.is_blocked:
		return {"error": "This user is blocking you."}, 403

	return user.json

@app.post("/follow/<username>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def follow_user(username, v):

	target = get_user(username)

	if target.id==v.id: return {"error": "You can't follow yourself!"}, 400

	if g.db.query(Follow).filter_by(user_id=v.id, target_id=target.id).one_or_none(): return {"message": "User followed!"}

	new_follow = Follow(user_id=v.id, target_id=target.id)
	g.db.add(new_follow)

	g.db.flush()
	target.stored_subscriber_count = g.db.query(Follow).filter_by(target_id=target.id).count()
	g.db.add(target)

	send_notification(target.id, f"@{v.username} has followed you!")

	g.db.commit()

	return {"message": "User followed!"}

@app.post("/unfollow/<username>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def unfollow_user(username, v):

	target = get_user(username)

	if target.fish:
		send_notification(target.id, f"@{v.username} has tried to unfollow you and failed because of your fish award!")
		g.db.commit()
		return {"error": "You can't unfollow this user!"}

	follow = g.db.query(Follow).filter_by(user_id=v.id, target_id=target.id).one_or_none()

	if follow:
		g.db.delete(follow)
		
		g.db.flush()
		target.stored_subscriber_count = g.db.query(Follow).filter_by(target_id=target.id).count()
		g.db.add(target)

		send_notification(target.id, f"@{v.username} has unfollowed you!")

		g.db.commit()

	return {"message": "User unfollowed!"}

@app.post("/remove_follow/<username>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def remove_follow(username, v):
	target = get_user(username)

	follow = g.db.query(Follow).filter_by(user_id=target.id, target_id=v.id).one_or_none()

	if not follow: return {"message": "Follower removed!"}

	g.db.delete(follow)
	
	g.db.flush()
	v.stored_subscriber_count = g.db.query(Follow).filter_by(target_id=v.id).count()
	g.db.add(v)

	send_repeatable_notification(target.id, f"@{v.username} has removed your follow!")

	g.db.commit()

	return {"message": "Follower removed!"}

@app.get("/pp/<id>")
@app.get("/uid/<id>/pic")
@app.get("/uid/<id>/pic/profile")
@app.get("/logged_out/pp/<id>")
@app.get("/logged_out/uid/<id>/pic")
@app.get("/logged_out/uid/<id>/pic/profile")
@limiter.exempt
@auth_desired
def user_profile_uid(v, id):
	if not v and not request.path.startswith('/logged_out'): return redirect(f"/logged_out{request.full_path}")
	if v and request.path.startswith('/logged_out'): return redirect(request.full_path.replace('/logged_out',''))

	try: id = int(id)
	except:
		try: id = int(id, 36)
		except: abort(404)

	x=get_account(id)
	return redirect(x.profile_url)

@app.get("/@<username>/pic")
@limiter.exempt
@auth_required
def user_profile_name(v, username):
	x = get_user(username)
	return redirect(x.profile_url)

@app.get("/@<username>/saved/posts")
@auth_required
def saved_posts(v, username):

	page=int(request.values.get("page",1))

	ids=v.saved_idlist(page=page)

	next_exists=len(ids)>25

	ids=ids[:25]

	listing = get_posts(ids, v=v)

	if request.headers.get("Authorization"): return {"data": [x.json for x in listing]}
	return render_template("userpage.html",
											u=v,
											v=v,
											listing=listing,
											page=page,
											next_exists=next_exists,
											)


@app.get("/@<username>/saved/comments")
@auth_required
def saved_comments(v, username):

	page=int(request.values.get("page",1))

	ids=v.saved_comment_idlist(page=page)

	next_exists=len(ids) > 25

	ids=ids[:25]

	listing = get_comments(ids, v=v)


	if request.headers.get("Authorization"): return {"data": [x.json for x in listing]}
	return render_template("userpage_comments.html",
											u=v,
											v=v,
											listing=listing,
											page=page,
											next_exists=next_exists,
											standalone=True)


@app.post("/fp/<fp>")
@auth_required
def fp(v, fp):
	v.fp = fp
	users = g.db.query(User).filter(User.fp == fp, User.id != v.id).all()
	if users: print(f'{v.username}: fp')
	if v.email and v.is_activated:
		alts = g.db.query(User).filter(User.email == v.email, User.is_activated, User.id != v.id).all()
		if alts:
			print(f'{v.username}: email')
			users += alts
	for u in users:
		li = [v.id, u.id]
		existing = g.db.query(Alt).filter(Alt.user1.in_(li), Alt.user2.in_(li)).one_or_none()
		if existing: continue
		new_alt = Alt(user1=v.id, user2=u.id)
		g.db.add(new_alt)
		g.db.flush()
		print(v.username + ' + ' + u.username)
	g.db.add(v)
	g.db.commit()
	return '', 204