from random import vonmisesvariate
from sqlalchemy.sql import visitors
from werkzeug.wrappers.response import Response as RespObj
from .get import *
from .alerts import send_notification
from files.__main__ import app
from files.helpers.const import *


def get_logged_in_user():

	if request.headers.get("Authorization"):
		token = request.headers.get("Authorization")
		if not token: return None

		client = g.db.query(ClientAuth).filter(ClientAuth.access_token == token).first()

		x = (client.user, client) if client else (None, None)


	else:

		uid = session.get("user_id")
		nonce = session.get("login_nonce", 0)
		if not uid: x= (None, None)
		v = g.db.query(User).filter_by(id=uid).first()

		if v and v.agendaposter_expires_utc and v.agendaposter_expires_utc < g.timestamp:
			v.agendaposter_expires_utc = 0
			v.agendaposter = False

			g.db.add(v)

		if v and (nonce < v.login_nonce):
			x= (None, None)
		else:
			x=(v, None)


	if x[0]: x[0].client=x[1]

	return x[0]


def check_ban_evade(v):

	if not v or not v.ban_evade or v.admin_level > 0:
		return
	
	if random.randint(0,30) < v.ban_evade:
		v.ban(reason="ban evasion")
		send_notification(NOTIFICATIONS_ACCOUNT, v, "Your account has been permanently suspended for the following reason:\n\n> ban evasion")

		for post in g.db.query(Submission).filter_by(author_id=v.id).all():
			if post.is_banned:
				continue

			post.is_banned=True
			post.ban_reason="ban evasion"
			g.db.add(post)

			ma=ModAction(
				kind="ban_post",
				user_id=AUTOJANNY_ACCOUNT,
				target_submission_id=post.id,
				note="ban evasion"
				)
			g.db.add(ma)

		g.db.flush()

		for comment in g.db.query(Comment).filter_by(author_id=v.id).all():
			if comment.is_banned:
				continue

			comment.is_banned=True
			comment.ban_reason="ban evasion"
			g.db.add(comment)

			ma=ModAction(
				kind="ban_comment",
				user_id=AUTOJANNY_ACCOUNT,
				target_comment_id=comment.id,
				note="ban evasion"
				)
			g.db.add(ma)

		g.db.flush()
		try: abort(403)
		except Exception as e: print(e)

	else:
		v.ban_evade +=1
		g.db.add(v)
		g.db.flush()




# Wrappers
def auth_desired(f):
	def wrapper(*args, **kwargs):

		v = get_logged_in_user()
		check_ban_evade(v)

		resp = make_response(f(*args, v=v, **kwargs))
		return resp

	wrapper.__name__ = f.__name__
	return wrapper


def auth_required(f):
	# decorator for any view that requires login (ex. settings)

	def wrapper(*args, **kwargs):

		v = get_logged_in_user()

		if not v:
			abort(401)
			
		check_ban_evade(v)

		g.v = v

		# an ugly hack to make api work
		resp = make_response(f(*args, v=v, **kwargs))
		return resp

	wrapper.__name__ = f.__name__
	return wrapper


def is_not_banned(f):
	# decorator that enforces lack of ban

	def wrapper(*args, **kwargs):

		v = get_logged_in_user()

		if not v:
			abort(401)
			
		check_ban_evade(v)

		if v.is_suspended:
			abort(403)

		g.v = v

		resp = make_response(f(*args, v=v, **kwargs))
		return resp

	wrapper.__name__ = f.__name__
	return wrapper


# this wrapper takes args and is a bit more complicated
def admin_level_required(x):

	def wrapper_maker(f):

		def wrapper(*args, **kwargs):

			v = get_logged_in_user()

			if not v:
				abort(401)

			if v.is_banned:
				abort(403)

			if v.admin_level < x:
				abort(403)

			g.v = v

			response = f(*args, v=v, **kwargs)

			if isinstance(response, tuple):
				resp = make_response(response[0])
			else:
				resp = make_response(response)

			return resp

		wrapper.__name__ = f.__name__
		return wrapper

	return wrapper_maker


def validate_formkey(f):
	"""Always use @auth_required or @admin_level_required above @validate_form"""

	def wrapper(*args, v, **kwargs):

		if not request.headers.get("Authorization"):

			submitted_key = request.values.get("formkey", None)

			if not submitted_key: abort(401)

			elif not v.validate_formkey(submitted_key): abort(401)

		return f(*args, v=v, **kwargs)

	wrapper.__name__ = f.__name__
	return wrapper

def api(*scopes, no_ban=False):

	def wrapper_maker(f):

		def wrapper(*args, **kwargs):

			if request.path.startswith(('/api/v1','/api/v2')):

				v = kwargs.get('v')

				result = f(*args, **kwargs)

				if isinstance(result, dict):
					resp = result['api']()
				else:
					resp = result

				if not isinstance(resp, RespObj):
					resp = make_response(resp)

				return resp

			else:

				result = f(*args, **kwargs)

				if not isinstance(result, dict):
					return result

				try:
					if request.path.startswith('/inpage/'):
						return result['inpage']()
					elif request.path.startswith(('/api/vue/','/test/')):
						return result['api']()
					else:
						return result['html']()
				except KeyError:
					return result

		wrapper.__name__ = f.__name__
		return wrapper

	return wrapper_maker
