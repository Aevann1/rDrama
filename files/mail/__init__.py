from os import environ
import time
from flask import *
from urllib.parse import quote

from files.helpers.security import *
from files.helpers.wrappers import *
from files.helpers.const import *
from files.classes import *
from files.__main__ import app, mail, limiter
from flask_mail import Message

name = environ.get("SITE_NAME").strip()

def send_mail(to_address, subject, html):

	msg = Message(html=html, subject=subject, sender=f"{name}@{SITE}", recipients=[to_address])
	mail.send(msg)


def send_verification_email(user, email=None):

	if not email:
		email = user.email

	url = f"https://{app.config['SERVER_NAME']}/activate"
	now = int(time.time())

	token = generate_hash(f"{email}+{user.id}+{now}")
	params = f"?email={quote(email)}&id={user.id}&time={now}&token={token}"

	link = url + params

	send_mail(to_address=email,
			  html=render_template("email/email_verify.html",
								   action_url=link,
								   v=user),
			  subject=f"Validate your {name} account email."
			  )


@app.post("/verify_email")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def api_verify_email(v):

	send_verification_email(v)

	return {"message": "Email has been sent (ETA ~5 minutes)"}


@app.get("/activate")
@auth_required
def activate(v):

	email = request.values.get("email", "").strip().lower()

	if not email_regex.fullmatch(email):
		return render_template("message.html", v=v, title="Invalid email.", error="Invalid email."), 400


	id = request.values.get("id", "").strip()
	timestamp = int(request.values.get("time", "0"))
	token = request.values.get("token", "").strip()

	if int(time.time()) - timestamp > 3600:
		return render_template("message.html", v=v, title="Verification link expired.",
							   message="That link has expired. Visit your settings to send yourself another verification email."), 410

	if not validate_hash(f"{email}+{id}+{timestamp}", token):
		abort(403)

	user = g.db.query(User).filter_by(id=id).one_or_none()
	if not user:
		abort(404)

	if user.is_activated and user.email == email:
		return render_template("message_success.html", v=v, title="Email already verified.", message="Email already verified."), 404

	user.email = email
	user.is_activated = True

	if not any(b.badge_id == 2 for b in user.badges):
		mail_badge = Badge(user_id=user.id, badge_id=2)
		g.db.add(mail_badge)
		g.db.flush()
		send_notification(user.id, f"@AutoJanny has given you the following profile badge:\n\n![]({mail_badge.path})\n\n{mail_badge.name}")


	g.db.add(user)
	g.db.commit()

	return render_template("message_success.html", v=v, title="Email verified.", message=f"Your email {email} has been verified. Thank you.")
