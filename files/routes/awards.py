from files.__main__ import app, limiter
from files.helpers.wrappers import *
from files.helpers.alerts import *
from files.helpers.get import *
from files.helpers.const import *
from files.helpers.discord import *
from files.classes.award import *
from .front import frontlist
from flask import g, request
from files.helpers.sanitize import filter_emojis_only
from copy import deepcopy

@app.get("/shop")
@app.get("/settings/shop")
@auth_required
def shop(v):
	AWARDS = deepcopy(AWARDS2)

	for val in AWARDS.values(): val["owned"] = 0

	for useraward in g.db.query(AwardRelationship).filter(AwardRelationship.user_id == v.id, AwardRelationship.submission_id == None, AwardRelationship.comment_id == None).all():
		if useraward.kind in AWARDS: AWARDS[useraward.kind]["owned"] += 1

	for val in AWARDS.values():
		val["baseprice"] = int(val["price"])
		val["price"] = int(val["price"] * v.discount)

	sales = g.db.query(func.sum(User.coins_spent)).scalar()
	return render_template("shop.html", awards=list(AWARDS.values()), v=v, sales=sales)


@app.post("/buy/<award>")
@auth_required
def buy(v, award):
	if award == 'benefactor' and not request.values.get("mb"):
		return {"error": "You can only buy the Benefactor award with marseybux."}, 403

	if award == 'ghost' and v.admin_level < 2:
		return {"error": "Only admins can buy that award."}, 403

	AWARDS = deepcopy(AWARDS2)

	if award not in AWARDS: abort(400)
	og_price = AWARDS[award]["price"]

	price = int(og_price * v.discount)

	if request.values.get("mb"):
		if v.procoins < price: return {"error": "Not enough marseybux."}, 400
		if award == "grass": return {"error": "You can't buy the grass award with marseybux."}, 403
		v.procoins -= price
	else:
		if v.coins < price: return {"error": "Not enough coins."}, 400
		v.coins -= price
		v.coins_spent += price
		if v.coins_spent >= 1000000 and not v.has_badge(73):
			new_badge = Badge(badge_id=73, user_id=v.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		elif v.coins_spent >= 500000 and not v.has_badge(72):
			new_badge = Badge(badge_id=72, user_id=v.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		elif v.coins_spent >= 250000 and not v.has_badge(71):
			
			new_badge = Badge(badge_id=71, user_id=v.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		elif v.coins_spent >= 100000 and not v.has_badge(70):
			new_badge = Badge(badge_id=70, user_id=v.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		elif v.coins_spent >= 10000 and not v.has_badge(69):
			new_badge = Badge(badge_id=69, user_id=v.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		g.db.add(v)


	if award == "lootbox":
		send_repeatable_notification(995, f"@{v.username} bought a lootbox!")
		for i in [1,2,3,4,5]:
			award = random.choice(["snow", "gingerbread", "lights", "candycane", "fireplace"])
			award = AwardRelationship(user_id=v.id, kind=award)
			g.db.add(award)
			g.db.flush()
		v.lootboxes_bought += 1
		if v.lootboxes_bought == 10 and not v.has_badge(76):
			new_badge = Badge(badge_id=76, user_id=v.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		elif v.lootboxes_bought == 50 and not v.has_badge(77):
			new_badge = Badge(badge_id=77, user_id=v.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		elif v.lootboxes_bought == 150 and not v.has_badge(78):
			new_badge = Badge(badge_id=78, user_id=v.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")

	else:
		award_object = AwardRelationship(user_id=v.id, kind=award)
		g.db.add(award_object)

	g.db.add(v)

	if CARP_ID and v.id != CARP_ID and og_price >= 10000:
		send_repeatable_notification(CARP_ID, f"@{v.username} has bought a `{award}` award!")

	g.db.commit()

	return {"message": "Award bought!"}

@app.post("/award_post/<pid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@is_not_permabanned
def award_post(pid, v):
	if v.shadowbanned: return render_template('errors/500.html', err=True, v=v), 500
	
	kind = request.values.get("kind", "").strip()
	
	if kind not in AWARDS:
		return {"error": "That award doesn't exist."}, 404

	post_award = g.db.query(AwardRelationship).filter(
		AwardRelationship.kind == kind,
		AwardRelationship.user_id == v.id,
		AwardRelationship.submission_id == None,
		AwardRelationship.comment_id == None
	).first()

	if not post_award:
		return {"error": "You don't have that award."}, 404

	post = g.db.query(Submission).filter_by(id=pid).one_or_none()

	if not post:
		return {"error": "That post doesn't exist."}, 404

	post_award.submission_id = post.id
	g.db.add(post_award)

	note = request.values.get("note", "").strip()

	author = post.author

	if author.id in (PIZZASHILL_ID, DAD_ID) and v.id not in (PIZZASHILL_ID, DAD_ID):
		return {"error": "This user is immune to awards."}, 403

	if kind == "benefactor" and author.id == v.id:
		return {"error": "You can't use this award on yourself."}, 400

	if v.id != author.id:
		if author.deflector and AWARDS[kind]['price'] > 300 and kind not in ('pin','unpin','benefactor'):
			msg = f"@{v.username} has tried to give your [post]({post.shortlink}) the {AWARDS[kind]['title']} Award but it was deflected and applied to them :marseytroll:"
			send_repeatable_notification(author.id, msg)
			msg = f"@{author.username} is under the effect of a deflector award; your {AWARDS[kind]['title']} Award has been deflected back to you :marseytroll:"
			send_repeatable_notification(v.id, msg)
			author = v
		else:
			msg = f"@{v.username} has given your [post]({post.shortlink}) the {AWARDS[kind]['title']} Award!"
			if note: msg += f"\n\n> {note}"
			send_repeatable_notification(author.id, msg)

	if kind == "ban":
		link = f"[this post]({post.shortlink})"

		if not author.is_suspended:
			author.ban(reason=f"1-Day ban award used by @{v.username} on /post/{post.id}", days=1)
			send_repeatable_notification(author.id, f"Your account has been banned for **a day** for {link}. It sucked and you should feel bad.")
		elif author.unban_utc:
			author.unban_utc += 86400
			send_repeatable_notification(author.id, f"Your account has been banned for **yet another day** for {link}. Seriously man?")
	elif kind == "unban":
		if not author.is_suspended or not author.unban_utc or time.time() > author.unban_utc: abort(403)

		if author.unban_utc - time.time() > 86400:
			author.unban_utc -= 86400
			send_repeatable_notification(author.id, "Your ban duration has been reduced by 1 day!")
		else:
			author.unban_utc = 0
			author.is_banned = 0
			author.ban_evade = 0
			send_repeatable_notification(author.id, "You have been unbanned!")
	elif kind == "grass":
		author.is_banned = AUTOJANNY_ID
		author.ban_reason = f"grass award used by @{v.username} on /post/{post.id}"
		author.unban_utc = int(time.time()) + 30 * 86400
		link = f"[this post]({post.shortlink})"
		send_repeatable_notification(author.id, f"Your account has been banned permanently for {link}. You must [provide the admins](/contact) a timestamped picture of you touching grass/snow/sand/ass to get unbanned!")
	elif kind == "pin":
		if post.stickied and post.stickied_utc:
			post.stickied_utc += 3600
		else:
			post.stickied = f'{v.username} (pin award)'
			post.stickied_utc = int(time.time()) + 3600
		g.db.add(post)
		cache.delete_memoized(frontlist)
	elif kind == "unpin":
		if not post.stickied_utc: abort(403)
		t = post.stickied_utc - 3600
		if time.time() > t:
			post.stickied = None
			post.stickied_utc = None
			cache.delete_memoized(frontlist)
		else: post.stickied_utc = t
		g.db.add(post)
	elif kind == "agendaposter" and not (author.agendaposter and author.agendaposter == 0):
		if author.marseyawarded:
			return {"error": "This user is the under the effect of a conflicting award: Marsey award."}, 404

		if author.agendaposter and time.time() < author.agendaposter: author.agendaposter += 86400
		else: author.agendaposter = int(time.time()) + 86400
		
		if not author.has_badge(28):
			badge = Badge(user_id=author.id, badge_id=28)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "flairlock":
		new_name = note[:100].replace("𒐪","")
		if not new_name and author.flairchanged:
			author.flairchanged += 86400
		else:
			author.customtitleplain = new_name
			author.customtitle = filter_emojis_only(new_name)
			if len(author.customtitle) > 1000: abort(403)
			author.flairchanged = int(time.time()) + 86400
			if not author.has_badge(96):
				badge = Badge(user_id=author.id, badge_id=96)
				g.db.add(badge)
				g.db.flush()
				send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "pause":
		author.mute = True
		if not author.has_badge(68):
			new_badge = Badge(badge_id=68, user_id=author.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "unpausable":
		author.unmutable = True
		if not author.has_badge(67):
			new_badge = Badge(badge_id=67, user_id=author.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "marsey":
		if author.marseyawarded: author.marseyawarded += 86400
		else: author.marseyawarded = int(time.time()) + 86400
		if not author.has_badge(98):
			badge = Badge(user_id=author.id, badge_id=98)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "pizzashill":
		if author.bird:
			return {"error": "This user is the under the effect of a conflicting award: Bird Site award."}, 404
		if author.longpost: author.longpost += 86400
		else: author.longpost = int(time.time()) + 86400
		if not author.has_badge(97):
			badge = Badge(user_id=author.id, badge_id=97)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "bird":
		if author.longpost:
			return {"error": "This user is the under the effect of a conflicting award: Pizzashill award."}, 404
		if author.bird: author.bird += 86400
		else: author.bird = int(time.time()) + 86400
		if not author.has_badge(95):
			badge = Badge(user_id=author.id, badge_id=95)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "eye":
		author.eye = True
		if not author.has_badge(83):
			new_badge = Badge(badge_id=83, user_id=author.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "alt":
		author.alt = True
		if not author.has_badge(84):
			new_badge = Badge(badge_id=84, user_id=author.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "unblockable":
		author.unblockable = True
		if not author.has_badge(87):
			new_badge = Badge(badge_id=87, user_id=author.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		for block in g.db.query(UserBlock).filter_by(target_id=author.id).all(): g.db.delete(block)
	elif kind == "fish":
		author.fish = True
		if not author.has_badge(90):
			new_badge = Badge(badge_id=90, user_id=author.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "progressivestack":
		if author.progressivestack: author.progressivestack += 21600
		else: author.progressivestack = int(time.time()) + 21600
		if not author.has_badge(94):
			badge = Badge(user_id=author.id, badge_id=94)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "benefactor":
		author.patron = 1
		if author.patron_utc: author.patron_utc += 2629746
		else: author.patron_utc = int(time.time()) + 2629746
		author.procoins += 2500
		if author.discord_id: add_role(author, "1")
		if not v.has_badge(103):
			badge = Badge(user_id=v.id, badge_id=103)
			g.db.add(badge)
			g.db.flush()
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "rehab":
		if author.rehab: author.rehab += 86400
		else: author.rehab = int(time.time()) + 86400
		if not author.has_badge(109):
			badge = Badge(user_id=author.id, badge_id=109)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "deflector":
		if author.deflector: author.deflector += 36000
		else: author.deflector = int(time.time()) + 36000
	elif kind == "beano":
		if not author.has_badge(128):
			badge = Badge(user_id=author.id, badge_id=128)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")

	if author.received_award_count: author.received_award_count += 1
	else: author.received_award_count = 1
	g.db.add(author)

	g.db.commit()
	if request.referrer and len(request.referrer) > 1:
		if request.referrer == f'{SITE_FULL}/submit': return redirect(post.permalink)
		elif request.referrer.startswith(f'{SITE_FULL}/'): return redirect(request.referrer)
	return redirect(SITE_FULL)


@app.post("/award_comment/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@is_not_permabanned
def award_comment(cid, v):
	if v.shadowbanned: return render_template('errors/500.html', err=True, v=v), 500

	kind = request.values.get("kind", "").strip()

	if kind not in AWARDS:
		return {"error": "That award doesn't exist."}, 404

	comment_award = g.db.query(AwardRelationship).filter(
		AwardRelationship.kind == kind,
		AwardRelationship.user_id == v.id,
		AwardRelationship.submission_id == None,
		AwardRelationship.comment_id == None
	).first()

	if not comment_award:
		return {"error": "You don't have that award."}, 404

	c = g.db.query(Comment).filter_by(id=cid).one_or_none()

	if not c:
		return {"error": "That comment doesn't exist."}, 404

	comment_award.comment_id = c.id
	g.db.add(comment_award)

	note = request.values.get("note", "").strip()

	author = c.author

	if author.id in (PIZZASHILL_ID, DAD_ID) and v.id not in (PIZZASHILL_ID, DAD_ID):
		return {"error": "This user is immune to awards."}, 403

	if v.id != author.id:
		if author.deflector and AWARDS[kind]['price'] > 300 and kind not in ('pin','unpin','benefactor'):
			msg = f"@{v.username} has tried to give your [comment]({c.shortlink}) the {AWARDS[kind]['title']} Award but it was deflected and applied to them :marseytroll:"
			send_repeatable_notification(author.id, msg)
			msg = f"@{author.username} is under the effect of a deflector award; your {AWARDS[kind]['title']} Award has been deflected back to you :marseytroll:"
			send_repeatable_notification(v.id, msg)
			author = v
		else:
			msg = f"@{v.username} has given your [comment]({c.shortlink}) the {AWARDS[kind]['title']} Award!"
			if note: msg += f"\n\n> {note}"
			send_repeatable_notification(author.id, msg)

	if kind == "benefactor" and author.id == v.id:
		return {"error": "You can't use this award on yourself."}, 400

	if author.deflector: author = v

	if kind == "ban":
		link = f"[this comment]({c.shortlink})"

		if not author.is_suspended:
			author.ban(reason=f"1-Day ban award used by @{v.username} on /comment/{c.id}", days=1)
			send_repeatable_notification(author.id, f"Your account has been banned for **a day** for {link}. It sucked and you should feel bad.")
		elif author.unban_utc:
			author.unban_utc += 86400
			send_repeatable_notification(author.id, f"Your account has been banned for **yet another day** for {link}. Seriously man?")
	elif kind == "unban":
		if not author.is_suspended or not author.unban_utc or time.time() > author.unban_utc: abort(403)

		if author.unban_utc - time.time() > 86400:
			author.unban_utc -= 86400
			send_repeatable_notification(author.id, "Your ban duration has been reduced by 1 day!")
		else:
			author.unban_utc = 0
			author.is_banned = 0
			author.ban_evade = 0
			send_repeatable_notification(author.id, "You have been unbanned!")
	elif kind == "grass":
		author.is_banned = AUTOJANNY_ID
		author.ban_reason = f"grass award used by @{v.username} on /comment/{c.id}"
		author.unban_utc = int(time.time()) + 30 * 86400
		link = f"[this comment]({c.shortlink})"
		send_repeatable_notification(author.id, f"Your account has been banned permanently for {link}. You must [provide the admins](/contact) a timestamped picture of you touching grass/snow/sand/ass to get unbanned!")
	elif kind == "pin":
		if c.is_pinned and c.is_pinned_utc: c.is_pinned_utc += 3600
		else:
			c.is_pinned = f'{v.username} (pin award)'
			c.is_pinned_utc = int(time.time()) + 3600
		g.db.add(c)
	elif kind == "unpin":
		if not c.is_pinned_utc: abort(403)
		t = c.is_pinned_utc - 3600
		if time.time() > t:
			c.is_pinned = None
			c.is_pinned_utc = None
		else: c.is_pinned_utc = t
		g.db.add(c)
	elif kind == "agendaposter" and not (author.agendaposter and author.agendaposter == 0):
		if author.marseyawarded:
			return {"error": "This user is the under the effect of a conflicting award: Marsey award."}, 404

		if author.agendaposter and time.time() < author.agendaposter: author.agendaposter += 86400
		else: author.agendaposter = int(time.time()) + 86400
		
		if not author.has_badge(28):
			badge = Badge(user_id=author.id, badge_id=28)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "flairlock":
		new_name = note[:100].replace("𒐪","")
		if not new_name and author.flairchanged:
			author.flairchanged += 86400
		else:
			author.customtitleplain = new_name
			author.customtitle = filter_emojis_only(new_name)
			if len(author.customtitle) > 1000: abort(403)
			author.flairchanged = int(time.time()) + 86400
			if not author.has_badge(96):
				badge = Badge(user_id=author.id, badge_id=96)
				g.db.add(badge)
				g.db.flush()
				send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "pause":
		author.mute = True
		if not author.has_badge(68):
			new_badge = Badge(badge_id=68, user_id=author.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "unpausable":
		author.unmutable = True
		if not author.has_badge(67):
			new_badge = Badge(badge_id=67, user_id=author.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "marsey":
		if author.marseyawarded: author.marseyawarded += 86400
		else: author.marseyawarded = int(time.time()) + 86400
		if not author.has_badge(98):
			badge = Badge(user_id=author.id, badge_id=98)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "pizzashill":
		if author.bird:
			return {"error": "This user is the under the effect of a conflicting award: Bird Site award."}, 404
		if author.longpost: author.longpost += 86400
		else: author.longpost = int(time.time()) + 86400
		if not author.has_badge(97):
			badge = Badge(user_id=author.id, badge_id=97)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "bird":
		if author.longpost:
			return {"error": "This user is the under the effect of a conflicting award: Pizzashill award."}, 404
		if author.bird: author.bird += 86400
		else: author.bird = int(time.time()) + 86400
		if not author.has_badge(95):
			badge = Badge(user_id=author.id, badge_id=95)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "eye":
		author.eye = True
		if not author.has_badge(83):
			new_badge = Badge(badge_id=83, user_id=author.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "alt":
		author.alt = True
		if not author.has_badge(84):
			new_badge = Badge(badge_id=84, user_id=author.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "unblockable":
		author.unblockable = True
		if not author.has_badge(87):
			new_badge = Badge(badge_id=87, user_id=author.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
		for block in g.db.query(UserBlock).filter_by(target_id=author.id).all(): g.db.delete(block)
	elif kind == "fish":
		author.fish = True
		if not author.has_badge(90):
			new_badge = Badge(badge_id=90, user_id=author.id)
			g.db.add(new_badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	elif kind == "progressivestack":
		if author.progressivestack: author.progressivestack += 21600
		else: author.progressivestack = int(time.time()) + 21600
		if not author.has_badge(94):
			badge = Badge(user_id=author.id, badge_id=94)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "benefactor":
		author.patron = 1
		if author.patron_utc: author.patron_utc += 2629746
		else: author.patron_utc = int(time.time()) + 2629746
		author.procoins += 2500
		if author.discord_id: add_role(author, "1")
		if not v.has_badge(103):
			badge = Badge(user_id=v.id, badge_id=103)
			g.db.add(badge)
			g.db.flush()
			send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "rehab":
		if author.rehab: author.rehab += 86400
		else: author.rehab = int(time.time()) + 86400
		if not author.has_badge(109):
			badge = Badge(user_id=author.id, badge_id=109)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
	elif kind == "deflector":
		if author.deflector: author.deflector += 36000
		else: author.deflector = int(time.time()) + 36000
	elif kind == "beano":
		if not author.has_badge(128):
			badge = Badge(user_id=author.id, badge_id=128)
			g.db.add(badge)
			g.db.flush()
			send_notification(author.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")

	if author.received_award_count: author.received_award_count += 1
	else: author.received_award_count = 1
	g.db.add(author)

	g.db.commit()
	if request.referrer and len(request.referrer) > 1 and request.referrer.startswith(f'{SITE_FULL}/'):
		return redirect(request.referrer)
	return redirect(SITE_FULL)

@app.get("/admin/awards")
@admin_level_required(2)
def admin_userawards_get(v):
	if request.host == 'pcmemes.net' and v.admin_level < 3: abort(403)

	if v.admin_level != 3:
		return render_template("admin/awards.html", awards=list(AWARDS3.values()), v=v)

	return render_template("admin/awards.html", awards=list(AWARDS.values()), v=v) 

@app.post("/admin/awards")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def admin_userawards_post(v):
	emoji_whitelist = ["shit", "fireflies", "train", "scooter", "wholesome", "tilt", "glowie"]
	if request.host == 'pcmemes.net' and v.admin_level < 3: abort(403)

	try: u = request.values.get("username").strip()
	except: abort(404)

	u = get_user(u, graceful=False, v=v)

	notify_awards = {}

	for key, value in request.values.items():
		# Check if award exists and is allowed
		if key not in AWARDS.extend(emoji_whitelist): abort(403)
                
		if value:
			
			if int(value) > 10: abort(403)

			if int(value): notify_awards[key] = int(value)

			for x in range(int(value)):
				award = AwardRelationship(
					user_id=u.id,
					kind=key
				)

				g.db.add(award)

	if v.id != u.id:
		text = f"@{v.username} has given the following awards:\n\n"
		for key, value in notify_awards.items():
			text += f" - **{value}** {AWARDS[key]['title']} {'Awards' if value != 1 else 'Award'}\n"
		send_repeatable_notification(u.id, text)

	note = ""

	for key, value in notify_awards.items():
		note += f"{value} {AWARDS[key]['title']}, "

	if len(note) > 256: return {"error": "You're giving too many awards at the same time!"}
	
	ma=ModAction(
		kind="grant_awards",
		user_id=v.id,
		target_user_id=u.id,
		_note=note[:-2]
		)
	g.db.add(ma)

	g.db.commit()

	if v.admin_level != 3: return render_template("admin/awards.html", awards=list(AWARDS3.values()), v=v)
	return render_template("admin/awards.html", awards=list(AWARDS.values()), v=v) 
