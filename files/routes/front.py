from files.helpers.wrappers import *
from files.helpers.get import *

from files.__main__ import app, cache
from files.classes.submission import Submission

defaulttimefilter = environ.get("DEFAULT_TIME_FILTER", "all").strip()
SITE_NAME = environ.get("SITE_NAME", "").strip()

@app.get("/post/")
def slash_post():
	return redirect("/")

@app.post("/clear")
@auth_required
@validate_formkey
def clear(v):
	for n in v.notifications.filter_by(read=False).all():
		n.read = True
		g.db.add(n)
	g.db.commit()
	return {"message": "Notifications cleared!"}

@app.get("/notifications")
@auth_required
def notifications(v):
	try: page = int(request.values.get('page', 1))
	except: page = 1
	messages = request.values.get('messages', False)
	modmail = request.values.get('modmail', False)
	posts = request.values.get('posts', False)
	if modmail and v.admin_level > 1:
		comments = g.db.query(Comment).filter(Comment.sentto==0).order_by(Comment.created_utc.desc()).offset(25*(page-1)).limit(26).all()
		next_exists = (len(comments) > 25)
		comments = comments[:25]
	elif messages:
		comments = g.db.query(Comment).filter(or_(Comment.author_id==v.id, Comment.sentto==v.id), Comment.parent_submission == None).order_by(Comment.created_utc.desc(), not_(Comment.child_comments.any())).offset(25*(page-1)).limit(26).all()
		next_exists = (len(comments) > 25)
		comments = comments[:25]
	elif posts:
		notifications = v.notifications.join(Notification.comment).filter(Comment.author_id == AUTOJANNY_ID).order_by(Notification.id.desc()).offset(25 * (page - 1)).limit(101).all()

		listing = []

		for index, x in enumerate(notifications[:100]):
			c = x.comment
			if x.read and index > 24: break
			elif not x.read:
				x.read = True
				c.unread = True
				g.db.add(x)
			listing.append(c)

		g.db.commit()

		next_exists = (len(notifications) > len(listing))

	else:
		notifications = v.notifications.join(Notification.comment).filter(
			Comment.is_banned == False,
			Comment.deleted_utc == 0,
			Comment.author_id != AUTOJANNY_ID,
		).order_by(Notification.id.desc()).offset(25 * (page - 1)).limit(26).all()

		next_exists = (len(notifications) > 25)
		notifications = notifications[:25]
		cids = [x.comment_id for x in notifications]
		comments = get_comments(cids, v=v, load_parent=True)

		i = 0
		for x in notifications:
			try:
				if not x.read: comments[i].unread = True
			except: continue
			x.read = True
			g.db.add(x)
			i += 1
		g.db.commit()
		
	if not posts:
		listing = []
		for c in comments:
			c.is_blocked = False
			c.is_blocking = False
			if c.parent_submission and c.parent_comment and c.parent_comment.author_id == v.id:
				c.replies = []
				while c.parent_comment and c.parent_comment.author_id == v.id:
					parent = c.parent_comment
					if c not in parent.replies2:
						parent.replies2 = parent.replies2 + [c]
						parent.replies = parent.replies2
					c = parent
				if c not in listing:
					listing.append(c)
					c.replies = c.replies2
			elif c.parent_submission:
				c.replies = []
				if c not in listing:
					listing.append(c)
			else:
				if c.parent_comment:
					while c.level > 1:
						c = c.parent_comment

				if c not in listing:
					listing.append(c)

	if request.headers.get("Authorization"): return {"data":[x.json for x in listing]}

	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}notifications.html",
							v=v,
							notifications=listing,
							next_exists=next_exists,
							page=page,
							standalone=True,
							render_replies=True
						   )



@app.get("/")
@app.get("/logged_out")
@auth_desired
def front_all(v):

	if not v and request.path == "/" and not request.headers.get("Authorization"): return redirect(f"/logged_out{request.full_path}")

	if v and v.is_banned and not v.unban_utc: return render_template('errors/500.html', error=True, v=v), 500

	if v and request.path.startswith('/logged_out'): v = None

	try: page = max(int(request.values.get("page", 1)), 1)
	except: abort(400)

	if v:
		defaultsorting = v.defaultsorting
		defaulttime = v.defaulttime
	else:
		defaultsorting = "hot"
		defaulttime = defaulttimefilter

	sort=request.values.get("sort", defaultsorting)
	t=request.values.get('t', defaulttime)

	ids, next_exists = frontlist(sort=sort,
					page=page,
					t=t,
					v=v,
					filter_words=v.filter_words if v else [],
					gt=int(request.values.get("utc_greater_than", 0)),
					lt=int(request.values.get("utc_less_than", 0)),
					)

	posts = get_posts(ids, v=v)

	if v:
		if v.hidevotedon: posts = [x for x in posts if not hasattr(x, 'voted') or not x.voted]

		if v.agendaposter_expires_utc and v.agendaposter_expires_utc < time.time():
			v.agendaposter_expires_utc = 0
			v.agendaposter = None
			send_notification(v.id, "Your agendaposter theme has expired!")
			g.db.add(v)
			badge = v.has_badge(26)
			if badge: g.db.delete(badge)
			g.db.commit()

		if v.flairchanged and v.flairchanged < time.time():
			v.flairchanged = None
			send_notification(v.id, "Your flair lock has expired. You can now change your flair!")
			g.db.add(v)
			g.db.commit()

		if v.marseyawarded and v.marseyawarded < time.time():
			v.marseyawarded = None
			send_notification(v.id, "Your marsey award has expired!")
			g.db.add(v)
			g.db.commit()

		if v.longpost and v.longpost < time.time():
			v.longpost = None
			send_notification(v.id, "Your pizzashill award has expired!")
			g.db.add(v)
			g.db.commit()

		if v.bird and v.bird < time.time():
			v.bird = None
			send_notification(v.id, "Your bird site award has expired!")
			g.db.add(v)
			g.db.commit()

	if request.headers.get("Authorization"): return {"data": [x.json for x in posts], "next_exists": next_exists}
	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}home.html", v=v, listing=posts, next_exists=next_exists, sort=sort, t=t, page=page)



@cache.memoize(timeout=86400)
def frontlist(v=None, sort="hot", page=1, t="all", ids_only=True, filter_words='', gt=None, lt=None):

	posts = g.db.query(Submission)

	if t == 'all': cutoff = 0
	else:
		now = int(time.time())
		if t == 'hour': cutoff = now - 3600
		elif t == 'week': cutoff = now - 604800
		elif t == 'month': cutoff = now - 2592000
		elif t == 'year': cutoff = now - 31536000
		else: cutoff = now - 86400
		posts = posts.filter(Submission.created_utc >= cutoff)

	if sort != "hot": posts = posts.filter_by(is_banned=False, private=False, deleted_utc = 0)
	else: posts = posts.filter_by(is_banned=False, stickied=None, private=False, deleted_utc = 0)

	if v and v.admin_level == 0:
		blocking = [x[0] for x in g.db.query(
			UserBlock.target_id).filter_by(
			user_id=v.id).all()]
		blocked = [x[0] for x in g.db.query(
			UserBlock.user_id).filter_by(
			target_id=v.id).all()]
		posts = posts.filter(
			Submission.author_id.notin_(blocking),
			Submission.author_id.notin_(blocked)
		)

	if not (v and v.changelogsub):
		posts=posts.filter(not_(Submission.title.ilike(f'[changelog]%')))

	if v and filter_words:
		for word in filter_words:
			posts=posts.filter(not_(Submission.title.ilike(f'%{word}%')))

	if gt: posts = posts.filter(Submission.created_utc > gt)
	if lt: posts = posts.filter(Submission.created_utc < lt)

	if not (v and v.shadowbanned):
		posts = posts.join(User, User.id == Submission.author_id).filter(User.shadowbanned == None)

	if sort == "hot":
		ti = int(time.time()) + 3600
		posts = posts.order_by(-1000000*(Submission.realupvotes + 1 + Submission.comment_count/5)/(func.power(((ti - Submission.created_utc)/1000), 1.35)))
	elif sort == "new":
		posts = posts.order_by(Submission.created_utc.desc())
	elif sort == "old":
		posts = posts.order_by(Submission.created_utc.asc())
	elif sort == "controversial":
		posts = posts.order_by(-1 * Submission.upvotes * Submission.downvotes * Submission.downvotes)
	elif sort == "top":
		posts = posts.order_by(Submission.downvotes - Submission.upvotes)
	elif sort == "bottom":
		posts = posts.order_by(Submission.upvotes - Submission.downvotes)
	elif sort == "comments":
		posts = posts.order_by(Submission.comment_count.desc())

	if v: size = v.frontsize or 0
	else: size = 25

	posts = posts.offset(size * (page - 1)).limit(size+1).all()

	next_exists = (len(posts) > size)

	posts = posts[:size]

	if sort == "hot" and page == 1:
		pins = g.db.query(Submission).filter(Submission.stickied != None, Submission.is_banned == False)
		if v and v.admin_level == 0:
			blocking = [x[0] for x in g.db.query(UserBlock.target_id).filter_by(user_id=v.id).all()]
			blocked = [x[0] for x in g.db.query(UserBlock.user_id).filter_by(target_id=v.id).all()]
			pins = pins.filter(Submission.author_id.notin_(blocking), Submission.author_id.notin_(blocked))

		posts = pins.all() + posts

	if ids_only: posts = [x.id for x in posts]

	return posts, next_exists


@app.get("/changelog")
@auth_desired
def changelog(v):


	page = int(request.values.get("page") or 1)
	page = max(page, 1)

	sort=request.values.get("sort", "new")
	t=request.values.get('t', "all")

	ids = changeloglist(sort=sort,
					page=page,
					t=t,
					v=v,
					)

	next_exists = (len(ids) > 25)
	ids = ids[:25]

	posts = get_posts(ids, v=v)

	if request.headers.get("Authorization"): return {"data": [x.json for x in posts], "next_exists": next_exists}
	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}changelog.html", v=v, listing=posts, next_exists=next_exists, sort=sort, t=t, page=page)


@cache.memoize(timeout=86400)
def changeloglist(v=None, sort="new", page=1 ,t="all"):

	posts = g.db.query(Submission.id).filter_by(is_banned=False, private=False,).filter(Submission.deleted_utc == 0)

	if v and v.admin_level == 0:
		blocking = [x[0] for x in g.db.query(
			UserBlock.target_id).filter_by(
			user_id=v.id).all()]
		blocked = [x[0] for x in g.db.query(
			UserBlock.user_id).filter_by(
			target_id=v.id).all()]
		posts = posts.filter(
			Submission.author_id.notin_(blocking),
			Submission.author_id.notin_(blocked)
		)

	admins = [x[0] for x in g.db.query(User.id).filter(User.admin_level > 1).all()]
	posts = posts.filter(Submission.title.ilike('_changelog%'), Submission.author_id.in_(admins))

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

	if sort == "new":
		posts = posts.order_by(Submission.created_utc.desc())
	elif sort == "old":
		posts = posts.order_by(Submission.created_utc.asc())
	elif sort == "controversial":
		posts = posts.order_by(-1 * Submission.upvotes * Submission.downvotes * Submission.downvotes)
	elif sort == "top":
		posts = posts.order_by(Submission.downvotes - Submission.upvotes)
	elif sort == "bottom":
		posts = posts.order_by(Submission.upvotes - Submission.downvotes)
	elif sort == "comments":
		posts = posts.order_by(Submission.comment_count.desc())

	posts = posts.offset(25 * (page - 1)).limit(26).all()

	return [x[0] for x in posts]


@app.get("/random")
@auth_desired
def random_post(v):

	x = g.db.query(Submission).filter(Submission.deleted_utc == 0, Submission.is_banned == False)
	total = x.count()
	n = random.randint(1, total - 2)

	post = x.offset(n).limit(1).first()
	return redirect(f"/post/{post.id}")

@cache.memoize(timeout=86400)
def comment_idlist(page=1, v=None, nsfw=False, sort="new", t="all"):

	posts = g.db.query(Submission)
	cc_idlist = [x[0] for x in g.db.query(Submission.id).filter(Submission.club == True).all()]

	posts = posts.subquery()

	comments = g.db.query(Comment.id).filter(Comment.parent_submission.notin_(cc_idlist))

	if v and v.admin_level <= 3:
		blocking = [x[0] for x in g.db.query(
			UserBlock.target_id).filter_by(
			user_id=v.id).all()]
		blocked = [x[0] for x in g.db.query(
			UserBlock.user_id).filter_by(
			target_id=v.id).all()]

		comments = comments.filter(Comment.author_id.notin_(blocking), Comment.author_id.notin_(blocked))

	if not v or not v.admin_level > 1:
		comments = comments.filter(Comment.is_banned==False, Comment.deleted_utc == 0)

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
		comments = comments.order_by(Comment.created_utc.asc())
	elif sort == "controversial":
		comments = comments.order_by(-1 * Comment.upvotes * Comment.downvotes * Comment.downvotes)
	elif sort == "top":
		comments = comments.order_by(Comment.realupvotes.desc())
	elif sort == "bottom":
		comments = comments.order_by(Comment.upvotes - Comment.downvotes)

	comments = comments.offset(25 * (page - 1)).limit(26).all()
	return [x[0] for x in comments]

@app.get("/comments")
@auth_desired
def all_comments(v):


	page = int(request.values.get("page", 1))

	sort=request.values.get("sort", "new")
	t=request.values.get("t", defaulttimefilter)

	idlist = comment_idlist(v=v,
							page=page,
							sort=sort,
							t=t,
							)

	comments = get_comments(idlist, v=v)

	next_exists = len(idlist) > 25

	idlist = idlist[:25]

	if request.headers.get("Authorization"): return {"data": [x.json for x in comments]}
	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}home_comments.html", v=v, sort=sort, t=t, page=page, comments=comments, standalone=True, next_exists=next_exists)