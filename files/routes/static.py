from files.mail import *
from files.__main__ import app, limiter, mail
from files.helpers.alerts import *
from files.helpers.const import *
from files.classes.award import AWARDS
from sqlalchemy import func
import os
import calendar
import matplotlib.pyplot as plt
from files.classes.mod_logs import ACTIONTYPES, ACTIONTYPES2
from files.classes.badges import BadgeDef

@app.get("/r/drama/comments/<id>/<title>")
@app.get("/r/Drama/comments/<id>/<title>")
def rdrama(id, title):
	id = ''.join(f'{x}/' for x in id)
	return redirect(f'/archives/drama/comments/{id}{title}.html')


@app.get("/marseys")
@auth_required
def marseys(v):
	if SITE_NAME == 'rDrama':
		marseys = g.db.query(Marsey, User).join(User, User.id==Marsey.author_id)
		sort = request.values.get("sort", "usage")
		if sort == "usage": marseys = marseys.order_by(Marsey.count.desc(), User.username)
		else: marseys = marseys.order_by(User.username, Marsey.count.desc())
	else:
		marseys = g.db.query(Marsey).order_by(Marsey.count.desc())
	return render_template("marseys.html", v=v, marseys=marseys)

@app.get("/marsey_list.json")
@cache.memoize(timeout=600)
def marsey_list():
	# From database
	emojis = [{
		"name": emoji.name,
		"author": author if SITE_NAME == 'rDrama' or author == "anton-d" else None,
		# yikes, I don't really like this DB schema. Next time be better
		"tags": emoji.tags.split(" ") + [emoji.name[len("marsey"):] if emoji.name.startswith("marsey") else emoji.name],
		"count": emoji.count,
		"class": "Marsey"
	} for emoji, author in g.db.query(Marsey, User.username).join(User, User.id==Marsey.author_id).order_by(Marsey.count.desc())]

	# Stastic shit
	shit = open("files/assets/emojis.json", "r", encoding="utf-8")
	emojis = emojis + json.load(shit)
	shit.close()

	if SITE_NAME == 'Cringetopia':
		shit = open("files/assets/emojis.cringetopia.json", "r", encoding="utf-8")
		emojis = emojis + json.load(shit)
		shit.close()

	# return str(marseys).replace("'",'"')
	return jsonify(emojis)

@app.get('/rules')
@app.get('/sidebar')
@app.get('/logged_out/rules')
@app.get('/logged_out/sidebar')
@auth_desired
def sidebar(v):
	if not v and not request.path.startswith('/logged_out'): return redirect(f"/logged_out{request.full_path}")
	if v and request.path.startswith('/logged_out'): return redirect(request.full_path.replace('/logged_out',''))

	return render_template('sidebar.html', v=v)


@app.get("/stats")
@auth_required
def participation_stats(v):

	return render_template("admin/content_stats.html", v=v, title="Content Statistics", data=stats(site=SITE))


@cache.memoize(timeout=86400)
def stats(site=None):
	day = int(time.time()) - 86400

	week = int(time.time()) - 604800
	posters = g.db.query(Submission.author_id).distinct(Submission.author_id).filter(Submission.created_utc > week).all()
	commenters = g.db.query(Comment.author_id).distinct(Comment.author_id).filter(Comment.created_utc > week).all()
	voters = g.db.query(Vote.user_id).distinct(Vote.user_id).filter(Vote.created_utc > week).all()
	commentvoters = g.db.query(CommentVote.user_id).distinct(CommentVote.user_id).filter(CommentVote.created_utc > week).all()

	active_users = set(posters) | set(commenters) | set(voters) | set(commentvoters)

	stats = {"marseys": g.db.query(Marsey).count(),
			"users": g.db.query(User).count(),
			"private users": g.db.query(User).filter_by(is_private=True).count(),
			"banned users": g.db.query(User).filter(User.is_banned > 0).count(),
			"verified email users": g.db.query(User).filter_by(is_activated=True).count(),
			"coins in circulation": g.db.query(func.sum(User.coins)).scalar(),
			"total shop sales": g.db.query(func.sum(User.coins_spent)).scalar(),
			"signups last 24h": g.db.query(User).filter(User.created_utc > day).count(),
			"total posts": g.db.query(Submission).count(),
			"posting users": g.db.query(Submission.author_id).distinct().count(),
			"listed posts": g.db.query(Submission).filter_by(is_banned=False).filter(Submission.deleted_utc == 0).count(),
			"removed posts (by admins)": g.db.query(Submission).filter_by(is_banned=True).count(),
			"deleted posts (by author)": g.db.query(Submission).filter(Submission.deleted_utc > 0).count(),
			"posts last 24h": g.db.query(Submission).filter(Submission.created_utc > day).count(),
			"total comments": g.db.query(Comment).filter(Comment.author_id.notin_((AUTOJANNY_ID,NOTIFICATIONS_ID))).count(),
			"commenting users": g.db.query(Comment.author_id).distinct().count(),
			"removed comments (by admins)": g.db.query(Comment).filter_by(is_banned=True).count(),
			"deleted comments (by author)": g.db.query(Comment).filter(Comment.deleted_utc > 0).count(),
			"comments last_24h": g.db.query(Comment).filter(Comment.created_utc > day, Comment.author_id.notin_((AUTOJANNY_ID,NOTIFICATIONS_ID))).count(),
			"post votes": g.db.query(Vote).count(),
			"post voting users": g.db.query(Vote.user_id).distinct().count(),
			"comment votes": g.db.query(CommentVote).count(),
			"comment voting users": g.db.query(CommentVote.user_id).distinct().count(),
			"total upvotes": g.db.query(Vote).filter_by(vote_type=1).count() + g.db.query(CommentVote.comment_id).filter_by(vote_type=1).count(),
			"total downvotes": g.db.query(Vote).filter_by(vote_type=-1).count() + g.db.query(CommentVote.comment_id).filter_by(vote_type=-1).count(),
			"total awards": g.db.query(AwardRelationship).count(),
			"awards given": g.db.query(AwardRelationship).filter(or_(AwardRelationship.submission_id != None, AwardRelationship.comment_id != None)).count(),
			"users who posted, commented, or voted in the past 7 days": len(active_users),
			}


	if SITE_NAME == 'rDrama':
		furries1 = g.db.query(User).filter(User.house.like('Furry%')).count()
		femboys1 = g.db.query(User).filter(User.house.like('Femboy%')).count()
		vampires1 = g.db.query(User).filter(User.house.like('Vampire%')).count()
		racists1 = g.db.query(User).filter(User.house.like('Racist%')).count()

		furries2 = g.db.query(func.sum(User.truecoins)).filter(User.house.like('Furry%')).scalar()
		femboys2 = g.db.query(func.sum(User.truecoins)).filter(User.house.like('Femboy%')).scalar()
		vampires2 = g.db.query(func.sum(User.truecoins)).filter(User.house.like('Vampire%')).scalar()
		racists2 = g.db.query(func.sum(User.truecoins)).filter(User.house.like('Racist%')).scalar()

		stats2 = {"House furry members": furries1,
			"House femboy members": femboys1,
			"House vampire members": vampires1,
			"House racist members": racists1,
			"House furry total truescore": furries2,
			"House femboy total truescore": femboys2,
			"House vampire total truescore": vampires2,
			"House racist total truescore": racists2,
			}

		stats.update(stats2)

		accs = g.db.query(User).filter(User.id.in_(bots))

		for u in accs:
			g.db.add(u)

			if u.patron_utc and u.patron_utc < time.time():
				u.patron = 0
				u.patron_utc = 0

			if u.unban_utc and u.unban_utc < time.time():
				u.is_banned = 0
				u.unban_utc = 0
				u.ban_evade = 0

			if u.agendaposter and u.agendaposter < time.time():
				u.agendaposter = 0
				badge = u.has_badge(28)
				if badge: g.db.delete(badge)

			if u.flairchanged and u.flairchanged < time.time():
				u.flairchanged = None
				badge = u.has_badge(96)
				if badge: g.db.delete(badge)

			if u.marseyawarded and u.marseyawarded < time.time():
				u.marseyawarded = None
				badge = u.has_badge(98)
				if badge: g.db.delete(badge)

			if u.longpost and u.longpost < time.time():
				u.longpost = None
				badge = u.has_badge(97)
				if badge: g.db.delete(badge)

			if u.bird and u.bird < time.time():
				u.bird = None
				badge = u.has_badge(95)
				if badge: g.db.delete(badge)

			if u.progressivestack and u.progressivestack < time.time():
				u.progressivestack = None
				badge = u.has_badge(94)
				if badge: g.db.delete(badge)

			if u.rehab and u.rehab < time.time():
				u.rehab = None
				badge = u.has_badge(109)
				if badge: g.db.delete(badge)

			if u.deflector and u.deflector < time.time():
				u.deflector = None

	g.db.commit()

	return stats


@app.get("/chart")
def chart():
	return redirect('/weekly_chart')


@app.get("/weekly_chart")
@auth_required
def weekly_chart(v):
	file = cached_chart(kind="weekly", site=SITE)
	f = send_file(file)
	return f

@app.get("/daily_chart")
@auth_required
def daily_chart(v):
	file = cached_chart(kind="daily", site=SITE)
	f = send_file(file)
	return f


@cache.memoize(timeout=86400)
def cached_chart(kind, site):
	now = time.gmtime()
	midnight_this_morning = time.struct_time((now.tm_year,
											  now.tm_mon,
											  now.tm_mday,
											  0,
											  0,
											  0,
											  now.tm_wday,
											  now.tm_yday,
											  0)
											 )
	today_cutoff = calendar.timegm(midnight_this_morning)

	if SITE == 'rdrama.net':
		time_diff = time.time() - 1619827200
		num_of_weeks = int(time_diff / 604800)
		chart_width = int(num_of_weeks/1.4)
	else:
		num_of_weeks = 30
		chart_width = 30

	if kind == "daily": day_cutoffs = [today_cutoff - 86400 * i for i in range(num_of_weeks)][1:]
	else: day_cutoffs = [today_cutoff - 86400 * 7 * i for i in range(num_of_weeks)][1:]

	day_cutoffs.insert(0, calendar.timegm(now))

	daily_times = [time.strftime("%d/%m", time.gmtime(day_cutoffs[i + 1])) for i in range(len(day_cutoffs) - 1)][::-1]

	daily_signups = [g.db.query(User).filter(User.created_utc < day_cutoffs[i], User.created_utc > day_cutoffs[i + 1]).count() for i in range(len(day_cutoffs) - 1)][::-1]

	post_stats = [g.db.query(Submission).filter(Submission.created_utc < day_cutoffs[i], Submission.created_utc > day_cutoffs[i + 1], Submission.is_banned == False).count() for i in range(len(day_cutoffs) - 1)][::-1]

	comment_stats = [g.db.query(Comment).filter(Comment.created_utc < day_cutoffs[i], Comment.created_utc > day_cutoffs[i + 1],Comment.is_banned == False, Comment.author_id.notin_((AUTOJANNY_ID,NOTIFICATIONS_ID))).count() for i in range(len(day_cutoffs) - 1)][::-1]

	plt.rcParams["figure.figsize"] = (chart_width, 20)

	signup_chart = plt.subplot2grid((chart_width, 20), (0, 0), rowspan=6, colspan=chart_width)
	posts_chart = plt.subplot2grid((chart_width, 20), (10, 0), rowspan=6, colspan=chart_width)
	comments_chart = plt.subplot2grid((chart_width, 20), (20, 0), rowspan=6, colspan=chart_width)

	signup_chart.grid(), posts_chart.grid(), comments_chart.grid()

	signup_chart.plot(
		daily_times,
		daily_signups,
		color='red')
	posts_chart.plot(
		daily_times,
		post_stats,
		color='blue')
	comments_chart.plot(
		daily_times,
		comment_stats,
		color='purple')

	signup_chart.set_ylim(ymin=0)
	posts_chart.set_ylim(ymin=0)
	comments_chart.set_ylim(ymin=0)

	signup_chart.set_ylabel("Signups")
	posts_chart.set_ylabel("Posts")
	comments_chart.set_ylabel("Comments")
	comments_chart.set_xlabel("Time (UTC)")

	file = f"/{SITE}_{kind}.png"

	plt.savefig(file)
	plt.clf()
	return file


@app.get("/patrons")
@app.get("/paypigs")
@admin_level_required(3)
def patrons(v):
	users = g.db.query(User).filter(User.patron > 0).order_by(User.patron.desc(), User.id).all()

	return render_template("patrons.html", v=v, users=users)

@app.get("/admins")
@app.get("/badmins")
@auth_required
def admins(v):
	if v and v.admin_level > 2:
		admins = g.db.query(User).filter(User.admin_level>1).order_by(User.truecoins.desc()).all()
		admins += g.db.query(User).filter(User.admin_level==1).order_by(User.truecoins.desc()).all()
	else: admins = g.db.query(User).filter(User.admin_level>0).order_by(User.truecoins.desc()).all()
	return render_template("admins.html", v=v, admins=admins)


@app.get("/log")
@app.get("/modlog")
@auth_required
def log(v):

	try: page = max(int(request.values.get("page", 1)), 1)
	except: page = 1

	admin = request.values.get("admin")
	if admin: admin_id = get_id(admin)
	else: admin_id = 0

	kind = request.values.get("kind")

	if v and v.admin_level > 1: types = ACTIONTYPES
	else: types = ACTIONTYPES2

	if kind not in types: kind = None

	actions = g.db.query(ModAction)
	if not (v and v.admin_level > 1): 
		actions = actions.filter(ModAction.kind.notin_(["shadowban","unshadowban","flair_post","edit_post"]))
	
	if admin_id:
		actions = actions.filter_by(user_id=admin_id)
		kinds = set([x.kind for x in actions])
		types2 = {}
		for k,val in types.items():
			if k in kinds: types2[k] = val
		types = types2
	if kind: actions = actions.filter_by(kind=kind)

	actions = actions.order_by(ModAction.id.desc()).offset(25*(page-1)).limit(26).all()
	next_exists=len(actions)>25
	actions=actions[:25]

	admins = [x[0] for x in g.db.query(User.username).filter(User.admin_level > 1).order_by(User.username).all()]

	return render_template("log.html", v=v, admins=admins, types=types, admin=admin, type=kind, actions=actions, next_exists=next_exists, page=page)

@app.get("/log/<id>")
@auth_required
def log_item(id, v):

	try: id = int(id)
	except: abort(404)

	action=g.db.query(ModAction).filter_by(id=id).one_or_none()

	if not action: abort(404)

	admins = [x[0] for x in g.db.query(User.username).filter(User.admin_level > 1).all()]

	if v and v.admin_level > 1: types = ACTIONTYPES
	else: types = ACTIONTYPES2

	return render_template("log.html", v=v, actions=[action], next_exists=False, page=1, action=action, admins=admins, types=types)


@app.get("/api")
@auth_required
def api(v):
	return render_template("api.html", v=v)

@app.get("/contact")
@app.get("/press")
@app.get("/media")
@auth_required
def contact(v):

	return render_template("contact.html", v=v)

@app.post("/send_admin")
@limiter.limit("1/second;2/minute;6/hour;10/day")
@limiter.limit("1/second;2/minute;6/hour;10/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def submit_contact(v):
	body = request.values.get("message")
	if not body: abort(400)

	body = f'This message has been sent automatically to all admins via [/contact](/contact)\n\nMessage:\n\n' + body
	body_html = sanitize(body)

	if request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
		file=request.files["file"]
		if file.content_type.startswith('image/'):
			name = f'/images/{time.time()}'.replace('.','') + '.webp'
			file.save(name)
			url = process_image(v.patron, name)
			body_html += f'<img data-bs-target="#expandImageModal" data-bs-toggle="modal" onclick="expandDesktopImage(this.src)" class="img" src="{url}" loading="lazy">'
		elif file.content_type.startswith('video/'):
			value = process_video(file)
			if type(value) is str: body_html += f"<p>{value}</p>"
			else: return value
		elif file.content_type.startswith('audio/'):
			body_html += f"<p>{process_audio(file)}</p>"
		else: return {"error": "Image/Video/Audio files only"}, 400



	new_comment = Comment(author_id=v.id,
						  parent_submission=None,
						  level=1,
						  body_html=body_html,
						  sentto=2
						  )
	g.db.add(new_comment)
	g.db.flush()
	new_comment.top_comment_id = new_comment.id
	
	for admin in g.db.query(User).filter(User.admin_level > 2).all():
		notif = Notification(comment_id=new_comment.id, user_id=admin.id)
		g.db.add(notif)



	g.db.commit()
	return render_template("contact.html", v=v, msg="Your message has been sent.")

@app.get('/archives')
def archivesindex():
	return redirect("/archives/index.html")

@app.get('/archives/<path:path>')
def archives(path):
	resp = make_response(send_from_directory('/archives', path))
	if request.path.endswith('.css'): resp.headers.add("Content-Type", "text/css")
	return resp

@app.get('/e/<emoji>')
@limiter.exempt
def emoji(emoji):
	if not emoji.endswith('.webp'): abort(404)
	resp = make_response(send_from_directory('assets/images/emojis', emoji))
	resp.headers.remove("Cache-Control")
	resp.headers.add("Cache-Control", "public, max-age=3153600")
	resp.headers.remove("Content-Type")
	resp.headers.add("Content-Type", "image/webp")
	return resp

@app.get('/assets/<path:path>')
@app.get('/static/assets/<path:path>')
@limiter.exempt
def static_service(path):
	resp = make_response(send_from_directory('assets', path))
	if request.path.endswith('.webp') or request.path.endswith('.gif') or request.path.endswith('.ttf') or request.path.endswith('.woff2'):
		resp.headers.remove("Cache-Control")
		resp.headers.add("Cache-Control", "public, max-age=3153600")

	if request.path.endswith('.webp'):
		resp.headers.remove("Content-Type")
		resp.headers.add("Content-Type", "image/webp")

	return resp

@app.get('/images/<path>')
@app.get('/hostedimages/<path>')
@app.get("/static/images/<path>")
@limiter.exempt
def images(path):
	resp = make_response(send_from_directory('/images', path))
	resp.headers.remove("Cache-Control")
	resp.headers.add("Cache-Control", "public, max-age=3153600")
	resp.headers.remove("Content-Type")
	resp.headers.add("Content-Type" ,"image/webp")
	return resp

@app.get('/videos/<path>')
@limiter.exempt
def videos(path):
	resp = make_response(send_from_directory('/videos', path))
	resp.headers.remove("Cache-Control")
	resp.headers.add("Cache-Control", "public, max-age=3153600")
	return resp

@app.get('/audio/<path>')
@limiter.exempt
def audio(path):
	resp = make_response(send_from_directory('/audio', path))
	resp.headers.remove("Cache-Control")
	resp.headers.add("Cache-Control", "public, max-age=3153600")
	return resp

@app.get("/robots.txt")
def robots_txt():
	try: f = send_file("assets/robots.txt")
	except:
		print('/robots.txt', flush=True)
		abort(404)
	return f

no = (21,22,23,24,25,26,27)

@cache.memoize(timeout=3600)
def badge_list(site):
	badges = g.db.query(BadgeDef).filter(BadgeDef.id.notin_(no)).order_by(BadgeDef.id).all()
	counts_raw = g.db.query(Badge.badge_id, func.count()).group_by(Badge.badge_id).all()
	users = g.db.query(User).count()

	counts = {}
	for c in counts_raw:
		counts[c[0]] = (c[1], float(c[1]) * 100 / max(users, 1))
	
	return badges, counts

@app.get("/badges")
@auth_required
def badges(v):
	badges, counts = badge_list(SITE)
	return render_template("badges.html", v=v, badges=badges, counts=counts)

@app.get("/blocks")
@auth_required
def blocks(v):


	blocks=g.db.query(UserBlock).all()
	users = []
	targets = []
	for x in blocks:
		users.append(get_account(x.user_id))
		targets.append(get_account(x.target_id))

	return render_template("blocks.html", v=v, users=users, targets=targets)

@app.get("/banned")
@auth_required
def banned(v):

	users = g.db.query(User).filter(User.is_banned > 0, User.unban_utc == 0).all()
	return render_template("banned.html", v=v, users=users)

@app.get("/formatting")
@auth_required
def formatting(v):

	return render_template("formatting.html", v=v)

@app.get("/worker.js")
def serviceworker():
	with open("files/assets/js/worker.js", "r", encoding="utf-8") as f: return Response(f.read(), mimetype='application/javascript')

@app.get("/settings/security")
@auth_required
def settings_security(v):

	return render_template("settings_security.html",
						   v=v,
						   mfa_secret=pyotp.random_base32() if not v.mfa_secret else None
						   )

@app.get("/.well-known/assetlinks.json")
def googleplayapp():
	with open("files/assets/assetlinks.json", "r") as f:
		return Response(f.read(), mimetype='application/json')



@app.post("/dismiss_mobile_tip")
def dismiss_mobile_tip():
	session["tooltip_last_dismissed"] = int(time.time())
	return "", 204
