from files.__main__ import app, limiter
from files.helpers.wrappers import *
from files.helpers.alerts import *
from files.helpers.get import *
from files.helpers.const import *
from files.classes.award import *
from .front import frontlist
from flask import g, request
from files.helpers.sanitize import filter_title

discounts = {
	69: 0.02,
	70: 0.04,
	71: 0.06,
	72: 0.08,
	73: 0.10,
}

AWARDS2 = {
	"ban": {
		"kind": "ban",
		"title": "1-Day Ban",
		"description": "Bans the recipient for a day.",
		"icon": "fas fa-gavel",
		"color": "text-danger",
		"price": 3000
	},
	"fireflies": {
		"kind": "fireflies",
		"title": "Fireflies",
		"description": "Makes fireflies swarm the post.",
		"icon": "fas fa-sparkles",
		"color": "text-warning",
		"price": 500
	},
	"shit": {
		"kind": "shit",
		"title": "Shit",
		"description": "Makes flies swarm the post.",
		"icon": "fas fa-poop",
		"color": "text-black-50",
		"price": 500
	},
}

@app.get("/shop")
@app.get("/settings/shop")
@auth_required
def shop(v):
	AWARDS = {
		"shit": {
			"kind": "shit",
			"title": "Shit",
			"description": "Makes flies swarm the post.",
			"icon": "fas fa-poop",
			"color": "text-black-50",
			"owned": 0,
			"price": 500,
			"MB": True
		},
		"fireflies": {
			"kind": "fireflies",
			"title": "Fireflies",
			"description": "Makes fireflies swarm the post.",
			"icon": "fas fa-sparkles",
			"color": "text-warning",
			"owned": 0,
			"price": 500,
			"MB": True
		},
		"train": {
			"kind": "train",
			"title": "Train",
			"description": "Summons a train on the post.",
			"icon": "fas fa-train",
			"color": "text-pink",
			"owned": 0,
			"price": 500,
			"MB": True
		},
		"pin": {
			"kind": "pin",
			"title": "1-Hour Pin",
			"description": "Pins the post/comment.",
			"icon": "fas fa-thumbtack fa-rotate--45",
			"color": "text-warning",
			"owned": 0,
			"price": 750,
			"MB": True
		},
		"unpin": {
			"kind": "unpin",
			"title": "1-Hour Unpin",
			"description": "Removes 1 hour from the pin duration of the post/comment.",
			"icon": "fas fa-thumbtack fa-rotate--45",
			"color": "text-black",
			"owned": 0,
			"price": 1000,
			"MB": True
		},
		"pizzashill": {
			"kind": "pizzashill",
			"title": "Pizzashill",
			"description": "Forces the recipient to make all posts/comments > 280 characters for 24 hours.",
			"icon": "fas fa-pizza-slice",
			"color": "text-orange",
			"owned": 0,
			"price": 1000,
			"MB": True
		},
		"flairlock": {
			"kind": "flairlock",
			"title": "1-Day Flairlock",
			"description": "Sets a flair for the recipient and locks it or 24 hours.",
			"icon": "fas fa-lock",
			"color": "text-black",
			"owned": 0,
			"price": 1250,
			"MB": True
		},
		"agendaposter": {
			"kind": "agendaposter",
			"title": "Agendaposter",
			"description": "Forces the agendaposter theme on the recipient for 24 hours.",
			"icon": "fas fa-snooze",
			"color": "text-purple",
			"owned": 0,
			"price": 2500,
			"MB": True
		},
		"marsey": {
			"kind": "marsey",
			"title": "Marsey",
			"description": "Makes the recipient unable to post/comment anything but marsey emojis for 24 hours.",
			"icon": "fas fa-cat",
			"color": "text-orange",
			"owned": 0,
			"price": 3000,
			"MB": True
		},
		"ban": {
			"kind": "ban",
			"title": "1-Day Ban",
			"description": "Bans the recipient for a day.",
			"icon": "fas fa-gavel",
			"color": "text-danger",
			"owned": 0,
			"price": 3000,
			"MB": True
		},
		"unban": {
			"kind": "unban",
			"title": "1-Day Unban",
			"description": "Removes 1 day from the ban duration of the recipient.",
			"icon": "fas fa-gavel",
			"color": "text-success",
			"owned": 0,
			"price": 3500,
			"MB": True
		},
		"grass": {
			"kind": "grass",
			"title": "Grass",
			"description": "Ban the recipient permanently (must provide a timestamped picture of them touching grass to the admins to get unbanned)",
			"icon": "fas fa-seedling",
			"color": "text-success",
			"owned": 0,
			"price": 10000,
			"MB": False
		},
		"eye": {
			"kind": "eye",
			"title": "All-Seeing Eye",
			"description": "Gives the recipient the ability to view private profiles.",
			"icon": "fas fa-eye",
			"color": "text-silver",
			"owned": 0,
			"price": 10000,
			"MB": False
		},
		"pause": {
			"kind": "pause",
			"title": "Pause",
			"description": "Gives the recipient the ability to pause profile anthems.",
			"icon": "fas fa-volume-mute",
			"color": "text-danger",
			"owned": 0,
			"price": 20000,
			"MB": False
		},
		"unpausable": {
			"kind": "unpausable",
			"title": "Unpausable",
			"description": "Makes the profile anthem of the recipient unpausable.",
			"icon": "fas fa-volume",
			"color": "text-success",
			"owned": 0,
			"price": 40000,
			"MB": False
		},
		"alt": {
			"kind": "alt",
			"title": "Alt-Seeing Eye",
			"description": "Gives the recipient the ability to view alts.",
			"icon": "fas fa-eye",
			"color": "text-gold",
			"owned": 0,
			"price": 50000,
			"MB": False
		},
	}

	for useraward in g.db.query(AwardRelationship).filter(AwardRelationship.user_id == v.id, AwardRelationship.submission_id == None, AwardRelationship.comment_id == None).all():
		if useraward.kind in AWARDS: AWARDS[useraward.kind]["owned"] += 1

	if v.patron == 1: discount = 0.90
	elif v.patron == 2: discount = 0.85
	elif v.patron == 3: discount = 0.80
	elif v.patron == 4: discount = 0.75
	elif v.patron == 5: discount = 0.70
	else: discount = 1

	for badge in [69,70,71,72,73]:
		if v.has_badge(badge): discount -= discounts[badge]

	for val in AWARDS.values():
		val["price"] = int(val["price"]*discount)

	sales = g.db.query(Vote.id).count() + g.db.query(CommentVote.id).count() - g.db.query(func.sum(User.coins)).scalar()
	return render_template("shop.html", awards=list(AWARDS.values()), v=v, sales=sales)


@app.post("/buy/<award>")
@auth_required
def buy(v, award):
	AWARDS = {
		"shit": {
			"kind": "shit",
			"title": "Shit",
			"description": "Makes flies swarm the post.",
			"icon": "fas fa-poop",
			"color": "text-black-50",
			"price": 500
		},
		"fireflies": {
			"kind": "fireflies",
			"title": "Fireflies",
			"description": "Makes fireflies swarm the post.",
			"icon": "fas fa-sparkles",
			"color": "text-warning",
			"price": 500
		},
		"train": {
			"kind": "train",
			"title": "Train",
			"description": "Summons a train on the post.",
			"icon": "fas fa-train",
			"color": "text-pink",
			"price": 500
		},
		"pin": {
			"kind": "pin",
			"title": "1-Hour Pin",
			"description": "Pins the post/comment.",
			"icon": "fas fa-thumbtack fa-rotate--45",
			"color": "text-warning",
			"price": 750
		},
		"unpin": {
			"kind": "unpin",
			"title": "1-Hour Unpin",
			"description": "Removes 1 hour from the pin duration of the post/comment.",
			"icon": "fas fa-thumbtack fa-rotate--45",
			"color": "text-black",
			"price": 1000
		},
		"pizzashill": {
			"kind": "pizzashill",
			"title": "Pizzashill",
			"description": "Forces the recipient to make all posts/comments > 280 characters for 24 hours.",
			"icon": "fas fa-pizza-slice",
			"color": "text-orange",
			"price": 1000,
		},
		"flairlock": {
			"kind": "flairlock",
			"title": "1-Day Flairlock",
			"description": "Sets a flair for the recipient and locks it or 24 hours.",
			"icon": "fas fa-lock",
			"color": "text-black",
			"price": 1250
		},
		"agendaposter": {
			"kind": "agendaposter",
			"title": "Agendaposter",
			"description": "Forces the agendaposter theme on the recipient for 24 hours.",
			"icon": "fas fa-snooze",
			"color": "text-purple",
			"price": 2500
		},
		"marsey": {
			"kind": "marsey",
			"title": "Marsey",
			"description": "Makes the recipient unable to post/comment anything but marsey emojis for 24 hours.",
			"icon": "fas fa-cat",
			"color": "text-orange",
			"price": 3000
		},
		"ban": {
			"kind": "ban",
			"title": "1-Day Ban",
			"description": "Bans the recipient for a day.",
			"icon": "fas fa-gavel",
			"color": "text-danger",
			"price": 3000
		},
		"unban": {
			"kind": "unban",
			"title": "1-Day Unban",
			"description": "Removes 1 day from the ban duration of the recipient.",
			"icon": "fas fa-gavel",
			"color": "text-success",
			"price": 3500
		},
		"grass": {
			"kind": "grass",
			"title": "Grass",
			"description": "Ban the recipient permanently (must provide a timestamped picture of them touching grass to the admins to get unbanned)",
			"icon": "fas fa-seedling",
			"color": "text-success",
			"price": 10000
		},
		"eye": {
			"kind": "eye",
			"title": "All-Seeing Eye",
			"description": "Gives the recipient the ability to view private profiles.",
			"icon": "fas fa-eye",
			"color": "text-silver",
			"price": 10000
		},
		"pause": {
			"kind": "pause",
			"title": "Pause",
			"description": "Gives the recipient the ability to pause profile anthems.",
			"icon": "fas fa-volume-mute",
			"color": "text-danger",
			"price": 20000
		},
		"unpausable": {
			"kind": "unpausable",
			"title": "Unpausable",
			"description": "Makes the profile anthem of the recipient unpausable.",
			"icon": "fas fa-volume",
			"color": "text-success",
			"price": 40000
		},
		"alt": {
			"kind": "alt",
			"title": "Alt-Seeing Eye",
			"description": "Gives the recipient the ability to view alts.",
			"icon": "fas fa-eye",
			"color": "text-gold",
			"price": 50000
		},
	}

	if award not in AWARDS: abort(400)
	price = AWARDS[award]["price"]

	if v.patron == 1: discount = 0.90
	elif v.patron == 2: discount = 0.85
	elif v.patron == 3: discount = 0.80
	elif v.patron == 4: discount = 0.75
	elif v.patron == 5: discount = 0.70
	else: discount = 1

	for badge in [69,70,71,72,73]:
		if v.has_badge(badge): discount -= discounts[badge]

	price = int(price*discount)

	if request.values.get("mb"):
		if v.procoins < price: return {"error": "Not enough marseybux."}, 400
		v.procoins -= price
	else:
		if v.coins < price: return {"error": "Not enough coins."}, 400
		v.coins -= price
		v.coins_spent += price
		if v.coins_spent >= 1000000 and not v.has_badge(73):
			new_badge = Badge(badge_id=73, user_id=v.id)
			g.db.add(new_badge)
			old_badge = v.has_badge(72)
			if old_badge: g.db.delete(old_badge)
		elif v.coins_spent >= 500000 and not v.has_badge(72):
			new_badge = Badge(badge_id=72, user_id=v.id)
			g.db.add(new_badge)
			old_badge = v.has_badge(71)
			if old_badge: g.db.delete(old_badge)
		elif v.coins_spent >= 250000 and not v.has_badge(71):
			new_badge = Badge(badge_id=71, user_id=v.id)
			g.db.add(new_badge)
			old_badge = v.has_badge(70)
			if old_badge: g.db.delete(old_badge)
		elif v.coins_spent >= 100000 and not v.has_badge(70):
			new_badge = Badge(badge_id=70, user_id=v.id)
			g.db.add(new_badge)
			old_badge = v.has_badge(69)
			if old_badge: g.db.delete(old_badge)
		elif v.coins_spent >= 10000 and not v.has_badge(69):
			new_badge = Badge(badge_id=69, user_id=v.id)
			g.db.add(new_badge)
		g.db.add(v)

	g.db.add(v)
	g.db.flush()
	thing = g.db.query(AwardRelationship).order_by(AwardRelationship.id.desc()).first().id
	thing += 1

	award = AwardRelationship(id=thing, user_id=v.id, kind=award)
	g.db.add(award)

	g.db.commit()

	return {"message": "Award bought!"}


@app.post("/post/<pid>/awards")
@limiter.limit("1/second")
@auth_required
def award_post(pid, v):

	if v.is_banned and not v.unban_utc: return {"error": "forbidden."}, 403

	kind = request.values.get("kind", "").strip()
	
	if kind not in AWARDS:
		return {"error": "That award doesn't exist."}, 404

	post_award = g.db.query(AwardRelationship).filter(
		and_(
			AwardRelationship.kind == kind,
			AwardRelationship.user_id == v.id,
			AwardRelationship.submission_id == None,
			AwardRelationship.comment_id == None
		)
	).first()

	if not post_award:
		return {"error": "You don't have that award."}, 404

	post = g.db.query(Submission).filter_by(id=pid).first()

	if not post:
		return {"error": "That post doesn't exist."}, 404

	existing_award = g.db.query(AwardRelationship).filter(
		and_(
			AwardRelationship.submission_id == post.id,
			AwardRelationship.user_id == v.id,
			AwardRelationship.kind == kind
		)
	).first()

	post_award.submission_id = post.id
	g.db.add(post_award)

	msg = f"@{v.username} has given your [post]({post.permalink}) the {AWARDS[kind]['title']} Award!"

	note = request.values.get("note", "").strip()
	if note: msg += f"\n\n> {note}"

	send_notification(post.author.id, msg)

	author = post.author
	if kind == "ban":
		link = f"[this post]({post.permalink})"

		if not author.is_suspended:
			author.ban(reason=f"1-Day ban award used by @{v.username} on /post/{post.id}", days=1)
			send_notification(author.id, f"Your account has been suspended for a day for {link}. It sucked and you should feel bad.")
		elif author.unban_utc > 0:
			author.unban_utc += 86400
			send_notification(author.id, f"Your account has been suspended for yet another day for {link}. Seriously man?")
	elif kind == "unban":
		if not author.is_suspended or not author.unban_utc or time.time() > author.unban_utc: abort(403)

		if author.unban_utc - time.time() > 86400:
			author.unban_utc -= 86400
			send_notification(author.id, f"Your ban duration has been reduced by 1 day!")
		else:
			author.unban_utc = 0
			author.is_banned = 0
			author.ban_evade = 0
			send_notification(author.id, f"You have been unbanned!")
	elif kind == "grass":
		author.is_banned = AUTOJANNY_ID
		author.ban_reason = f"grass award used by @{v.username} on /post/{post.id}"
		link = f"[this post]({post.permalink})"
		send_notification(author.id, f"Your account has been suspended permanently for {link}. You must [provide the admins](/contact) a timestamped picture of you touching grass to get unbanned!")
	elif kind == "pin":
		if post.stickied and post.stickied.startswith("t:"): t = int(post.stickied[2:]) + 3600
		else: t = int(time.time()) + 3600
		post.stickied = f"t:{t}"
		g.db.add(post)
		cache.delete_memoized(frontlist)
	elif kind == "unpin":
		if not (post.stickied and post.stickied.startswith("t:")): abort(403)
		t = int(post.stickied[2:]) - 3600
		if time.time() > t:
			post.stickied = None
			cache.delete_memoized(frontlist)
		else: post.stickied = f"t:{t}"
		g.db.add(post)
	elif kind == "agendaposter" and not (author.agendaposter and author.agendaposter_expires_utc == 0):
		if author.agendaposter_expires_utc and time.time() < author.agendaposter_expires_utc: author.agendaposter_expires_utc += 86400
		else: author.agendaposter_expires_utc = time.time() + 86400
		
		author.agendaposter = True
		if not author.has_badge(26):
			badge = Badge(user_id=author.id, badge_id=26)
			g.db.add(badge)
	elif kind == "flairlock":
		new_name = note[:100].replace("𒐪","")
		author.customtitleplain = new_name
		author.customtitle = filter_title(new_name)
		if len(author.customtitle) > 1000: abort(403)
		author.flairchanged = time.time() + 86400
	elif kind == "pause":
		author.mute = True
		send_notification(995, f"@{v.username} bought {kind} award!")
		new_badge = Badge(badge_id=68, user_id=author.id)
		g.db.add(new_badge)
	elif kind == "unpausable":
		author.unmutable = True
		send_notification(995, f"@{v.username} bought {kind} award!")
		new_badge = Badge(badge_id=67, user_id=author.id)
		g.db.add(new_badge)
	elif kind == "marsey":
		if author.marseyawarded: author.marseyawarded += 86400
		else: author.marseyawarded = time.time() + 86400
	elif kind == "pizzashill":
		if author.longpost: author.longpost += 86400
		else: author.longpost = time.time() + 86400
	elif kind == "eye":
		author.eye = True
		send_notification(995, f"@{v.username} bought {kind} award!")
		new_badge = Badge(badge_id=83, user_id=author.id)
		g.db.add(new_badge)
	elif kind == "alt":
		author.alt = True
		send_notification(995, f"@{v.username} bought {kind} award!")
		new_badge = Badge(badge_id=84, user_id=author.id)
		g.db.add(new_badge)

	post.author.received_award_count += 1
	g.db.add(post.author)

	g.db.commit()
	if request.referrer and len(request.referrer) > 1: return redirect(request.referrer)
	else: return redirect("/")


@app.post("/comment/<cid>/awards")
@limiter.limit("1/second")
@auth_required
def award_comment(cid, v):

	if v.is_suspended and v.unban_utc == 0: return {"error": "forbidden"}, 403

	kind = request.values.get("kind", "").strip()

	if kind not in AWARDS:
		return {"error": "That award doesn't exist."}, 404

	comment_award = g.db.query(AwardRelationship).filter(
		and_(
			AwardRelationship.kind == kind,
			AwardRelationship.user_id == v.id,
			AwardRelationship.submission_id == None,
			AwardRelationship.comment_id == None
		)
	).first()

	if not comment_award:
		return {"error": "You don't have that award."}, 404

	c = g.db.query(Comment).filter_by(id=cid).first()

	if not c:
		return {"error": "That comment doesn't exist."}, 404

	existing_award = g.db.query(AwardRelationship).filter(
		and_(
			AwardRelationship.comment_id == c.id,
			AwardRelationship.user_id == v.id,
			AwardRelationship.kind == kind
		)
	).first()

	comment_award.comment_id = c.id
	g.db.add(comment_award)

	msg = f"@{v.username} has given your [comment]({c.permalink}) the {AWARDS[kind]['title']} Award!"

	note = request.values.get("note", "").strip()
	if note: msg += f"\n\n> {note}"

	send_notification(c.author.id, msg)
	author = c.author

	if kind == "ban":
		link = f"[this comment]({c.permalink})"

		if not author.is_suspended:
			author.ban(reason=f"1-Day ban award used by @{v.username} on /comment/{c.id}", days=1)
			send_notification(author.id, f"Your account has been suspended for a day for {link}. It sucked and you should feel bad.")
		elif author.unban_utc > 0:
			author.unban_utc += 86400
			send_notification(author.id, f"Your account has been suspended for yet another day for {link}. Seriously man?")
	elif kind == "unban":
		if not author.is_suspended or not author.unban_utc or time.time() > author.unban_utc: abort(403)

		if author.unban_utc - time.time() > 86400:
			author.unban_utc -= 86400
			send_notification(author.id, f"Your ban duration has been reduced by 1 day!")
		else:
			author.unban_utc = 0
			author.is_banned = 0
			author.ban_evade = 0
			send_notification(author.id, f"You have been unbanned!")
	elif kind == "grass":
		author.is_banned = AUTOJANNY_ID
		author.ban_reason = f"grass award used by @{v.username} on /comment/{c.id}"
		link = f"[this comment]({c.permalink})"
		send_notification(author.id, f"Your account has been suspended permanently for {link}. You must [provide the admins](/contact) a timestamped picture of you touching grass to get unbanned!")
	elif kind == "pin":
		if c.is_pinned and c.is_pinned.startswith("t:"): t = int(c.is_pinned[2:]) + 3600
		else: t = int(time.time()) + 3600
		c.is_pinned = f"t:{t}"
		g.db.add(c)
	elif kind == "unpin":
		if not (c.is_pinned and c.is_pinned.startswith("t:")): abort(403)
		t = int(c.is_pinned[2:]) - 3600
		if time.time() > t: c.is_pinned = None
		else: c.is_pinned = f"t:{t}"
		g.db.add(c)
	elif kind == "agendaposter" and not (author.agendaposter and author.agendaposter_expires_utc == 0):
		if author.agendaposter_expires_utc and time.time() < author.agendaposter_expires_utc: author.agendaposter_expires_utc += 86400
		else: author.agendaposter_expires_utc = time.time() + 86400
		
		author.agendaposter = True
		if not author.has_badge(26):
			badge = Badge(user_id=author.id, badge_id=26)
			g.db.add(badge)
	elif kind == "flairlock":
		new_name = note[:100].replace("𒐪","")
		author.customtitleplain = new_name
		author.customtitle = filter_title(new_name)
		if len(author.customtitle) > 1000: abort(403)
		author.flairchanged = time.time() + 86400
	elif kind == "pause":
		author.mute = True
		send_notification(995, f"@{v.username} bought {kind} award!")
		new_badge = Badge(badge_id=68, user_id=author.id)
		g.db.add(new_badge)
	elif kind == "unpausable":
		author.unmutable = True
		send_notification(995, f"@{v.username} bought {kind} award!")
		new_badge = Badge(badge_id=67, user_id=author.id)
		g.db.add(new_badge)
	elif kind == "marsey":
		if author.marseyawarded: author.marseyawarded += 86400
		else: author.marseyawarded = time.time() + 86400
	elif kind == "pizzashill":
		if author.longpost: author.longpost += 86400
		else: author.longpost = time.time() + 86400
	elif kind == "eye":
		author.eye = True
		send_notification(995, f"@{v.username} bought {kind} award!")
		new_badge = Badge(badge_id=83, user_id=author.id)
		g.db.add(new_badge)
	elif kind == "alt":
		author.alt = True
		send_notification(995, f"@{v.username} bought {kind} award!")
		new_badge = Badge(badge_id=84, user_id=author.id)
		g.db.add(new_badge)

	c.author.received_award_count += 1
	g.db.add(c.author)

	g.db.commit()
	if request.referrer and len(request.referrer) > 1: return redirect(request.referrer)
	else: return redirect("/")

@app.get("/admin/awards")
@admin_level_required(2)
def admin_userawards_get(v):

	if request.host == 'rdrama.net' and v.admin_level != 3: render_template("admin/awards.html", awards=list(AWARDS2.values()), v=v)
	return render_template("admin/awards.html", awards=list(AWARDS.values()), v=v) 

@app.post("/admin/awards")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def admin_userawards_post(v):

	try: u = request.values.get("username").strip()
	except: abort(404)

	u = get_user(u, graceful=False, v=v)

	notify_awards = {}

	latest = g.db.query(AwardRelationship).order_by(AwardRelationship.id.desc()).first()
	thing = latest.id

	for key, value in request.values.items():
		if key not in AWARDS: continue

		if value:
			
			if int(value) > 10: abort(403)

			if int(value) > 0: notify_awards[key] = int(value)

			for x in range(int(value)):
				thing += 1

				award = AwardRelationship(
					id=thing,
					user_id=u.id,
					kind=key
				)

				g.db.add(award)

	text = "You were given the following awards:\n\n"

	for key, value in notify_awards.items(): text += f" - **{value}** {AWARDS[key]['title']} {'Awards' if value != 1 else 'Award'}\n"

	send_notification(u.id, text)

	g.db.commit()

	if request.host == 'rdrama.net' and v.admin_level != 3: render_template("admin/awards.html", awards=list(AWARDS2.values()), v=v)
	return render_template("admin/awards.html", awards=list(AWARDS.values()), v=v) 