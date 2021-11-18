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
from files.helpers.sanitize import filter_title

site = environ.get("DOMAIN").strip()
if site == 'pcmemes.net': cc = "SPLASH MOUNTAIN"
else: cc = "COUNTRY CLUB"

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
	
	if not v and not request.path.startswith('/logged_out'): return redirect(f"/logged_out{request.full_path}")

	if v and request.path.startswith('/logged_out'): v = None
	
	try: cid = int(cid)
	except:
		try: cid = int(cid, 36)
		except: abort(404)

	comment = get_comment(cid, v=v)
	
	if v and request.values.get("read"):
		notif = g.db.query(Notification).filter_by(comment_id=cid, user_id=v.id, read=False).first()
		if notif:
			notif.read = True
			g.db.add(notif)
			g.db.commit()

	if comment.post and comment.post.club and not (v and v.paid_dues): abort(403)

	if not comment.parent_submission and not (v and (comment.author.id == v.id or comment.sentto == v.id)) and not (v and v.admin_level > 1) : abort(403)
	
	if not pid:
		if comment.parent_submission: pid = comment.parent_submission
		elif "rama" in request.host: pid = 6489
		elif 'pcmemes.net' in request.host: pid = 2487
		else: pid = 1
	
	try: pid = int(pid)
	except: abort(404)
	
	post = get_post(pid, v=v)
		
	if post.over_18 and not (v and v.over_18) and not session.get('over_18', 0) >= int(time.time()):
		if request.headers.get("Authorization"): return {'error': f'This content is not suitable for some users and situations.'}
		else: render_template("errors/nsfw.html", v=v)

	try: context = int(request.values.get("context", 0))
	except: context = 0
	comment_info = comment
	c = comment
	while context > 0 and c.level > 1:
		c = c.parent_comment
		context -= 1
	top_comment = c

	if v: defaultsortingcomments = v.defaultsortingcomments
	else: defaultsortingcomments = "top"
	sort=request.values.get("sort", defaultsortingcomments)

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

		if not (v and v.shadowbanned) and not (v and v.admin_level > 1):
			comments = comments.join(User, User.id == Comment.author_id).filter(User.shadowbanned == None)
		 
		comments=comments.filter(
			Comment.parent_submission == post.id,
			Comment.author_id != AUTOPOLLER_ID
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

		output = []
		for c in comments:
			comment = c[0]
			comment.voted = c[1] or 0
			comment.is_blocking = c[2] or 0
			comment.is_blocked = c[3] or 0
			output.append(comment)

	post.replies=[top_comment]
			
	if request.headers.get("Authorization"): return top_comment.json
	else: 
		if post.is_banned and not (v and (v.admin_level > 1 or post.author_id == v.id)): template = "submission_banned.html"
		else: template = "submission.html"
		return render_template(template, v=v, p=post, sort=sort, linked_comment=comment, comment_info=comment_info, render_replies=True)


@app.post("/comment")
@limiter.limit("1/second")
@limiter.limit("6/minute")
@is_not_banned
@validate_formkey
def api_comment(v):
	if v and v.patron:
		if request.content_length > 8 * 1024 * 1024: return "Max file size is 8 MB.", 413
	elif request.content_length > 4 * 1024 * 1024: return "Max file size is 4 MB.", 413

	parent_submission = request.values.get("submission").strip()
	parent_fullname = request.values.get("parent_fullname").strip()

	parent_post = get_post(parent_submission, v=v)
	if parent_post.club and not (v and v.paid_dues): abort(403)

	if parent_fullname.startswith("t2_"):
		parent = parent_post
		parent_comment_id = None
		level = 1
	elif parent_fullname.startswith("t3_"):
		parent = get_comment(parent_fullname.split("_")[1], v=v)
		parent_comment_id = parent.id
		level = parent.level + 1
	else: abort(400)

	body = request.values.get("body", "").strip()[:10000]

	if v.marseyawarded:
		if time.time() > v.marseyawarded:
			v.marseyawarded = None
			g.db.add(v)
		else:
			marregex = list(re.finditer("^(:!?m\w+:\s*)+$", body))
			if len(marregex) == 0: return {"error":"You can only type marseys!"}, 403

	if v.longpost:
		if time.time() > v.longpost:
			v.longpost = None
			g.db.add(v)
		elif len(body) < 280: return {"error":"You have to type more than 280 characters!"}, 403

	if not body and not request.files.get('file'): return {"error":"You need to actually write something!"}, 400
	
	for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|webp|PNG|JPG|JPEG|GIF|WEBP|9999))', body, re.MULTILINE):
		if "wikipedia" not in i.group(1): body = body.replace(i.group(1), f'![]({i.group(1)})')

	options = []
	for i in re.finditer('\s*\$\$([^\$\n]+)\$\$\s*', body):
		options.append(i.group(1))
		body = body.replace(i.group(0), "")

	if request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
		file=request.files["file"]
		if not file.content_type.startswith('image/'): return {"error": "That wasn't an image!"}, 400

		name = f'/images/{int(time.time())}{secrets.token_urlsafe(2)}.webp'
		file.save(name)
		url = request.host_url[:-1] + process_image(name)
		
		body += f"\n\n![]({url})"

	body_html = sanitize(CustomRenderer().render(mistletoe.Document(body)))

	if v.marseyawarded and len(list(re.finditer('>[^<\s+]|[^>\s+]<', body_html))) > 0: return {"error":"You can only type marseys!"}, 403

	if v.longpost and len(body) < 280: return {"error":"You have to type more than 280 characters!"}, 403

	bans = filter_comment_html(body_html)

	if bans:
		ban = bans[0]
		reason = f"Remove the {ban.domain} link from your comment and try again."
		if ban.reason: reason += f" {ban.reason}"
		return {"error": reason}, 401

	existing = g.db.query(Comment.id).filter(Comment.author_id == v.id,
															 Comment.deleted_utc == 0,
															 Comment.parent_comment_id == parent_comment_id,
															 Comment.parent_submission == parent_submission,
															 Comment.body == body
															 ).first()
	if existing: return {"error": f"You already made that comment: /comment/{existing.id}"}, 409

	if parent.author.any_block_exists(v) and v.admin_level < 2: return {"error": "You can't reply to users who have blocked you, or users you have blocked."}, 403

	is_bot = request.headers.get("Authorization")

	if not is_bot and not v.marseyawarded and 'trans lives matters' not in body.lower():
		now = int(time.time())
		cutoff = now - 60 * 60 * 24

		similar_comments = g.db.query(Comment).filter(
			Comment.author_id == v.id,
			Comment.body.op(
				'<->')(body) < app.config["COMMENT_SPAM_SIMILAR_THRESHOLD"],
			Comment.created_utc > cutoff
		).all()

		threshold = app.config["COMMENT_SPAM_COUNT_THRESHOLD"]
		if v.age >= (60 * 60 * 24 * 7):
			threshold *= 3
		elif v.age >= (60 * 60 * 24):
			threshold *= 2

		if len(similar_comments) > threshold:
			text = "Your account has been suspended for 1 day for the following reason:\n\n> Too much spam!"
			send_notification(v.id, text)

			v.ban(reason="Spamming.",
					days=1)

			for alt in v.alts:
				if not alt.is_suspended:
					alt.ban(reason="Spamming.", days=1)

			for comment in similar_comments:
				comment.is_banned = True
				comment.ban_reason = "AutoJanny"
				g.db.add(comment)
				ma=ModAction(
					user_id=AUTOJANNY_ID,
					target_comment_id=comment.id,
					kind="ban_comment",
					_note="spam"
					)
				g.db.add(ma)

			return {"error": "Too much spam!"}, 403

	if len(body_html) > 20000: abort(400)

	c = Comment(author_id=v.id,
				parent_submission=parent_submission,
				parent_comment_id=parent_comment_id,
				level=level,
				over_18=request.host == 'pcmemes.net' and v.id == 1578 or parent_post.over_18 or request.values.get("over_18","")=="true",
				is_bot=is_bot,
				app_id=v.client.application.id if v.client else None,
				body_html=body_html,
				body=body[:10000]
				)

	c.upvotes = 1
	g.db.add(c)
	g.db.flush()

	for option in options:
		c_option = Comment(author_id=AUTOPOLLER_ID,
			parent_submission=parent_submission,
			parent_comment_id=c.id,
			level=level+1,
			body_html=filter_title(option),
			upvotes=0
			)

		g.db.add(c_option)


	if 'pcmemes.net' in request.host and c.body.lower().startswith("based"):
		pill = re.match("based and (.{1,20}?)(-| )pilled", body, re.IGNORECASE)

		if level == 1: basedguy = get_account(c.post.author_id)
		else: basedguy = get_account(c.parent_comment.author_id)
		basedguy.basedcount += 1
		if pill:
			if basedguy.pills: basedguy.pills += f", {pill.group(1)}"
			else: basedguy.pills += f"{pill.group(1)}"
		g.db.add(basedguy)

		body2 = f"@{basedguy.username}'s Based Count has increased by 1. Their Based Count is now {basedguy.basedcount}."
		if basedguy.pills: body2 += f"\n\nPills: {basedguy.pills}"
		
		body_md = CustomRenderer().render(mistletoe.Document(body2))

		body_based_html = sanitize(body_md)

		c_based = Comment(author_id=BASEDBOT_ID,
			parent_submission=parent_submission,
			distinguish_level=6,
			parent_comment_id=c.id,
			level=level+1,
			is_bot=True,
			body_html=body_based_html,
			)

		g.db.add(c_based)
		g.db.flush()

		n = Notification(comment_id=c_based.id, user_id=v.id)
		g.db.add(n)


	if "rama" in request.host and "ivermectin" in c.body.lower():

		c.is_banned = True
		c.ban_reason = "AutoJanny"

		g.db.add(c)

		body2 = VAXX_MSG.format(username=v.username)

		body_md = CustomRenderer().render(mistletoe.Document(body2))

		body_jannied_html = sanitize(body_md)



		c_jannied = Comment(author_id=AUTOJANNY_ID,
			parent_submission=parent_submission,
			distinguish_level=6,
			parent_comment_id=c.id,
			level=level+1,
			is_bot=True,
			body_html=body_jannied_html,
			)

		g.db.add(c_jannied)
		g.db.flush()



		n = Notification(comment_id=c_jannied.id, user_id=v.id)
		g.db.add(n)

	if v.agendaposter and not v.marseyawarded and "trans lives matter" not in c.body_html.lower():

		c.is_banned = True
		c.ban_reason = "AutoJanny"

		g.db.add(c)


		body = AGENDAPOSTER_MSG.format(username=v.username)

		body_md = CustomRenderer().render(mistletoe.Document(body))

		body_jannied_html = sanitize(body_md)



		c_jannied = Comment(author_id=AUTOJANNY_ID,
			parent_submission=parent_submission,
			distinguish_level=6,
			parent_comment_id=c.id,
			level=level+1,
			is_bot=True,
			body_html=body_jannied_html,
			)

		g.db.add(c_jannied)
		g.db.flush()




		n = Notification(comment_id=c_jannied.id, user_id=v.id)
		g.db.add(n)

	if v.id == PIZZA_SHILL_ID:
		cratvote = CommentVote(user_id=TAX_RECEIVER_ID, comment_id=c.id, vote_type=1)
		g.db.add(cratvote)
		v.coins += 1
		v.truecoins += 1
		g.db.add(v)
		c.upvotes += 1
		g.db.add(c)

	if "rama" in request.host and len(c.body) >= 1000 and "<" not in body and "</blockquote>" not in body_html:
	
		body = random.choice(LONGPOST_REPLIES)
		body_md = CustomRenderer().render(mistletoe.Document(body))
		body_html2 = sanitize(body_md)



		c2 = Comment(author_id=LONGPOSTBOT_ID,
			parent_submission=parent_submission,
			parent_comment_id=c.id,
			level=level+1,
			is_bot=True,
			body_html=body_html2,
			)

		g.db.add(c2)

		longpostbot = g.db.query(User).filter_by(id = LONGPOSTBOT_ID).first()
		longpostbot.comment_count += 1
		longpostbot.coins += 1
		g.db.add(longpostbot)
		
		g.db.flush()



		n = Notification(comment_id=c2.id, user_id=v.id)
		g.db.add(n)







	if "rama" in request.host and random.random() < 0.001:
	
		body = "zoz"
		body_md = CustomRenderer().render(mistletoe.Document(body))
		body_html2 = sanitize(body_md)




		c2 = Comment(author_id=ZOZBOT_ID,
			parent_submission=parent_submission,
			parent_comment_id=c.id,
			level=level+1,
			is_bot=True,
			body_html=body_html2,
			)

		g.db.add(c2)
		g.db.flush()



		n = Notification(comment_id=c2.id, user_id=v.id)
		g.db.add(n)




	
		body = "zle"
		body_md = CustomRenderer().render(mistletoe.Document(body))
		body_html2 = sanitize(body_md)



		c3 = Comment(author_id=ZOZBOT_ID,
			parent_submission=parent_submission,
			parent_comment_id=c2.id,
			level=level+2,
			is_bot=True,
			body_html=body_html2,
			)

		g.db.add(c3)
		g.db.flush()
		
		



		
	
		body = "zozzle"
		body_md = CustomRenderer().render(mistletoe.Document(body))
		body_html2 = sanitize(body_md)


		c4 = Comment(author_id=ZOZBOT_ID,
			parent_submission=parent_submission,
			parent_comment_id=c3.id,
			level=level+3,
			is_bot=True,
			body_html=body_html2,
			)

		g.db.add(c4)

		zozbot = g.db.query(User).filter_by(id = ZOZBOT_ID).first()
		zozbot.comment_count += 3
		zozbot.coins += 3
		g.db.add(zozbot)

		g.db.flush()










	if not v.shadowbanned:
		notify_users = set()
		
		for x in g.db.query(Subscription.user_id).filter_by(submission_id=c.parent_submission).all(): notify_users.add(x[0])
		
		if parent.author.id not in [v.id, BASEDBOT_ID, AUTOJANNY_ID, SNAPPY_ID, LONGPOSTBOT_ID, ZOZBOT_ID, AUTOPOLLER_ID]: notify_users.add(parent.author.id)

		soup = BeautifulSoup(body_html, features="html.parser")
		mentions = soup.find_all("a", href=re.compile("^/@(\w+)"))

		for mention in mentions:
			username = mention["href"].split("@")[1]

			user = g.db.query(User).filter_by(username=username).first()

			if user:
				if v.any_block_exists(user): continue
				if user.id != v.id: notify_users.add(user.id)

		if request.host == 'rdrama.net':
			if 'aevann' in body_html.lower() and 1 not in notify_users: notify_users.add(1)
			if 'joan' in body_html.lower() and 28 not in notify_users: notify_users.add(28)
			if 'carp' in body_html.lower() and 995 not in notify_users:
				notify_users.add(995)
				notify_users.add(541)
			if ('idio3' in body_html.lower() or 'idio ' in body_html.lower()) and 30 not in notify_users: notify_users.add(30)

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
							'deep_link': f'http://{site}/comment/{c.id}?context=9&read=true#context',
					  },
					},
				  },
				)
			except Exception as e:
				print(e)				



	vote = CommentVote(user_id=v.id,
						 comment_id=c.id,
						 vote_type=1
						 )

	g.db.add(vote)
	

	cache.delete_memoized(comment_idlist)

	v.comment_count = g.db.query(Comment.id).filter(Comment.author_id == v.id, Comment.parent_submission != None).filter_by(is_banned=False, deleted_utc=0).count()
	g.db.add(v)

	parent_post.comment_count += 1
	g.db.add(parent_post)

	c.voted = 1
	
	g.db.commit()

	if request.headers.get("Authorization"): return c.json
	else: return render_template("comments.html", v=v, comments=[c])



@app.post("/edit_comment/<cid>")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def edit_comment(cid, v):
	if v and v.patron:
		if request.content_length > 8 * 1024 * 1024: return "Max file size is 8 MB.", 413
	elif request.content_length > 4 * 1024 * 1024: return "Max file size is 4 MB.", 413

	c = get_comment(cid, v=v)

	if not c.author_id == v.id: abort(403)

	if c.is_banned or c.deleted_utc > 0: abort(403)

	body = request.values.get("body", "").strip()[:10000]

	if body != c.body and body != "":
		if v.marseyawarded:
			if time.time() > v.marseyawarded:
				v.marseyawarded = None
				g.db.add(v)
			else:
				marregex = list(re.finditer("^(:!?m\w+:\s*)+$", body))
				if len(marregex) == 0: return {"error":"You can only type marseys!"}, 403

		if v.longpost:
			if time.time() > v.longpost:
				v.longpost = None
				g.db.add(v)
			elif len(body) < 280: return {"error":"You have to type more than 280 characters!"}, 403

		for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|webp|PNG|JPG|JPEG|GIF|WEBP|9999))', body, re.MULTILINE):
			if "wikipedia" not in i.group(1): body = body.replace(i.group(1), f'![]({i.group(1)})')
		body_md = CustomRenderer().render(mistletoe.Document(body))
		body_html = sanitize(body_md)

		if v.marseyawarded and len(list(re.finditer('>[^<\s+]|[^>\s+]<', body_html))) > 0: return {"error":"You can only type marseys!"}, 403

		if v.longpost and len(body) < 280: return {"error":"You have to type more than 280 characters!"}, 403

		bans = filter_comment_html(body_html)

		if bans:
			
			ban = bans[0]
			reason = f"Remove the {ban.domain} link from your comment and try again."
			
			if ban.reason: reason += f" {ban.reason}"	
		
			if request.headers.get("Authorization"): return {'error': f'A blacklisted domain was used.'}, 400
			else: return render_template("comment_failed.html",
													action=f"/edit_comment/{c.id}",
													badlinks=[x.domain for x in bans],
													body=body,
													v=v
													)
		if 'trans lives matters' not in body.lower():
			now = int(time.time())
			cutoff = now - 60 * 60 * 24

			similar_comments = g.db.query(Comment
			).filter(
				Comment.author_id == v.id,
				Comment.body.op(
					'<->')(body) < app.config["SPAM_SIMILARITY_THRESHOLD"],
				Comment.created_utc > cutoff
			).all()

			threshold = app.config["SPAM_SIMILAR_COUNT_THRESHOLD"]
			if v.age >= (60 * 60 * 24 * 30):
				threshold *= 4
			elif v.age >= (60 * 60 * 24 * 7):
				threshold *= 3
			elif v.age >= (60 * 60 * 24):
				threshold *= 2

			if len(similar_comments) > threshold:
				text = "Your account has been suspended for 1 day for the following reason:\n\n> Too much spam!"
				send_notification(v.id, text)

				v.ban(reason="Spamming.",
						days=1)

				for comment in similar_comments:
					comment.is_banned = True
					comment.ban_reason = "AutoJanny"
					g.db.add(comment)

				return {"error": "Too much spam!"}, 403

		if request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
			file=request.files["file"]
			if not file.content_type.startswith('image/'): return {"error": "That wasn't an image!"}, 400

			name = f'/images/{int(time.time())}{secrets.token_urlsafe(2)}.webp'
			file.save(name)
			url = request.host_url[:-1] + process_image(name)

			body += f"\n\n![]({url})"
			body_md = CustomRenderer().render(mistletoe.Document(body))
			body_html = sanitize(body_md)

		if len(body_html) > 20000: abort(400)

		c.body = body[:10000]
		c.body_html = body_html

		if "rama" in request.host and "ivermectin" in c.body_html.lower():

			c.is_banned = True
			c.ban_reason = "AutoJanny"

			g.db.add(c)

			body = VAXX_MSG.format(username=v.username)

			body_md = CustomRenderer().render(mistletoe.Document(body))

			body_jannied_html = sanitize(body_md)



			c_jannied = Comment(author_id=AUTOJANNY_ID,
				parent_submission=c.parent_submission,
				distinguish_level=6,
				parent_comment_id=c.id,
				level=c.level+1,
				is_bot=True,
				body_html=body_jannied_html,
				)

			g.db.add(c_jannied)
			g.db.flush()



			n = Notification(comment_id=c_jannied.id, user_id=v.id)
			g.db.add(n)


		if v.agendaposter and not v.marseyawarded and "trans lives matter" not in c.body_html.lower():

			c.is_banned = True
			c.ban_reason = "AutoJanny"

			g.db.add(c)


			body = AGENDAPOSTER_MSG.format(username=v.username)

			body_md = CustomRenderer().render(mistletoe.Document(body))

			body_jannied_html = sanitize(body_md)



			c_jannied = Comment(author_id=AUTOJANNY_ID,
				parent_submission=c.parent_submission,
				distinguish_level=6,
				parent_comment_id=c.id,
				level=c.level+1,
				is_bot=True,
				body_html=body_jannied_html,
				)

			g.db.add(c_jannied)
			g.db.flush()



			n = Notification(comment_id=c_jannied.id, user_id=v.id)
			g.db.add(n)

		if int(time.time()) - c.created_utc > 60 * 3: c.edited_utc = int(time.time())

		g.db.add(c)

		g.db.flush()
		
		notify_users = set()
		soup = BeautifulSoup(body_html, features="html.parser")
		mentions = soup.find_all("a", href=re.compile("^/@(\w+)"))
		
		if len(mentions) > 0:
			for mention in mentions:
				username = mention["href"].split("@")[1]

				user = g.db.query(User).filter_by(username=username).first()

				if user:
					if v.any_block_exists(user): continue
					if user.id != v.id: notify_users.add(user.id)

		if request.host == 'rdrama.net':
			if 'aevann' in body_html.lower() and 1 not in notify_users: notify_users.add(1)
			if 'joan' in body_html.lower() and 28 not in notify_users: notify_users.add(28)
			if 'carp' in body_html.lower() and 995 not in notify_users:
				notify_users.add(995)
				notify_users.add(541)
			if ('idio3' in body_html.lower() or 'idio ' in body_html.lower()) and 30 not in notify_users: notify_users.add(30)

		for x in notify_users:
			notif = g.db.query(Notification).filter_by(comment_id=c.id, user_id=x).first()
			if not notif:
				n = Notification(comment_id=c.id, user_id=x)
				g.db.add(n)

		g.db.commit()

	return c.body_html


@app.post("/delete/comment/<cid>")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def delete_comment(cid, v):

	c = g.db.query(Comment).filter_by(id=cid).first()

	if not c: abort(404)

	if not c.author_id == v.id: abort(403)

	c.deleted_utc = int(time.time())

	g.db.add(c)
	
	cache.delete_memoized(comment_idlist)

	g.db.commit()

	return {"message": "Comment deleted!"}

@app.post("/undelete/comment/<cid>")
@limiter.limit("1/second")
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

	g.db.commit()

	return {"message": "Comment undeleted!"}


@app.post("/pin_comment/<cid>")
@auth_required
@validate_formkey
def toggle_pin_comment(cid, v):
	
	comment = get_comment(cid, v=v)
	
	if v.admin_level < 1 and v.id != comment.post.author_id: abort(403)

	if comment.is_pinned:
		if comment.is_pinned.startswith("t:"): abort(403)
		else:
			if v.admin_level > 1 or comment.is_pinned.endswith(" (OP)"): comment.is_pinned = None
			else: abort(403)
	else:
		if v.admin_level > 1: comment.is_pinned = v.username
		else: comment.is_pinned = v.username + " (OP)"

	g.db.add(comment)
	g.db.flush()

	if v.admin_level > 1:
		ma=ModAction(
			kind="pin_comment" if comment.is_pinned else "unpin_comment",
			user_id=v.id,
			target_comment_id=comment.id
		)
		g.db.add(ma)

	g.db.commit()

	if comment.is_pinned:
		if v.id != comment.author_id:
			message = f"@{v.username} has pinned your [comment]({comment.permalink})!"
			existing = g.db.query(Comment.id).filter(Comment.author_id == NOTIFICATIONS_ID, Comment.body == message).first()
			if not existing: send_notification(comment.author_id, message)
		g.db.commit()
		return {"message": "Comment pinned!"}
	else:
		if v.id != comment.author_id:
			message = f"@{v.username} has unpinned your [comment]({comment.permalink})!"
			existing = g.db.query(Comment.id).filter(Comment.author_id == NOTIFICATIONS_ID, Comment.body == message).first()
			if not existing: send_notification(comment.author_id, message)
		g.db.commit()
		return {"message": "Comment unpinned!"}
	
	
@app.post("/save_comment/<cid>")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def save_comment(cid, v):

	comment=get_comment(cid)

	save=g.db.query(SaveRelationship).filter_by(user_id=v.id, comment_id=comment.id, type=2).first()

	if not save:
		new_save=SaveRelationship(user_id=v.id, comment_id=comment.id, type=2)
		g.db.add(new_save)

		try: g.db.commit()
		except: g.db.rollback()

	return {"message": "Comment saved!"}

@app.post("/unsave_comment/<cid>")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def unsave_comment(cid, v):

	comment=get_comment(cid)

	save=g.db.query(SaveRelationship).filter_by(user_id=v.id, comment_id=comment.id, type=2).first()

	if save:
		g.db.delete(save)
		g.db.commit()

	return {"message": "Comment unsaved!"}
