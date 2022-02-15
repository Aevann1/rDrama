from .get import *
from .alerts import *
from files.helpers.const import *
from files.__main__ import db_session
from random import randint

def get_logged_in_user():
	if not (hasattr(g, 'db') and g.db): g.db = db_session()

	token = request.headers.get("Authorization","").strip()
	if token:
		client = g.db.query(ClientAuth).filter(ClientAuth.access_token == token).one_or_none()

		if not client: return None

		v = client.user
		v.client = client
	else:
		lo_user = session.get("lo_user")
		if not lo_user: return None

		nonce = session.get("login_nonce", 0)
		id = int(lo_user)
		v = g.db.query(User).filter_by(id=id).one_or_none()
		if not v or nonce < v.login_nonce: return None

		if v.id != id: abort(400)
		v.client = None

		if request.method != "GET":
			submitted_key = request.values.get("formkey")
			if not submitted_key: abort(401)
			elif not v.validate_formkey(submitted_key): abort(401)

	return v

def check_ban_evade(v):
	if v and not v.patron and v.admin_level == 0 and v.ban_evade and not v.unban_utc:
		if randint(0,30) < v.ban_evade: v.shadowbanned = "AutoJanny"
		else: v.ban_evade +=1
		g.db.add(v)
		g.db.commit()

def auth_desired(f):
	def wrapper(*args, **kwargs):

		v = get_logged_in_user()

		check_ban_evade(v)

		g.v = v
		return make_response(f(*args, v=v, **kwargs))

	wrapper.__name__ = f.__name__
	return wrapper


def auth_required(f):

	def wrapper(*args, **kwargs):

		v = get_logged_in_user()
		if not v: abort(401)

		check_ban_evade(v)

		g.v = v
		return make_response(f(*args, v=v, **kwargs))

	wrapper.__name__ = f.__name__
	return wrapper


def is_not_permabanned(f):

	def wrapper(*args, **kwargs):

		v = get_logged_in_user()

		if not v: abort(401)
		
		check_ban_evade(v)

		if v.is_banned and v.unban_utc == 0:
			return {"error": "Interal server error"}, 500

		g.v = v
		return make_response(f(*args, v=v, **kwargs))

	wrapper.__name__ = f.__name__
	return wrapper


def admin_level_required(x):

	def wrapper_maker(f):

		def wrapper(*args, **kwargs):

			v = get_logged_in_user()

			if not v: abort(401)

			if v.admin_level < x: abort(403)
			
			g.v = v
			return make_response(f(*args, v=v, **kwargs))

		wrapper.__name__ = f.__name__
		return wrapper

	return wrapper_maker