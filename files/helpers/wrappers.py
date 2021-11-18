from .get import *
from .alerts import send_notification
from files.helpers.const import *


def get_logged_in_user():

	if request.headers.get("Authorization"):
		token = request.headers.get("Authorization")
		if not token: return None

		try:
			client = g.db.query(ClientAuth).filter(ClientAuth.access_token == token).first()
			x = (client.user, client) if client else (None, None)
		except: x = (None, None)


	else:

		uid = session.get("user_id")
		nonce = session.get("login_nonce", 0)
		if not uid: x= (None, None)
		try:
			if g.db: v = g.db.query(User).filter_by(id=uid).first()
			else: v = None
		except: v = None

		if v and (nonce < v.login_nonce):
			x= (None, None)
		else:
			x=(v, None)


	if x[0]: x[0].client=x[1]

	return x[0]

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

		g.v = v

		resp = make_response(f(*args, v=v, **kwargs))
		return resp

	wrapper.__name__ = f.__name__
	return wrapper


def is_not_banned(f):

	def wrapper(*args, **kwargs):

		v = get_logged_in_user()

		if not v: abort(401)
			
		check_ban_evade(v)

		if v.is_suspended: abort(403)

		g.v = v

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

			g.v = v

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