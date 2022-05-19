from files.helpers.wrappers import *
from files.helpers.alerts import *
from files.helpers.images import *
from files.helpers.const import *
from files.helpers.slots import *
from files.helpers.blackjack import *
from files.helpers.treasure import *
from files.classes import *
from files.routes.front import comment_idlist
from files.routes.static import marsey_list
from pusher_push_notifications import PushNotifications
from flask import *
from files.__main__ import app, limiter
from files.helpers.sanitize import filter_emojis_only
import requests
from shutil import copyfile
from json import loads
from collections import Counter
from enchant import Dict
import gevent
from sys import stdout
import os

d = Dict("en_US")

if PUSHER_ID != 'blahblahblah':
	beams_client = PushNotifications(instance_id=PUSHER_ID, secret_key=PUSHER_KEY)

WORDLE_COLOR_MAPPINGS = {-1: "🟥", 0: "🟨", 1: "🟩"}

def pusher_thread(interests, c, username):
	if len(c.body) > 500: notifbody = c.body[:500] + '...'
	else: notifbody = c.body

	beams_client.publish_to_interests(
		interests=[interests],
		publish_body={
			'web': {
				'notification': {
					'title': f'New reply by @{username}',
					'body': notifbody,
					'deep_link': f'{SITE_FULL}/comment/{c.id}?context=8&read=true#context',
					'icon': f'{SITE_FULL}/assets/images/{SITE_NAME}/icon.webp?v=1015',
				}
			},
			'fcm': {
				'notification': {
					'title': f'New reply by @{username}',
					'body': notifbody,
				},
				'data': {
					'url': f'/comment/{c.id}?context=8&read=true#context',
				}
			}
		},
	)
	stdout.flush()

@app.get("/comment/<cid>")
@app.get("/post/<pid>/<anything>/<cid>")
@app.get("/h/<sub>/comment/<cid>")
@app.get("/h/<sub>/post/<pid>/<anything>/<cid>")
@app.get("/logged_out/comment/<cid>")
@app.get("/logged_out/post/<pid>/<anything>/<cid>")
@app.get("/logged_out/h/<sub>/comment/<cid>")
@app.get("/logged_out/h/<sub>/post/<pid>/<anything>/<cid>")
@auth_desired
def post_pid_comment_cid(cid, pid=None, anything=None, v=None, sub=None):

	if not v and not request.path.startswith('/logged_out'): return redirect(f"/logged_out{request.full_path}")
	if v and request.path.startswith('/logged_out'): return redirect(request.full_path.replace('/logged_out',''))

	try: cid = int(cid)
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
		elif SITE_NAME == 'rDrama': pid = 6489
		elif request.host == 'pcmemes.net': pid = 2487
		else: pid = 1
	
	try: pid = int(pid)
	except: abort(404)
	
	post = get_post(pid, v=v)
	
	if post.over_18 and not (v and v.over_18) and not session.get('over_18', 0) >= int(time.time()):
		if request.headers.get("Authorization"): return {'error': 'This content is not suitable for some users and situations.'}
		else: return render_template("errors/nsfw.html", v=v)

	try: context = min(int(request.values.get("context", 0)), 8)
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
			blocking.c.target_id,
			blocked.c.target_id,
		)

		if not (v and v.shadowbanned) and not (v and v.admin_level > 2):
			comments = comments.join(User, User.id == Comment.author_id).filter(User.shadowbanned == None)
		 
		comments=comments.filter(
			Comment.parent_submission == post.id,
			Comment.author_id.notin_((AUTOPOLLER_ID, AUTOBETTER_ID, AUTOCHOICE_ID))
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
		return render_template(template, v=v, p=post, sort=sort, comment_info=comment_info, render_replies=True, sub=post.subr)

@app.post("/comment")
@limiter.limit("1/second;20/minute;200/hour;1000/day")
@limiter.limit("1/second;20/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def api_comment(v):
	if v.is_suspended: return {"error": "You can't perform this action while banned."}, 403

	parent_submission = request.values.get("submission").strip()
	parent_fullname = request.values.get("parent_fullname").strip()

	parent_post = get_post(parent_submission, v=v)
	sub = parent_post.sub
	if sub and v.exiled_from(sub): return {"error": f"You're exiled from /h/{sub}"}, 403

	if parent_post.club and not (v and (v.paid_dues or v.id == parent_post.author_id)): abort(403)

	rts = False
	if parent_fullname.startswith("t2_"):
		parent = parent_post
		parent_comment_id = None
		level = 1
	elif parent_fullname.startswith("t3_"):
		parent = get_comment(parent_fullname.split("_")[1], v=v)
		parent_comment_id = parent.id
		level = parent.level + 1
		if parent.author_id == v.id: rts = True
	else: abort(400)

	body = request.values.get("body", "").strip()[:10000]

	if v.admin_level > 2 and parent_post.id == 37749 and level == 1:
		with open(f"snappy_{SITE_NAME}.txt", "a", encoding="utf-8") as f:
			f.write('\n{[para]}\n' + body)

	if parent_post.id not in ADMIGGERS:
		if v.longpost and (len(body) < 280 or ' [](' in body or body.startswith('[](')):
			return {"error":"You have to type more than 280 characters!"}, 403
		elif v.bird and len(body) > 140:
			return {"error":"You have to type less than 140 characters!"}, 403

	if not body and not request.files.get('file'): return {"error":"You need to actually write something!"}, 400
	
	options = []
	for i in poll_regex.finditer(body):
		options.append(i.group(1))
		body = body.replace(i.group(0), "")

	choices = []
	for i in choice_regex.finditer(body):
		choices.append(i.group(1))
		body = body.replace(i.group(0), "")

	if request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
		files = request.files.getlist('file')[:4]
		for file in files:
			if file.content_type.startswith('image/'):
				oldname = f'/images/{time.time()}'.replace('.','') + '.webp'
				file.save(oldname)
				image = process_image(v.patron, oldname)
				if image == "": return {"error":"Image upload failed"}
				if v.admin_level > 2 and level == 1:
					if parent_post.id == 37696:
						li = sorted(os.listdir('files/assets/images/rDrama/sidebar'),
							key=lambda e: int(e.split('.webp')[0]))[-1]
						num = int(li.split('.webp')[0]) + 1
						filename = f'files/assets/images/rDrama/sidebar/{num}.webp'
						copyfile(oldname, filename)
						process_image(v.patron, filename, 400)
					elif parent_post.id == 37697:
						li = sorted(os.listdir('files/assets/images/rDrama/banners'),
							key=lambda e: int(e.split('.webp')[0]))[-1]
						num = int(li.split('.webp')[0]) + 1
						filename = f'files/assets/images/rDrama/banners/{num}.webp'
						copyfile(oldname, filename)
						process_image(v.patron, filename)
					elif parent_post.id == 37833:
						try:
							badge_def = loads(body)
							name = badge_def["name"]

							existing = g.db.query(BadgeDef).filter_by(name=name).one_or_none()
							if existing: return {"error": "A badge with this name already exists!"}, 403

							badge = BadgeDef(name=name, description=badge_def["description"])
							g.db.add(badge)
							g.db.flush()
							filename = f'files/assets/images/badges/{badge.id}.webp'
							copyfile(oldname, filename)
							process_image(v.patron, filename, 200)
							requests.post(f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/purge_cache', headers=CF_HEADERS, data={'files': [f"https://{request.host}/assets/images/badges/{badge.id}.webp"]}, timeout=5)
						except Exception as e:
							return {"error": str(e)}, 400
					elif v.admin_level > 2 and parent_post.id == 37838:
						try:
							marsey = loads(body.lower())

							name = marsey["name"]
							if not marsey_regex.fullmatch(name): return {"error": "Invalid name!"}, 400
							existing = g.db.query(Marsey.name).filter_by(name=name).one_or_none()
							if existing: return {"error": "A marsey with this name already exists!"}, 403

							tags = marsey["tags"]
							if not tags_regex.fullmatch(tags): return {"error": "Invalid tags!"}, 400

							if "author" in marsey: user = get_user(marsey["author"])
							elif "author_id" in marsey: user = get_account(marsey["author_id"])
							else: abort(400)

							filename = f'files/assets/images/emojis/{name}.webp'
							copyfile(oldname, filename)
							process_image(v.patron, filename, 200)

							marsey = Marsey(name=name, author_id=user.id, tags=tags, count=0)
							g.db.add(marsey)
							g.db.flush()

							all_by_author = g.db.query(Marsey).filter_by(author_id=user.id).count()

							if all_by_author >= 10 and not user.has_badge(16):
								new_badge = Badge(badge_id=16, user_id=user.id)

								g.db.add(new_badge)
								g.db.flush()

								if v.id != user.id:
									text = f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}"
									send_notification(user.id, text)

							elif all_by_author < 10 and not user.has_badge(17):
								new_badge = Badge(badge_id=17, user_id=user.id)

								g.db.add(new_badge)
								g.db.flush()

								if v.id != user.id:
									text = f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}"
									send_notification(user.id, text)



							requests.post(f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/purge_cache', headers=CF_HEADERS, data={'files': [f"https://{request.host}/e/{name}.webp"]}, timeout=5)
							cache.delete_memoized(marsey_list)

						except Exception as e:
							return {"error": str(e)}, 400
				body += f"\n\n![]({image})"
			elif file.content_type.startswith('video/'):
				if file.content_type == 'video/webm':
					file.save("video.mp4")
				else:
					file.save("unsanitized.mp4")
					os.system(f'ffmpeg -y -loglevel warning -i unsanitized.mp4 -map_metadata -1 -c:v copy -c:a copy video.mp4')
				with open("video.mp4", 'rb') as f:
					try: req = requests.request("POST", "https://pomf2.lain.la/upload.php", files={'files[]': f}, timeout=5).json()
					except requests.Timeout: return {"error": "Video upload timed out, please try again!"}
					try: url = req['files'][0]['url']
					except: return {"error": req['description']}, 400
				body += f"\n\n{url}"
			else: return {"error": "Image/Video files only"}, 400

	if v.agendaposter and not v.marseyawarded and parent_post.id not in ADMIGGERS:
		body = torture_ap(body, v.username)

	body_html = sanitize(body, comment=True)


	if parent_post.id not in ADMIGGERS and '!slots' not in body.lower() and '!blackjack' not in body.lower() and '!wordle' not in body.lower() and AGENDAPOSTER_PHRASE not in body.lower():
		existing = g.db.query(Comment.id).filter(Comment.author_id == v.id,
																	Comment.deleted_utc == 0,
																	Comment.parent_comment_id == parent_comment_id,
																	Comment.parent_submission == parent_submission,
																	Comment.body_html == body_html
																	).one_or_none()
		if existing: return {"error": f"You already made that comment: /comment/{existing.id}"}, 409

	if parent.author.any_block_exists(v) and v.admin_level < 2:
		return {"error": "You can't reply to users who have blocked you, or users you have blocked."}, 403

	is_bot = bool(request.headers.get("Authorization")) or (SITE == 'pcmemes.net' and v.id == SNAPPY_ID)

	if '!slots' not in body.lower() and '!blackjack' not in body.lower() and '!wordle' not in body.lower() and parent_post.id not in ADMIGGERS and not is_bot and not v.marseyawarded and AGENDAPOSTER_PHRASE not in body.lower() and len(body) > 10:
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
			text = "Your account has been banned for **1 day** for the following reason:\n\n> Too much spam!"
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
				level=level,
				over_18=parent_post.over_18 or request.values.get("over_18")=="true",
				is_bot=is_bot,
				app_id=v.client.application.id if v.client else None,
				body_html=body_html,
				body=body[:10000],
				ghost=parent_post.ghost
				)

	c.upvotes = 1
	g.db.add(c)
	g.db.flush()

	if blackjack and any(i in c.body.lower() for i in blackjack.split()):
		v.shadowbanned = 'AutoJanny'
		notif = Notification(comment_id=c.id, user_id=CARP_ID)
		g.db.add(notif)

	if c.level == 1: c.top_comment_id = c.id
	else: c.top_comment_id = parent.top_comment_id

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

	for choice in choices:
		c_choice = Comment(author_id=AUTOCHOICE_ID,
			parent_submission=parent_submission,
			parent_comment_id=c.id,
			level=level+1,
			body_html=filter_emojis_only(choice),
			upvotes=0,
			is_bot=True
			)

		g.db.add(c_choice)

	if request.host == 'pcmemes.net' and c.body.lower().startswith("based"):
		pill = based_regex.match(body)

		if level == 1: basedguy = get_account(parent_post.author_id)
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
			top_comment_id=c.top_comment_id,
			ghost=parent_post.ghost
			)

		g.db.add(c_based)
		g.db.flush()

		n = Notification(comment_id=c_based.id, user_id=v.id)
		g.db.add(n)

	if parent_post.id not in ADMIGGERS:
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
				top_comment_id=c.top_comment_id,
				ghost=parent_post.ghost
				)

			g.db.add(c_jannied)
			g.db.flush()

			n = Notification(comment_id=c_jannied.id, user_id=v.id)
			g.db.add(n)


		if SITE_NAME == 'rDrama' and len(c.body.split()) >= 200 and "<" not in body and "</blockquote>" not in body_html:
		
			body = random.choice(LONGPOST_REPLIES)


			if body.startswith('▼'):
				body = body[1:]
				vote = CommentVote(user_id=LONGPOSTBOT_ID,
							vote_type=-1,
							comment_id=c.id,
							real = True
							)
				g.db.add(vote)
				c.downvotes = 1



			body_html2 = sanitize(body)

			c2 = Comment(author_id=LONGPOSTBOT_ID,
				parent_submission=parent_submission,
				parent_comment_id=c.id,
				level=level+1,
				is_bot=True,
				body_html=body_html2,
				top_comment_id=c.top_comment_id,
				ghost=parent_post.ghost
				)

			g.db.add(c2)

			longpostbot = g.db.query(User).filter_by(id = LONGPOSTBOT_ID).one_or_none()
			longpostbot.comment_count += 1
			longpostbot.coins += 1
			g.db.add(longpostbot)
			
			g.db.flush()

			n = Notification(comment_id=c2.id, user_id=v.id)
			g.db.add(n)


		if SITE_NAME == 'rDrama' and random.random() < 0.001:
		
			body = "zoz"
			body_html2 = sanitize(body)




			c2 = Comment(author_id=ZOZBOT_ID,
				parent_submission=parent_submission,
				parent_comment_id=c.id,
				level=level+1,
				is_bot=True,
				body_html=body_html2,
				top_comment_id=c.top_comment_id,
				ghost=parent_post.ghost,
				distinguish_level=6
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
				top_comment_id=c.top_comment_id,
				ghost=parent_post.ghost,
				distinguish_level=6
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
				top_comment_id=c.top_comment_id,
				ghost=parent_post.ghost,
				distinguish_level=6
				)

			g.db.add(c4)

			zozbot = g.db.query(User).filter_by(id = ZOZBOT_ID).one_or_none()
			zozbot.comment_count += 3
			zozbot.coins += 3
			g.db.add(zozbot)


		if not v.shadowbanned:
			notify_users = NOTIFY_USERS(body, v)
			
			for x in g.db.query(Subscription.user_id).filter_by(submission_id=c.parent_submission).all(): notify_users.add(x[0])
			
			if parent.author.id not in (v.id, BASEDBOT_ID, AUTOJANNY_ID, SNAPPY_ID, LONGPOSTBOT_ID, ZOZBOT_ID, AUTOPOLLER_ID, AUTOCHOICE_ID):
				notify_users.add(parent.author.id)

			for x in notify_users:
				n = Notification(comment_id=c.id, user_id=x)
				g.db.add(n)

			if parent.author.id != v.id and PUSHER_ID != 'blahblahblah' and not v.shadowbanned:				
				try: gevent.spawn(pusher_thread, f'{request.host}{parent.author.id}', c, c.author_name)
				except: pass

				

	vote = CommentVote(user_id=v.id,
						 comment_id=c.id,
						 vote_type=1,
						 )

	g.db.add(vote)
	

	cache.delete_memoized(comment_idlist)

	v.comment_count = g.db.query(Comment).filter(Comment.author_id == v.id, Comment.parent_submission != None).filter_by(is_banned=False, deleted_utc=0).count()
	g.db.add(v)

	c.voted = 1
	
	if v.id == PIZZASHILL_ID:
		for uid in PIZZA_VOTERS:
			autovote = CommentVote(user_id=uid, comment_id=c.id, vote_type=1)
			g.db.add(autovote)
		v.coins += 3
		v.truecoins += 3
		g.db.add(v)
		c.upvotes += 3
		g.db.add(c)

	if not v.rehab:
		check_for_slots_command(body, v, c)

		check_for_blackjack_commands(body, v, c)

	if not c.slots_result and not c.blackjack_result and v.marseyawarded and parent_post.id not in ADMIGGERS and marseyaward_body_regex.search(body_html):
		return {"error":"You can only type marseys!"}, 403

	check_for_treasure(body, c)

	if "!wordle" in body:
		answer = random.choice(WORDLE_LIST)
		c.wordle_result = f'_active_{answer}'

	if not c.slots_result and not c.blackjack_result and not c.wordle_result and not rts:
		parent_post.comment_count += 1
		g.db.add(parent_post)

	g.db.commit()

	if request.headers.get("Authorization"): return c.json
	return {"comment": render_template("comments.html", v=v, comments=[c], ajax=True)}



@app.post("/edit_comment/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def edit_comment(cid, v):

	c = get_comment(cid, v=v)

	if c.author_id != v.id: abort(403)

	body = request.values.get("body", "").strip()[:10000]

	if len(body) < 1 and not (request.files.get("file") and request.headers.get("cf-ipcountry") != "T1"):
		return {"error":"You have to actually type something!"}, 400

	if body != c.body or request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
		if v.longpost and (len(body) < 280 or ' [](' in body or body.startswith('[](')):
			return {"error":"You have to type more than 280 characters!"}, 403
		elif v.bird and len(body) > 140:
			return {"error":"You have to type less than 140 characters!"}, 403

		if v.agendaposter and not v.marseyawarded:
			body = torture_ap(body, v.username)

		for i in poll_regex.finditer(body):
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

		for i in choice_regex.finditer(body):
			body = body.replace(i.group(0), "")
			c_choice = Comment(author_id=AUTOCHOICE_ID,
				parent_submission=c.parent_submission,
				parent_comment_id=c.id,
				level=c.level+1,
				body_html=filter_emojis_only(i.group(1)),
				upvotes=0,
				is_bot=True
				)
			g.db.add(c_choice)

		body_html = sanitize(body, edit=True)

		if '!slots' not in body.lower() and '!blackjack' not in body.lower() and '!wordle' not in body.lower() and AGENDAPOSTER_PHRASE not in body.lower():
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
				text = "Your account has been banned for **1 day** for the following reason:\n\n> Too much spam!"
				send_repeatable_notification(v.id, text)

				v.ban(reason="Spamming.",
						days=1)

				for comment in similar_comments:
					comment.is_banned = True
					comment.ban_reason = "AutoJanny"
					g.db.add(comment)

				return {"error": "Too much spam!"}, 403

		if request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
			files = request.files.getlist('file')[:4]
			for file in files:
				if file.content_type.startswith('image/'):
					name = f'/images/{time.time()}'.replace('.','') + '.webp'
					file.save(name)
					url = process_image(v.patron, name)
					body += f"\n\n![]({url})"
				elif file.content_type.startswith('video/'):
					if file.content_type == 'video/webm':
						file.save("video.mp4")
					else:
						file.save("unsanitized.mp4")
						os.system(f'ffmpeg -y -loglevel warning -i unsanitized.mp4 -map_metadata -1 -c:v copy -c:a copy video.mp4')
					with open("video.mp4", 'rb') as f:
						try: req = requests.request("POST", "https://pomf2.lain.la/upload.php", files={'files[]': f}, timeout=5).json()
						except requests.Timeout: return {"error": "Video upload timed out, please try again!"}
						try: url = req['files'][0]['url']
						except: return {"error": req['description']}, 400
					body += f"\n\n{url}"
				else: return {"error": "Image/Video files only"}, 400

			body_html = sanitize(body, edit=True)

		if len(body_html) > 20000: abort(400)

		if v.marseyawarded and marseyaward_body_regex.search(body_html):
			return {"error":"You can only type marseys!"}, 403

		c.body = body[:10000]
		c.body_html = body_html

		if blackjack and any(i in c.body.lower() for i in blackjack.split()):
			v.shadowbanned = 'AutoJanny'
			g.db.add(v)
			notif = g.db.query(Notification).filter_by(comment_id=c.id, user_id=CARP_ID).one_or_none()
			if not notif:
				notif = Notification(comment_id=c.id, user_id=CARP_ID)
				g.db.add(notif)

		if v.agendaposter and not v.marseyawarded and AGENDAPOSTER_PHRASE not in c.body.lower() and not c.is_banned:

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
				top_comment_id=c.top_comment_id,
				ghost=c.ghost
				)

			g.db.add(c_jannied)
			g.db.flush()

			n = Notification(comment_id=c_jannied.id, user_id=v.id)
			g.db.add(n)



		if int(time.time()) - c.created_utc > 60 * 3: c.edited_utc = int(time.time())

		g.db.add(c)
		
		notify_users = NOTIFY_USERS(body, v)
		
		for x in notify_users:
			notif = g.db.query(Notification).filter_by(comment_id=c.id, user_id=x).one_or_none()
			if not notif:
				n = Notification(comment_id=c.id, user_id=x)
				g.db.add(n)

		g.db.commit()

	return {"comment": c.realbody(v)}


@app.post("/delete/comment/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def delete_comment(cid, v):

	c = get_comment(cid, v=v)

	if not c.deleted_utc:

		if c.author_id != v.id: abort(403)

		c.deleted_utc = int(time.time())

		g.db.add(c)
		
		cache.delete_memoized(comment_idlist)

		g.db.commit()

	return {"message": "Comment deleted!"}

@app.post("/undelete/comment/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def undelete_comment(cid, v):

	c = get_comment(cid, v=v)

	if c.deleted_utc:
		if c.author_id != v.id: abort(403)

		c.deleted_utc = 0

		g.db.add(c)

		cache.delete_memoized(comment_idlist)

		g.db.commit()

	return {"message": "Comment undeleted!"}


@app.post("/pin_comment/<cid>")
@auth_required
def pin_comment(cid, v):
	
	comment = get_comment(cid, v=v)
	
	if not comment.is_pinned:
		if v.id != comment.post.author_id: abort(403)
		
		if comment.post.ghost: comment.is_pinned = "(OP)"
		else: comment.is_pinned = v.username + " (OP)"

		g.db.add(comment)

		if v.id != comment.author_id:
			if comment.post.ghost: message = f"OP has pinned your [comment]({comment.shortlink})!"
			else: message = f"@{v.username} (OP) has pinned your [comment]({comment.shortlink})!"
			send_repeatable_notification(comment.author_id, message)

		g.db.commit()
	return {"message": "Comment pinned!"}
	

@app.post("/unpin_comment/<cid>")
@auth_required
def unpin_comment(cid, v):
	
	comment = get_comment(cid, v=v)
	
	if comment.is_pinned:
		if v.id != comment.post.author_id: abort(403)

		if not comment.is_pinned.endswith(" (OP)"): 
			return {"error": "You can only unpin comments you have pinned!"}

		comment.is_pinned = None
		g.db.add(comment)

		if v.id != comment.author_id:
			message = f"@{v.username} (OP) has unpinned your [comment]({comment.shortlink})!"
			send_repeatable_notification(comment.author_id, message)
		g.db.commit()
	return {"message": "Comment unpinned!"}


@app.post("/mod_pin/<cid>")
@auth_required
def mod_pin(cid, v):
	
	comment = get_comment(cid, v=v)
	
	if not comment.is_pinned:
		if not (comment.post.sub and v.mods(comment.post.sub)): abort(403)
		
		comment.is_pinned = v.username + " (Mod)"

		g.db.add(comment)

		if v.id != comment.author_id:
			message = f"@{v.username} (Mod) has pinned your [comment]({comment.shortlink})!"
			send_repeatable_notification(comment.author_id, message)

		g.db.commit()
	return {"message": "Comment pinned!"}
	

@app.post("/unmod_pin/<cid>")
@auth_required
def mod_unpin(cid, v):
	
	comment = get_comment(cid, v=v)
	
	if comment.is_pinned:
		if not (comment.post.sub and v.mods(comment.post.sub)): abort(403)

		comment.is_pinned = None
		g.db.add(comment)

		if v.id != comment.author_id:
			message = f"@{v.username} (Mod) has unpinned your [comment]({comment.shortlink})!"
			send_repeatable_notification(comment.author_id, message)
		g.db.commit()
	return {"message": "Comment unpinned!"}


@app.post("/save_comment/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def save_comment(cid, v):

	comment=get_comment(cid)

	save=g.db.query(CommentSaveRelationship).filter_by(user_id=v.id, comment_id=comment.id).one_or_none()

	if not save:
		new_save=CommentSaveRelationship(user_id=v.id, comment_id=comment.id)
		g.db.add(new_save)

		g.db.commit()

	return {"message": "Comment saved!"}

@app.post("/unsave_comment/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def unsave_comment(cid, v):

	comment=get_comment(cid)

	save=g.db.query(CommentSaveRelationship).filter_by(user_id=v.id, comment_id=comment.id).one_or_none()

	if save:
		g.db.delete(save)
		g.db.commit()

	return {"message": "Comment unsaved!"}

@app.post("/blackjack/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def handle_blackjack_action(cid, v):
	comment = get_comment(cid)
	if 'active' in comment.blackjack_result:
		try: action = request.values.get("thing").strip().lower()
		except: abort(400)

		if action == 'hit': player_hit(comment)
		elif action == 'stay': player_stayed(comment)
		elif action == 'doubledown': player_doubled_down(comment)
		elif action == 'insurance': player_bought_insurance(comment)

		g.db.add(comment)
		g.db.add(v)
		g.db.commit()
	return {"response" : comment.blackjack_html(v)}


def diff_words(answer, guess):
	"""
	Return a list of numbers corresponding to the char's relevance.
	-1 means char is not in solution or the character appears too many times in the guess
	0 means char is in solution but in the wrong spot
	1 means char is in the correct spot
	"""
	diffs = [
			1 if cs == cg else -1 for cs, cg in zip(answer, guess)
		]
	char_freq = Counter(
		c_guess for c_guess, diff, in zip(answer, diffs) if diff == -1
	)
	for i, cg in enumerate(guess):
		if diffs[i] == -1 and cg in char_freq and char_freq[cg] > 0:
			char_freq[cg] -= 1
			diffs[i] = 0
	return diffs


@app.post("/wordle/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def handle_wordle_action(cid, v):

	comment = get_comment(cid)

	guesses, status, answer = comment.wordle_result.split("_")
	count = len(guesses.split(" -> "))

	try: guess = request.values.get("thing").strip().lower()
	except: abort(400)

	if len(guess) != 5 or not d.check(guess) and guess not in WORDLE_LIST:
		return {"error": "Not a valid guess!"}, 400

	if status == "active":
		guesses += "".join(cg + WORDLE_COLOR_MAPPINGS[diff] for cg, diff in zip(guess, diff_words(answer, guess)))

		if (guess == answer): status = "won"
		elif (count == 6): status = "lost"
		else: guesses += ' -> '

		comment.wordle_result = f'{guesses}_{status}_{answer}'

		g.db.add(comment)
		g.db.commit()
	
	return {"response" : comment.wordle_html(v)}