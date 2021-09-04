import traceback
import sys

from files.helpers.wrappers import *
from files.helpers.filters import *
from files.helpers.alerts import *
from files.helpers.images import *
from files.helpers.session import *
from files.helpers.const import *
from files.classes import *
from files.routes.front import comment_idlist
from pusher_push_notifications import PushNotifications

from flask import *
from files.__main__ import app, limiter

site = environ.get("DOMAIN").strip()

beams_client = PushNotifications(
		instance_id=PUSHER_INSTANCE_ID,
		secret_key=PUSHER_KEY,
)

@app.get("/comment/<cid>")
@app.get("/post/<pid>/<anything>/<cid>")
@app.get("/logged_out/comment/<cid>")
@app.get("/logged_out/post/<pid>/<anything>/<cid>")
@auth_desired
def post_pid_comment_cid(cid, pid=None, anything=None, v=None):


	
	if not v and "logged_out" not in request.path: return redirect(f"/logged_out/comment/{cid}")

	if v and "logged_out" in request.full_path: v = None
	
	try: cid = int(cid)
	except:
		try: cid = int(cid, 36)
		except: abort(404)

	comment = get_comment(cid, v=v)
	
	if not comment.parent_submission and not (v and (comment.author.id == v.id or comment.sentto == v.id)) and not (v and v.admin_level == 6) : abort(403)
	
	if not pid:
		if comment.parent_submission: pid = comment.parent_submission
		else: pid = 6489
	
	try: pid = int(pid)
	except: abort(404)
	
	post = get_post(pid, v=v)
		
	if post.over_18 and not (v and v.over_18) and not session.get('over_18', 0) >= int(time.time()):
		if request.headers.get("Authorization"): return {'error': f'This content is not suitable for some users and situations.'}
		else: render_template("errors/nsfw.html", v=v)

	post._preloaded_comments = [comment]

	# context improver
	try: context = int(request.args.get("context", 0))
	except: context = 0
	comment_info = comment
	c = comment
	while context > 0 and c.level > 1:

		parent = get_comment(c.parent_comment_id, v=v)

		post._preloaded_comments += [parent]

		c = parent
		context -= 1
	top_comment = c

	if v: defaultsortingcomments = v.defaultsortingcomments
	else: defaultsortingcomments = "top"
	sort=request.args.get("sort", defaultsortingcomments)

	post.replies=[top_comment]

	if v:
		votes = g.db.query(CommentVote).filter_by(user_id=v.id).subquery()

		blocking = v.blocking.subquery()

		blocked = v.blocked.subquery()

		comments = g.db.query(
			Comment,
			votes.c.vote_type,
			blocking.c.id,
			blocked.c.id,
		)
		if v.admin_level >=4:
			comments=comments.options(joinedload(Comment.oauth_app))
 
		comments=comments.filter(
			Comment.parent_submission == post.id
		).join(
			votes,
			votes.c.comment_id == Comment.id,
			isouter=True
		).join(
			blocking,
			blocking.c.target_id == Comment.author_id,
			isouter=True
		).join(
			blocked,
			blocked.c.user_id == Comment.author_id,
			isouter=True
		)

		for c in comments:
			comment = c[0]
			if comment.author and comment.author.shadowbanned and not (v and v.id == comment.author_id): continue
			comment.voted = c[1] or 0
			comment._is_blocking = c[2] or 0
			comment._is_blocked = c[3] or 0

	if request.headers.get("Authorization"): return top_comment.json
	else: return post.rendered_page(v=v, sort=sort, comment=top_comment, comment_info=comment_info)


@app.post("/comment")
@limiter.limit("6/minute")
@is_not_banned
@validate_formkey
def api_comment(v):

	parent_submission = request.form.get("submission")
	parent_fullname = request.form.get("parent_fullname")

	# get parent item info
	parent_id = parent_fullname.split("_")[1]
	if parent_fullname.startswith("t2"):
		parent_post = get_post(parent_id, v=v)
		parent = parent_post
		parent_comment_id = None
		level = 1
		parent_submission = parent_id
	elif parent_fullname.startswith("t3"):
		parent = get_comment(parent_id, v=v)
		parent_comment_id = parent.id
		level = parent.level + 1
		parent_id = parent.parent_submission
		parent_submission = parent_id
		parent_post = get_post(parent_id)
	else:
		abort(400)

	#process and sanitize
	body = request.form.get("body", "")[:10000]
	body = body.strip()

	if not body and not request.files.get('file'): return {"error":"You need to actually write something!"}, 400
	
	for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|PNG|JPG|JPEG|GIF|9999))', body, re.MULTILINE): body = body.replace(i.group(1), f'![]({i.group(1)})')
	body = body.replace("\n", "\n\n").replace("\n\n\n\n\n\n", "\n\n").replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
	with CustomRenderer(post_id=parent_id) as renderer: body_md = renderer.render(mistletoe.Document(body))
	body_html = sanitize(body_md)

	# Run safety filter
	bans = filter_comment_html(body_html)

	if bans:
		ban = bans[0]
		reason = f"Remove the {ban.domain} link from your comment and try again."
		if ban.reason:
			reason += f" {ban.reason}"
			
		#auto ban for digitally malicious content
		if any([x.reason==4 for x in bans]):
			v.ban(days=30, reason="Digitally malicious content")
		if any([x.reason==7 for x in bans]):
			v.ban( reason="Sexualizing minors")
		return {"error": reason}, 401

	# check existing
	existing = g.db.query(Comment).join(CommentAux).filter(Comment.author_id == v.id,
															 Comment.deleted_utc == 0,
															 Comment.parent_comment_id == parent_comment_id,
															 Comment.parent_submission == parent_submission,
															 CommentAux.body == body
															 ).options(contains_eager(Comment.comment_aux)).first()
	if existing:
		return {"error": f"You already made that comment: {existing.permalink}"}, 409

	if parent.author.any_block_exists(v) and not v.admin_level>=3:
		return {"error": "You can't reply to users who have blocked you, or users you have blocked."}, 403

	# get bot status
	is_bot = request.headers.get("X-User-Type","")=="Bot"

	# check spam - this should hopefully be faster
	if not is_bot:
		now = int(time.time())
		cutoff = now - 60 * 60 * 24

		similar_comments = g.db.query(Comment
										).options(
			lazyload('*')
		).join(Comment.comment_aux
				 ).filter(
			Comment.author_id == v.id,
			CommentAux.body.op(
				'<->')(body) < app.config["COMMENT_SPAM_SIMILAR_THRESHOLD"],
			Comment.created_utc > cutoff
		).options(contains_eager(Comment.comment_aux)).all()

		threshold = app.config["COMMENT_SPAM_COUNT_THRESHOLD"]
		if v.age >= (60 * 60 * 24 * 7):
			threshold *= 3
		elif v.age >= (60 * 60 * 24):
			threshold *= 2

		if len(similar_comments) > threshold:
			text = "Your account has been suspended for 1 day for the following reason:\n\n> Too much spam!"
			send_notification(NOTIFICATIONS_ACCOUNT, v, text)

			v.ban(reason="Spamming.",
					days=1)

			for alt in v.alts:
				if not alt.is_suspended:
					alt.ban(reason="Spamming.", days=1)

			for comment in similar_comments:
				comment.is_banned = True
				comment.ban_reason = "Automatic spam removal. This happened because the post's creator submitted too much similar content too quickly."
				g.db.add(comment)
				ma=ModAction(
					user_id=AUTOJANNY_ACCOUNT,
					target_comment_id=comment.id,
					kind="ban_comment",
					note="spam"
					)
				g.db.add(ma)

			return {"error": "Too much spam!"}, 403

	# check badlinks
	soup = BeautifulSoup(body_html, features="html.parser")
	links = [x['href'] for x in soup.find_all('a') if x.get('href')]

	for link in links:
		parse_link = urlparse(link)
		check_url = ParseResult(scheme="https",
								netloc=parse_link.netloc,
								path=parse_link.path,
								params=parse_link.params,
								query=parse_link.query,
								fragment='')
		check_url = urlunparse(check_url)

		badlink = g.db.query(BadLink).filter(
			literal(check_url).contains(
				BadLink.link)).first()

		if badlink: return {"error": f"Remove the following link and try again: `{check_url}`. Reason: {badlink.reason}"}, 403
	# create comment
	parent_id = parent_fullname.split("_")[1]
	c = Comment(author_id=v.id,
				parent_submission=parent_submission,
				parent_comment_id=parent_comment_id,
				level=level,
				over_18=parent_post.over_18 or request.form.get("over_18","")=="true",
				is_bot=is_bot,
				app_id=v.client.application.id if v.client else None
				)

	g.db.add(c)
	g.db.flush()

	if request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
		file=request.files["file"]
		if not file.content_type.startswith('image/'): return {"error": "That wasn't an image!"}, 400
		
		url = upload_file(file)
		
		body = request.form.get("body") + f"\n![]({url})"
		body = body.replace("\n", "\n\n").replace("\n\n\n\n\n\n", "\n\n").replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
		with CustomRenderer(post_id=parent_id) as renderer:
			body_md = renderer.render(mistletoe.Document(body))
		body_html = sanitize(body_md)

	c_aux = CommentAux(
		id=c.id,
		body_html=body_html,
		body=body
	)

	g.db.add(c_aux)
	g.db.flush()

	if v.agendaposter and "trans lives matter" not in c_aux.body_html.lower():

		c.is_banned = True
		c.ban_reason = "ToS Violation"

		g.db.add(c)

		c_jannied = Comment(author_id=AUTOJANNY_ACCOUNT,
			parent_submission=parent_submission,
			distinguish_level=6,
			parent_comment_id=c.id,
			level=level+1,
			is_bot=True,
			)

		g.db.add(c_jannied)
		g.db.flush()

		body = AGENDAPOSTER_MSG.format(username=v.username)

		#body = body.replace("\n", "\n\n").replace("\n\n\n\n\n\n", "\n\n").replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
		with CustomRenderer(post_id=parent_id) as renderer:
			body_md = renderer.render(mistletoe.Document(body))

		body_jannied_html = sanitize(body_md)
		c_aux = CommentAux(
			id=c_jannied.id,
			body_html=body_jannied_html,
			body=body
		)
		g.db.add(c_aux)
		g.db.flush()
		n = Notification(comment_id=c_jannied.id, user_id=v.id)
		g.db.add(n)

	if "rdrama" in request.host and len(body) >= 1000 and v.username != "Snappy" and "</blockquote>" not in body_html:
		c2 = Comment(author_id=LONGPOSTBOT_ACCOUNT,
			parent_submission=parent_submission,
			parent_comment_id=c.id,
			level=level+1,
			is_bot=True,
			)

		g.db.add(c2)
		g.db.flush()
	
		body = random.choice(LONGPOST_REPLIES)
		body = body.replace("\n", "\n\n").replace("\n\n\n\n\n\n", "\n\n").replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
		with CustomRenderer(post_id=parent_id) as renderer: body_md = renderer.render(mistletoe.Document(body))
		body_html2 = sanitize(body_md)
		c_aux = CommentAux(
			id=c2.id,
			body_html=body_html2,
			body=body
		)
		g.db.add(c_aux)
		g.db.flush()
		n = Notification(comment_id=c2.id, user_id=v.id)
		g.db.add(n)







	if "rdrama" in request.host and random.random() < 0.001 and v.username != "Snappy" and v.username != "zozbot":
		c2 = Comment(author_id=1833,
			parent_submission=parent_submission,
			parent_comment_id=c.id,
			level=level+1,
			is_bot=True,
			)

		g.db.add(c2)
		g.db.flush()
	
		body = "zoz"
		with CustomRenderer(post_id=parent_id) as renderer: body_md = renderer.render(mistletoe.Document(body))
		body_html2 = sanitize(body_md)
		c_aux = CommentAux(
			id=c2.id,
			body_html=body_html2,
			body=body
		)
		g.db.add(c_aux)
		g.db.flush()
		n = Notification(comment_id=c2.id, user_id=v.id)
		g.db.add(n)




		c3 = Comment(author_id=1833,
			parent_submission=parent_submission,
			parent_comment_id=c2.id,
			level=level+2,
			is_bot=True,
			)

		g.db.add(c3)
		g.db.flush()
	
		body = "zle"
		with CustomRenderer(post_id=parent_id) as renderer: body_md = renderer.render(mistletoe.Document(body))
		body_html2 = sanitize(body_md)
		c_aux = CommentAux(
			id=c3.id,
			body_html=body_html2,
			body=body
		)
		g.db.add(c_aux)
		g.db.flush()
		
		



		
		c4 = Comment(author_id=1833,
			parent_submission=parent_submission,
			parent_comment_id=c3.id,
			level=level+3,
			is_bot=True,
			)

		g.db.add(c4)
		g.db.flush()
	
		body = "zozzle"
		with CustomRenderer(post_id=parent_id) as renderer: body_md = renderer.render(mistletoe.Document(body))
		body_html2 = sanitize(body_md)
		c_aux = CommentAux(
			id=c4.id,
			body_html=body_html2,
			body=body
		)
		g.db.add(c_aux)
		g.db.flush()












	if not v.shadowbanned:
		# queue up notification for parent author
		notify_users = set()
		
		for x in g.db.query(Subscription.user_id).filter_by(submission_id=c.parent_submission).all():
			notify_users.add(x[0])
		
		if parent.author.id != v.id: notify_users.add(parent.author.id)

		soup = BeautifulSoup(body_html, features="html.parser")
		mentions = soup.find_all("a", href=re.compile("^/@(\w+)"))
		for mention in mentions:
			username = mention["href"].split("@")[1]

			user = g.db.query(User).filter_by(username=username).first()

			if user:
				if v.any_block_exists(user):
					continue
				if user.id != v.id:
					notify_users.add(user.id)
		for x in notify_users:
			n = Notification(comment_id=c.id, user_id=x)
			g.db.add(n)
			g.db.flush()

		if parent.author.id != v.id:
			try:
				beams_client.publish_to_interests(
				  interests=[str(parent.author.id)],
				  publish_body={
					'web': {
					  'notification': {
							'title': f'New reply by @{v.username}',
							'body': c.body,
							'deep_link': f'https://{site}{c.permalink}?context=5#context',
					  },
					},
				  },
				)
			except Exception as e:
				print(e)				



	# create auto upvote
	vote = CommentVote(user_id=v.id,
						 comment_id=c.id,
						 vote_type=1
						 )

	g.db.add(vote)

	cache.delete_memoized(comment_idlist)
	cache.delete_memoized(User.commentlisting, v)

	v.comment_count = v.comments.filter(Comment.parent_submission != None).filter_by(is_banned=False, deleted_utc=0).count()
	g.db.add(v)

	parent_post.comment_count = g.db.query(Comment).filter_by(parent_submission=parent_post.id).count()
	g.db.add(parent_post)
	g.db.commit()

	if request.headers.get("Authorization"): return c.json
	else: return jsonify({"html": render_template("comments.html",
													v=v,
													comments=[c],
													render_replies=False,
													)})



@app.post("/edit_comment/<cid>")
@auth_required
@validate_formkey
def edit_comment(cid, v):

	c = get_comment(cid, v=v)

	if not c.author_id == v.id: abort(403)

	if c.is_banned or c.deleted_utc > 0: abort(403)

	body = request.form.get("body", "")[:10000]
	for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|PNG|JPG|JPEG|GIF|9999))', body, re.MULTILINE): body = body.replace(i.group(1), f'![]({i.group(1)})')
	body = body.replace("\n", "\n\n").replace("\n\n\n\n\n\n", "\n\n").replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
	with CustomRenderer(post_id=c.post.id) as renderer: body_md = renderer.render(mistletoe.Document(body))
	body_html = sanitize(body_md)

	bans = filter_comment_html(body_html)

	if bans:
		
		ban = bans[0]
		reason = f"Remove the {ban.domain} link from your comment and try again."

		#auto ban for digitally malicious content
		if any([x.reason==4 for x in bans]):
			v.ban(days=30, reason="Digitally malicious content is not allowed.")
			return {"error":"Digitally malicious content is not allowed."}
		
		if ban.reason:
			reason += f" {ban.reason}"	
	
		if request.headers.get("Authorization"): return {'error': f'A blacklisted domain was used.'}, 400
		else: return render_template("comment_failed.html",
												action=f"/edit_comment/{c.id}",
												badlinks=[
													x.domain for x in bans],
												body=body,
												v=v
												)
	# check badlinks
	soup = BeautifulSoup(body_html, features="html.parser")
	links = [x['href'] for x in soup.find_all('a') if x.get('href')]

	for link in links:
		parse_link = urlparse(link)
		check_url = ParseResult(scheme="https",
								netloc=parse_link.netloc,
								path=parse_link.path,
								params=parse_link.params,
								query=parse_link.query,
								fragment='')
		check_url = urlunparse(check_url)

		badlink = g.db.query(BadLink).filter(
			literal(check_url).contains(
				BadLink.link)).first()

		if badlink:
			return {"error": f"Remove the following link and try again: `{check_url}`. Reason: {badlink.reason}"}, 403

	# check spam - this should hopefully be faster
	now = int(time.time())
	cutoff = now - 60 * 60 * 24

	similar_comments = g.db.query(Comment
									).options(
		lazyload('*')
	).join(Comment.comment_aux
			 ).filter(
		Comment.author_id == v.id,
		CommentAux.body.op(
			'<->')(body) < app.config["SPAM_SIMILARITY_THRESHOLD"],
		Comment.created_utc > cutoff
	).options(contains_eager(Comment.comment_aux)).all()

	threshold = app.config["SPAM_SIMILAR_COUNT_THRESHOLD"]
	if v.age >= (60 * 60 * 24 * 30):
		threshold *= 4
	elif v.age >= (60 * 60 * 24 * 7):
		threshold *= 3
	elif v.age >= (60 * 60 * 24):
		threshold *= 2

	if len(similar_comments) > threshold:
		text = "Your account has been suspended for 1 day for the following reason:\n\n> Too much spam!"
		send_notification(NOTIFICATIONS_ACCOUNT, v, text)

		v.ban(reason="Spamming.",
				days=1)

		for comment in similar_comments:
			comment.is_banned = True
			comment.ban_reason = "Automatic spam removal. This happened because the post's creator submitted too much similar content too quickly."
			g.db.add(comment)

		return {"error": "Too much spam!"}, 403

	if request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
		file=request.files["file"]
		if not file.content_type.startswith('image/'): return {"error": "That wasn't an image!"}, 400
		
		name = f'comment/{c.id}/{secrets.token_urlsafe(8)}'
		url = upload_file(file)

		body += f"\n![]({url})"
		body = body.replace("\n", "\n\n").replace("\n\n\n\n\n\n", "\n\n").replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
		with CustomRenderer(post_id=c.parent_submission) as renderer:
			body_md = renderer.render(mistletoe.Document(body))
		body_html = sanitize(body_md)

	c.body = body
	c.body_html = body_html

	if v.agendaposter and "trans lives matter" not in c.body_html.lower():

		c.is_banned = True
		c.ban_reason = "ToS Violation"

		g.db.add(c)

		c_jannied = Comment(author_id=AUTOJANNY_ACCOUNT,
			parent_submission=c.parent_submission,
			distinguish_level=6,
			parent_comment_id=c.id,
			level=c.level+1,
			is_bot=True,
			)

		g.db.add(c_jannied)
		g.db.flush()

		body = AGENDAPOSTER_MSG.format(username=v.username)

		with CustomRenderer(post_id=c.parent_submission) as renderer:
			body_md = renderer.render(mistletoe.Document(body))

		body_jannied_html = sanitize(body_md)
		c_aux = CommentAux(
			id=c_jannied.id,
			body_html=body_jannied_html,
			body=body
		)
		g.db.add(c_aux)
		g.db.flush()
		n = Notification(comment_id=c_jannied.id, user_id=v.id)
		g.db.add(n)

	if int(time.time()) - c.created_utc > 60 * 3: c.edited_utc = int(time.time())

	g.db.add(c)

	g.db.flush()
	
	# queue up notifications for username mentions
	notify_users = set()
	soup = BeautifulSoup(body_html, features="html.parser")
	mentions = soup.find_all("a", href=re.compile("^/@(\w+)"))
	
	if len(mentions) > 0:
		notifs = g.db.query(Notification)
		for mention in mentions:
			username = mention["href"].split("@")[1]

			user = g.db.query(User).filter_by(username=username).first()

			if user:
				if v.any_block_exists(user):
					continue
				if user.id != v.id:
					notify_users.add(user.id)

		for x in notify_users:
			notif = notifs.filter_by(comment_id=c.id, user_id=x).first()
			if not notif:
				n = Notification(comment_id=c.id, user_id=x)
				g.db.add(n)

	return jsonify({"html": c.body_html})


@app.post("/delete/comment/<cid>")
@auth_required
@validate_formkey
def delete_comment(cid, v):

	c = g.db.query(Comment).filter_by(id=cid).first()

	if not c:
		abort(404)

	if not c.author_id == v.id:
		abort(403)

	c.deleted_utc = int(time.time())

	g.db.add(c)
	
	cache.delete_memoized(comment_idlist)
	cache.delete_memoized(User.commentlisting, v)

	return "", 204

@app.post("/undelete/comment/<cid>")
@auth_required
@validate_formkey
def undelete_comment(cid, v):

	c = g.db.query(Comment).filter_by(id=cid).first()

	if not c:
		abort(404)

	if not c.author_id == v.id:
		abort(403)

	c.deleted_utc = 0

	g.db.add(c)

	cache.delete_memoized(comment_idlist)
	cache.delete_memoized(User.commentlisting, v)

	return "", 204


@app.post("/comment_pin/<cid>")
@auth_required
@validate_formkey
def toggle_comment_pin(cid, v):
	
	comment = get_comment(cid, v=v)
	
	if v.admin_level < 1 and v.id != comment.post.author_id:
		abort(403)

	comment.is_pinned = not comment.is_pinned

	g.db.add(comment)
	g.db.flush()

	if v.admin_level == 6:
		ma=ModAction(
			kind="pin_comment" if comment.is_pinned else "unpin_comment",
			user_id=v.id,
			target_comment_id=comment.id
		)
		g.db.add(ma)

	html=render_template(
				"comments.html",
				v=v,
				comments=[comment],
				render_replies=False,
				)

	html=str(BeautifulSoup(html, features="html.parser").find(id=f"comment-{comment.id}-only"))

	return html
	
	
@app.post("/save_comment/<cid>")
@auth_required
@validate_formkey
def save_comment(cid, v):

	comment=get_comment(cid)

	new_save=SaveRelationship(user_id=v.id, submission_id=comment.id, type=2)

	g.db.add(new_save)

	try: g.db.flush()
	except: g.db.rollback()

	return "", 204

@app.post("/unsave_comment/<cid>")
@auth_required
@validate_formkey
def unsave_comment(cid, v):

	comment=get_comment(cid)

	save=g.db.query(SaveRelationship).filter_by(user_id=v.id, submission_id=comment.id, type=2).first()

	if save: g.db.delete(save)

	return "", 204
