import time
import imagehash
from os import remove
from PIL import Image as IMAGE

from files.helpers.wrappers import *
from files.helpers.alerts import *
from files.helpers.sanitize import *
from files.helpers.markdown import *
from files.helpers.security import *
from files.helpers.get import *
from files.helpers.images import *
from files.helpers.const import *
from files.classes import *
from flask import *
from files.__main__ import app, cache, limiter
from .front import frontlist
from files.helpers.discord import add_role

SITE_NAME = environ.get("SITE_NAME", "").strip()
if SITE_NAME == 'PCM': cc = "splash mountain"
else: cc = "country club"

@app.get("/distribute/<cid>")
@admin_level_required(3)
def distribute(v, cid):
	try: int(cid)
	except: abort(400)
	post = g.db.query(Comment).filter_by(id=cid).first().post.permalink
	votes = g.db.query(CommentVote).filter_by(comment_id=cid)
	autobetter = g.db.query(User).filter_by(id=AUTOBETTER_ID).first()
	coinsperperson = int(autobetter.coins / votes.count())
	for vote in votes:
		u = vote.user
		u.coins += coinsperperson
		send_notification(u.id, f"You won {coinsperperson} coins betting on {post} !")
		g.db.add(u)

	autobetter.coins = 0
	g.db.add(autobetter)
	g.db.commit()
	return str(coinsperperson)

@app.get("/truescore")
@admin_level_required(2)
def truescore(v):
	users = g.db.query(User).order_by(User.truecoins.desc()).limit(25).all()
	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}truescore.html", v=v, users=users)

@app.post("/@<username>/revert_actions")
@limiter.limit("1/second")
@admin_level_required(3)
@validate_formkey
def revert_actions(v, username):
	user = get_user(username)
	if not user: abort(404)
	
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
		g.db.add(user)
		for u in user.alts:
			u.shadowbanned = None
			u.is_banned = 0
			u.unban_utc = 0
			u.ban_evade = 0
			g.db.add(u)

	g.db.commit()
	return {"message": "Admin actions reverted!"}

@app.post("/@<username>/club_allow")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def club_allow(v, username):

	u = get_user(username, v=v)

	if not u: abort(404)

	if u.admin_level >= v.admin_level: return {"error": "noob"}

	u.club_allowed = True
	u.club_banned = False
	g.db.add(u)

	for x in u.alts_unique:
		x.club_allowed = True
		x.club_banned = False
		g.db.add(x)

	g.db.commit()
	return {"message": f"@{username} has been allowed into the {cc}!"}

@app.post("/@<username>/club_ban")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def club_ban(v, username):

	u = get_user(username, v=v)

	if not u: abort(404)

	if u.admin_level >= v.admin_level: return {"error": "noob"}

	u.club_banned = True
	u.club_allowed = False

	for x in u.alts_unique:
		x.club_banned = True
		u.club_allowed = False
		g.db.add(x)

	g.db.commit()
	return {"message": f"@{username} has been kicked from the {cc}. Deserved."}


@app.post("/@<username>/make_admin")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def make_admin(v, username):
	if 'pcm' in request.host or (SITE_NAME == 'Drama' and v.admin_level > 2) or ('rama' not in request.host and 'pcm' not in request.host):
		user = get_user(username)
		if not user: abort(404)
		user.admin_level = 2
		g.db.add(user)
		g.db.commit()
	return {"message": "User has been made admin!"}


@app.post("/@<username>/remove_admin")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def remove_admin(v, username):
	if 'pcm' in request.host or (SITE_NAME == 'Drama' and v.admin_level > 2) or ('rama' not in request.host and 'pcm' not in request.host):
		user = get_user(username)
		if not user: abort(404)
		user.admin_level = 0
		g.db.add(user)
		g.db.commit()
	return {"message": "Admin removed!"}


@app.post("/@<username>/make_meme_admin")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def make_meme_admin(v, username):
	if 'pcm' in request.host or (SITE_NAME == 'Drama' and v.admin_level > 2) or ('rama' not in request.host and 'pcm' not in request.host):
		user = get_user(username)
		if not user: abort(404)
		user.admin_level = 1
		g.db.add(user)
		g.db.commit()
	return {"message": "User has been made meme admin!"}


@app.post("/@<username>/remove_meme_admin")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def remove_meme_admin(v, username):
	if 'pcm' in request.host or (SITE_NAME == 'Drama' and v.admin_level > 2) or ('rama' not in request.host and 'pcm' not in request.host):
		user = get_user(username)
		if not user: abort(404)
		user.admin_level = 0
		g.db.add(user)
		g.db.commit()
	return {"message": "Meme admin removed!"}


@app.post("/admin/monthly")
@limiter.limit("1/day")
@admin_level_required(2)
@validate_formkey
def monthly(v):
	if 'pcm' in request.host or (SITE_NAME == 'Drama' and v.admin_level > 2) or ('rama' not in request.host and 'pcm' not in request.host):
		thing = g.db.query(AwardRelationship).order_by(AwardRelationship.id.desc()).first().id
		for u in g.db.query(User).filter(User.patron > 0).all():
			if u.patron == 1: procoins = 2500
			elif u.patron == 2: procoins = 5000
			elif u.patron == 3: procoins = 10000
			elif u.patron == 4: procoins = 25000
			elif u.patron == 5: procoins = 50000

			u.procoins += procoins
			send_notification(u.id, f"You were given {procoins} Marseybux! You can use them to buy awards in the [shop](/shop).")
			g.db.add(u)

		g.db.commit()
	return {"message": "Monthly coins granted"}


@app.get('/admin/rules')
@admin_level_required(2)
def get_rules(v):

	try:
		with open(f'rules_{SITE_NAME}.html', 'r') as f: rules = f.read()
	except Exception:
		rules = None

	return render_template('admin/rules.html', v=v, rules=rules)


@app.post('/admin/rules')
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def post_rules(v):

	text = request.values.get('rules', '').strip()

	with open(f'rules_{SITE_NAME}.html', 'w+') as f: f.write(text)

	with open(f'rules_{SITE_NAME}.html', 'r') as f: rules = f.read()

	ma = ModAction(
		kind="change_rules",
		user_id=v.id,
	)
	g.db.add(ma)

	g.db.commit()

	return render_template('admin/rules.html', v=v, rules=rules)


@app.get("/admin/shadowbanned")
@auth_required
def shadowbanned(v):
	if not (v and v.admin_level > 1): abort(404)
	users = [x for x in g.db.query(User).filter(User.shadowbanned != None).all()]
	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}shadowbanned.html", v=v, users=users)


@app.get("/admin/agendaposters")
@auth_required
def agendaposters(v):
	if not (v and v.admin_level > 1): abort(404)
	users = [x for x in g.db.query(User).filter_by(agendaposter = True).all()]
	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}agendaposters.html", v=v, users=users)


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

	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}admin/image_posts.html", v=v, listing=posts, next_exists=next_exists, page=page, sort="new")


@app.get("/admin/reported/posts")
@admin_level_required(2)
def reported_posts(v):

	page = max(1, int(request.values.get("page", 1)))

	posts = g.db.query(Submission).filter_by(
		is_approved=0,
		is_banned=False
	).join(Submission.reports).order_by(Submission.id.desc()).offset(25 * (page - 1)).limit(26)

	listing = [p.id for p in posts]
	next_exists = (len(listing) > 25)
	listing = listing[:25]

	listing = get_posts(listing, v=v)

	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}admin/reported_posts.html",
						   next_exists=next_exists, listing=listing, page=page, v=v)


@app.get("/admin/reported/comments")
@admin_level_required(2)
def reported_comments(v):

	page = max(1, int(request.values.get("page", 1)))

	posts = g.db.query(Comment
					   ).filter_by(
		is_approved=0,
		is_banned=False
	).join(Comment.reports).order_by(Comment.id.desc()).offset(25 * (page - 1)).limit(26).all()

	listing = [p.id for p in posts]
	next_exists = (len(listing) > 25)
	listing = listing[:25]

	listing = get_comments(listing, v=v)

	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}admin/reported_comments.html",
						   next_exists=next_exists,
						   listing=listing,
						   page=page,
						   v=v,
						   standalone=True)

@app.get("/admin")
@admin_level_required(2)
def admin_home(v):
	with open('disablesignups', 'r') as f:
		x = f.read()
		if v and v.oldsite: template = ''
		else: template = 'CHRISTMAS/'
		return render_template(f"{template}admin/admin_home.html", v=v, x=x)

@app.post("/admin/disablesignups")
@admin_level_required(2)
@validate_formkey
def disablesignups(v):
	with open('disablesignups', 'r') as f: content = f.read()

	with open('disablesignups', 'w') as f:
		if content == "yes":
			f.write("no")
			return {"message": "Signups enabed!"}
		else:
			f.write("yes")
			return {"message": "Signups disabled!"}

@app.get("/admin/badge_grant")
@admin_level_required(2)
def badge_grant_get(v):

	errors = {"already_owned": "That user already has that badge.",
			  "no_user": "That user doesn't exist."
			  }

	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}admin/badge_grant.html",
						   v=v,
						   badge_types=BADGES,
						   error=errors.get(
							   request.values.get("error"),
							   None) if request.values.get('error') else None,
						   msg="Badge successfully assigned" if request.values.get(
							   "msg") else None
						   )


@app.post("/admin/badge_grant")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def badge_grant_post(v):

	user = get_user(request.values.get("username").strip(), graceful=True)
	if not user: return redirect("/badge_grant?error=no_user")

	try: badge_id = int(request.values.get("badge_id"))
	except: abort(400)

	existing = user.has_badge(badge_id)
	if existing:
		g.db.delete(existing)
		g.db.commit()
		return redirect("/admin/badge_grant")
	
	new_badge = Badge(badge_id=badge_id, user_id=user.id)

	desc = request.values.get("description")
	if desc: new_badge.description = desc

	url = request.values.get("url")
	if url: new_badge.url = url

	g.db.add(new_badge)
	g.db.flush()
	
	text = f"""
	@{v.username} has given you the following profile badge:
	\n\n![]({new_badge.path})
	\n\n{new_badge.name}
	"""
	send_notification(user.id, text)	
	
	g.db.commit()
	return redirect("/admin/badge_grant")


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

	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}admin/new_users.html",
						   v=v,
						   users=users,
						   next_exists=next_exists,
						   page=page,
						   )

@app.get("/admin/alt_votes")
@admin_level_required(2)
def alt_votes_get(v):

	if not request.values.get("u1") or not request.values.get("u2"):
		if v and v.oldsite: template = ''
		else: template = 'CHRISTMAS/'
		return render_template(f"{template}admin/alt_votes.html", v=v)

	u1 = request.values.get("u1")
	u2 = request.values.get("u2")

	if not u1 or not u2:
		return redirect("/admin/alt_votes")

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

	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}admin/alt_votes.html",
						   u1=u1,
						   u2=u2,
						   v=v,
						   data=data
						   )


@app.post("/admin/link_accounts")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def admin_link_accounts(v):

	u1 = int(request.values.get("u1"))
	u2 = int(request.values.get("u2"))

	new_alt = Alt(
		user1=u1, 
		user2=u2,
		is_manual=True
		)

	g.db.add(new_alt)

	g.db.commit()
	return redirect(f"/admin/alt_votes?u1={g.db.query(User).get(u1).username}&u2={g.db.query(User).get(u2).username}")


@app.get("/admin/removed/posts")
@admin_level_required(2)
def admin_removed(v):

	page = int(request.values.get("page", 1))
	
	ids = g.db.query(Submission.id).join(User, User.id == Submission.author_id).filter(or_(Submission.is_banned==True, User.shadowbanned != None)).order_by(Submission.id.desc()).offset(25 * (page - 1)).limit(26).all()

	ids=[x[0] for x in ids]

	next_exists = len(ids) > 25

	ids = ids[:25]

	posts = get_posts(ids, v=v)

	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}admin/removed_posts.html",
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

	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}admin/removed_comments.html",
						   v=v,
						   listing=comments,
						   page=page,
						   next_exists=next_exists
						   )


@app.post("/agendaposter/<user_id>")
@admin_level_required(2)
@validate_formkey
def agendaposter(user_id, v):
	user = g.db.query(User).filter_by(id=user_id).first()

	expiry = request.values.get("days", 0)
	if expiry:
		expiry = int(expiry)
		expiry = g.timestamp + expiry*60*60*24
	else: expiry = 0

	user.agendaposter = not user.agendaposter
	user.agendaposter_expires_utc = expiry
	g.db.add(user)
	for alt in user.alts:
		if alt.admin_level > 0: break
		alt.agendaposter = user.agendaposter
		alt.agendaposter_expires_utc = expiry
		g.db.add(alt)

	note = None

	if not user.agendaposter: kind = "unagendaposter"
	else:
		kind = "agendaposter"
		note = f"for {request.values.get('days')} days" if expiry else "never expires"

	ma = ModAction(
		kind=kind,
		user_id=v.id,
		target_user_id=user.id,
		note = note
	)
	g.db.add(ma)

	if user.agendaposter:
		if not user.has_badge(26):
			badge = Badge(user_id=user.id, badge_id=26)
			g.db.add(badge)
	else:
		badge = user.has_badge(26)
		if badge: g.db.delete(badge)

	if user.agendaposter: send_notification(user.id, f"You have been marked by an admin as an agendaposter ({note}).")
	else: send_notification(user.id, f"You have been unmarked by an admin as an agendaposter.")

	g.db.commit()
	if user.agendaposter: return redirect(user.url)
	return {"message": "Agendaposter theme disabled!"}


@app.post("/shadowban/<user_id>")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def shadowban(user_id, v):
	user = g.db.query(User).filter_by(id=user_id).first()
	if user.admin_level != 0: abort(403)
	user.shadowbanned = v.username
	g.db.add(user)
	for alt in user.alts:
		if alt.admin_level > 0: break
		alt.shadowbanned = v.username
		g.db.add(alt)
	ma = ModAction(
		kind="shadowban",
		user_id=v.id,
		target_user_id=user.id,
	)
	g.db.add(ma)
	
	cache.delete_memoized(frontlist)

	g.db.commit()
	return {"message": "User shadowbanned!"}


@app.post("/unshadowban/<user_id>")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def unshadowban(user_id, v):
	user = g.db.query(User).filter_by(id=user_id).first()
	if user.admin_level != 0: abort(403)
	user.shadowbanned = None
	g.db.add(user)
	for alt in user.alts:
		alt.shadowbanned = None
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
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def verify(user_id, v):
	user = g.db.query(User).filter_by(id=user_id).first()
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
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def unverify(user_id, v):
	user = g.db.query(User).filter_by(id=user_id).first()
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
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def admin_title_change(user_id, v):

	user = g.db.query(User).filter_by(id=user_id).first()

	if user.admin_level != 0: abort(403)

	new_name=request.values.get("title").strip()[:256]

	user.customtitleplain=new_name
	new_name = sanitize(new_name)

	user=g.db.query(User).with_for_update().filter_by(id=user.id).first()
	user.customtitle=new_name
	if request.values.get("locked"): user.flairchanged = time.time() + 2629746
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
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def ban_user(user_id, v):
	
	user = g.db.query(User).filter_by(id=user_id).first()

	if user.admin_level >= v.admin_level: abort(403)

	days = float(request.values.get("days")) if request.values.get('days') else 0
	reason = sanitize(request.values.get("reason", ""))[:256]
	message = request.values.get("reason", "").strip()[:256]

	if not user: abort(400)
	
	if days > 0:
		if message:
			text = f"Your account has been suspended for {days} days for the following reason:\n\n> {message}"
		else:
			text = f"Your account has been suspended for {days} days."
		user.ban(admin=v, reason=reason, days=days)

	else:
		if message:
			text = f"Your account has been permanently suspended for the following reason:\n\n> {message}"
		else:
			text = "Your account has been permanently suspended."

		user.ban(admin=v, reason=reason)

	if request.values.get("alts", ""):
		for x in user.alts:
			if x.admin_level > 0: break
			x.ban(admin=v, reason=reason)

	send_notification(user.id, text)
	
	if days == 0: duration = "permanent"
	elif days == 1: duration = "1 day"
	else: duration = f"{days} days"
	ma=ModAction(
		kind="ban_user",
		user_id=v.id,
		target_user_id=user.id,
		_note=f'reason: "{reason}", duration: {duration}'
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
	g.db.commit()

	if 'redir' in request.values: return redirect(user.url)
	else: return {"message": f"@{user.username} was banned!"}


@app.post("/unban_user/<user_id>")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def unban_user(user_id, v):

	user = g.db.query(User).filter_by(id=user_id).first()

	if not user:
		abort(400)

	user.is_banned = 0
	user.unban_utc = 0
	user.ban_evade = 0
	g.db.add(user)

	if request.values.get("alts", ""):
		for x in user.alts:
			if x.admin_level == 0:
				x.is_banned = 0
				x.unban_utc = 0
				x.ban_evade = 0
				g.db.add(x)

	send_notification(user.id,
					  "Your account has been reinstated. Please carefully review and abide by the [rules](/post/2510) to ensure that you don't get suspended again.")

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
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def ban_post(post_id, v):

	post = g.db.query(Submission).filter_by(id=post_id).first()

	if not post:
		abort(400)

	post.is_banned = True
	post.is_approved = 0
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

	v.coins += 2
	g.db.add(v)

	g.db.commit()

	return {"message": "Post removed!"}


@app.post("/unban_post/<post_id>")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def unban_post(post_id, v):

	post = g.db.query(Submission).filter_by(id=post_id).first()

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

	v.coins -= 2
	g.db.add(v)

	g.db.commit()

	return {"message": "Post approved!"}


@app.post("/distinguish/<post_id>")
@admin_level_required(1)
@validate_formkey
def api_distinguish_post(post_id, v):

	post = g.db.query(Submission).filter_by(id=post_id).first()

	if not post:
		abort(404)

	if not post.author_id == v.id:
		abort(403)

	if post.distinguish_level:
		post.distinguish_level = 0
	else:
		post.distinguish_level = v.admin_level

	g.db.add(post)

	g.db.commit()

	return {"message": "Post distinguished!"}


@app.post("/sticky/<post_id>")
@admin_level_required(2)
@validate_formkey
def api_sticky_post(post_id, v):

	post = g.db.query(Submission).filter_by(id=post_id).first()
	if post:
		if post.stickied:
			if post.stickied.startswith("t:"): abort(403)
			else: post.stickied = None
		else:
			pins = g.db.query(Submission.id).filter(Submission.stickied != None, Submission.is_banned == False).count()
			if pins > 2: return {"error": "Can't exceed 3 pinned posts limit!"}, 403
			post.stickied = v.username
		g.db.add(post)

		ma=ModAction(
			kind="pin_post" if post.stickied else "unpin_post",
			user_id=v.id,
			target_submission_id=post.id
		)
		g.db.add(ma)

		cache.delete_memoized(frontlist)

		if post.stickied:
			if v.id != post.author_id:
				message = f"@{v.username} has pinned your [post](/post/{post_id})!"
				send_notification(post.author_id, message)
			g.db.commit()
			return {"message": "Post pinned!"}
		else:
			if v.id != post.author_id:
				message = f"@{v.username} has unpinned your [post](/post/{post_id})!"
				send_notification(post.author_id, message)
			g.db.commit()
			return {"message": "Post unpinned!"}

@app.post("/ban_comment/<c_id>")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def api_ban_comment(c_id, v):

	comment = g.db.query(Comment).filter_by(id=c_id).first()
	if not comment:
		abort(404)

	comment.is_banned = True
	comment.is_approved = 0
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
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def api_unban_comment(c_id, v):

	comment = g.db.query(Comment).filter_by(id=c_id).first()
	if not comment: abort(404)
	g.db.add(comment)

	if comment.is_banned:
		ma=ModAction(
			kind="unban_comment",
			user_id=v.id,
			target_comment_id=comment.id,
			)
		g.db.add(ma)

	comment.is_banned = False
	comment.is_approved = v.id

	g.db.commit()

	return {"message": "Comment approved!"}


@app.post("/distinguish_comment/<c_id>")
@admin_level_required(1)
@validate_formkey
def admin_distinguish_comment(c_id, v):
	
	
	comment = get_comment(c_id, v=v)

	if comment.author_id != v.id: abort(403)

	comment.distinguish_level = 0 if comment.distinguish_level else v.admin_level

	g.db.add(comment)
	html = render_template("comments.html", v=v, comments=[comment])

	html = str(BeautifulSoup(html, features="html.parser").find(id=f"comment-{comment.id}-only"))

	g.db.commit()

	return html

@app.get("/admin/dump_cache")
@admin_level_required(2)
def admin_dump_cache(v):
	cache.clear()
	return {"message": "Internal cache cleared."}


@app.get("/admin/banned_domains/")
@admin_level_required(2)
def admin_banned_domains(v):

	banned_domains = g.db.query(BannedDomain).all()
	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}admin/banned_domains.html", v=v, banned_domains=banned_domains)

@app.post("/admin/banned_domains")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def admin_toggle_ban_domain(v):

	domain=request.values.get("domain", "").strip()
	if not domain: abort(400)

	reason=request.values.get("reason", "").strip()

	d = g.db.query(BannedDomain).filter_by(domain=domain).first()
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

	return redirect("/admin/banned_domains/")


@app.post("/admin/nuke_user")
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
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
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
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