from os import environ
import requests
import time
from flask import *
from urllib.parse import quote

from files.helpers.security import *
from files.helpers.wrappers import *
from files.classes import *
from files.__main__ import app

site = environ.get("DOMAIN").strip()
name = environ.get("SITE_NAME").strip()
mailgun_domain = environ.get("MAILGUN_DOMAIN", "").strip()

def send_mail(to_address, subject, html, plaintext=None, files={},
			  from_address=f"{name} <noreply@mail.{site}>"):

	url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

	data = {"from": from_address,
			"to": [to_address],
			"subject": subject,
			"text": plaintext,
			"html": html,
			}

	return requests.post(url,
						 auth=(
							 "api", environ.get("MAILGUN_KEY").strip()),
						 data=data,
						 files=[("attachment", (k, files[k])) for k in files]
						 )


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
@auth_required
def api_verify_email(v):

	send_verification_email(v)

	return "", 204


@app.get("/activate")
@auth_desired
def activate(v):

	email = request.args.get("email", "")
	id = request.args.get("id", "")
	timestamp = int(request.args.get("time", "0"))
	token = request.args.get("token", "")

	if int(time.time()) - timestamp > 3600:
		return render_template("message.html", v=v, title="Verification link expired.",
							   message="That link has expired. Visit your settings to send yourself another verification email."), 410

	if not validate_hash(f"{email}+{id}+{timestamp}", token):
		abort(403)

	user = g.db.query(User).filter_by(id=id).first()
	if not user:
		abort(404)

	if user.is_activated and user.email == email:
		return render_template("message_success.html", v=v,
							   title="Email already verified.", message="Email already verified."), 404

	user.email = email
	user.is_activated = True

	if not any([b.badge_id == 2 for b in user.badges]):
		mail_badge = Badge(user_id=user.id,
						   badge_id=2)
		g.db.add(mail_badge)

	g.db.add(user)

	return render_template("message_success.html", v=v, title="Email verified.", message=f"Your email {email} has been verified. Thank you.")
