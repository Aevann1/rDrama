from files.helpers.wrappers import *
from files.helpers.get import *
from files.helpers.discord import *
from files.__main__ import app, cache, limiter
from files.classes.submission import Submission
from files.helpers.awards import award_timers

defaulttimefilter = environ.get("DEFAULT_TIME_FILTER", "all").strip()

@app.post("/clear")
@auth_required
def clear(v):
	notifs = g.db.query(Notification).join(Comment, Notification.comment_id == Comment.id).filter(Notification.read == False, Notification.user_id == v.id).all()
	for n in notifs:
		n.read = True
		g.db.add(n)
	return {"message": "Notifications cleared!"}

@app.get("/unread")
@auth_required
def unread(v):
	listing = g.db.query(Notification, Comment).join(Comment, Notification.comment_id == Comment.id).filter(
		Notification.read == False,
		Notification.user_id == v.id,
		Comment.is_banned == False,
		Comment.deleted_utc == 0,
		Comment.author_id != AUTOJANNY_ID,
	).order_by(Notification.created_utc.desc()).all()

	for n, c in listing:
		n.read = True
		g.db.add(n)

	return {"data":[x[1].json for x in listing]}


@app.get("/notifications")
@auth_required
def notifications(v):
	try: page = max(int(request.values.get("page", 1)), 1)
	except: page = 1

	messages = request.values.get('messages')
	modmail = request.values.get('modmail')
	modactions = request.values.get('modactions')
	posts = request.values.get('posts')
	reddit = request.values.get('reddit')
	if modmail and v.admin_level >= 2:
		comments = g.db.query(Comment).filter(Comment.sentto==2).order_by(Comment.id.desc()).offset(25*(page-1)).limit(26).all()
		next_exists = (len(comments) > 25)
		listing = comments[:25]
	elif messages:
		if v and (v.shadowbanned or v.admin_level > 2):
			comments = g.db.query(Comment).filter(Comment.sentto != None, or_(Comment.author_id==v.id, Comment.sentto==v.id), Comment.parent_submission == None, Comment.level == 1).order_by(Comment.id.desc()).offset(25*(page-1)).limit(26).all()
		else:
			comments = g.db.query(Comment).join(User, User.id == Comment.author_id).filter(User.shadowbanned == None, Comment.sentto != None, or_(Comment.author_id==v.id, Comment.sentto==v.id), Comment.parent_submission == None, Comment.level == 1).order_by(Comment.id.desc()).offset(25*(page-1)).limit(26).all()

		next_exists = (len(comments) > 25)
		listing = comments[:25]
	elif posts:
		notifications = g.db.query(Notification, Comment).join(Comment, Notification.comment_id == Comment.id).filter(Notification.user_id == v.id, Comment.author_id == AUTOJANNY_ID).order_by(Notification.created_utc.desc()).offset(25 * (page - 1)).limit(101).all()

		listing = []

		for index, x in enumerate(notifications[:100]):
			n, c = x
			if n.read and index > 24: break
			elif not n.read:
				n.read = True
				c.unread = True
				g.db.add(n)
			if n.created_utc > 1620391248: c.notif_utc = n.created_utc
			listing.append(c)

		next_exists = (len(notifications) > len(listing))
	elif modactions:
		notifications = g.db.query(Notification, Comment) \
			.join(Comment, Notification.comment_id == Comment.id) \
			.filter(Notification.user_id == v.id, 
				Comment.body_html.like(f'%<p>{NOTIF_MODACTION_PREFIX}%'),
				Comment.parent_submission == None, Comment.author_id == NOTIFICATIONS_ID) \
			.order_by(Notification.created_utc.desc()).offset(25 * (page - 1)).limit(101).all()
		listing = []

		for index, x in enumerate(notifications[:100]):
			n, c = x
			if n.read and index > 24: break
			elif not n.read:
				n.read = True
				c.unread = True
				g.db.add(n)
			if n.created_utc > 1620391248: c.notif_utc = n.created_utc
			listing.append(c)

		next_exists = (len(notifications) > len(listing))
	elif reddit:
		notifications = g.db.query(Notification, Comment).join(Comment, Notification.comment_id == Comment.id).filter(Notification.user_id == v.id, Comment.body_html.like('%<p>New site mention: <a href="https://old.reddit.com/r/%'), Comment.parent_submission == None, Comment.author_id == NOTIFICATIONS_ID).order_by(Notification.created_utc.desc()).offset(25 * (page - 1)).limit(101).all()

		listing = []

		for index, x in enumerate(notifications[:100]):
			n, c = x
			if n.read and index > 24: break
			elif not n.read:
				n.read = True
				c.unread = True
				g.db.add(n)
			if n.created_utc > 1620391248: c.notif_utc = n.created_utc
			listing.append(c)

		next_exists = (len(notifications) > len(listing))
	else:		
		comments = g.db.query(Comment, Notification).join(Notification, Notification.comment_id == Comment.id).filter(
			Notification.user_id == v.id,
			Comment.is_banned == False,
			Comment.deleted_utc == 0,
			Comment.author_id != AUTOJANNY_ID,
			Comment.body_html.notlike('%<p>New site mention: <a href="https://old.reddit.com/r/%'),
			Comment.body_html.notlike(f'%<p>{NOTIF_MODACTION_PREFIX}%')
		).order_by(Notification.created_utc.desc())

		if not (v and (v.shadowbanned or v.admin_level > 2)):
			comments = comments.join(User, User.id == Comment.author_id).filter(User.shadowbanned == None)

		comments = comments.offset(25 * (page - 1)).limit(26).all()

		next_exists = (len(comments) > 25)
		comments = comments[:25]

		cids = [x[0].id for x in comments]

		comms = get_comments(cids, v=v)

		listing = []
		for c, n in comments:
			if n.created_utc > 1620391248: c.notif_utc = n.created_utc
			if not n.read:
				n.read = True
				c.unread = True
				g.db.add(n)

			if c.parent_submission:
				if c.replies2 == None:
					c.replies2 = c.child_comments.filter(or_(Comment.author_id == v.id, Comment.id.in_(cids))).all()
					for x in c.replies2:
						if x.replies2 == None: x.replies2 = []
				count = 0
				while count < 50 and c.parent_comment and (c.parent_comment.author_id == v.id or c.parent_comment.id in cids):
					count += 1
					c = c.parent_comment
					if c.replies2 == None:
						c.replies2 = c.child_comments.filter(or_(Comment.author_id == v.id, Comment.id.in_(cids))).all()
						for x in c.replies2:
							if x.replies2 == None:
								x.replies2 = x.child_comments.filter(or_(Comment.author_id == v.id, Comment.id.in_(cids))).all()
			else:
				while c.parent_comment:
					c = c.parent_comment
				c.replies2 = g.db.query(Comment).filter_by(parent_comment_id=c.id).order_by(Comment.id).all()

			if c not in listing: listing.append(c)

	g.db.commit()

	if request.headers.get("Authorization"): return {"data":[x.json for x in listing]}

	return render_template("notifications.html",
							v=v,
							notifications=listing,
							next_exists=next_exists,
							page=page,
							standalone=True,
							render_replies=True,
							NOTIF_MODACTION_JL_MIN=NOTIF_MODACTION_JL_MIN,
						   )


@app.get("/")
@app.get("/catalog")
@app.get("/h/<sub>")
@app.get("/s/<sub>")
@app.get("/logged_out")
@app.get("/logged_out/catalog")
@app.get("/logged_out/h/<sub>")
@app.get("/logged_out/s/<sub>")
@limiter.limit("3/second;30/minute;5000/hour;10000/day")
@auth_desired
def front_all(v, sub=None, subdomain=None):

	if not v and not request.path.startswith('/logged_out'):
		r = request.full_path
		if r == '/?': r = '/'
		return redirect(f"/logged_out{r}")
	if v and request.path.startswith('/logged_out'): return redirect(request.full_path.replace('/logged_out',''))

	if sub: sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	
	if (request.path.startswith('/h/') or request.path.startswith('/s/')) and not sub: abort(404)

	try: page = max(int(request.values.get("page", 1)), 1)
	except: abort(400)

	if v:
		defaultsorting = v.defaultsorting
		if sub or SITE_NAME != 'rDrama': defaulttime = 'all'
		else: defaulttime = v.defaulttime
	else:
		defaultsorting = "hot"
		if sub or SITE_NAME != 'rDrama': defaulttime = 'all'
		else: defaulttime = defaulttimefilter

	sort=request.values.get("sort", defaultsorting)
	t=request.values.get('t', defaulttime)
	ccmode=request.values.get('ccmode', "false").lower()

	if sort == 'bump': t='all'
	
	try: gt=int(request.values.get("after", 0))
	except: gt=0

	try: lt=int(request.values.get("before", 0))
	except: lt=0

	ids, next_exists = frontlist(sort=sort,
					page=page,
					t=t,
					v=v,
					ccmode=ccmode,
					filter_words=v.filter_words if v else [],
					gt=gt,
					lt=lt,
					sub=sub,
					site=SITE
					)

	posts = get_posts(ids, v=v)
	
	if v:
		if v.hidevotedon: posts = [x for x in posts if not hasattr(x, 'voted') or not x.voted]
		award_timers(v)

	if request.headers.get("Authorization"): return {"data": [x.json for x in posts], "next_exists": next_exists}
	return render_template("home.html", v=v, listing=posts, next_exists=next_exists, sort=sort, t=t, page=page, ccmode=ccmode, sub=sub, home=True)



@cache.memoize(timeout=86400)
def frontlist(v=None, sort="hot", page=1, t="all", ids_only=True, ccmode="false", filter_words='', gt=0, lt=0, sub=None, site=None):

	posts = g.db.query(Submission)
	
	if v and v.hidevotedon:
		voted = [x[0] for x in g.db.query(Vote.submission_id).filter_by(user_id=v.id).all()]
		posts = posts.filter(Submission.id.notin_(voted))

	if sub: posts = posts.filter_by(sub=sub.name)
	elif v: posts = posts.filter(or_(Submission.sub == None, Submission.sub.notin_(v.all_blocks)))

	if gt: posts = posts.filter(Submission.created_utc > gt)
	if lt: posts = posts.filter(Submission.created_utc < lt)

	if not gt and not lt:
		if t == 'all': cutoff = 0
		else:
			now = int(time.time())
			if t == 'hour': cutoff = now - 3600
			elif t == 'week': cutoff = now - 604800
			elif t == 'month': cutoff = now - 2592000
			elif t == 'year': cutoff = now - 31536000
			else: cutoff = now - 86400
			posts = posts.filter(Submission.created_utc >= cutoff)

	if (ccmode == "true"):
		posts = posts.filter(Submission.club == True)

	posts = posts.filter_by(is_banned=False, private=False, deleted_utc = 0)

	if (sort == "hot" or (v and v.id == Q_ID)) and ccmode == "false" and not gt and not lt:
		posts = posts.filter_by(stickied=None, hole_pinned=None)

	if v:
		posts = posts.filter(Submission.author_id.notin_(v.userblocks))

	if not (v and v.changelogsub):
		posts=posts.filter(not_(Submission.title.ilike('[changelog]%')))

	if v and filter_words:
		for word in filter_words:
			word  = word.replace('\\', '').replace('_', '\_').replace('%', '\%').strip()
			posts=posts.filter(not_(Submission.title.ilike(f'%{word}%')))

	if not (v and v.shadowbanned):
		posts = posts.join(User, User.id == Submission.author_id).filter(User.shadowbanned == None)

	if request.host == 'rdrama.net': num = 5
	else: num = 0.5

	if sort == "hot":
		ti = int(time.time()) + 3600
		posts = posts.order_by(-1000000*(Submission.realupvotes + 1 + Submission.comment_count/num)/(func.power(((ti - Submission.created_utc)/1000), 1.23)), Submission.created_utc.desc())
	elif sort == "bump":
		posts = posts.filter(Submission.comment_count > 1).order_by(Submission.bump_utc.desc(), Submission.created_utc.desc())
	else:
		posts = sort_posts(sort, posts)

	if v: size = v.frontsize or 0
	else: size = 25

	posts = posts.offset(size * (page - 1)).limit(size+1).all()

	next_exists = (len(posts) > size)

	posts = posts[:size]

	if (sort == "hot" or (v and v.id == Q_ID)) and page == 1 and ccmode == "false" and not gt and not lt:
		if sub:
			pins = g.db.query(Submission).filter(Submission.sub == sub.name, Submission.hole_pinned != None)
		else:
			pins = g.db.query(Submission).filter(Submission.stickied != None, Submission.is_banned == False)
			
			if v:
				pins = pins.filter(or_(Submission.sub == None, Submission.sub.notin_(v.all_blocks)))
				for pin in pins:
					if pin.stickied_utc and int(time.time()) > pin.stickied_utc:
						pin.stickied = None
						pin.stickied_utc = None
						g.db.add(pin)
						pins.remove(pin)


		if v: pins = pins.filter(Submission.author_id.notin_(v.userblocks))

		pins = pins.order_by(Submission.created_utc.desc()).all()

		posts = pins + posts

	if ids_only: posts = [x.id for x in posts]


	return posts, next_exists


@app.get("/changelog")
@auth_required
def changelog(v):


	try: page = max(int(request.values.get("page", 1)), 1)
	except: page = 1

	sort=request.values.get("sort", "new")
	t=request.values.get('t', "all")

	ids = changeloglist(sort=sort,
					page=page,
					t=t,
					v=v,
					site=SITE
					)

	next_exists = (len(ids) > 25)
	ids = ids[:25]

	posts = get_posts(ids, v=v)

	if request.headers.get("Authorization"): return {"data": [x.json for x in posts], "next_exists": next_exists}
	return render_template("changelog.html", v=v, listing=posts, next_exists=next_exists, sort=sort, t=t, page=page)


@cache.memoize(timeout=86400)
def changeloglist(v=None, sort="new", page=1, t="all", site=None):

	posts = g.db.query(Submission.id).filter_by(is_banned=False, private=False, deleted_utc=0)

	allowed = g.db.query(User.id).filter(User.admin_level > 0).all() + g.db.query(Badge.user_id).filter_by(badge_id=3).all()
	allowed = [x[0] for x in allowed]

	posts = posts.filter(Submission.title.ilike('_changelog%'), Submission.author_id.in_(allowed))

	if t != 'all':
		cutoff = 0
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
		posts = posts.filter(Submission.created_utc >= cutoff)

	posts = sort_posts(sort, posts)

	posts = posts.offset(25 * (page - 1)).limit(26).all()

	return [x[0] for x in posts]


@app.get("/random_post")
@auth_required
def random_post(v):

	p = g.db.query(Submission.id).filter(Submission.deleted_utc == 0, Submission.is_banned == False, Submission.private == False).order_by(func.random()).first()

	if p: p = p[0]
	else: abort(404)

	return redirect(f"/post/{p}")


@app.get("/random_user")
@auth_required
def random_user(v):

	u = g.db.query(User.username).filter(User.song != None).order_by(func.random()).first()
	
	if u: u = u[0]
	else: abort(404)

	return redirect(f"/@{u}")


@app.get("/comments")
@auth_required
def all_comments(v):


	try: page = max(int(request.values.get("page", 1)), 1)
	except: page = 1

	sort=request.values.get("sort", "new")
	t=request.values.get("t", defaulttimefilter)

	try: gt=int(request.values.get("after", 0))
	except: gt=0

	try: lt=int(request.values.get("before", 0))
	except: lt=0

	idlist = comment_idlist(v=v,
							page=page,
							sort=sort,
							t=t,
							gt=gt,
							lt=lt,
							site=SITE
							)

	comments = get_comments(idlist, v=v)

	next_exists = len(idlist) > 25

	idlist = idlist[:25]

	if request.headers.get("Authorization"): return {"data": [x.json for x in comments]}
	return render_template("home_comments.html", v=v, sort=sort, t=t, page=page, comments=comments, standalone=True, next_exists=next_exists)



@cache.memoize(timeout=86400)
def comment_idlist(page=1, v=None, nsfw=False, sort="new", t="all", gt=0, lt=0, site=None):

	comments = g.db.query(Comment.id).filter(Comment.parent_submission != None, Comment.author_id.notin_(v.userblocks))

	if v.admin_level < 2:
		private = [x[0] for x in g.db.query(Submission.id).filter(Submission.private == True).all()]

		comments = comments.filter(Comment.is_banned==False, Comment.deleted_utc == 0, Comment.parent_submission.notin_(private))


	if not v.paid_dues:
		club = [x[0] for x in g.db.query(Submission.id).filter(Submission.club == True).all()]
		comments = comments.filter(Comment.parent_submission.notin_(club))


	if gt: comments = comments.filter(Comment.created_utc > gt)
	if lt: comments = comments.filter(Comment.created_utc < lt)

	if not gt and not lt:
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

	comments = sort_comments(sort, comments)

	comments = comments.offset(25 * (page - 1)).limit(26).all()
	return [x[0] for x in comments]


@app.get("/transfers")
@auth_required
def transfers(v):

	comments = g.db.query(Comment).filter(Comment.author_id == NOTIFICATIONS_ID, Comment.parent_submission == None, Comment.body_html.like("%</a> has transferred %")).order_by(Comment.id.desc())

	if request.headers.get("Authorization"): return {"data": [x.json for x in comments.all()]}

	try: page = max(int(request.values.get("page", 1)), 1)
	except: page = 1

	comments = comments.offset(25 * (page - 1)).limit(26).all()
	next_exists = len(comments) > 25
	comments = comments[:25]
	return render_template("transfers.html", v=v, page=page, comments=comments, standalone=True, next_exists=next_exists)
