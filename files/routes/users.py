import qrcode
import io
import time
import math
from files.classes.user import ViewerRelationship
from files.helpers.alerts import *
from files.helpers.sanitize import *
from files.helpers.markdown import *
from files.helpers.const import *
from files.mail import *
from flask import *
from files.__main__ import app, limiter
from pusher_push_notifications import PushNotifications

site = environ.get("DOMAIN").strip()

beams_client = PushNotifications(
		instance_id=PUSHER_INSTANCE_ID,
		secret_key=PUSHER_KEY,
)


@app.post("/pay_rent")
@limiter.limit("1/second")
@auth_required
def pay_rent(v):
	if v.coins < 500: return "You must have more than 500 coins."
	v.coins -= 500
	v.rent_utc = int(time.time())
	g.db.add(v)
	u = get_account(253)
	u.coins += 500
	g.db.add(u)
	send_notification(NOTIFICATIONS_ACCOUNT, u, f"@{v.username} has paid rent!")
	g.db.commit()
	return {"message": "Rent paid!"}


@app.post("/steal")
@limiter.limit("1/second")
@is_not_banned
def steal(v):
	if int(time.time()) - v.created_utc < 604800:
		return "You must have an account older than 1 week in order to attempt stealing."
	if v.coins < 5000:
		return "You must have more than 5000 coins in order to attempt stealing."
	u = get_account(253)
	if random.randint(1, 10) < 5:
		v.coins += 700
		v.steal_utc = int(time.time())
		g.db.add(v)
		u.coins -= 700
		g.db.add(u)
		send_notification(NOTIFICATIONS_ACCOUNT, u, f"Some [grubby little rentoid](/@{v.username}) has absconded with 700 of your hard-earned dramacoins to fuel his Funko Pop addiction. Stop being so trusting.")
		send_notification(NOTIFICATIONS_ACCOUNT, v, f"You have successfully shorted your heroic landlord 700 dramacoins in rent. You're slightly less materially poor, but somehow even moreso morally. Are you proud of yourself?")
		g.db.commit()
		return {"message": "Attempt successful!"}

	else:
		if random.random() < 0.15:
			send_notification(NOTIFICATIONS_ACCOUNT, u, f"You caught [this sniveling little renthog](/@{v.username}) trying to rob you. After beating him within an inch of his life, you sold his Nintendo Switch for 500 dramacoins and called the cops. He was sentenced to one (1) day in renthog prison.")
			send_notification(NOTIFICATIONS_ACCOUNT, v, f"The ever-vigilant landchad has caught you trying to steal his hard-earned rent money. The police take you away and laugh as you impotently stutter A-ACAB :sob:  You are fined 500 dramacoins and sentenced to one (1) day in renthog prison.")
			v.ban(days=1, reason="Jailed thief")
			v.fail_utc = int(time.time())
		else:
			send_notification(NOTIFICATIONS_ACCOUNT, u, f"You caught [this sniveling little renthog](/@{v.username}) trying to rob you. After beating him within an inch of his life, you showed mercy in exchange for a 500 dramacoin tip. This time.")
			send_notification(NOTIFICATIONS_ACCOUNT, v, f"The ever-vigilant landchad has caught you trying to steal his hard-earned rent money. You were able to convince him to spare your life with a 500 dramacoin tip. This time.")
			v.fail2_utc = int(time.time())
		v.coins -= 500
		g.db.add(v)
		u.coins += 500
		g.db.add(u)
		g.db.commit()
		return {"message": "Attempt failed!"}


@app.get("/rentoids")
@auth_desired
def rentoids(v):
	users = g.db.query(User).options(lazyload('*')).filter(User.rent_utc > 0).all()
	return render_template("rentoids.html", v=v, users=users)


@app.get("/thiefs")
@auth_desired
def thiefs(v):
	successful = g.db.query(User).options(lazyload('*')).filter(User.steal_utc > 0).all()
	failed = g.db.query(User).options(lazyload('*')).filter(User.fail_utc > 0).all()
	failed2 = g.db.query(User).options(lazyload('*')).filter(User.fail2_utc > 0).all()
	return render_template("thiefs.html", v=v, successful=successful, failed=failed, failed2=failed2)


@app.post("/@<username>/suicide")
@limiter.limit("1/second")
@auth_required
def suicide(v, username):
	t = int(time.time())
	if v.admin_level == 0 and t - v.suicide_utc < 86400: return {"message": "You're on 1-day cooldown!"}
	user = get_user(username)
	suicide = f"Hi there,\n\nA [concerned user]({v.url}) reached out to us about you.\n\nWhen you're in the middle of something painful, it may feel like you don't have a lot of options. But whatever you're going through, you deserve help and there are people who are here for you.\n\nThere are resources available in your area that are free, confidential, and available 24/7:\n\n- Call, Text, or Chat with Canada's [Crisis Services Canada](https://www.crisisservicescanada.ca/en/)\n- Call, Email, or Visit the UK's [Samaritans](https://www.samaritans.org/)\n- Text CHAT to America's [Crisis Text Line](https://www.crisistextline.org/) at 741741.\nIf you don't see a resource in your area above, the moderators at r/SuicideWatch keep a comprehensive list of resources and hotlines for people organized by location. Find Someone Now\n\nIf you think you may be depressed or struggling in another way, don't ignore it or brush it aside. Take yourself and your feelings seriously, and reach out to someone.\n\nIt may not feel like it, but you have options. There are people available to listen to you, and ways to move forward.\n\nYour fellow users care about you and there are people who want to help."
	send_notification(NOTIFICATIONS_ACCOUNT, user, suicide)
	v.suicide_utc = t
	g.db.add(v)
	g.db.commit()
	return {"message": "Help message sent!"}


@app.get("/@<username>/coins")
@auth_required
def get_coins(v, username):
	user = get_user(username)
	if user != None: return {"coins": user.coins}, 200
	else: return {"error": "invalid_user"}, 404

@app.post("/@<username>/transfer_coins")
@limiter.limit("1/second")
@is_not_banned
@validate_formkey
def transfer_coins(v, username):
	TAX_RECEIVER_ID = 747
	TAX_RATE = 0.01

	receiver = g.db.query(User).filter_by(username=username).first()
	tax_receiver = g.db.query(User).filter_by(id=TAX_RECEIVER_ID).first()

	if receiver is None: return {"error": "That user doesn't exist."}, 404

	if receiver.id != v.id:
		amount = request.values.get("amount", "").strip()
		amount = int(amount) if amount.isdigit() else None

		if amount is None or amount <= 0: return {"error": f"Invalid amount of {app.config['COINS_NAME']}."}, 400
		if v.coins < amount: return {"error": f"You don't have enough {app.config['COINS_NAME']}"}, 400
		if amount < 100: return {"error": f"You have to gift at least 100 {app.config['COINS_NAME']}."}, 400

		tax = math.ceil(amount*TAX_RATE)
		v.coins -= amount
		receiver.coins += amount-tax
		tax_receiver.coins += tax
		g.db.add(receiver)
		g.db.add(tax_receiver)
		g.db.add(v)

		transfer_message = f"🤑 [@{v.username}]({v.url}) has gifted you {amount} {app.config['COINS_NAME']}!"
		send_notification(NOTIFICATIONS_ACCOUNT, receiver, transfer_message)

		log_message = f"[@{v.username}]({v.url}) has transferred {amount} {app.config['COINS_NAME']} to [@{receiver.username}]({receiver.url})"
		send_notification(NOTIFICATIONS_ACCOUNT, TAX_RECEIVER_ID, log_message)

		g.db.commit()

		return {"message": f"{amount-tax} {app.config['COINS_NAME']} transferred!"}, 200

	return {"message": f"You can't transfer {app.config['COINS_NAME']} to yourself!"}, 400


@app.get("/leaderboard")
@auth_desired
def leaderboard(v):
	users = g.db.query(User).options(lazyload('*'))
	users1 = users.order_by(User.coins.desc()).limit(25).all()
	users2 = users.order_by(User.stored_subscriber_count.desc()).limit(10).all()
	users3 = users.order_by(User.post_count.desc()).limit(10).all()
	users4 = users.order_by(User.comment_count.desc()).limit(10).all()
	users5 = users.order_by(User.received_award_count.desc()).limit(10).all()
	if 'pcmemes.net' in request.host:
		users6 = users.order_by(User.basedcount.desc()).limit(10).all()
		return render_template("leaderboard.html", v=v, users1=users1, users2=users2, users3=users3, users4=users4, users5=users5, users6=users6)
	return render_template("leaderboard.html", v=v, users1=users1, users2=users2, users3=users3, users4=users4, users5=users5)


@app.get("/@<username>/css")
def get_css(username):
	user = get_user(username)
	if user.css: css = user.css
	else: css = ""
	resp=make_response(css)
	resp.headers.add("Content-Type", "text/css")
	return resp

@app.get("/@<username>/profilecss")
def get_profilecss(username):
	user = get_user(username)
	if user.profilecss: profilecss = user.profilecss
	else: profilecss = ""
	resp=make_response(profilecss)
	resp.headers.add("Content-Type", "text/css")
	return resp

@app.get("/songs/<id>")
def songs(id):
	try: id = int(id)
	except: return "", 400
	user = g.db.query(User).options(lazyload('*')).filter_by(id=id).first()
	if user and user.song: return redirect(f"/song/{user.song}.mp3")
	else: abort(404)

@app.get("/song/<song>")
def song(song):
	resp = make_response(send_from_directory('/songs/', song))
	resp.headers.remove("Cache-Control")
	resp.headers.add("Cache-Control", "public, max-age=2628000")
	return resp

@app.post("/subscribe/<post_id>")
@limiter.limit("1/second")
@auth_required
def subscribe(v, post_id):
	new_sub = Subscription(user_id=v.id, submission_id=post_id)
	g.db.add(new_sub)
	g.db.commit()
	return {"message": "Post subscribed!"}
	
@app.post("/unsubscribe/<post_id>")
@limiter.limit("1/second")
@auth_required
def unsubscribe(v, post_id):
	sub=g.db.query(Subscription).options(lazyload('*')).filter_by(user_id=v.id, submission_id=post_id).first()
	if sub:
		g.db.delete(sub)
		g.db.commit()
	return {"message": "Post unsubscribed!"}

@app.post("/@<username>/message")
@limiter.limit("1/second")
@limiter.limit("10/hour")
@auth_required
def message2(v, username):

	user = get_user(username, v=v)
	if hasattr(user, 'is_blocking') and user.is_blocking: return {"error": "You're blocking this user."}, 403

	if v.admin_level <= 1:
		if hasattr(user, 'is_blocked') and user.is_blocked: return {"error": "This user is blocking you."}, 403

	message = request.values.get("message", "").strip()[:1000].strip()

	existing = g.db.query(Comment).options(lazyload('*')).filter(Comment.author_id == v.id,
															Comment.sentto == user.id,
															Comment.body == message,
															).first()
	if existing: return redirect('/notifications?messages=true')

	text = re.sub('([^\n])\n([^\n])', r'\1\n\n\2', message)

	text_html = Renderer().render(mistletoe.Document(text))

	text_html = sanitize(text_html, True)

	new_comment = Comment(author_id=v.id,
						  parent_submission=None,
						  level=1,
						  sentto=user.id,
						  body=text,
						  body_html=text_html,
						  )
	g.db.add(new_comment)

	g.db.flush()


	notif = Notification(comment_id=new_comment.id, user_id=user.id)
	g.db.add(notif)

	
	try:
		beams_client.publish_to_interests(
			interests=[str(user.id)],
			publish_body={
				'web': {
					'notification': {
						'title': f'New message from @{v.username}',
						'body': message,
						'deep_link': f'https://{site}/notifications',
					},
				},
			},
		)
	except Exception as e:
		print(e)

	g.db.commit()

	return redirect(f"/@{username}")


@app.post("/reply")
@limiter.limit("1/second")
@limiter.limit("6/minute")
@auth_required
def messagereply(v):

	message = request.values.get("body", "").strip()[:1000].strip()
	id = int(request.values.get("parent_id"))
	parent = get_comment(id, v=v)
	user = parent.author
	message = re.sub('([^\n])\n([^\n])', r'\1\n\n\2', message)

	text_html = Renderer().render(mistletoe.Document(message))
	text_html = sanitize(text_html, True)
	new_comment = Comment(author_id=v.id,
							parent_submission=None,
							parent_comment_id=id,
							level=parent.level + 1,
							sentto=user.id,
							body=message,
							body_html=text_html,
							)
	g.db.add(new_comment)
	g.db.flush()

	notif = Notification(comment_id=new_comment.id, user_id=user.id)
	g.db.add(notif)

	g.db.commit()

	return render_template("comments.html", v=v, comments=[new_comment])

@app.get("/2faqr/<secret>")
@auth_required
def mfa_qr(secret, v):
	x = pyotp.TOTP(secret)
	qr = qrcode.QRCode(
		error_correction=qrcode.constants.ERROR_CORRECT_L
	)
	qr.add_data(x.provisioning_uri(v.username, issuer_name=app.config["SITE_NAME"]))
	img = qr.make_image(fill_color="#000000", back_color="white")

	mem = io.BytesIO()

	img.save(mem, format="PNG")
	mem.seek(0, 0)
	return send_file(mem, mimetype="image/png", as_attachment=False)


@app.get("/is_available/<name>")
@auth_desired
def api_is_available(name, v):

	name=name.strip()

	if len(name)<3 or len(name)>25:
		return {name:False}
		
	name=name.replace('_','\_')

	x= g.db.query(User).options(
		lazyload('*')
		).filter(
		or_(
			User.username.ilike(name),
			User.original_username.ilike(name)
			)
		).first()

	if x:
		return {name: False}
	else:
		return {name: True}


@app.get("/id/<id>")
def user_id(id):

	user = get_account(int(id))
	return redirect(user.url)
		
@app.get("/u/<username>")
def redditor_moment_redirect(username):
	return redirect(f"/@{username}")

@app.get("/@<username>/followers")
@auth_required
def followers(username, v):


	u = get_user(username, v=v)
	users = [x.user for x in u.followers]
	return render_template("followers.html", v=v, u=u, users=users)

@app.get("/views")
@auth_required
def visitors(v):
	if v.admin_level < 1 and not v.patron: return render_template("errors/patron.html", v=v)
	viewers=sorted(v.viewers, key = lambda x: x.last_view_utc, reverse=True)
	return render_template("viewers.html", v=v, viewers=viewers)


@app.get("/@<username>")
@app.get("/logged_out/@<username>")
@auth_desired
def u_username(username, v=None):


	if not v and not request.path.startswith('/logged_out'): return redirect(f"/logged_out{request.full_path}")

	if v and request.path.startswith('/logged_out'): v = None



	u = get_user(username, v=v)


	if username != u.username:
		return redirect(request.path.replace(username, u.username))

	if u.reserved:
		if request.headers.get("Authorization"): return {"error": f"That username is reserved for: {u.reserved}"}
		else: return render_template("userpage_reserved.html", u=u, v=v)

	if v and u.id != v.id:
		view = g.db.query(ViewerRelationship).options(lazyload('*')).filter(
			and_(
				ViewerRelationship.viewer_id == v.id,
				ViewerRelationship.user_id == u.id
			)
		).first()

		if view:
			view.last_view_utc = g.timestamp
		else:
			view = ViewerRelationship(user_id = u.id,
									  viewer_id = v.id)

		g.db.add(view)
		g.db.commit()

		
	if u.is_private and (not v or (v.id != u.id and v.admin_level < 3)):
		
		if v and u.id == 253:
			if int(time.time()) - v.rent_utc > 600:
				if request.headers.get("Authorization"): return {"error": "That userpage is private"}
				else: return render_template("userpage_private.html", time=int(time.time()), u=u, v=v)
		else:
			if request.headers.get("Authorization"): return {"error": "That userpage is private"}
			else: return render_template("userpage_private.html", time=int(time.time()), u=u, v=v)

	
	if hasattr(u, 'is_blocking') and u.is_blocking and (not v or v.admin_level < 3):
		if request.headers.get("Authorization"): return {"error": f"You are blocking @{u.username}."}
		else: return render_template("userpage_blocking.html", u=u, v=v)


	if hasattr(u, 'is_blocked') and u.is_blocked and (not v or v.admin_level < 3):
		if request.headers.get("Authorization"): return {"error": "This person is blocking you."}
		else: return render_template("userpage_blocked.html", u=u, v=v)


	sort = request.values.get("sort", "new")
	t = request.values.get("t", "all")
	page = int(request.values.get("page", "1"))
	page = max(page, 1)

	ids = u.userpagelisting(v=v, page=page, sort=sort, t=t)

	next_exists = (len(ids) > 25)
	ids = ids[:25]

   # If page 1, check for sticky
	if page == 1:
		sticky = []
		sticky = g.db.query(Submission).options(lazyload('*')).filter_by(is_pinned=True, author_id=u.id).all()
		if sticky:
			for p in sticky:
				ids = [p.id] + ids

	listing = get_posts(ids, v=v)

	if u.unban_utc:
		if request.headers.get("Authorization"): {"data": [x.json for x in listing]}
		else: return render_template("userpage.html",
												unban=u.unban_string,
												u=u,
												v=v,
												listing=listing,
												page=page,
												sort=sort,
												t=t,
												next_exists=next_exists,
												is_following=(v and u.has_follower(v)))



	if request.headers.get("Authorization"): return {"data": [x.json for x in listing]}
	else: return render_template("userpage.html",
									u=u,
									v=v,
									listing=listing,
									page=page,
									sort=sort,
									t=t,
									next_exists=next_exists,
									is_following=(v and u.has_follower(v)))


@app.get("/@<username>/comments")
@app.get("/logged_out/@<username>/comments")
@auth_desired
def u_username_comments(username, v=None):


	if not v and not request.path.startswith('/logged_out'): return redirect(f"/logged_out{request.full_path}")

	if v and request.path.startswith('/logged_out'): v = None



	user = get_user(username, v=v)


	if username != user.username: return redirect(f'{user.url}/comments')

	u = user

	if u.reserved:
		if request.headers.get("Authorization"): return {"error": f"That username is reserved for: {u.reserved}"}
		else: return render_template("userpage_reserved.html",
												u=u,
												v=v)


	if u.is_private and (not v or (v.id != u.id and v.admin_level < 3)):
		if v and u.id == 253:
			if int(time.time()) - v.rent_utc > 600:
				if request.headers.get("Authorization"): return {"error": "That userpage is private"}
				else: return render_template("userpage_private.html", time=int(time.time()), u=u, v=v)
		else:
			if request.headers.get("Authorization"): return {"error": "That userpage is private"}
			else: return render_template("userpage_private.html", time=int(time.time()), u=u, v=v)

	if hasattr(u, 'is_blocking') and u.is_blocking and (not v or v.admin_level < 3):
		if request.headers.get("Authorization"): return {"error": f"You are blocking @{u.username}."}
		else: return render_template("userpage_blocking.html",
													u=u,
													v=v)

	if hasattr(u, 'is_blocked') and u.is_blocked and (not v or v.admin_level < 3):
		if request.headers.get("Authorization"): return {"error": "This person is blocking you."}
		else: return render_template("userpage_blocked.html",
													u=u,
													v=v)


	page = int(request.values.get("page", "1"))
	sort=request.values.get("sort","new")
	t=request.values.get("t","all")


	comments = g.db.query(Comment.id).options(lazyload('*')).filter(Comment.author_id == u.id, Comment.parent_submission != None)

	if (not v) or (v.id != u.id and v.admin_level == 0):
		comments = comments.filter(Comment.deleted_utc == 0)
		comments = comments.filter(Comment.is_banned == False)

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
		comments = comments.order_by(Comment.downvotes - Comment.upvotes)
	elif sort == "bottom":
		comments = comments.order_by(Comment.upvotes - Comment.downvotes)

	comments = comments.offset(25 * (page - 1)).limit(26).all()
	ids = [x.id for x in comments]

	next_exists = (len(ids) > 25)
	ids = ids[:25]

	listing = get_comments(ids, v=v)

	is_following = (v and user.has_follower(v))

	if request.headers.get("Authorization"): return {"data": [c.json for c in listing]}
	else: return render_template("userpage_comments.html", u=user, v=v, listing=listing, page=page, sort=sort, t=t,next_exists=next_exists, is_following=is_following, standalone=True)


@app.get("/@<username>/info")
@auth_desired
def u_username_info(username, v=None):

	user=get_user(username, v=v)

	if hasattr(user, 'is_blocking') and user.is_blocking:
		return {"error": "You're blocking this user."}, 401
	elif hasattr(user, 'is_blocked') and user.is_blocked:
		return {"error": "This user is blocking you."}, 403

	return user.json


@app.post("/follow/<username>")
@limiter.limit("1/second")
@auth_required
def follow_user(username, v):

	target = get_user(username)

	if target.id==v.id: return {"error": "You can't follow yourself!"}, 400

	if g.db.query(Follow).options(lazyload('*')).filter_by(user_id=v.id, target_id=target.id).first(): return {"message": "User followed!"}

	new_follow = Follow(user_id=v.id, target_id=target.id)
	g.db.add(new_follow)

	g.db.flush()
	target.stored_subscriber_count = g.db.query(Follow.id).options(lazyload('*')).filter_by(target_id=target.id).count()
	g.db.add(target)

	existing = g.db.query(Notification).options(lazyload('*')).filter_by(followsender=v.id, user_id=target.id).first()
	if not existing: send_follow_notif(v.id, target.id, f"@{v.username} has followed you!")

	g.db.commit()

	return {"message": "User followed!"}

@app.post("/unfollow/<username>")
@limiter.limit("1/second")
@auth_required
def unfollow_user(username, v):

	target = get_user(username)

	if target.id == 995: abort(403)

	follow = g.db.query(Follow).options(lazyload('*')).filter_by(user_id=v.id, target_id=target.id).first()

	if not follow: return {"message": "User unfollowed!"}

	g.db.delete(follow)
	
	g.db.flush()
	target.stored_subscriber_count = g.db.query(Follow.id).options(lazyload('*')).filter_by(target_id=target.id).count()
	g.db.add(target)

	existing = g.db.query(Notification).options(lazyload('*')).filter_by(unfollowsender=v.id, user_id=target.id).first()
	if not existing: send_unfollow_notif(v.id, target.id, f"@{v.username} has unfollowed you!")

	g.db.commit()

	return {"message": "User unfollowed!"}

@app.post("/remove_follow/<username>")
@limiter.limit("1/second")
@auth_required
def remove_follow(username, v):
	target = get_user(username)

	follow = g.db.query(Follow).options(lazyload('*')).filter_by(user_id=target.id, target_id=v.id).first()

	if not follow: return {"message": "Follower removed!"}

	g.db.delete(follow)
	
	g.db.flush()
	v.stored_subscriber_count = g.db.query(Follow.id).options(lazyload('*')).filter_by(target_id=v.id).count()
	g.db.add(v)

	existing = g.db.query(Notification).options(lazyload('*')).filter_by(removefollowsender=v.id, user_id=target.id).first()
	if not existing: send_unfollow_notif(v.id, target.id, f"@{v.username} has removed your follow!")

	g.db.commit()

	return {"message": "Follower removed!"}


@app.get("/uid/<id>/pic/profile")
@limiter.exempt
def user_profile_uid(id):
	try: id = int(id)
	except:
		try: id = int(id, 36)
		except: abort(404)
	x=get_account(id)
	return redirect(x.profile_url)


@app.get("/@<username>/saved/posts")
@auth_required
def saved_posts(v, username):

	page=int(request.values.get("page",1))

	ids=v.saved_idlist(page=page)

	next_exists=len(ids)>25

	ids=ids[:25]

	listing = get_posts(ids, v=v)

	if request.headers.get("Authorization"): return {"data": [x.json for x in listing]}
	else: return render_template("userpage.html",
											u=v,
											v=v,
											listing=listing,
											page=page,
											next_exists=next_exists,
											)


@app.get("/@<username>/saved/comments")
@auth_required
def saved_comments(v, username):

	page=int(request.values.get("page",1))

	firstrange = 25 * (page - 1)
	secondrange = firstrange+26

	ids=v.saved_comment_idlist()[firstrange:secondrange]

	next_exists=len(ids) > 25

	ids=ids[:25]

	listing = get_comments(ids, v=v)


	if request.headers.get("Authorization"): return {"data": [x.json for x in listing]}
	else: return render_template("userpage_comments.html",
											u=v,
											v=v,
											listing=listing,
											page=page,
											next_exists=next_exists,
											standalone=True)
