from files.helpers.wrappers import *
from files.helpers.filters import *
from files.helpers.alerts import *
from files.helpers.images import *
from files.helpers.const import *
from files.classes import *
from files.routes.front import comment_idlist
from pusher_push_notifications import PushNotifications
from flask import *
from files.__main__ import app, limiter
from files.helpers.sanitize import filter_emojis_only
import requests
from json import loads

IMGUR_KEY = environ.get("IMGUR_KEY").strip()

if PUSHER_ID: beams_client = PushNotifications(instance_id=PUSHER_ID, secret_key=PUSHER_KEY)

CF_KEY = environ.get("CF_KEY", "").strip()
CF_ZONE = environ.get("CF_ZONE", "").strip()
CF_HEADERS = {"Authorization": f"Bearer {CF_KEY}", "Content-Type": "application/json"}

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
		notif = g.db.query(Notification).filter_by(comment_id=cid, user_id=v.id, read=False).one_or_none()
		if notif:
			notif.read = True
			g.db.add(notif)
			g.db.commit()

	if comment.post and comment.post.club and not (v and (v.paid_dues or v.id in [comment.author_id, comment.post.author_id])): abort(403)

	if not comment.parent_submission and not (v and (comment.author.id == v.id or comment.sentto == v.id)) and not (v and v.admin_level > 1) : abort(403)
	
	if not pid:
		if comment.parent_submission: pid = comment.parent_submission
		elif request.host == "rdrama.net": pid = 6489
		elif request.host == 'pcmemes.net': pid = 2487
		else: pid = 1
	
	try: pid = int(pid)
	except: abort(404)
	
	post = get_post(pid, v=v)
		
	if post.over_18 and not (v and v.over_18) and not session.get('over_18', 0) >= int(time.time()):
		if request.headers.get("Authorization"): return {'error': 'This content is not suitable for some users and situations.'}
		else: render_template("errors/nsfw.html", v=v)

	try: context = int(request.values.get("context", 0))
	except: context = 0
	comment_info = comment
	c = comment
	while context and c.level > 1:
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
			Comment.author_id.notin_((AUTOPOLLER_ID, AUTOBETTER_ID))
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
		return render_template(template, v=v, p=post, sort=sort, comment_info=comment_info, render_replies=True)

@app.post("/comment")
@limiter.limit("1/second;6/minute;200/hour;1000/day")
@auth_required
def api_comment(v):
	if v.is_suspended: return {"error": "You can't perform this action while banned."}, 403

	if v and v.patron:
		if request.content_length > 8 * 1024 * 1024: return {"error":"Max file size is 8 MB."}, 413
	elif request.content_length > 4 * 1024 * 1024: return {"error":"Max file size is 4 MB."}, 413

	parent_submission = request.values.get("submission").strip()
	parent_fullname = request.values.get("parent_fullname").strip()

	parent_post = get_post(parent_submission, v=v)
	if parent_post.club and not (v and (v.paid_dues or v.id == parent_post.author_id)): abort(403)

	if parent_fullname.startswith("t2_"):
		parent = parent_post
		parent_comment_id = None
		top_comment_id = None
		level = 1
	elif parent_fullname.startswith("t3_"):
		parent = get_comment(parent_fullname.split("_")[1], v=v)
		parent_comment_id = parent.id
		level = parent.level + 1
		if level == 2: top_comment_id = parent.id
		else: top_comment_id = parent.top_comment_id
	else: abort(400)

	body = request.values.get("body", "").strip()[:10000]
	
	if v.admin_level == 3 and parent_post.id == 37749:
		with open(f"snappy_{SITE_NAME}.txt", "a") as f:
			f.write('\n{[para]}\n' + body)

	if v.marseyawarded:
		marregex = list(re.finditer("^(:[!#]{0,2}m\w+:\s*)+$", body))
		if len(marregex) == 0: return {"error":"You can only type marseys!"}, 403

	if v.longpost and len(body) < 280 or ' [](' in body or body.startswith('[]('): return {"error":"You have to type more than 280 characters!"}, 403
	elif v.bird and len(body) > 140: return {"error":"You have to type less than 140 characters!"}, 403

	if not body and not request.files.get('file'): return {"error":"You need to actually write something!"}, 400
	
	for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|webp|PNG|JPG|JPEG|GIF|WEBP|9999))', body, re.MULTILINE):
		if "wikipedia" not in i.group(1): body = body.replace(i.group(1), f'![]({i.group(1)})')

	options = []
	for i in re.finditer('\s*\$\$([^\$\n]+)\$\$\s*', body):
		options.append(i.group(1))
		body = body.replace(i.group(0), "")

	if request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
		file=request.files["file"]
		if file.content_type.startswith('image/'):
			image = process_image(file)
			if image == "": return {"error":"Image upload failed"}
			if v.admin_level == 3:
				if parent_post.id == 37696:
					filename = 'files/assets/images/Drama/sidebar/' + str(len(listdir('files/assets/images/Drama/sidebar'))+1) + '.webp'
					text = process_image(file, filename, 400)
				elif parent_post.id == 37697:
					filename = 'files/assets/images/Drama/banners/' + str(len(listdir('files/assets/images/Drama/banners'))+1) + '.webp'
					process_image(file, filename)
				elif parent_post.id == 37833:
					try: badge_def = loads(body.lower())
					except: return {"error": "You didn't follow the format retard"}, 500
					name = badge_def["name"]
					badge = g.db.query(BadgeDef).filter_by(name=name).first()
					if not badge:
						badge = BadgeDef(name=name, description=badge_def["description"])
						g.db.add(badge)
						g.db.flush()
					filename = f'files/assets/images/badges/{badge.id}.webp'
					process_image(file, filename, 200)
					requests.post(f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/purge_cache', headers=CF_HEADERS, data={'files': [f"https://{request.host}/static/assets/images/badges/{badge.id}.webp"]})
				elif v.id in (CARP_ID,AEVANN_ID) and parent_post.id == 37838:
					marsey = loads(body.lower())
					name = marsey["name"]
					if not g.db.query(Marsey.name).filter_by(name=name).first():
						marsey = Marsey(name=marsey["name"], author_id=marsey["author_id"], tags=marsey["tags"], count=0)
						g.db.add(marsey)
					filename = f'files/assets/images/emojis/{name}.webp'
					process_image(file, filename, 200)
					requests.post(f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/purge_cache', headers=CF_HEADERS, data={'files': [f"https://{request.host}/static/assets/images/emojis/{name}.webp"]})
			body += f"\n\n![]({image})"
		elif file.content_type.startswith('video/'):
			file.save("video.mp4")
			with open("video.mp4", 'rb') as f:
				try: url = requests.request("POST", "https://api.imgur.com/3/upload", headers={'Authorization': f'Client-ID {IMGUR_KEY}'}, files=[('video', f)]).json()['data']['link']
				except: return {"error": "Imgur error"}, 400
			if url.endswith('.'): url += 'mp4'
			body += f"\n\n{url}"
		else: return {"error": "Image/Video files only"}, 400

	if v.agendaposter and not v.marseyawarded: body = torture_ap(body, v.username)

	body_html = sanitize(body, comment=True)

	if v.marseyawarded and len(list(re.finditer('>[^<\s+]|[^>\s+]<', body_html))): return {"error":"You can only type marseys!"}, 403

	if v.longpost:
		if len(body) < 280 or ' [](' in body or body.startswith('[]('): return {"error":"You have to type more than 280 characters!"}, 403
	elif v.bird:
		if len(body) > 140 : return {"error":"You have to type less than 140 characters!"}, 403

	bans = filter_comment_html(body_html)

	if bans:
		ban = bans[0]
		reason = f"Remove the {ban.domain} link from your comment and try again."
		if ban.reason: reason += f" {ban.reason}"
		return {"error": reason}, 401

	if parent_post.id not in (37696,37697,37749,37833,37838):
		existing = g.db.query(Comment.id).filter(Comment.author_id == v.id,
																	Comment.deleted_utc == 0,
																	Comment.parent_comment_id == parent_comment_id,
																	Comment.parent_submission == parent_submission,
																	Comment.body_html == body_html
																	).one_or_none()
		if existing: return {"error": f"You already made that comment: /comment/{existing.id}"}, 409

	if parent.author.any_block_exists(v) and v.admin_level < 2: return {"error": "You can't reply to users who have blocked you, or users you have blocked."}, 403

	is_bot = bool(request.headers.get("Authorization"))

	if not is_bot and not v.marseyawarded and AGENDAPOSTER_PHRASE not in body.lower() and len(body) > 10:
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
			send_repeatable_notification(v.id, text)

			v.ban(reason="Spamming.",
					days=1)

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
				top_comment_id=top_comment_id,
				level=level,
				over_18=parent_post.over_18 or request.values.get("over_18")=="true",
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
			body_html=filter_emojis_only(option),
			upvotes=0,
			is_bot=True
			)

		g.db.add(c_option)


	if request.host == 'pcmemes.net' and c.body.lower().startswith("based"):
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
		
		body_based_html = sanitize(body2)

		c_based = Comment(author_id=BASEDBOT_ID,
			parent_submission=parent_submission,
			distinguish_level=6,
			parent_comment_id=c.id,
			level=level+1,
			is_bot=True,
			body_html=body_based_html,
			top_comment_id=c.top_comment_id
			)

		g.db.add(c_based)
		g.db.flush()

		n = Notification(comment_id=c_based.id, user_id=v.id)
		g.db.add(n)

	if v.agendaposter and not v.marseyawarded and AGENDAPOSTER_PHRASE not in c.body.lower():

		c.is_banned = True
		c.ban_reason = "AutoJanny"

		g.db.add(c)


		body = AGENDAPOSTER_MSG.format(username=v.username, type='comment', AGENDAPOSTER_PHRASE=AGENDAPOSTER_PHRASE)

		body_jannied_html = sanitize(body)



		c_jannied = Comment(author_id=NOTIFICATIONS_ID,
			parent_submission=parent_submission,
			distinguish_level=6,
			parent_comment_id=c.id,
			level=level+1,
			is_bot=True,
			body_html=body_jannied_html,
			top_comment_id=c.top_comment_id
			)

		g.db.add(c_jannied)
		g.db.flush()

		n = Notification(comment_id=c_jannied.id, user_id=v.id)
		g.db.add(n)

	if request.host == "rdrama.net" and len(c.body) >= 1000 and "<" not in body and "</blockquote>" not in body_html:
	
		body = random.choice(LONGPOST_REPLIES)

		body_html2 = sanitize(body)

		c2 = Comment(author_id=LONGPOSTBOT_ID,
			parent_submission=parent_submission,
			parent_comment_id=c.id,
			level=level+1,
			is_bot=True,
			body_html=body_html2,
			top_comment_id=c.top_comment_id
			)

		g.db.add(c2)

		longpostbot = g.db.query(User).filter_by(id = LONGPOSTBOT_ID).one_or_none()
		longpostbot.comment_count += 1
		longpostbot.coins += 1
		g.db.add(longpostbot)
		
		g.db.flush()

		n = Notification(comment_id=c2.id, user_id=v.id)
		g.db.add(n)







	if request.host == "rdrama.net" and random.random() < 0.001:
	
		body = "zoz"
		body_html2 = sanitize(body)




		c2 = Comment(author_id=ZOZBOT_ID,
			parent_submission=parent_submission,
			parent_comment_id=c.id,
			level=level+1,
			is_bot=True,
			body_html=body_html2,
			top_comment_id=c.top_comment_id
			)

		g.db.add(c2)
		g.db.flush()
		n = Notification(comment_id=c2.id, user_id=v.id)
		g.db.add(n)




	
		body = "zle"
		body_html2 = sanitize(body)



		c3 = Comment(author_id=ZOZBOT_ID,
			parent_submission=parent_submission,
			parent_comment_id=c2.id,
			level=level+2,
			is_bot=True,
			body_html=body_html2,
			top_comment_id=c.top_comment_id
			)

		g.db.add(c3)
		g.db.flush()
		
		body = "zozzle"
		body_html2 = sanitize(body)


		c4 = Comment(author_id=ZOZBOT_ID,
			parent_submission=parent_submission,
			parent_comment_id=c3.id,
			level=level+3,
			is_bot=True,
			body_html=body_html2,
			top_comment_id=c.top_comment_id
			)

		g.db.add(c4)

		zozbot = g.db.query(User).filter_by(id = ZOZBOT_ID).one_or_none()
		zozbot.comment_count += 3
		zozbot.coins += 3
		g.db.add(zozbot)





	if not v.shadowbanned and parent_post.id not in (37696,37697,37749,37833,37838):
		notify_users = NOTIFY_USERS(body_html, v)
		
		for x in g.db.query(Subscription.user_id).filter_by(submission_id=c.parent_submission).all(): notify_users.add(x[0])
		
		if parent.author.id not in [v.id, BASEDBOT_ID, AUTOJANNY_ID, SNAPPY_ID, LONGPOSTBOT_ID, ZOZBOT_ID, AUTOPOLLER_ID]: notify_users.add(parent.author.id)

		for x in notify_users:
			n = Notification(comment_id=c.id, user_id=x)
			g.db.add(n)

		if parent.author.id != v.id and PUSHER_ID:
			if len(c.body) > 500: notifbody = c.body[:500] + '...'
			else: notifbody = c.body

			beams_client.publish_to_interests(
				interests=[f'{request.host}{parent.author.id}'],
				publish_body={
					'web': {
						'notification': {
							'title': f'New reply by @{c.author_name}',
							'body': notifbody,
							'deep_link': f'{request.host_url}comment/{c.id}?context=9&read=true#context',
							'icon': f'{request.host_url}assets/images/{SITE_NAME}/icon.webp',
						}
					},
					'fcm': {
						'notification': {
							'title': f'New reply by @{c.author_name}',
							'body': notifbody,
						},
						'data': {
							'url': f'/comment/{c.id}?context=9&read=true#context',
						}
					}
				},
			)

	vote = CommentVote(user_id=v.id,
						 comment_id=c.id,
						 vote_type=1,
						 )

	g.db.add(vote)
	

	cache.delete_memoized(comment_idlist)

	v.comment_count = g.db.query(Comment.id).filter(Comment.author_id == v.id, Comment.parent_submission != None).filter_by(is_banned=False, deleted_utc=0).count()
	g.db.add(v)

	parent_post.comment_count += 1
	g.db.add(parent_post)

	c.voted = 1
	
	if v.id == PIZZASHILL_ID:
		autovote = CommentVote(user_id=CARP_ID, comment_id=c.id, vote_type=1)
		g.db.add(autovote)
		autovote = CommentVote(user_id=AEVANN_ID, comment_id=c.id, vote_type=1)
		g.db.add(autovote)
		autovote = CommentVote(user_id=CRAT_ID, comment_id=c.id, vote_type=1)
		g.db.add(autovote)
		v.coins += 3
		v.truecoins += 3
		g.db.add(v)
		c.upvotes += 3
		g.db.add(c)
	elif v.id == HIL_ID:
		autovote = CommentVote(user_id=CARP_ID, comment_id=c.id, vote_type=1)
		g.db.add(autovote)
		v.coins += 1
		v.truecoins += 1
		g.db.add(v)
		c.upvotes += 1
		g.db.add(c)

	slots = Slots(g)
	slots.check_for_slots_command(body, v, c)

	g.db.commit()

	if request.headers.get("Authorization"): return c.json
	return render_template("comments.html", v=v, comments=[c])



@app.post("/edit_comment/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def edit_comment(cid, v):
	if v and v.patron:
		if request.content_length > 8 * 1024 * 1024: return {"error":"Max file size is 8 MB."}, 413
	elif request.content_length > 4 * 1024 * 1024: return {"error":"Max file size is 4 MB."}, 413

	c = get_comment(cid, v=v)

	if c.author_id != v.id: abort(403)

	body = request.values.get("body", "").strip()[:10000]

	if len(body) < 1: return {"error":"You have to actually type something!"}, 400

	if body != c.body or request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
		if v.marseyawarded:
			marregex = list(re.finditer("^(:[!#]{0,2}m\w+:\s*)+$", body))
			if len(marregex) == 0: return {"error":"You can only type marseys!"}, 403

		if v.longpost and len(body) < 280 or ' [](' in body or body.startswith('[]('): return {"error":"You have to type more than 280 characters!"}, 403
		elif v.bird and len(body) > 140: return {"error":"You have to type less than 140 characters!"}, 403

		for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|webp|PNG|JPG|JPEG|GIF|WEBP|9999))', body, re.MULTILINE):
			if "wikipedia" not in i.group(1): body = body.replace(i.group(1), f'![]({i.group(1)})')

		if v.agendaposter and not v.marseyawarded: body = torture_ap(body, v.username)

		if not c.options:
			for i in re.finditer('\s*\$\$([^\$\n]+)\$\$\s*', body):
				body = body.replace(i.group(0), "")
				c_option = Comment(author_id=AUTOPOLLER_ID,
					parent_submission=c.parent_submission,
					parent_comment_id=c.id,
					level=c.level+1,
					body_html=filter_emojis_only(i.group(1)),
					upvotes=0,
					is_bot=True
					)
				g.db.add(c_option)

		body_html = sanitize(body, edit=True)

		if v.marseyawarded and len(list(re.finditer('>[^<\s+]|[^>\s+]<', body_html))): return {"error":"You can only type marseys!"}, 403

		if v.longpost:
			if len(body) < 280 or ' [](' in body or body.startswith('[]('): return {"error":"You have to type more than 280 characters!"}, 403
		elif v.bird:
			if len(body) > 140 : return {"error":"You have to type less than 140 characters!"}, 403

		bans = filter_comment_html(body_html)

		if bans:
			
			ban = bans[0]
			reason = f"Remove the {ban.domain} link from your comment and try again."
			
			if ban.reason: reason += f" {ban.reason}"	
		
			if request.headers.get("Authorization"): return {'error': 'A blacklisted domain was used.'}, 400
			return render_template("comment_failed.html",
													action=f"/edit_comment/{c.id}",
													badlinks=[x.domain for x in bans],
													body=body,
													v=v
													)
		if AGENDAPOSTER_PHRASE not in body.lower():
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
				send_repeatable_notification(v.id, text)

				v.ban(reason="Spamming.",
						days=1)

				for comment in similar_comments:
					comment.is_banned = True
					comment.ban_reason = "AutoJanny"
					g.db.add(comment)

				return {"error": "Too much spam!"}, 403

		if request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
			file=request.files["file"]
			if file.content_type.startswith('image/'):
				body += f"\n\n![]({process_image(file)})"
			elif file.content_type.startswith('video/'):
				file.save("video.mp4")
				with open("video.mp4", 'rb') as f:
					try: url = requests.request("POST", "https://api.imgur.com/3/upload", headers={'Authorization': f'Client-ID {IMGUR_KEY}'}, files=[('video', f)]).json()['data']['link']
					except: return {"error": "Imgur error"}, 400
				if url.endswith('.'): url += 'mp4'
				body += f"\n\n{url}"
			else: return {"error": "Image/Video files only"}, 400

			body_html = sanitize(body, edit=True)

		if len(body_html) > 20000: abort(400)

		c.body = body[:10000]
		c.body_html = body_html

		if v.agendaposter and not v.marseyawarded and AGENDAPOSTER_PHRASE not in c.body.lower():

			c.is_banned = True
			c.ban_reason = "AutoJanny"

			g.db.add(c)


			body = AGENDAPOSTER_MSG.format(username=v.username, type='comment', AGENDAPOSTER_PHRASE=AGENDAPOSTER_PHRASE)

			body_jannied_html = sanitize(body)



			c_jannied = Comment(author_id=NOTIFICATIONS_ID,
				parent_submission=c.parent_submission,
				distinguish_level=6,
				parent_comment_id=c.id,
				level=c.level+1,
				is_bot=True,
				body_html=body_jannied_html,
				top_comment_id=c.top_comment_id
				)

			g.db.add(c_jannied)
			g.db.flush()



			n = Notification(comment_id=c_jannied.id, user_id=v.id)
			g.db.add(n)

		if int(time.time()) - c.created_utc > 60 * 3: c.edited_utc = int(time.time())

		g.db.add(c)
		
		notify_users = NOTIFY_USERS(body_html, v)
		
		for x in notify_users:
			notif = g.db.query(Notification).filter_by(comment_id=c.id, user_id=x).one_or_none()
			if not notif:
				n = Notification(comment_id=c.id, user_id=x)
				g.db.add(n)

		g.db.commit()

	return c.realbody(v)


@app.post("/delete/comment/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def delete_comment(cid, v):

	c = g.db.query(Comment).filter_by(id=cid).one_or_none()

	if not c: abort(404)

	if c.author_id != v.id: abort(403)

	c.deleted_utc = int(time.time())

	g.db.add(c)
	
	cache.delete_memoized(comment_idlist)

	g.db.commit()

	return {"message": "Comment deleted!"}

@app.post("/undelete/comment/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def undelete_comment(cid, v):

	c = g.db.query(Comment).filter_by(id=cid).one_or_none()

	if not c:
		abort(404)

	if c.author_id != v.id:
		abort(403)

	c.deleted_utc = 0

	g.db.add(c)

	cache.delete_memoized(comment_idlist)

	g.db.commit()

	return {"message": "Comment undeleted!"}


@app.post("/pin_comment/<cid>")
@auth_required
def pin_comment(cid, v):
	
	comment = get_comment(cid, v=v)
	
	if v.id != comment.post.author_id: abort(403)
	
	comment.is_pinned = v.username + " (OP)"

	g.db.add(comment)

	if v.id != comment.author_id:
		message = f"@{v.username} (OP) has pinned your [comment]({comment.permalink})!"
		send_repeatable_notification(comment.author_id, message)

	g.db.commit()
	return {"message": "Comment pinned!"}
	

@app.post("/unpin_comment/<cid>")
@auth_required
def unpin_comment(cid, v):
	
	comment = get_comment(cid, v=v)
	
	if v.id != comment.post.author_id: abort(403)

	if not comment.is_pinned.endswith(" (OP)"): 
		return {"error": "You can only unpin comments you have pinned!"}

	comment.is_pinned = None
	g.db.add(comment)

	if v.id != comment.author_id:
		message = f"@{v.username} (OP) has unpinned your [comment]({comment.permalink})!"
		send_repeatable_notification(comment.author_id, message)
	g.db.commit()
	return {"message": "Comment unpinned!"}

@app.post("/save_comment/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def save_comment(cid, v):

	comment=get_comment(cid)

	save=g.db.query(SaveRelationship).filter_by(user_id=v.id, comment_id=comment.id, type=2).one_or_none()

	if not save:
		new_save=SaveRelationship(user_id=v.id, comment_id=comment.id, type=2)
		g.db.add(new_save)

		try: g.db.commit()
		except: g.db.rollback()

	return {"message": "Comment saved!"}

@app.post("/unsave_comment/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def unsave_comment(cid, v):

	comment=get_comment(cid)

	save=g.db.query(SaveRelationship).filter_by(user_id=v.id, comment_id=comment.id, type=2).one_or_none()

	if save:
		g.db.delete(save)
		g.db.commit()

	return {"message": "Comment unsaved!"}