import time
from os import remove
from PIL import Image as IMAGE

from files.helpers.wrappers import *
from files.helpers.alerts import *
from files.helpers.sanitize import *
from files.helpers.security import *
from files.helpers.get import *
from files.helpers.images import *
from files.helpers.const import *
from files.classes import *
from flask import *
from files.__main__ import app, cache, limiter
from .front import frontlist
from files.helpers.discord import add_role
from datetime import datetime
import requests

GUMROAD_ID = environ.get("GUMROAD_ID", "tfcvri").strip()
GUMROAD_TOKEN = environ.get("GUMROAD_TOKEN", "").strip()

month = datetime.now().strftime('%B')

if SITE_NAME == 'PCM':
	@app.get('/admin/sidebar')
	@admin_level_required(3)
	def get_sidebar(v):

		try:
			with open(f'files/templates/sidebar_{SITE_NAME}.html', 'r', encoding="utf-8") as f: sidebar = f.read()
		except:
			sidebar = None

		return render_template('admin/sidebar.html', v=v, sidebar=sidebar)


	@app.post('/admin/sidebar')
	@limiter.limit("1/second;30/minute;200/hour;1000/day")
	@admin_level_required(3)
	def post_sidebar(v):

		text = request.values.get('sidebar', '').strip()

		with open(f'files/templates/sidebar_{SITE_NAME}.html', 'w+', encoding="utf-8") as f: f.write(text)

		with open(f'files/templates/sidebar_{SITE_NAME}.html', 'r', encoding="utf-8") as f: sidebar = f.read()

		ma = ModAction(
			kind="change_sidebar",
			user_id=v.id,
		)
		g.db.add(ma)

		g.db.commit()

		return render_template('admin/sidebar.html', v=v, sidebar=sidebar, msg='Sidebar edited successfully!')


@app.post("/@<username>/make_admin")
@limiter.limit("1/second;5/day")
@admin_level_required(3)
def make_admin(v, username):
	user = get_user(username)
	if not user: abort(404)
	user.admin_level = 2
	g.db.add(user)

	ma = ModAction(
		kind="make_admin",
		user_id=v.id,
		target_user_id=user.id
	)
	g.db.add(ma)

	g.db.commit()
	return {"message": "User has been made admin!"}


@app.post("/@<username>/remove_admin")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(3)
def remove_admin(v, username):
	user = get_user(username)
	if not user: abort(404)
	user.admin_level = 0
	g.db.add(user)

	ma = ModAction(
		kind="remove_admin",
		user_id=v.id,
		target_user_id=user.id
	)
	g.db.add(ma)

	g.db.commit()
	return {"message": "Admin removed!"}

@app.post("/distribute/<comment>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(3)
def distribute(v, comment):
	autobetter = g.db.query(User).filter_by(id=AUTOBETTER_ID).one_or_none()
	if autobetter.coins == 0: return {"error": "@AutoBetter has 0 coins"}

	try: comment = int(comment)
	except: abort(400)
	post = g.db.query(Comment.parent_submission).filter_by(id=comment).one_or_none()[0]
	post = g.db.query(Submission).filter_by(id=post).one_or_none()

	pool = 0
	for option in post.bet_options: pool += option.upvotes
	pool *= 200

	autobetter.coins -= pool
	if autobetter.coins < 0: autobetter.coins = 0
	g.db.add(autobetter)

	votes = g.db.query(CommentVote).filter_by(comment_id=comment)
	coinsperperson = int(pool / votes.count())

	cid = notif_comment(f"You won {coinsperperson} coins betting on [{post.title}]({post.sl}) :marseyparty:")
	for vote in votes:
		u = vote.user
		u.coins += coinsperperson
		add_notif(cid, u.id)

	cid = notif_comment(f"You lost the 200 coins you bet on [{post.title}]({post.sl}) :marseylaugh:")
	cids = [x.id for x in post.bet_options]
	cids.remove(comment)
	votes = g.db.query(CommentVote).filter(CommentVote.comment_id.in_(cids)).all()
	for vote in votes: add_notif(cid, vote.user.id)

	post.body += '\n\nclosed'
	g.db.add(post)
	
	ma = ModAction(
		kind="distribute",
		user_id=v.id,
		target_comment_id=cid
	)
	g.db.add(ma)

	g.db.commit()
	return {"message": f"Each winner has received {coinsperperson} coins!"}

@app.post("/@<username>/revert_actions")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(3)
def revert_actions(v, username):
	user = get_user(username)
	if not user: abort(404)
	
	ma = ModAction(
		kind="revert",
		user_id=v.id,
		target_user_id=user.id
	)
	g.db.add(ma)

	cutoff = int(time.time()) - 86400

	posts = [x[0] for x in g.db.query(ModAction.target_submission_id).filter(ModAction.user_id == user.id, ModAction.created_utc > cutoff, ModAction.kind == 'ban_post').all()]
	posts = g.db.query(Submission).filter(Submission.id.in_(posts)).all()

	comments = [x[0] for x in g.db.query(ModAction.target_comment_id).filter(ModAction.user_id == user.id, ModAction.created_utc > cutoff, ModAction.kind == 'ban_comment').all()]
	comments = g.db.query(Comment).filter(Comment.id.in_(comments)).all()
	
	for item in posts + comments:
		item.is_banned = False
		g.db.add(item)

	users = (x[0] for x in g.db.query(ModAction.target_user_id).filter(ModAction.user_id == user.id, ModAction.created_utc > cutoff, ModAction.kind.in_(('shadowban', 'ban_user'))).all())
	users = g.db.query(User).filter(User.id.in_(users)).all()

	for user in users:
		user.shadowbanned = None
		user.is_banned = 0
		user.unban_utc = 0
		user.ban_evade = 0
		send_repeatable_notification(user.id, f"@{v.username} has unbanned you!")
		g.db.add(user)
		for u in user.alts:
			u.shadowbanned = None
			u.is_banned = 0
			u.unban_utc = 0
			u.ban_evade = 0
			send_repeatable_notification(u.id, f"@{v.username} has unbanned you!")
			g.db.add(u)

	g.db.commit()
	return {"message": "Admin actions reverted!"}

@app.post("/@<username>/club_allow")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def club_allow(v, username):

	u = get_user(username, v=v)

	if not u: abort(404)

	if u.admin_level >= v.admin_level: return {"error": "noob"}

	u.club_allowed = True
	g.db.add(u)

	for x in u.alts_unique:
		x.club_allowed = True
		g.db.add(x)

	ma = ModAction(
		kind="club_allow",
		user_id=v.id,
		target_user_id=u.id
	)
	g.db.add(ma)

	g.db.commit()
	return {"message": f"@{username} has been allowed into the {CC_TITLE}!"}

@app.post("/@<username>/club_ban")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def club_ban(v, username):

	u = get_user(username, v=v)

	if not u: abort(404)

	if u.admin_level >= v.admin_level: return {"error": "noob"}

	u.club_allowed = False

	for x in u.alts_unique:
		u.club_allowed = False
		g.db.add(x)

	ma = ModAction(
		kind="club_ban",
		user_id=v.id,
		target_user_id=u.id
	)
	g.db.add(ma)

	g.db.commit()
	return {"message": f"@{username} has been kicked from the {CC_TITLE}. Deserved."}


@app.post("/@<username>/make_meme_admin")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(3)
def make_meme_admin(v, username):
	user = get_user(username)
	if not user: abort(404)
	user.admin_level = 1
	g.db.add(user)

	ma = ModAction(
		kind="make_meme_admin",
		user_id=v.id,
		target_user_id=user.id
	)
	g.db.add(ma)

	g.db.commit()
	return {"message": "User has been made meme admin!"}


@app.post("/@<username>/remove_meme_admin")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(3)
def remove_meme_admin(v, username):
	user = get_user(username)
	if not user: abort(404)
	user.admin_level = 0
	g.db.add(user)

	ma = ModAction(
		kind="remove_meme_admin",
		user_id=v.id,
		target_user_id=user.id
	)
	g.db.add(ma)

	g.db.commit()
	return {"message": "Meme admin removed!"}


@app.post("/admin/monthly")
@limiter.limit("1/day")
@admin_level_required(3)
def monthly(v):
	if SITE_NAME == 'Drama' and v.id != AEVANN_ID: abort (403)

	data = {'access_token': GUMROAD_TOKEN}

	emails = [x['email'] for x in requests.get(f'https://api.gumroad.com/v2/products/{GUMROAD_ID}/subscribers', data=data, timeout=5).json()["subscribers"]]

	for u in g.db.query(User).filter(User.patron > 0, User.patron_utc == 0).all():
		if u.email and u.email.lower() in emails:
			if u.patron == 1: procoins = 2500
			elif u.patron == 2: procoins = 5000
			elif u.patron == 3: procoins = 10000
			elif u.patron == 4: procoins = 25000
			elif u.patron == 5: procoins = 50000
			elif u.patron == 6: procoins = 125000
			u.procoins += procoins
			g.db.add(u)
			send_repeatable_notification(u.id, f"@{v.username} has given you {procoins} Marseybux for the month of {month}! You can use them to buy awards in the [shop](/shop).")
		elif u.patron == 5:
			procoins = 50000
			u.procoins += procoins
			g.db.add(u)
			send_repeatable_notification(u.id, f"@{v.username} has given you {procoins} Marseybux for the month of {month}! You can use them to buy awards in the [shop](/shop).")
		elif u.patron == 1 and u.admin_level > 0:
			procoins = 2500
			u.procoins += procoins
			g.db.add(u)
			send_repeatable_notification(u.id, f"@{v.username} has given you {procoins} Marseybux for the month of {month}! You can use them to buy awards in the [shop](/shop).")
		else: print(u.username)

	if request.host == 'pcmemes.net':
		u = g.db.query(User).filter_by(id=KIPPY_ID).one()
		u.procoins += 50000
		g.db.add(u)

	ma = ModAction(
		kind="monthly",
		user_id=v.id
	)
	g.db.add(ma)

	g.db.commit()
	
	return {"message": "Monthly coins granted"}


@app.get("/admin/shadowbanned")
@auth_required
def shadowbanned(v):
	if not (v and v.admin_level > 1): abort(404)
	users = [x for x in g.db.query(User).filter(User.shadowbanned != None).order_by(User.shadowbanned).all()]
	return render_template("shadowbanned.html", v=v, users=users)


@app.get("/admin/image_posts")
@admin_level_required(2)
def image_posts_listing(v):

	try: page = int(request.values.get('page', 1))
	except: page = 1

	posts = g.db.query(Submission).order_by(Submission.id.desc())

	firstrange = 25 * (page - 1)
	secondrange = firstrange+26
	posts = [x.id for x in posts if x.is_image][firstrange:secondrange]
	next_exists = (len(posts) > 25)
	posts = get_posts(posts[:25], v=v)

	return render_template("admin/image_posts.html", v=v, listing=posts, next_exists=next_exists, page=page, sort="new")


@app.get("/admin/reported/posts")
@admin_level_required(2)
def reported_posts(v):

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(Submission).filter_by(
		is_approved=None,
		is_banned=False
	).join(Submission.reports).order_by(Submission.id.desc()).offset(25 * (page - 1)).limit(26)

	listing = [p.id for p in listing]
	next_exists = len(listing) > 25
	listing = listing[:25]

	listing = get_posts(listing, v=v)

	return render_template("admin/reported_posts.html",
						   next_exists=next_exists, listing=listing, page=page, v=v)


@app.get("/admin/reported/comments")
@admin_level_required(2)
def reported_comments(v):

	page = max(1, int(request.values.get("page", 1)))

	listing = g.db.query(Comment
					   ).filter_by(
		is_approved=None,
		is_banned=False
	).join(Comment.reports).order_by(Comment.id.desc()).offset(25 * (page - 1)).limit(26).all()

	listing = [c.id for c in listing]
	next_exists = len(listing) > 25
	listing = listing[:25]

	listing = get_comments(listing, v=v)

	return render_template("admin/reported_comments.html",
						   next_exists=next_exists,
						   listing=listing,
						   page=page,
						   v=v,
						   standalone=True)

@app.get("/admin")
@admin_level_required(2)
def admin_home(v):
	with open('disable_signups', 'r') as f: x = f.read()

	if CF_ZONE == '3435tdfsdudebussylmaoxxt43': response = 'high'
	else: response = requests.get(f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/settings/security_level', headers=CF_HEADERS).json()['result']['value']
	
	x2 = response == 'under_attack'

	return render_template("admin/admin_home.html", v=v, x=x, x2=x2)

@app.post("/admin/disable_signups")
@admin_level_required(3)
def disable_signups(v):
	with open('disable_signups', 'r') as f: content = f.read()

	with open('disable_signups', 'w') as f:
		if content == "yes":
			f.write("no")
			ma = ModAction(
				kind="enable_signups",
				user_id=v.id,
			)
			g.db.add(ma)
			g.db.commit()
			return {"message": "Signups enabled!"}
		else:
			f.write("yes")
			ma = ModAction(
				kind="disable_signups",
				user_id=v.id,
			)
			g.db.add(ma)
			g.db.commit()
			return {"message": "Signups disabled!"}


@app.post("/admin/purge_cache")
@admin_level_required(3)
def purge_cache(v):
	cache.clear()
	response = str(requests.post(f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/purge_cache', headers=CF_HEADERS, data='{"purge_everything":true}'))

	ma = ModAction(
		kind="purge_cache",
		user_id=v.id
	)
	g.db.add(ma)

	if response == "<Response [200]>": return {"message": "Cache purged!"}
	return {"error": "Failed to purge cache."}


@app.post("/admin/under_attack")
@admin_level_required(3)
def under_attack(v):
	response = requests.get(f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/settings/security_level', headers=CF_HEADERS).json()['result']['value']

	if response == 'under_attack':
		ma = ModAction(
			kind="disable_under_attack",
			user_id=v.id,
		)
		g.db.add(ma)
		g.db.commit()

		response = str(requests.patch(f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/settings/security_level', headers=CF_HEADERS, data='{"value":"medium"}'))
		if response == "<Response [200]>": return {"message": "Under attack mode disabled!"}
		return {"error": "Failed to disable under attack mode."}
	else:
		ma = ModAction(
			kind="enable_under_attack",
			user_id=v.id,
		)
		g.db.add(ma)
		g.db.commit()

		response = str(requests.patch(f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/settings/security_level', headers=CF_HEADERS, data='{"value":"under_attack"}'))
		if response == "<Response [200]>": return {"message": "Under attack mode enabled!"}
		return {"error": "Failed to enable under attack mode."}

@app.get("/admin/badge_grant")
@admin_level_required(2)
def badge_grant_get(v):
	badges = g.db.query(BadgeDef).order_by(BadgeDef.id).all()
	return render_template("admin/badge_grant.html", v=v, badge_types=badges)


@app.post("/admin/badge_grant")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def badge_grant_post(v):
	badges = g.db.query(BadgeDef).order_by(BadgeDef.id).all()

	user = get_user(request.values.get("username").strip(), graceful=True)
	if not user:
		return render_template("admin/badge_grant.html", v=v, badge_types=badges, error="User not found.")

	try: badge_id = int(request.values.get("badge_id"))
	except: abort(400)

	if badge_id in (94,95,96,97,98,109): abort(403)

	if user.has_badge(badge_id):
		return render_template("admin/badge_grant.html", v=v, badge_types=badges, error="User already has that badge.")
	
	new_badge = Badge(badge_id=badge_id, user_id=user.id)

	desc = request.values.get("description")
	if desc: new_badge.description = desc

	url = request.values.get("url")
	if url: new_badge.url = url

	g.db.add(new_badge)
	g.db.flush()

	if v.id != user.id:
		text = f"@{v.username} has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}"
		send_notification(user.id, text)
	
	ma = ModAction(
		kind="badge_grant",
		user_id=v.id,
		target_user_id=user.id,
		_note=new_badge.name
	)
	g.db.add(ma)

	g.db.commit()
	return render_template("admin/badge_grant.html", v=v, badge_types=badges, msg="Badge granted!")



@app.get("/admin/badge_remove")
@admin_level_required(2)
def badge_remove_get(v):
	badges = g.db.query(BadgeDef).order_by(BadgeDef.id).all()

	return render_template("admin/badge_remove.html", v=v, badge_types=badges)


@app.post("/admin/badge_remove")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def badge_remove_post(v):
	badges = g.db.query(BadgeDef).order_by(BadgeDef.id).all()

	user = get_user(request.values.get("username").strip(), graceful=True)
	if not user:
		return render_template("admin/badge_remove.html", v=v, badge_types=badges, error="User not found.")

	try: badge_id = int(request.values.get("badge_id"))
	except: abort(400)

	badge = user.has_badge(badge_id)
	if badge:
		ma = ModAction(
			kind="badge_remove",
			user_id=v.id,
			target_user_id=user.id,
			_note=badge.name
		)
		g.db.add(ma)

		g.db.delete(badge)

		g.db.commit()
	
	return render_template("admin/badge_remove.html", v=v, badge_types=badges, msg="Badge removed!")


@app.get("/admin/users")
@admin_level_required(2)
def users_list(v):

	page = int(request.values.get("page", 1))

	users = g.db.query(User).filter_by(is_banned=0
									   ).order_by(User.created_utc.desc()
												  ).offset(25 * (page - 1)).limit(26)

	users = [x for x in users]

	next_exists = (len(users) > 25)
	users = users[:25]

	return render_template("admin/new_users.html",
						   v=v,
						   users=users,
						   next_exists=next_exists,
						   page=page,
						   )

@app.get("/admin/alt_votes")
@admin_level_required(2)
def alt_votes_get(v):

	u1 = request.values.get("u1")
	u2 = request.values.get("u2")

	if not u1 or not u2:
		return render_template("admin/alt_votes.html", v=v)

	u1 = get_user(u1)
	u2 = get_user(u2)

	u1_post_ups = g.db.query(
		Vote.submission_id).filter_by(
		user_id=u1.id,
		vote_type=1).all()
	u1_post_downs = g.db.query(
		Vote.submission_id).filter_by(
		user_id=u1.id,
		vote_type=-1).all()
	u1_comment_ups = g.db.query(
		CommentVote.comment_id).filter_by(
		user_id=u1.id,
		vote_type=1).all()
	u1_comment_downs = g.db.query(
		CommentVote.comment_id).filter_by(
		user_id=u1.id,
		vote_type=-1).all()
	u2_post_ups = g.db.query(
		Vote.submission_id).filter_by(
		user_id=u2.id,
		vote_type=1).all()
	u2_post_downs = g.db.query(
		Vote.submission_id).filter_by(
		user_id=u2.id,
		vote_type=-1).all()
	u2_comment_ups = g.db.query(
		CommentVote.comment_id).filter_by(
		user_id=u2.id,
		vote_type=1).all()
	u2_comment_downs = g.db.query(
		CommentVote.comment_id).filter_by(
		user_id=u2.id,
		vote_type=-1).all()

	data = {}
	data['u1_only_post_ups'] = len(
		[x for x in u1_post_ups if x not in u2_post_ups])
	data['u2_only_post_ups'] = len(
		[x for x in u2_post_ups if x not in u1_post_ups])
	data['both_post_ups'] = len(list(set(u1_post_ups) & set(u2_post_ups)))

	data['u1_only_post_downs'] = len(
		[x for x in u1_post_downs if x not in u2_post_downs])
	data['u2_only_post_downs'] = len(
		[x for x in u2_post_downs if x not in u1_post_downs])
	data['both_post_downs'] = len(
		list(set(u1_post_downs) & set(u2_post_downs)))

	data['u1_only_comment_ups'] = len(
		[x for x in u1_comment_ups if x not in u2_comment_ups])
	data['u2_only_comment_ups'] = len(
		[x for x in u2_comment_ups if x not in u1_comment_ups])
	data['both_comment_ups'] = len(
		list(set(u1_comment_ups) & set(u2_comment_ups)))

	data['u1_only_comment_downs'] = len(
		[x for x in u1_comment_downs if x not in u2_comment_downs])
	data['u2_only_comment_downs'] = len(
		[x for x in u2_comment_downs if x not in u1_comment_downs])
	data['both_comment_downs'] = len(
		list(set(u1_comment_downs) & set(u2_comment_downs)))

	data['u1_post_ups_unique'] = 100 * \
		data['u1_only_post_ups'] // len(u1_post_ups) if u1_post_ups else 0
	data['u2_post_ups_unique'] = 100 * \
		data['u2_only_post_ups'] // len(u2_post_ups) if u2_post_ups else 0
	data['u1_post_downs_unique'] = 100 * \
		data['u1_only_post_downs'] // len(
			u1_post_downs) if u1_post_downs else 0
	data['u2_post_downs_unique'] = 100 * \
		data['u2_only_post_downs'] // len(
			u2_post_downs) if u2_post_downs else 0

	data['u1_comment_ups_unique'] = 100 * \
		data['u1_only_comment_ups'] // len(
			u1_comment_ups) if u1_comment_ups else 0
	data['u2_comment_ups_unique'] = 100 * \
		data['u2_only_comment_ups'] // len(
			u2_comment_ups) if u2_comment_ups else 0
	data['u1_comment_downs_unique'] = 100 * \
		data['u1_only_comment_downs'] // len(
			u1_comment_downs) if u1_comment_downs else 0
	data['u2_comment_downs_unique'] = 100 * \
		data['u2_only_comment_downs'] // len(
			u2_comment_downs) if u2_comment_downs else 0

	return render_template("admin/alt_votes.html",
						   u1=u1,
						   u2=u2,
						   v=v,
						   data=data
						   )


@app.post("/admin/link_accounts")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def admin_link_accounts(v):

	u1 = int(request.values.get("u1"))
	u2 = int(request.values.get("u2"))

	new_alt = Alt(
		user1=u1, 
		user2=u2,
		is_manual=True
		)

	g.db.add(new_alt)

	ma = ModAction(
		kind="link_accounts",
		user_id=v.id,
		target_user_id=u1,
		_note=f'with {u2}'
	)
	g.db.add(ma)

	g.db.commit()
	return redirect(f"{SITE_FULL}/admin/alt_votes?u1={g.db.query(User).get(u1).username}&u2={g.db.query(User).get(u2).username}")


@app.get("/admin/removed/posts")
@admin_level_required(2)
def admin_removed(v):

	page = int(request.values.get("page", 1))

	if page < 1: abort(400)
	
	ids = g.db.query(Submission.id).join(User, User.id == Submission.author_id).filter(or_(Submission.is_banned==True, User.shadowbanned != None)).order_by(Submission.id.desc()).offset(25 * (page - 1)).limit(26).all()

	ids=[x[0] for x in ids]

	next_exists = len(ids) > 25

	ids = ids[:25]

	posts = get_posts(ids, v=v)

	return render_template("admin/removed_posts.html",
						   v=v,
						   listing=posts,
						   page=page,
						   next_exists=next_exists
						   )


@app.get("/admin/removed/comments")
@admin_level_required(2)
def admin_removed_comments(v):

	page = int(request.values.get("page", 1))
	
	ids = g.db.query(Comment.id).join(User, User.id == Comment.author_id).filter(or_(Comment.is_banned==True, User.shadowbanned != None)).order_by(Comment.id.desc()).offset(25 * (page - 1)).limit(26).all()

	ids=[x[0] for x in ids]

	next_exists = len(ids) > 25

	ids = ids[:25]

	comments = get_comments(ids, v=v)

	return render_template("admin/removed_comments.html",
						   v=v,
						   listing=comments,
						   page=page,
						   next_exists=next_exists
						   )


@app.post("/agendaposter/<user_id>")
@admin_level_required(2)
def agendaposter(user_id, v):
	user = g.db.query(User).filter_by(id=user_id).one_or_none()

	days = request.values.get("days", 30)
	expiry = float(days)
	expiry = int(time.time() + expiry*60*60*24)

	user.agendaposter = expiry
	g.db.add(user)

	for alt in user.alts:
		if alt.admin_level: return {"error": "User is an admin!"}
		alt.agendaposter = expiry
		g.db.add(alt)

	note = f"for {days} days"

	ma = ModAction(
		kind="agendaposter",
		user_id=v.id,
		target_user_id=user.id,
		note = note
	)
	g.db.add(ma)

	if not user.has_badge(28):
		badge = Badge(user_id=user.id, badge_id=28)
		g.db.add(badge)
		g.db.flush()
		send_notification(user.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")


	send_repeatable_notification(user.id, f"@{v.username} has marked you as an agendaposter ({note}).")

	g.db.commit()
	
	return redirect(user.url)



@app.post("/unagendaposter/<user_id>")
@admin_level_required(2)
def unagendaposter(user_id, v):
	user = g.db.query(User).filter_by(id=user_id).one_or_none()

	user.agendaposter = 0
	g.db.add(user)

	for alt in user.alts:
		alt.agendaposter = 0
		g.db.add(alt)

	ma = ModAction(
		kind="unagendaposter",
		user_id=v.id,
		target_user_id=user.id
	)

	g.db.add(ma)

	badge = user.has_badge(28)
	if badge: g.db.delete(badge)

	send_repeatable_notification(user.id, f"@{v.username} has unmarked you as an agendaposter.")

	g.db.commit()
	return {"message": "Chud theme disabled!"}


@app.post("/shadowban/<user_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def shadowban(user_id, v):
	user = g.db.query(User).filter_by(id=user_id).one_or_none()
	if user.admin_level != 0: abort(403)
	user.shadowbanned = v.username
	g.db.add(user)
	for alt in user.alts:
		if alt.admin_level: break
		alt.shadowbanned = v.username
		g.db.add(alt)
	ma = ModAction(
		kind="shadowban",
		user_id=v.id,
		target_user_id=user.id,
	)
	g.db.add(ma)
	
	cache.delete_memoized(frontlist)

	body = f"@{v.username} has shadowbanned @{user.username}"

	body_html = sanitize(body)


	new_comment = Comment(author_id=NOTIFICATIONS_ID,
						  parent_submission=None,
						  level=1,
						  body_html=body_html,
						  )
	g.db.add(new_comment)
	g.db.flush()
	for admin in g.db.query(User).filter(User.admin_level > 2, User.id != v.id).all():
		notif = Notification(comment_id=new_comment.id, user_id=admin.id)
		g.db.add(notif)



	g.db.commit()
	return {"message": "User shadowbanned!"}


@app.post("/unshadowban/<user_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def unshadowban(user_id, v):
	user = g.db.query(User).filter_by(id=user_id).one_or_none()
	if user.admin_level != 0: abort(403)
	user.shadowbanned = None
	user.ban_evade = 0
	g.db.add(user)
	for alt in user.alts:
		alt.shadowbanned = None
		alt.ban_evade = 0
		g.db.add(alt)

	ma = ModAction(
		kind="unshadowban",
		user_id=v.id,
		target_user_id=user.id,
	)
	g.db.add(ma)
	
	cache.delete_memoized(frontlist)

	g.db.commit()
	return {"message": "User unshadowbanned!"}

@app.post("/admin/verify/<user_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(3)
def verify(user_id, v):
	user = g.db.query(User).filter_by(id=user_id).one_or_none()
	user.verified = "Verified"
	g.db.add(user)

	ma = ModAction(
		kind="check",
		user_id=v.id,
		target_user_id=user.id,
	)
	g.db.add(ma)

	g.db.commit()
	return {"message": "User verfied!"}

@app.post("/admin/unverify/<user_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(3)
def unverify(user_id, v):
	user = g.db.query(User).filter_by(id=user_id).one_or_none()
	user.verified = None
	g.db.add(user)

	ma = ModAction(
		kind="uncheck",
		user_id=v.id,
		target_user_id=user.id,
	)
	g.db.add(ma)

	g.db.commit()
	return {"message": "User unverified!"}


@app.post("/admin/title_change/<user_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def admin_title_change(user_id, v):

	user = g.db.query(User).filter_by(id=user_id).one_or_none()

	new_name=request.values.get("title").strip()[:256]

	user.customtitleplain=new_name
	new_name = filter_emojis_only(new_name)

	user=g.db.query(User).filter_by(id=user.id).one_or_none()
	user.customtitle=new_name
	if request.values.get("locked"): user.flairchanged = int(time.time()) + 2629746
	else:
		user.flairchanged = None
		badge = user.has_badge(96)
		if badge: g.db.delete(badge)

	g.db.add(user)

	if user.flairchanged: kind = "set_flair_locked"
	else: kind = "set_flair_notlocked"
	
	ma=ModAction(
		kind=kind,
		user_id=v.id,
		target_user_id=user.id,
		_note=f'"{user.customtitleplain}"'
		)
	g.db.add(ma)
	g.db.commit()

	return redirect(user.url)

@app.post("/ban_user/<user_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def ban_user(user_id, v):
	
	user = g.db.query(User).filter_by(id=user_id).one_or_none()

	if not user: abort(404)

	if user.admin_level >= v.admin_level: abort(403)

	days = float(request.values.get("days")) if request.values.get('days') else 0

	reason = request.values.get("reason", "").strip()[:256]
	passed_reason = filter_emojis_only(reason)

	if len(passed_reason) > 256: passed_reason = reason

	user.ban(admin=v, reason=passed_reason, days=days)

	if request.values.get("alts"):
		for x in user.alts:
			if x.admin_level: break
			user.ban(admin=v, reason=passed_reason, days=days)

	if days:
		if reason: text = f"Your account has been suspended for {days} days for the following reason:\n\n> {reason}"
		else: text = f"Your account has been suspended for {days} days."
	else:
		if reason: text = f"Your account has been permanently suspended for the following reason:\n\n> {reason}"
		else: text = "Your account has been permanently suspended."

	send_repeatable_notification(user.id, text)
	
	if days == 0: duration = "permanent"
	elif days == 1: duration = "1 day"
	else: duration = f"{days} days"

	note = f'reason: "{reason}", duration: {duration}'
	ma=ModAction(
		kind="ban_user",
		user_id=v.id,
		target_user_id=user.id,
		_note=note
		)
	g.db.add(ma)

	if 'reason' in request.values:
		if reason.startswith("/post/"):
			post = int(reason.split("/post/")[1].split(None, 1)[0])
			post = get_post(post)
			post.bannedfor = True
			g.db.add(post)
		elif reason.startswith("/comment/"):
			comment = int(reason.split("/comment/")[1].split(None, 1)[0])
			comment = get_comment(comment)
			comment.bannedfor = True
			g.db.add(comment)


	body = f"@{v.username} has banned @{user.username} ({note})"

	body_html = sanitize(body)


	new_comment = Comment(author_id=NOTIFICATIONS_ID,
						  parent_submission=None,
						  level=1,
						  body_html=body_html,
						  )
	g.db.add(new_comment)
	g.db.flush()
	for admin in g.db.query(User).filter(User.admin_level > 2, User.id != v.id).all():
		notif = Notification(comment_id=new_comment.id, user_id=admin.id)
		g.db.add(notif)


	g.db.commit()

	if 'redir' in request.values: return redirect(user.url)
	else: return {"message": f"@{user.username} was banned!"}


@app.post("/unban_user/<user_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def unban_user(user_id, v):

	user = g.db.query(User).filter_by(id=user_id).one_or_none()

	if not user: abort(400)

	user.is_banned = 0
	user.unban_utc = 0
	user.ban_evade = 0
	user.ban_reason = None
	send_repeatable_notification(user.id, f"@{v.username} has unbanned you!")
	g.db.add(user)

	for x in user.alts:
		x.is_banned = 0
		x.unban_utc = 0
		x.ban_evade = 0
		x.ban_reason = None
		send_repeatable_notification(x.id, f"@{v.username} has unbanned you!")
		g.db.add(x)

	ma=ModAction(
		kind="unban_user",
		user_id=v.id,
		target_user_id=user.id,
		)
	g.db.add(ma)

	g.db.commit()

	if "@" in request.referrer: return redirect(user.url)
	else: return {"message": f"@{user.username} was unbanned!"}


@app.post("/ban_post/<post_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def ban_post(post_id, v):

	post = g.db.query(Submission).filter_by(id=post_id).one_or_none()

	if not post:
		abort(400)

	post.is_banned = True
	post.is_approved = None
	post.stickied = None
	post.is_pinned = False
	post.ban_reason = v.username
	g.db.add(post)

	

	ma=ModAction(
		kind="ban_post",
		user_id=v.id,
		target_submission_id=post.id,
		)
	g.db.add(ma)

	cache.delete_memoized(frontlist)

	v.coins += 1
	g.db.add(v)

	requests.post(f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/purge_cache', headers=CF_HEADERS, json={'files': [f"{SITE_FULL}/logged_out/"]})

	g.db.commit()

	return {"message": "Post removed!"}


@app.post("/unban_post/<post_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def unban_post(post_id, v):

	post = g.db.query(Submission).filter_by(id=post_id).one_or_none()

	if not post:
		abort(400)

	if post.is_banned:
		ma=ModAction(
			kind="unban_post",
			user_id=v.id,
			target_submission_id=post.id,
		)
		g.db.add(ma)

	post.is_banned = False
	post.is_approved = v.id

	g.db.add(post)

	cache.delete_memoized(frontlist)

	v.coins -= 1
	g.db.add(v)

	g.db.commit()

	return {"message": "Post approved!"}


@app.post("/distinguish/<post_id>")
@admin_level_required(1)
def api_distinguish_post(post_id, v):

	post = g.db.query(Submission).filter_by(id=post_id).one_or_none()

	if not post: abort(404)

	if post.author_id != v.id and v.admin_level < 2 : abort(403)

	if post.distinguish_level:
		post.distinguish_level = 0
		kind = 'undistinguish_post'
	else:
		post.distinguish_level = v.admin_level
		kind = 'distinguish_post'

	g.db.add(post)

	ma = ModAction(
		kind=kind,
		user_id=v.id,
		target_submission_id=post.id
	)
	g.db.add(ma)

	g.db.commit()

	if post.distinguish_level: return {"message": "Post distinguished!"}
	else: return {"message": "Post undistinguished!"}


@app.post("/sticky/<post_id>")
@admin_level_required(2)
def sticky_post(post_id, v):

	post = g.db.query(Submission).filter_by(id=post_id).one_or_none()
	if post and not post.stickied:
		pins = g.db.query(Submission.id).filter(Submission.stickied != None, Submission.is_banned == False).count()
		if pins > 2:
			if v.admin_level > 2:
				post.stickied = v.username
				post.stickied_utc = int(time.time()) + 3600
			else: return {"error": "Can't exceed 3 pinned posts limit!"}, 403
		else: post.stickied = v.username
		g.db.add(post)

		ma=ModAction(
			kind="pin_post",
			user_id=v.id,
			target_submission_id=post.id
		)
		g.db.add(ma)

		if v.id != post.author_id:
			send_repeatable_notification(post.author_id, f"@{v.username} has pinned your [post](/post/{post_id})!")

		cache.delete_memoized(frontlist)
		g.db.commit()
	return {"message": "Post pinned!"}

@app.post("/unsticky/<post_id>")
@admin_level_required(2)
def unsticky_post(post_id, v):

	post = g.db.query(Submission).filter_by(id=post_id).one_or_none()
	if post and post.stickied:
		if post.stickied.endswith('(pin award)'): return {"error": "Can't unpin award pins!"}, 403

		post.stickied = None
		post.stickied_utc = None
		g.db.add(post)

		ma=ModAction(
			kind="unpin_post",
			user_id=v.id,
			target_submission_id=post.id
		)
		g.db.add(ma)

		if v.id != post.author_id:
			send_repeatable_notification(post.author_id, f"@{v.username} has unpinned your [post](/post/{post_id})!")

		cache.delete_memoized(frontlist)
		g.db.commit()
	return {"message": "Post unpinned!"}

@app.post("/sticky_comment/<cid>")
@admin_level_required(2)
def sticky_comment(cid, v):
	
	comment = get_comment(cid, v=v)

	if not comment.is_pinned:
		comment.is_pinned = v.username
		g.db.add(comment)

		ma=ModAction(
			kind="pin_comment",
			user_id=v.id,
			target_comment_id=comment.id
		)
		g.db.add(ma)

		if v.id != comment.author_id:
			message = f"@{v.username} has pinned your [comment]({comment.sl})!"
			send_repeatable_notification(comment.author_id, message)

		g.db.commit()
	return {"message": "Comment pinned!"}
	

@app.post("/unsticky_comment/<cid>")
@admin_level_required(2)
def unsticky_comment(cid, v):
	
	comment = get_comment(cid, v=v)
	
	if comment.is_pinned:
		if comment.is_pinned.endswith("(pin award)"): return {"error": "Can't unpin award pins!"}, 403

		comment.is_pinned = None
		g.db.add(comment)

		ma=ModAction(
			kind="unpin_comment",
			user_id=v.id,
			target_comment_id=comment.id
		)
		g.db.add(ma)

		if v.id != comment.author_id:
			message = f"@{v.username} has unpinned your [comment]({comment.sl})!"
			send_repeatable_notification(comment.author_id, message)

		g.db.commit()
	return {"message": "Comment unpinned!"}


@app.post("/ban_comment/<c_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def api_ban_comment(c_id, v):

	comment = g.db.query(Comment).filter_by(id=c_id).one_or_none()
	if not comment:
		abort(404)

	comment.is_banned = True
	comment.is_approved = None
	comment.ban_reason = v.username
	g.db.add(comment)
	ma=ModAction(
		kind="ban_comment",
		user_id=v.id,
		target_comment_id=comment.id,
		)
	g.db.add(ma)
	g.db.commit()
	return {"message": "Comment removed!"}


@app.post("/unban_comment/<c_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def api_unban_comment(c_id, v):

	comment = g.db.query(Comment).filter_by(id=c_id).one_or_none()
	if not comment: abort(404)
	
	if comment.author.agendaposter and AGENDAPOSTER_PHRASE not in comment.body.lower():
		return {"error": "You can't bypass the agendaposter award!"}

	if comment.is_banned:
		ma=ModAction(
			kind="unban_comment",
			user_id=v.id,
			target_comment_id=comment.id,
			)
		g.db.add(ma)

	comment.is_banned = False
	comment.is_approved = v.id

	g.db.add(comment)

	g.db.commit()

	return {"message": "Comment approved!"}


@app.post("/distinguish_comment/<c_id>")
@admin_level_required(1)
def admin_distinguish_comment(c_id, v):
	
	
	comment = get_comment(c_id, v=v)

	if comment.author_id != v.id: abort(403)

	if comment.distinguish_level:
		comment.distinguish_level = 0
		kind = 'distinguish_comment'
	else:
		comment.distinguish_level = v.admin_level
		kind = 'undistinguish_comment'

	g.db.add(comment)

	ma = ModAction(
		kind=kind,
		user_id=v.id,
		target_comment_id=comment.id
	)
	g.db.add(ma)

	g.db.commit()

	if comment.distinguish_level: return {"message": "Comment distinguished!"}
	else: return {"message": "Comment undistinguished!"}

@app.get("/admin/dump_cache")
@admin_level_required(2)
def admin_dump_cache(v):
	cache.clear()

	ma = ModAction(
		kind="dump_cache",
		user_id=v.id
	)
	g.db.add(ma)

	return {"message": "Internal cache cleared."}


@app.get("/admin/banned_domains/")
@admin_level_required(3)
def admin_banned_domains(v):

	banned_domains = g.db.query(BannedDomain).all()
	return render_template("admin/banned_domains.html", v=v, banned_domains=banned_domains)

@app.post("/admin/banned_domains")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(3)
def admin_toggle_ban_domain(v):

	domain=request.values.get("domain", "").strip()
	if not domain: abort(400)

	reason=request.values.get("reason", "").strip()

	d = g.db.query(BannedDomain).filter_by(domain=domain).one_or_none()
	if d:
		g.db.delete(d)
		ma = ModAction(
			kind="unban_domain",
			user_id=v.id,
			_note=domain
		)
		g.db.add(ma)

	else:
		d = BannedDomain(domain=domain, reason=reason)
		g.db.add(d)
		ma = ModAction(
			kind="ban_domain",
			user_id=v.id,
			_note=f'{domain}, reason: {reason}'
		)
		g.db.add(ma)

	g.db.commit()

	return redirect(f"{SITE_FULL}/admin/banned_domains/")


@app.post("/admin/nuke_user")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def admin_nuke_user(v):

	user=get_user(request.values.get("user"))

	for post in g.db.query(Submission).filter_by(author_id=user.id).all():
		if post.is_banned:
			continue
			
		post.is_banned=True
		g.db.add(post)

	for comment in g.db.query(Comment).filter_by(author_id=user.id).all():
		if comment.is_banned:
			continue

		comment.is_banned=True
		g.db.add(comment)

	ma=ModAction(
		kind="nuke_user",
		user_id=v.id,
		target_user_id=user.id,
		)
	g.db.add(ma)

	g.db.commit()

	return redirect(user.url)


@app.post("/admin/unnuke_user")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def admin_nunuke_user(v):

	user=get_user(request.values.get("user"))

	for post in g.db.query(Submission).filter_by(author_id=user.id).all():
		if not post.is_banned:
			continue
			
		post.is_banned=False
		g.db.add(post)

	for comment in g.db.query(Comment).filter_by(author_id=user.id).all():
		if not comment.is_banned:
			continue

		comment.is_banned=False
		g.db.add(comment)

	ma=ModAction(
		kind="unnuke_user",
		user_id=v.id,
		target_user_id=user.id,
		)
	g.db.add(ma)

	g.db.commit()

	return redirect(user.url)