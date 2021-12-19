from urllib.parse import urlencode
from files.mail import *
from files.__main__ import app, limiter
from files.helpers.const import *
import requests

valid_username_regex = re.compile("^[a-zA-Z0-9_\-]{3,25}$")
valid_password_regex = re.compile("^.{8,100}$")


@app.get("/login")
@auth_desired
def login_get(v):

	redir = request.values.get("redirect", "/").replace("/logged_out", "").strip()
	if v:
		return redirect(redir)

	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}login.html",
						   failed=False,
						   redirect=redir)


def check_for_alts(current_id):
	past_accs = set(session.get("history", []))
	past_accs.add(current_id)
	session["history"] = list(past_accs)

	for past_id in session["history"]:
		
		if past_id == MOM_ID or current_id == MOM_ID: break
		if past_id == current_id: continue

		check1 = g.db.query(Alt).filter_by(
			user1=current_id, user2=past_id).first()
		check2 = g.db.query(Alt).filter_by(
			user1=past_id, user2=current_id).first()

		if not check1 and not check2:

			try:
				new_alt = Alt(user1=past_id, user2=current_id)
				g.db.add(new_alt)
				g.db.flush()
			except BaseException:
				pass
			
		alts = g.db.query(Alt)
		otheralts = alts.filter(or_(Alt.user1 == past_id, Alt.user2 == past_id, Alt.user1 == current_id, Alt.user2 == current_id)).all()
		for a in otheralts:
			existing = alts.filter_by(user1=a.user1, user2=past_id).first()
			if not existing:
				new_alt = Alt(user1=a.user1, user2=past_id)
				g.db.add(new_alt)
				g.db.flush()

			existing = alts.filter_by(user1=a.user1, user2=current_id).first()
			if not existing:
				new_alt = Alt(user1=a.user1, user2=current_id)
				g.db.add(new_alt)
				g.db.flush()

			existing = alts.filter_by(user1=a.user2, user2=past_id).first()
			if not existing:
				new_alt = Alt(user1=a.user2, user2=past_id)
				g.db.add(new_alt)
				g.db.flush()

			existing = alts.filter_by(user1=a.user2, user2=current_id).first()
			if not existing:
				new_alt = Alt(user1=a.user2, user2=current_id)
				g.db.add(new_alt)
				g.db.flush()


@app.post("/login")
@limiter.limit("1/second")
@limiter.limit("6/minute")
def login_post():
	template = ''

	username = request.values.get("username")

	if not username: abort(400)
	if "@" in username:
		account = g.db.query(User).filter(
			User.email.ilike(username)).first()
	else:
		account = get_user(username, graceful=True)

	if not account:
		time.sleep(random.uniform(0, 2))
		return render_template(f"{template}login.html", failed=True)


	if request.values.get("password"):

		if not account.verifyPass(request.values.get("password")):
			time.sleep(random.uniform(0, 2))
			return render_template(f"{template}login.html", failed=True)

		if account.mfa_secret:
			now = int(time.time())
			hash = generate_hash(f"{account.id}+{now}+2fachallenge")
			return render_template(f"{template}login_2fa.html",
								   v=account,
								   time=now,
								   hash=hash,
								   redirect=request.values.get("redirect", "/")
								   )
	elif request.values.get("2fa_token", "x"):
		now = int(time.time())

		if now - int(request.values.get("time")) > 600:
			return redirect('/login')

		formhash = request.values.get("hash")
		if not validate_hash(f"{account.id}+{request.values.get('time')}+2fachallenge",
							 formhash
							 ):
			return redirect("/login")

		if not account.validate_2fa(request.values.get("2fa_token", "").strip()):
			hash = generate_hash(f"{account.id}+{time}+2fachallenge")
			return render_template(f"{template}login_2fa.html",
								   v=account,
								   time=now,
								   hash=hash,
								   failed=True,
								   )

	else:
		abort(400)

	session["user_id"] = account.id
	session["logged_in"] = account.id
	session["session_id"] = token_hex(16)
	session["login_nonce"] = account.login_nonce
	session.permanent = True

	if account.id not in (PW1_ID,PW2_ID): check_for_alts(account.id)


	redir = request.values.get("redirect", "/").replace("/logged_out", "").strip()

	g.db.commit()

	return redirect(redir)


@app.get("/me")
@app.get("/@me")
@auth_required
def me(v):
	if request.headers.get("Authorization"): return v.json
	else: return redirect(v.url)


@app.post("/logout")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def logout(v):

	session.pop("user_id", None)
	session.pop("session_id", None)
	session.pop("logged_in", None)

	return {"message": "Logout successful!"}


@app.get("/signup")
@auth_desired
def sign_up_get(v):
	with open('disablesignups', 'r') as f:
		if f.read() == "yes": return "New account registration is currently closed. Please come back later.", 403

	if v: return redirect("/")

	agent = request.headers.get("User-Agent", None)
	if not agent: abort(403)

	ref = request.values.get("ref", None)
	if ref:
		ref_user = g.db.query(User).filter(User.username.ilike(ref)).first()

	else:
		ref_user = None

	if ref_user and (ref_user.id in session.get("history", [])):
		if v and v.oldsite: template = ''
		else: template = 'CHRISTMAS/'
		return render_template(f"{template}sign_up_failed_ref.html")

	now = int(time.time())
	token = token_hex(16)
	session["signup_token"] = token

	formkey_hashstr = str(now) + token + agent

	formkey = hmac.new(key=bytes(environ.get("MASTER_KEY"), "utf-16"),
					   msg=bytes(formkey_hashstr, "utf-16"),
					   digestmod='md5'
					   ).hexdigest()

	redir = request.values.get("redirect", "/").replace("/logged_out", "").strip()

	error = request.values.get("error", None)

	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}sign_up.html",
						   formkey=formkey,
						   now=now,
						   redirect=redir,
						   ref_user=ref_user,
						   error=error,
						   hcaptcha=app.config["HCAPTCHA_SITEKEY"]
						   )


@app.post("/signup")
@limiter.limit("1/second")
@limiter.limit("5/day")
@auth_desired
def sign_up_post(v):
	with open('disablesignups', 'r') as f:
		if f.read() == "yes": return "New account registration is currently closed. Please come back later.", 403

	if v: abort(403)

	agent = request.headers.get("User-Agent", None)
	if not agent: abort(403)

	form_timestamp = request.values.get("now", '0')
	form_formkey = request.values.get("formkey", "none")

	submitted_token = session.get("signup_token", "")
	if not submitted_token: abort(400)

	correct_formkey_hashstr = form_timestamp + submitted_token + agent

	correct_formkey = hmac.new(key=bytes(environ.get("MASTER_KEY"), "utf-16"),
								msg=bytes(correct_formkey_hashstr, "utf-16"),
								digestmod='md5'
							   ).hexdigest()

	now = int(time.time())

	username = request.values.get("username").strip()

	def new_signup(error):

		args = {"error": error}
		if request.values.get("referred_by"):
			user = g.db.query(User).filter_by(
				id=request.values.get("referred_by")).first()
			if user:
				args["ref"] = user.username

		return redirect(f"/signup?{urlencode(args)}")

	if now - int(form_timestamp) < 5:
		return new_signup("There was a problem. Please try again.")

	if not hmac.compare_digest(correct_formkey, form_formkey):
		return new_signup("There was a problem. Please try again.")

	if not request.values.get(
			"password") == request.values.get("password_confirm"):
		return new_signup("Passwords did not match. Please try again.")

	if not re.fullmatch(valid_username_regex, username):
		return new_signup("Invalid username")

	if not re.fullmatch(valid_password_regex, request.values.get("password")):
		return new_signup("Password must be between 8 and 100 characters.")

	email = request.values.get("email")
	email = email.strip()

	if email.endswith("@gmail.com"):
		email=email.split('@')[0]
		email=email.split('+')[0]
		email=email.replace('.','').replace('_','')
		email=f"{email}@gmail.com"

	if not email: email = None

	existing_account = get_user(username, graceful=True)
	if existing_account and existing_account.reserved:
		return redirect(existing_account.url)

	if existing_account: return new_signup("An account with that username already exists.")

	if app.config.get("HCAPTCHA_SITEKEY"):
		token = request.values.get("h-captcha-response")
		if not token:
			return new_signup("Unable to verify captcha [1].")

		data = {"secret": app.config["HCAPTCHA_SECRET"],
				"response": token,
				"sitekey": app.config["HCAPTCHA_SITEKEY"]}
		url = "https://hcaptcha.com/siteverify"

		x = requests.post(url, data=data, timeout=5)

		if not x.json()["success"]:
			return new_signup("Unable to verify captcha [2].")

	session.pop("signup_token")

	ref_id = int(request.values.get("referred_by", 0))

	# if ref_id:
	# 	ref_user = g.db.query(User).filter_by(id=ref_id).first()

	# 	if ref_user:
	# 		badge_types = g.db.query(BadgeDef).filter(BadgeDef.qualification_expr.isnot(None)).all()
	# 		for badge in badge_types:
	# 			if eval(badge.qualification_expr, {}, {'v': ref_user}):
	# 				if not ref_user.has_badge(badge.id):
	# 					new_badge = Badge(user_id=ref_user.id, badge_id=badge.id)
	# 					g.db.add(new_badge)
	# 			else:
	# 				bad_badge = ref_user.has_badge(badge.id)
	# 				if bad_badge: g.db.delete(bad_badge)

	# 		g.db.add(ref_user)

	id_1 = g.db.query(User.id).filter_by(id=7).count()
	users_count = g.db.query(User.id).count()
	if id_1 == 0 and users_count < 7: admin_level=3
	else: admin_level=0

	new_user = User(
		username=username,
		original_username = username,
		admin_level = admin_level,
		password=request.values.get("password"),
		email=email,
		created_utc=int(time.time()),
		referred_by=ref_id or None,
		ban_evade =  int(any([(x.is_banned or x.shadowbanned) and not x.unban_utc for x in g.db.query(User).filter(User.id.in_(tuple(session.get("history", [])))).all() if x])),
		agendaposter = any([x.agendaposter for x in g.db.query(User).filter(User.id.in_(tuple(session.get("history", [])))).all() if x]),
		club_banned=any([x.club_banned for x in g.db.query(User).filter(User.id.in_(tuple(session.get("history", [])))).all() if x])
		)

	g.db.add(new_user)
	g.db.flush()


	check_for_alts(new_user.id)

	if email: send_verification_email(new_user)

	if "rama" in request.host: send_notification(new_user.id, WELCOME_MSG)

	session["user_id"] = new_user.id
	session["logged_in"] = new_user.id
	session["session_id"] = token_hex(16)

	g.db.commit()

	return redirect("/")


@app.get("/forgot")
def get_forgot():
	return render_template(f"forgot_password.html")


@app.post("/forgot")
@limiter.limit("1/second")
def post_forgot():

	username = request.values.get("username").lstrip('@')
	email = request.values.get("email",'').strip()

	email=email.replace("_","\_")

	user = g.db.query(User).filter(
		User.username.ilike(username),
		User.email.ilike(email)).first()

	if not user and email.endswith("@gmail.com"):
		email=email.split('@')[0]
		email=email.split('+')[0]
		email=email.replace('.','').replace('_','')
		email=f"{email}@gmail.com"
		user = g.db.query(User).filter(
			User.username.ilike(username),
			User.email.ilike(email)).first()

	if user:
		now = int(time.time())
		token = generate_hash(f"{user.id}+{now}+forgot+{user.login_nonce}")
		url = f"https://{app.config['SERVER_NAME']}/reset?id={user.id}&time={now}&token={token}"

		send_mail(to_address=user.email,
				  subject="Password Reset Request",
				  html=render_template("email/password_reset.html",
									   action_url=url,
									   v=user)
				  )

	return render_template(f"forgot_password.html",
						   msg="If the username and email matches an account, you will be sent a password reset email. You have ten minutes to complete the password reset process.")


@app.get("/reset")
def get_reset():

	user_id = request.values.get("id")
	timestamp = int(request.values.get("time",0))
	token = request.values.get("token")

	now = int(time.time())

	if now - timestamp > 600:
		return render_template(f"message.html", 
			title="Password reset link expired",
			error="That password reset link has expired.")

	user = g.db.query(User).filter_by(id=user_id).first()

	if not validate_hash(f"{user_id}+{timestamp}+forgot+{user.login_nonce}", token):
		abort(400)

	if not user:
		abort(404)

	reset_token = generate_hash(f"{user.id}+{timestamp}+reset+{user.login_nonce}")

	return render_template(f"reset_password.html",
						   v=user,
						   token=reset_token,
						   time=timestamp,
						   )


@app.post("/reset")
@limiter.limit("1/second")
@auth_desired
def post_reset(v):
	if v: return redirect('/')

	user_id = request.values.get("user_id")

	if user_id in (PW1_ID,PW2_ID): abort(403)
	timestamp = int(request.values.get("time"))
	token = request.values.get("token")

	password = request.values.get("password")
	confirm_password = request.values.get("confirm_password")

	now = int(time.time())

	if now - timestamp > 600:
		if v and v.oldsite: template = ''
		else: template = 'CHRISTMAS/'
		return render_template(f"{template}message.html",
							   title="Password reset expired",
							   error="That password reset form has expired.")

	user = g.db.query(User).filter_by(id=user_id).first()

	if not validate_hash(f"{user_id}+{timestamp}+reset+{user.login_nonce}", token):
		abort(400)
	if not user:
		abort(404)

	if not password == confirm_password:
		if v and v.oldsite: template = ''
		else: template = 'CHRISTMAS/'
		return render_template(f"{template}reset_password.html",
							   v=user,
							   token=token,
							   time=timestamp,
							   error="Passwords didn't match.")

	user.passhash = hash_password(password)
	g.db.add(user)

	g.db.commit()

	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}message_success.html",
						   title="Password reset successful!",
						   message="Login normally to access your account.")

@app.get("/lost_2fa")
@auth_desired
def lost_2fa(v):

	return render_template(
		"lost_2fa.html",
		v=v
		)

@app.post("/request_2fa_disable")
@limiter.limit("1/second")
@limiter.limit("6/minute")
def request_2fa_disable():

	username=request.values.get("username")
	user=get_user(username, graceful=True)
	if not user or not user.email or not user.mfa_secret:
		return render_template(f"message.html",
						   title="Removal request received",
						   message="If username, password, and email match, we will send you an email.")


	email=request.values.get("email")
	if email != user.email and email.endswith("@gmail.com"):
		email=email.split('@')[0]
		email=email.split('+')[0]
		email=email.replace('.','').replace('_','')
		email=f"{email}@gmail.com"
		if email != user.email:
			return render_template(f"message.html",
							title="Removal request received",
							message="If username, password, and email match, we will send you an email.")


	password =request.values.get("password")
	if not user.verifyPass(password):
		return render_template(f"message.html",
						   title="Removal request received",
						   message="If username, password, and email match, we will send you an email.")

	valid=int(time.time())
	token=generate_hash(f"{user.id}+{user.username}+disable2fa+{valid}+{user.mfa_secret}+{user.login_nonce}")

	action_url=f"https://{app.config['SERVER_NAME']}/reset_2fa?id={user.id}&t={valid}&token={token}"
	
	send_mail(to_address=user.email,
			  subject="2FA Removal Request",
			  html=render_template("email/2fa_remove.html",
								   action_url=action_url,
								   v=user)
			  )

	return render_template(f"message.html",
						   title="Removal request received",
						   message="If username, password, and email match, we will send you an email.")

@app.get("/reset_2fa")
def reset_2fa():

	now=int(time.time())
	t=int(request.values.get("t"))

	if now > t+3600*24:
		return render_template(f"message.html",
						   title="Expired Link",
						   error="That link has expired.")

	token=request.values.get("token")
	uid=request.values.get("id")

	user=get_account(uid)

	if not validate_hash(f"{user.id}+{user.username}+disable2fa+{t}+{user.mfa_secret}+{user.login_nonce}", token):
		abort(403)

	user.mfa_secret=None

	g.db.add(user)

	g.db.commit()

	return render_template(f"message_success.html",
						   title="Two-factor authentication removed.",
						   message="Login normally to access your account.")
