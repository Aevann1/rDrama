from files.mail import *
from files.__main__ import app, limiter, mail
from files.helpers.alerts import *
from files.classes.award import AWARDS
from sqlalchemy import func
from os import path
import calendar
import matplotlib.pyplot as plt

site = environ.get("DOMAIN").strip()
site_name = environ.get("SITE_NAME").strip()

@app.get('/rules')
@auth_desired
def static_rules(v):

	if not path.exists(f'./{site_name} rules.html'):
		if v and v.admin_level > 1:
			return render_template('norules.html', v=v)
		else:
			abort(404)

	with open(f'./{site_name} rules.html', 'r') as f:
		rules = f.read()

	return render_template('rules.html', rules=rules, v=v)


@app.get("/stats")
@auth_required
def participation_stats(v):

	now = int(time.time())

	day = now - 86400

	data = {"valid_users": g.db.query(User.id).count(),
			"private_users": g.db.query(User.id).filter_by(is_private=True).count(),
			"banned_users": g.db.query(User.id).filter(User.is_banned > 0).count(),
			"verified_email_users": g.db.query(User.id).filter_by(is_activated=True).count(),
			"total_coins": g.db.query(func.sum(User.coins)).scalar(),
			"signups_last_24h": g.db.query(User.id).filter(User.created_utc > day).count(),
			"total_posts": g.db.query(Submission.id).count(),
			"posting_users": g.db.query(Submission.author_id).distinct().count(),
			"listed_posts": g.db.query(Submission.id).filter_by(is_banned=False).filter(Submission.deleted_utc == 0).count(),
			"removed_posts": g.db.query(Submission.id).filter_by(is_banned=True).count(),
			"deleted_posts": g.db.query(Submission.id).filter(Submission.deleted_utc > 0).count(),
			"posts_last_24h": g.db.query(Submission.id).filter(Submission.created_utc > day).count(),
			"total_comments": g.db.query(Comment.id).count(),
			"commenting_users": g.db.query(Comment.author_id).distinct().count(),
			"removed_comments": g.db.query(Comment.id).filter_by(is_banned=True).count(),
			"deleted_comments": g.db.query(Comment.id).filter(Comment.deleted_utc>0).count(),
			"comments_last_24h": g.db.query(Comment.id).filter(Comment.created_utc > day).count(),
			"post_votes": g.db.query(Vote.id).count(),
			"post_voting_users": g.db.query(Vote.user_id).distinct().count(),
			"comment_votes": g.db.query(CommentVote.id).count(),
			"comment_voting_users": g.db.query(CommentVote.user_id).distinct().count(),
			"total_awards": g.db.query(AwardRelationship.id).count(),
			"awards_given": g.db.query(AwardRelationship.id).filter(or_(AwardRelationship.submission_id != None, AwardRelationship.comment_id != None)).count()
			}


	return render_template("admin/content_stats.html", v=v, title="Content Statistics", data=data)


@app.get("/chart")
@auth_required
def chart(v):
	file = cached_chart()
	return send_file(f"../{file}")


@cache.memoize(timeout=86400)
def cached_chart():
	days = int(request.values.get("days", 25))

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

	day = 3600 * 200

	day_cutoffs = [today_cutoff - day * i for i in range(days)]
	day_cutoffs.insert(0, calendar.timegm(now))

	daily_times = [time.strftime("%d/%m", time.gmtime(day_cutoffs[i + 1])) for i in range(len(day_cutoffs) - 1)][2:][::-1]

	daily_signups = [g.db.query(User.id).filter(User.created_utc < day_cutoffs[i], User.created_utc > day_cutoffs[i + 1]).count() for i in range(len(day_cutoffs) - 1)][2:][::-1]

	post_stats = [g.db.query(Submission.id).filter(Submission.created_utc < day_cutoffs[i], Submission.created_utc > day_cutoffs[i + 1], Submission.is_banned == False).count() for i in range(len(day_cutoffs) - 1)][2:][::-1]

	comment_stats = [g.db.query(Comment.id).filter(Comment.created_utc < day_cutoffs[i], Comment.created_utc > day_cutoffs[i + 1],Comment.is_banned == False, Comment.author_id != 1).count() for i in range(len(day_cutoffs) - 1)][2:][::-1]

	plt.rcParams["figure.figsize"] = (20,20)

	signup_chart = plt.subplot2grid((20, 4), (0, 0), rowspan=5, colspan=4)
	posts_chart = plt.subplot2grid((20, 4), (7, 0), rowspan=5, colspan=4)
	comments_chart = plt.subplot2grid((20, 4), (14, 0), rowspan=5, colspan=4)

	signup_chart.grid(), posts_chart.grid(), comments_chart.grid()

	signup_chart.plot(
		daily_times,
		daily_signups,
		color='red')
	posts_chart.plot(
		daily_times,
		post_stats,
		color='green')
	comments_chart.plot(
		daily_times,
		comment_stats,
		color='gold')

	signup_chart.set_ylabel("Signups")
	posts_chart.set_ylabel("Posts")
	comments_chart.set_ylabel("Comments")
	comments_chart.set_xlabel("Time (UTC)")

	signup_chart.legend(loc='upper left', frameon=True)
	posts_chart.legend(loc='upper left', frameon=True)
	comments_chart.legend(loc='upper left', frameon=True)

	file = "chart.png"
	plt.savefig(file)
	plt.clf()
	return file


@app.get("/patrons")
@app.get("/paypigs")
@auth_desired
def patrons(v):
	query = g.db.query(
			User.id, User.username, User.patron, User.namecolor,
			AwardRelationship.kind.label('last_award_kind'), func.count(AwardRelationship.id).label('last_award_count')
		).filter(AwardRelationship.submission_id==None, AwardRelationship.comment_id==None, User.patron > 0) \
		.group_by(User.username, User.patron, User.id, User.namecolor, AwardRelationship.kind) \
		.order_by(User.patron.desc(), AwardRelationship.kind.desc()) \
		.join(User).all()

	result = {}
	for row in (r._asdict() for r in query):
		user_id = row['id']
		if user_id not in result:
			result[user_id] = row
			result[user_id]['awards'] = {}

		kind = row['last_award_kind']
		if kind in AWARDS.keys():
			result[user_id]['awards'][kind] = (AWARDS[kind], row['last_award_count'])

	return render_template("patrons.html", v=v, result=result)

@app.get("/admins")
@app.get("/badmins")
@auth_desired
def admins(v):
	admins = g.db.query(User).filter(User.admin_level>1).order_by(User.coins.desc()).all()
	return render_template("admins.html", v=v, admins=admins)


@app.get("/log")
@app.get("/modlog")
@auth_desired
def log(v):

	page=int(request.args.get("page",1))

	if v and v.admin_level > 1: actions = g.db.query(ModAction).order_by(ModAction.id.desc()).offset(25 * (page - 1)).limit(26).all()
	else: actions=g.db.query(ModAction).filter(ModAction.kind!="shadowban", ModAction.kind!="unshadowban", ModAction.kind!="club", ModAction.kind!="unclub", ModAction.kind!="check").order_by(ModAction.id.desc()).offset(25*(page-1)).limit(26).all()

	next_exists=len(actions)>25
	actions=actions[:25]

	return render_template("log.html", v=v, actions=actions, next_exists=next_exists, page=page)

@app.get("/log/<id>")
@auth_desired
def log_item(id, v):

	try: id = int(id)
	except:
		try: id = int(id, 36)
		except: abort(404)

	action=g.db.query(ModAction).filter_by(id=id).first()

	if not action:
		abort(404)

	if request.path != action.permalink:
		return redirect(action.permalink)

	return render_template("log.html",
		v=v,
		actions=[action],
		next_exists=False,
		page=1,
		action=action
		)

@app.get("/assets/favicon.ico")
def favicon():
	return send_file(f"./assets/images/{site_name}/icon.webp")

@app.get("/api")
@auth_desired
def api(v):
	return render_template("api.html", v=v)

@app.get("/contact")
@app.get("/press")
@app.get("/media")
@auth_required
def contact(v):

	return render_template("contact.html", v=v)

@app.post("/contact")
@limiter.limit("1/second")
@auth_required
def submit_contact(v):
	message = f'This message has been sent automatically to all admins via http://{site}/contact, user email is "{v.email}"\n\nMessage:\n\n' + request.values.get("message", "")
	send_admin(v.id, message)
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

@app.get('/assets/<path:path>')
@limiter.exempt
def static_service(path):
	resp = make_response(send_from_directory('./assets', path))
	if request.path.endswith('.webp') or request.path.endswith('.gif') or request.path.endswith('.ttf') or request.path.endswith('.woff') or request.path.endswith('.woff2'):
		resp.headers.remove("Cache-Control")
		resp.headers.add("Cache-Control", "public, max-age=2628000")

	if request.path.endswith('.webp'):
		resp.headers.remove("Content-Type")
		resp.headers.add("Content-Type", "image/webp")

	return resp

@app.get('/images/<path:path>')
@app.get('/hostedimages/<path:path>')
@limiter.exempt
def images(path):
	resp = make_response(send_from_directory('/images', path))
	resp.headers.remove("Cache-Control")
	resp.headers.add("Cache-Control", "public, max-age=2628000")
	if request.path.endswith('.webp'):
		resp.headers.remove("Content-Type")
		resp.headers.add("Content-Type", "image/webp")
	return resp

@app.get("/robots.txt")
def robots_txt():
	return send_file("./assets/robots.txt")

@app.get("/settings")
@auth_required
def settings(v):


	return redirect("/settings/profile")


@app.get("/settings/profile")
@auth_required
def settings_profile(v):


	return render_template("settings_profile.html",
						   v=v)

@app.get("/badges")
@auth_desired
def badges(v):


	badges = g.db.query(BadgeDef).all()
	return render_template("badges.html", v=v, badges=badges)

@app.get("/blocks")
@auth_desired
def blocks(v):


	blocks=g.db.query(UserBlock).all()
	users = []
	targets = []
	for x in blocks:
		users.append(get_account(x.user_id))
		targets.append(get_account(x.target_id))

	return render_template("blocks.html", v=v, users=users, targets=targets)

@app.get("/banned")
@auth_desired
def banned(v):


	users = [x for x in g.db.query(User).filter(User.is_banned > 0, User.unban_utc == 0).all()]
	return render_template("banned.html", v=v, users=users)

@app.get("/formatting")
@auth_desired
def formatting(v):


	return render_template("formatting.html", v=v)

@app.get("/service-worker.js")
def serviceworker():
	with open("files/assets/js/service-worker.js", "r") as f: return Response(f.read(), mimetype='application/javascript')

@app.get("/settings/security")
@auth_required
def settings_security(v):


	return render_template("settings_security.html",
						   v=v,
						   mfa_secret=pyotp.random_base32() if not v.mfa_secret else None,
						   error=request.values.get("error") or None,
						   msg=request.values.get("msg") or None
						   )

@app.post("/dismiss_mobile_tip")
@limiter.limit("1/second")
def dismiss_mobile_tip():

	session["tooltip_last_dismissed"]=int(time.time())
	session.modified=True

	return "", 204
