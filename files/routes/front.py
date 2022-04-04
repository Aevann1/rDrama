from files.helpers.wrappers import *
from files.helpers.get import *
from files.helpers.discord import *
from files.__main__ import app, cache, limiter
from files.classes.submission import Submission

defaulttimefilter = environ.get("DEFAULT_TIME_FILTER", "all").strip()

@app.post("/clear")
@auth_required
def clear(v):
	notifs = g.db.query(Notification, Comment).join(Comment, Notification.comment_id == Comment.id).filter(Notification.read == False, Notification.user_id == v.id).all()
	for n in notifs:
		n.read = True
		g.db.add(n)
	g.db.commit()
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
	g.db.commit()

	return {"data":[x[1].json for x in listing]}


@app.get("/notifications")
@auth_required
def notifications(v):
	t = time.time()
	try: page = int(request.values.get('page', 1))
	except: page = 1
	messages = request.values.get('messages')
	modmail = request.values.get('modmail')
	posts = request.values.get('posts')
	reddit = request.values.get('reddit')
	if modmail and v.admin_level > 1:
		comments = g.db.query(Comment).filter(Comment.sentto==2).order_by(Comment.id.desc()).offset(25*(page-1)).limit(26).all()
		next_exists = (len(comments) > 25)
		listing = comments[:25]
	elif messages:
		comments = g.db.query(Comment).filter(Comment.sentto != None, or_(Comment.author_id==v.id, Comment.sentto==v.id), Comment.parent_submission == None, Comment.level == 1).order_by(Comment.id.desc()).offset(25*(page-1)).limit(26).all()
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

		g.db.commit()

		next_exists = (len(notifications) > len(listing))
	elif reddit:
		notifications = g.db.query(Notification, Comment).join(Comment, Notification.comment_id == Comment.id).filter(Notification.user_id == v.id, Comment.body_html.like('<html><body><p>New rdrama mention: <a href="https://old.reddit.com/r/%')).order_by(Notification.created_utc.desc()).offset(25 * (page - 1)).limit(101).all()

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

		g.db.commit()

		next_exists = (len(notifications) > len(listing))
	else:
		unread = g.db.query(Notification, Comment).join(Comment, Notification.comment_id == Comment.id).filter(
			Notification.read == False,
			Notification.user_id == v.id,
			Comment.author_id != AUTOJANNY_ID,
			Comment.body_html.notlike('<html><body><p>New rdrama mention: <a href="https://old.reddit.com/r/%'))
		
		for n, c in unread:
			n.read = True
			c.unread = True
			g.db.add(c)
		g.db.commit()

		print("1: " + str(time.time() - t), flush=True)

		all = [x[0] for x in g.db.query(Comment.id).join(Notification).filter(
			Notification.user_id == v.id,
			Comment.is_banned == False,
			Comment.deleted_utc == 0,
			Comment.author_id != AUTOJANNY_ID,
			Comment.body_html.notlike('<html><body><p>New rdrama mention: <a href="https://old.reddit.com/r/%')
		).order_by(Comment.top_comment_id.desc()).offset(25 * (page - 1)).limit(100).all()]

		print("2: " + str(time.time() - t), flush=True)

		comments = g.db.query(Comment).join(Notification).distinct(Comment.top_comment_id).filter(
			Notification.user_id == v.id,
			Comment.is_banned == False,
			Comment.deleted_utc == 0,
			Comment.author_id != AUTOJANNY_ID,
			Comment.body_html.notlike('<html><body><p>New rdrama mention: <a href="https://old.reddit.com/r/%')
		).order_by(Comment.top_comment_id.desc()).offset(25 * (page - 1)).limit(26).all()

		next_exists = (len(comments) > 25)
		comments = comments[:25]

		print("3: " + str(time.time() - t), flush=True)

		cids = set()
		listing = []
		for c in comments:
			if c.parent_submission:
				if not c.replies2:
					c.replies2 = c.child_comments.filter(or_(Comment.author_id == v.id, Comment.id.in_(all))).all()
					print(c.replies2)
					cids = cids | set(x.id for x in c.replies2)
				while c.parent_comment and (c.parent_comment.author_id == v.id or c.parent_comment in comments):
					c = c.parent_comment
					if not c.replies2:
						c.replies2 = c.child_comments.filter(or_(Comment.author_id == v.id, Comment.id.in_(all))).all()
						print(c.replies2)
						cids = cids | set(x.id for x in c.replies2)
				cids.add(c.id)
			else:
				while c.parent_comment:
					c = c.parent_comment
				c.replies2 = g.db.query(Comment).filter_by(parent_comment_id=c.id).order_by(Comment.id).all()

			if c not in listing: listing.append(c)

	print("4: " + str(time.time() - t), flush=True)

	comms = get_comments(list(cids), v=v)

	if request.headers.get("Authorization"): return {"data":[x.json for x in listing]}

	print("5: " + str(time.time() - t), flush=True)
	return render_template("notifications.html",
							v=v,
							notifications=listing,
							next_exists=next_exists,
							page=page,
							standalone=True,
							render_replies=True
						   )


@app.get("/")
@app.get("/h/<sub>")
@app.get("/s/<sub>")
@limiter.limit("3/second;30/minute;1000/hour;5000/day")
@auth_desired
def front_all(v, sub=None, subdomain=None):
	if sub: sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	
	if (request.path.startswith('/h/') or request.path.startswith('/s/')) and not sub: abort(404)

	if g.webview and not session.get("session_id"):
		session["session_id"] = secrets.token_hex(49)

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

	if v: subs = v.subs
	elif SITE_NAME == 'rDrama': subs = 1
	else: subs = 2

	ids, next_exists = frontlist(sort=sort,
					page=page,
					t=t,
					v=v,
					ccmode=ccmode,
					filter_words=v.filter_words if v else [],
					gt=gt,
					lt=lt,
					sub=sub,
					site=SITE,
					subs=subs
					)

	posts = get_posts(ids, v=v)
	
	if v:
		if v.hidevotedon: posts = [x for x in posts if not hasattr(x, 'voted') or not x.voted]

	
		if v.patron_utc and v.patron_utc < time.time():
			v.patron = 0
			v.patron_utc = 0
			send_repeatable_notification(v.id, "Your paypig status has expired!")
			if v.discord_id: remove_role(v, "1")
			g.db.add(v)
			g.db.commit()

		if v.unban_utc and v.unban_utc < time.time():
			v.is_banned = 0
			v.unban_utc = 0
			v.ban_evade = 0
			send_repeatable_notification(v.id, "You have been unbanned!")
			g.db.add(v)
			g.db.commit()

		if v.agendaposter and v.agendaposter < time.time():
			v.agendaposter = 0
			send_repeatable_notification(v.id, "Your chud theme has expired!")
			g.db.add(v)
			badge = v.has_badge(28)
			if badge: g.db.delete(badge)
			g.db.commit()

		if v.flairchanged and v.flairchanged < time.time():
			v.flairchanged = None
			send_repeatable_notification(v.id, "Your flair lock has expired. You can now change your flair!")
			g.db.add(v)
			badge = v.has_badge(96)
			if badge: g.db.delete(badge)
			g.db.commit()

		if v.marseyawarded and v.marseyawarded < time.time():
			v.marseyawarded = None
			send_repeatable_notification(v.id, "Your marsey award has expired!")
			g.db.add(v)
			badge = v.has_badge(98)
			if badge: g.db.delete(badge)
			g.db.commit()

		if v.longpost and v.longpost < time.time():
			v.longpost = None
			send_repeatable_notification(v.id, "Your pizzashill award has expired!")
			g.db.add(v)
			badge = v.has_badge(97)
			if badge: g.db.delete(badge)
			g.db.commit()

		if v.bird and v.bird < time.time():
			v.bird = None
			send_repeatable_notification(v.id, "Your bird site award has expired!")
			g.db.add(v)
			badge = v.has_badge(95)
			if badge: g.db.delete(badge)
			g.db.commit()

		if v.progressivestack and v.progressivestack < time.time():
			v.progressivestack = None
			send_repeatable_notification(v.id, "Your progressive stack has expired!")
			g.db.add(v)
			badge = v.has_badge(94)
			if badge: g.db.delete(badge)
			g.db.commit()

		if v.rehab and v.rehab < time.time():
			v.rehab = None
			send_repeatable_notification(v.id, "Your rehab has finished!")
			g.db.add(v)
			badge = v.has_badge(109)
			if badge: g.db.delete(badge)
			g.db.commit()

		if v.deflector and v.deflector < time.time():
			v.deflector = None
			send_repeatable_notification(v.id, "Your deflector has expired!")
			g.db.add(v)
			g.db.commit()

	if request.headers.get("Authorization"): return {"data": [x.json for x in posts], "next_exists": next_exists}
	return render_template("home.html", v=v, listing=posts, next_exists=next_exists, sort=sort, t=t, page=page, ccmode=ccmode, sub=sub, home=True)



@cache.memoize(timeout=86400)
def frontlist(v=None, sort="hot", page=1, t="all", ids_only=True, ccmode="false", filter_words='', gt=0, lt=0, sub=None, site=None, subs=2):

	posts = g.db.query(Submission)
	
	if v and v.hidevotedon:
		voted = [x[0] for x in g.db.query(Vote.submission_id).filter_by(user_id=v.id).all()]
		posts = posts.filter(Submission.id.notin_(voted))

	if sub:
		posts = posts.filter_by(sub=sub.name)
	elif not v:
		if subs == 1: posts = posts.filter(Submission.sub == None)
	elif v.subs == 1:
		posts = posts.filter(or_(Submission.sub == None, Submission.sub.in_(v.subbed_subs)))
	elif v.subs == 2:
		posts = posts.filter(or_(Submission.sub == None, Submission.sub.notin_(v.all_blocks)))
	elif v.subs == 3:
		posts = posts.filter(Submission.sub != None, Submission.sub.notin_(v.all_blocks))


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
		posts = posts.filter_by(stickied=None)

	if v and v.admin_level < 2:
		posts = posts.filter(Submission.author_id.notin_(v.userblocks))

	if not (v and v.changelogsub):
		posts=posts.filter(not_(Submission.title.ilike('[changelog]%')))

	if v and filter_words:
		for word in filter_words:
			word  = word.replace('\\', '').replace('_', '\_').replace('%', '\%').strip()
			posts=posts.filter(not_(Submission.title.ilike(f'%{word}%')))

	if not (v and v.shadowbanned):
		posts = posts.join(User, User.id == Submission.author_id).filter(User.shadowbanned == None)

	if sort == "hot":
		ti = int(time.time()) + 3600
		posts = posts.order_by(-1000000*(Submission.realupvotes + 1 + Submission.comment_count/5 + (func.length(Submission.body_html)-func.length(func.replace(Submission.body_html,'</a>','')))/4)/(func.power(((ti - Submission.created_utc)/1000), 1.23)), Submission.created_utc.desc())
	elif sort == "bump":
		posts = posts.filter(Submission.comment_count > 1).order_by(Submission.bump_utc.desc(), Submission.created_utc.desc())
	elif sort == "new":
		posts = posts.order_by(Submission.created_utc.desc())
	elif sort == "old":
		posts = posts.order_by(Submission.created_utc)
	elif sort == "controversial":
		posts = posts.order_by((Submission.upvotes+1)/(Submission.downvotes+1) + (Submission.downvotes+1)/(Submission.upvotes+1), Submission.downvotes.desc(), Submission.created_utc.desc())
	elif sort == "top":
		posts = posts.order_by(Submission.downvotes - Submission.upvotes, Submission.created_utc.desc())
	elif sort == "bottom":
		posts = posts.order_by(Submission.upvotes - Submission.downvotes, Submission.created_utc.desc())
	elif sort == "comments":
		posts = posts.order_by(Submission.comment_count.desc(), Submission.created_utc.desc())

	if v: size = v.frontsize or 0
	else: size = 25

	posts = posts.offset(size * (page - 1)).limit(size+1).all()

	next_exists = (len(posts) > size)

	posts = posts[:size]

	if (sort == "hot" or (v and v.id == Q_ID)) and page == 1 and ccmode == "false" and not gt and not lt:
		pins = g.db.query(Submission).filter(Submission.stickied != None, Submission.is_banned == False)
		if sub:
			pins = pins.filter_by(sub=sub.name)
		elif not v:
			if subs == 1: pins = pins.filter(Submission.sub == None)
		elif v.subs == 1:
			pins = pins.filter(or_(Submission.sub == None, Submission.sub.in_(v.subbed_subs)))
		elif v.subs == 2:
			pins = pins.filter(or_(Submission.sub == None, Submission.sub.notin_(v.all_blocks)))
		elif v.subs == 3:
			pins = pins.filter(Submission.sub != None, Submission.sub.notin_(v.all_blocks))

		if v and v.admin_level < 2:
			pins = pins.filter(Submission.author_id.notin_(v.userblocks))

		pins = pins.all()

		for pin in pins:
			if pin.stickied_utc and int(time.time()) > pin.stickied_utc:
				pin.stickied = None
				pin.stickied_utc = None
				g.db.add(pin)
				pins.remove(pin)

		posts = pins + posts

	if ids_only: posts = [x.id for x in posts]

	g.db.commit()

	return posts, next_exists


@app.get("/changelog")
@auth_required
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
	return render_template("changelog.html", v=v, listing=posts, next_exists=next_exists, sort=sort, t=t, page=page)


@cache.memoize(timeout=86400)
def changeloglist(v=None, sort="new", page=1 ,t="all"):

	posts = g.db.query(Submission.id).filter_by(is_banned=False, private=False,).filter(Submission.deleted_utc == 0)

	if v.admin_level < 2:
		posts = posts.filter(Submission.author_id.notin_(v.userblocks))

	admins = [x[0] for x in g.db.query(User.id).filter(User.admin_level > 0).all()]
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
		posts = posts.order_by(Submission.created_utc)
	elif sort == "controversial":
		posts = posts.order_by((Submission.upvotes+1)/(Submission.downvotes+1) + (Submission.downvotes+1)/(Submission.upvotes+1), Submission.downvotes.desc())
	elif sort == "top":
		posts = posts.order_by(Submission.downvotes - Submission.upvotes)
	elif sort == "bottom":
		posts = posts.order_by(Submission.upvotes - Submission.downvotes)
	elif sort == "comments":
		posts = posts.order_by(Submission.comment_count.desc())

	posts = posts.offset(25 * (page - 1)).limit(26).all()

	return [x[0] for x in posts]


@app.get("/random")
@auth_required
def random_post(v):

	x = g.db.query(Submission).filter(Submission.deleted_utc == 0, Submission.is_banned == False, Submission.private == False)
	total = x.count()
	n = random.randint(1, total - 2)

	post = x.offset(n).limit(1).one_or_none()
	return redirect(f"/post/{post.id}")

@app.get("/comments")
@auth_required
def all_comments(v):


	page = int(request.values.get("page", 1))

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
							lt=lt
							)

	comments = get_comments(idlist, v=v)

	next_exists = len(idlist) > 25

	idlist = idlist[:25]

	if request.headers.get("Authorization"): return {"data": [x.json for x in comments]}
	return render_template("home_comments.html", v=v, sort=sort, t=t, page=page, comments=comments, standalone=True, next_exists=next_exists)



@cache.memoize(timeout=86400)
def comment_idlist(page=1, v=None, nsfw=False, sort="new", t="all", gt=0, lt=0):

	comments = g.db.query(Comment.id).filter(Comment.parent_submission != None)

	if v.admin_level < 2:
		private = [x[0] for x in g.db.query(Submission.id).filter(Submission.private == True).all()]

		comments = comments.filter(Comment.author_id.notin_(v.userblocks), Comment.is_banned==False, Comment.deleted_utc == 0, Comment.parent_submission.notin_(private))


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
	return [x[0] for x in comments]


@app.get("/transfers")
@auth_required
def transfers(v):

	comments = g.db.query(Comment).filter(Comment.author_id == NOTIFICATIONS_ID, Comment.parent_submission == None, Comment.body_html.like("%</a> has transferred %")).order_by(Comment.id.desc())

	if request.headers.get("Authorization"): return {"data": [x.json for x in comments.all()]}

	page = int(request.values.get("page", 1))
	comments = comments.offset(25 * (page - 1)).limit(26).all()
	next_exists = len(comments) > 25
	comments = comments[:25]
	return render_template("transfers.html", v=v, page=page, comments=comments, standalone=True, next_exists=next_exists)