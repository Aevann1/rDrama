from .get import *
from .alerts import send_notification
from files.helpers.const import *


def get_logged_in_user():
	token = request.headers.get("Authorization")

	if token:
		client = g.db.query(ClientAuth).filter(ClientAuth.access_token == token).first()
		if not client: return None

		v = client.user
		v.client = client
		return v
	else:
		uid = session.get("user_id")
		nonce = session.get("login_nonce", 0)
		logged_in = session.get("logged_in")

		if not uid or not logged_in or uid != logged_in: return None

		try:
			if g.db: v = g.db.query(User).filter_by(id=uid).one_or_none()
			else: return None
		except: return None

		if not v or nonce < v.login_nonce: return None

		v.client = None
		return v

def check_ban_evade(v):
	if v and v.ban_evade and v.admin_level == 0 and not v.is_suspended:
		if random.randint(0,30) < v.ban_evade: v.shadowbanned = "AutoJanny"
		else: v.ban_evade +=1
		g.db.add(v)
		g.db.commit()

def auth_desired(f):
	def wrapper(*args, **kwargs):

		v = get_logged_in_user()

		check_ban_evade(v)

		resp = make_response(f(*args, v=v, **kwargs))
		return resp

	wrapper.__name__ = f.__name__
	return wrapper


def auth_required(f):

	def wrapper(*args, **kwargs):

		v = get_logged_in_user()

		if not v: abort(401)

		check_ban_evade(v)

		resp = make_response(f(*args, v=v, **kwargs))
		return resp

	wrapper.__name__ = f.__name__
	return wrapper


def is_not_banned(f):

	def wrapper(*args, **kwargs):

		v = get_logged_in_user()

		if not v: abort(401)
			
		check_ban_evade(v)

		if v.is_suspended: return {"error": "You can't perform this action while being banned."}, 403

		resp = make_response(f(*args, v=v, **kwargs))
		return resp

	wrapper.__name__ = f.__name__
	return wrapper


def admin_level_required(x):

	def wrapper_maker(f):

		def wrapper(*args, **kwargs):

			v = get_logged_in_user()

			if not v: abort(401)

			if v.admin_level < x: abort(403)

			response = f(*args, v=v, **kwargs)

			if isinstance(response, tuple): resp = make_response(response[0])
			else: resp = make_response(response)

			return resp

		wrapper.__name__ = f.__name__
		return wrapper

	return wrapper_maker


def validate_formkey(f):
	def wrapper(*args, v, **kwargs):

		if not request.headers.get("Authorization"):

			submitted_key = request.values.get("formkey", None)

			if not submitted_key: abort(401)

			elif not v.validate_formkey(submitted_key): abort(401)

		return f(*args, v=v, **kwargs)

	wrapper.__name__ = f.__name__
	return wrapper