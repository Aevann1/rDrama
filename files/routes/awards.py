from files.__main__ import app
from files.helpers.wrappers import *
from files.helpers.alerts import *
from files.helpers.get import *
from files.helpers.const import *
from files.classes.award import *
from flask import g, request

@app.get("/shop")
@app.get("/settings/shop")
@auth_required
def shop(v):
	if site_name == "Drama":
		AWARDS = {
			"ban": {
				"kind": "ban",
				"title": "One-Day Ban",
				"description": "Bans the author for a day.",
				"icon": "fas fa-gavel",
				"color": "text-danger",
				"price": 5000
			},
			"shit": {
				"kind": "shit",
				"title": "Shit",
				"description": "Makes flies swarm a post.",
				"icon": "fas fa-poop",
				"color": "text-black-50",
				"price": 1000
			},
			"fireflies": {
				"kind": "fireflies",
				"title": "Fireflies",
				"description": "Puts stars on the post.",
				"icon": "fas fa-sparkles",
				"color": "text-warning",
				"price": 1000
			}
		}
	else:
		AWARDS = {
			"shit": {
				"kind": "shit",
				"title": "Shit",
				"description": "Makes flies swarm a post.",
				"icon": "fas fa-poop",
				"color": "text-black-50",
				"price": 1000
			},
			"fireflies": {
				"kind": "fireflies",
				"title": "Fireflies",
				"description": "Puts stars on the post.",
				"icon": "fas fa-sparkles",
				"color": "text-warning",
				"price": 1000
			}
		}

	query = g.db.query(
	User.id, User.username, User.patron, User.namecolor,
	AwardRelationship.kind.label('last_award_kind'), func.count(AwardRelationship.id).label('last_award_count')
	).filter(AwardRelationship.submission_id==None, AwardRelationship.comment_id==None, User.patron > 0) \
	.group_by(User.username, User.patron, User.id, User.namecolor, AwardRelationship.kind) \
	.order_by(User.patron.desc(), AwardRelationship.kind.desc()) \
	.join(User).filter(User.id == v.id).all()

	owned = []
	for row in (r._asdict() for r in query):
		kind = row['last_award_kind']
		if kind in AWARDS.keys():
			award = AWARDS[kind]
			award["owned_num"] = row['last_award_count']
			owned.append(award)

	if v.patron:
		for val in AWARDS.values():
			if v.patron == 1: val["price"] = int(val["price"]*0.90)
			elif v.patron == 2: val["price"] = int(val["price"]*0.85)
			elif v.patron == 3: val["price"] = int(val["price"]*0.80)
			elif v.patron == 4: val["price"] = int(val["price"]*0.75)
			else: val["price"] = int(val["price"]*0.70)

	return render_template("settings_shop.html", owned=owned, awards=list(AWARDS.values()), v=v)


@app.post("/buy/<award>")
@auth_required
def buy(v, award):
	if site_name == "Drama":
		AWARDS = {
			"ban": {
				"kind": "ban",
				"title": "One-Day Ban",
				"description": "Bans the author for a day.",
				"icon": "fas fa-gavel",
				"color": "text-danger",
				"price": 5000
			},
			"shit": {
				"kind": "shit",
				"title": "Shit",
				"description": "Makes flies swarm a post.",
				"icon": "fas fa-poop",
				"color": "text-black-50",
				"price": 1000
			},
			"fireflies": {
				"kind": "fireflies",
				"title": "Fireflies",
				"description": "Puts stars on the post.",
				"icon": "fas fa-sparkles",
				"color": "text-warning",
				"price": 1000
			}
		}
	else:
		AWARDS = {
			"shit": {
				"kind": "shit",
				"title": "Shit",
				"description": "Makes flies swarm a post.",
				"icon": "fas fa-poop",
				"color": "text-black-50",
				"price": 1000
			},
			"fireflies": {
				"kind": "fireflies",
				"title": "Fireflies",
				"description": "Puts stars on the post.",
				"icon": "fas fa-sparkles",
				"color": "text-warning",
				"price": 1000
			}
		}

	if award not in AWARDS: abort(400)
	price = AWARDS[award]["price"]
	if v.patron:
		if v.patron == 1: price = int(price*0.90)
		elif v.patron == 2: price = int(price*0.85)
		elif v.patron == 3: price = int(price*0.80)
		elif v.patron == 4: price = int(price*0.75)
		else: price = int(price*0.70)

	if v.coins < price: return {"error": "Not enough coins."}, 400
	v.coins -= price
	g.db.add(v)

	thing = g.db.query(AwardRelationship).order_by(AwardRelationship.id.desc()).first().id
	thing += 1

	award = AwardRelationship(id=thing, user_id=v.id, kind=award)
	g.db.add(award)

	g.db.commit()

	return {"message": "Award bought!"}


def banaward_trigger(post=None, comment=None):

	author = post.author if post else comment.author
	link = f"[this post]({post.permalink})" if post else f"[this comment]({comment.permalink})"

	if not author.is_suspended:
		author.ban(reason="one-day ban award used", days=1)

		send_notification(NOTIFICATIONS_ACCOUNT, author, f"Your account has been suspended for a day for {link}. It sucked and you should feel bad.")
	elif author.unban_utc > 0:
		author.unban_utc += 24*60*60
		g.db.add(author)

		send_notification(NOTIFICATIONS_ACCOUNT, author, f"Your account has been suspended for yet another day for {link}. Seriously man?")


ACTIONS = {
	"ban": banaward_trigger
}

ALLOW_MULTIPLE = (
	"ban",
	"shit",
	"fireflies"
)

@app.post("/post/<pid>/awards")
@auth_required
def award_post(pid, v):

	if v.is_suspended and v.unban_utc == 0: return {"error": "forbidden."}, 403

	kind = request.values.get("kind", "")
	
	if kind not in AWARDS:
		return {"error": "That award doesn't exist."}, 404

	post_award = g.db.query(AwardRelationship).options(lazyload('*')).filter(
		and_(
			AwardRelationship.kind == kind,
			AwardRelationship.user_id == v.id,
			AwardRelationship.submission_id == None,
			AwardRelationship.comment_id == None
		)
	).first()

	if not post_award:
		return {"error": "You don't have that award."}, 404

	post = g.db.query(Submission).options(lazyload('*')).filter_by(id=pid).first()

	if not post or post.is_banned or post.deleted_utc > 0:
		return {"error": "That post doesn't exist or has been deleted or removed."}, 404

	if post.author_id == v.id:
		return {"error": "You can't award yourself."}, 403

	existing_award = g.db.query(AwardRelationship).options(lazyload('*')).filter(
		and_(
			AwardRelationship.submission_id == post.id,
			AwardRelationship.user_id == v.id,
			AwardRelationship.kind == kind
		)
	).first()

	if existing_award and kind not in ALLOW_MULTIPLE:
		return {"error": "You can't give that award multiple times to the same post."}, 409

	post_award.submission_id = post.id
	#print(f"give award to pid {post_award.submission_id} ({post.id})")
	g.db.add(post_award)

	msg = f"@{v.username} has given your [post]({post.permalink}) the {AWARDS[kind]['title']} Award!"

	note = request.values.get("note", "")
	if note:
		msg += f"\n\n> {note}"

	send_notification(NOTIFICATIONS_ACCOUNT, post.author, msg)

	if kind in ACTIONS: ACTIONS[kind](post=post)

	post.author.received_award_count += 1
	g.db.add(post.author)

	g.db.commit()
	if request.referrer: return redirect(request.referrer)
	else: return redirect("/")


@app.post("/comment/<cid>/awards")
@auth_required
def award_comment(cid, v):

	if v.is_suspended and v.unban_utc == 0: return {"error": "forbidden"}, 403

	kind = request.values.get("kind", "")

	if kind not in AWARDS:
		return {"error": "That award doesn't exist."}, 404

	comment_award = g.db.query(AwardRelationship).options(lazyload('*')).filter(
		and_(
			AwardRelationship.kind == kind,
			AwardRelationship.user_id == v.id,
			AwardRelationship.submission_id == None,
			AwardRelationship.comment_id == None
		)
	).first()

	if not comment_award:
		return {"error": "You don't have that award."}, 404

	c = g.db.query(Comment).options(lazyload('*')).filter_by(id=cid).first()

	if not c or c.is_banned or c.deleted_utc > 0:
		return {"error": "That comment doesn't exist or has been deleted or removed."}, 404

	if c.author_id == v.id:
		return {"error": "You can't award yourself."}, 403

	existing_award = g.db.query(AwardRelationship).options(lazyload('*')).filter(
		and_(
			AwardRelationship.comment_id == c.id,
			AwardRelationship.user_id == v.id,
			AwardRelationship.kind == kind
		)
	).first()

	if existing_award and kind not in ALLOW_MULTIPLE:
		return {"error": "You can't give that award multiple times to the same comment."}, 409

	comment_award.comment_id = c.id
	g.db.add(comment_award)

	msg = f"@{v.username} has given your [comment]({c.permalink}) the {AWARDS[kind]['title']} Award!"

	note = request.values.get("note", "")
	if note:
		msg += f"\n\n> {note}"

	send_notification(NOTIFICATIONS_ACCOUNT, c.author, msg)

	if kind in ACTIONS:
		ACTIONS[kind](comment=c)

	c.author.received_award_count += 1
	g.db.add(c.author)

	g.db.commit()
	return redirect(request.referrer)

@app.get("/admin/user_award")
@auth_required
def admin_userawards_get(v):

	if v.admin_level < 6:
		abort(403)

	return render_template("admin/user_award.html", awards=list(AWARDS.values()), v=v)

@app.post("/admin/user_award")
@auth_required
@validate_formkey
def admin_userawards_post(v):

	if v.admin_level < 6:
		abort(403)

	u = get_user(request.values.get("username", '1'), graceful=False, v=v)

	notify_awards = {}

	latest = g.db.query(AwardRelationship).order_by(AwardRelationship.id.desc()).first()
	thing = latest.id

	for key, value in request.values.items():
		if key not in AWARDS:
			continue

		if value:

			if int(value) > 0:
				notify_awards[key] = int(value)

			for x in range(int(value)):
				thing += 1

				award = AwardRelationship(
					id=thing,
					user_id=u.id,
					kind=key
				)

				g.db.add(award)

	text = "You were given the following awards:\n\n"

	for key, value in notify_awards.items():
		text += f" - **{value}** {AWARDS[key]['title']} {'Awards' if value != 1 else 'Award'}\n"

	send_notification(NOTIFICATIONS_ACCOUNT, u, text)

	g.db.commit()

	return render_template("admin/user_award.html", awards=list(AWARDS.values()), v=v)