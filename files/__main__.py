import gevent.monkey
gevent.monkey.patch_all()

from os import environ
import secrets
from flask import *
from flask_caching import Cache
from flask_limiter import Limiter
from flask_compress import Compress
from flask_limiter.util import get_ipaddr

from flaskext.markdown import Markdown
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, scoped_session, Query as _Query
from sqlalchemy import *
from sqlalchemy.pool import QueuePool
import redis
import gevent

from redis import ConnectionPool

from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__,
			template_folder='./templates',
			static_folder='./static'
			)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=3)
app.url_map.strict_slashes = False

app.config["SITE_NAME"]=environ.get("SITE_NAME").strip()
app.config["COINS_NAME"]=environ.get("COINS_NAME").strip()
app.config["GUMROAD_LINK"]=environ.get("GUMROAD_LINK", "https://marsey1.gumroad.com/l/tfcvri").strip()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DATABASE_URL'] = environ.get("DATABASE_CONNECTION_POOL_URL",environ.get("DATABASE_URL"))

app.config['SECRET_KEY'] = environ.get('MASTER_KEY')
app.config["SERVER_NAME"] = environ.get("DOMAIN").strip()
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400

app.config["SESSION_COOKIE_NAME"] = "session_" + environ.get("SITE_NAME").strip().lower()
app.config["VERSION"] = "1.0.0"
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
app.config["SESSION_COOKIE_SECURE"] = bool(int(environ.get("FORCE_HTTPS", 1)))
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 365
app.config["SESSION_REFRESH_EACH_REQUEST"] = True

app.config["SLOGAN"] = environ.get("SLOGAN", "").strip()
app.config["DEFAULT_COLOR"] = environ.get("DEFAULT_COLOR", "ff0000").strip()
app.config["DEFAULT_THEME"] = environ.get("DEFAULT_THEME", "light").strip() + "_" + environ.get("DEFAULT_COLOR", "ff0000").strip()

app.config["FORCE_HTTPS"] = int(environ.get("FORCE_HTTPS", 1)) if ("localhost" not in app.config["SERVER_NAME"] and "127.0.0.1" not in app.config["SERVER_NAME"]) else 0

app.jinja_env.cache = {}

app.config["UserAgent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"

if "localhost" in app.config["SERVER_NAME"]:
	app.config["CACHE_TYPE"] = "null"
else:
	app.config["CACHE_TYPE"] = "filesystem"

app.config["CACHE_DIR"] = environ.get("CACHE_DIR", "cache")

# captcha configs
app.config["HCAPTCHA_SITEKEY"] = environ.get("HCAPTCHA_SITEKEY","").strip()
app.config["HCAPTCHA_SECRET"] = environ.get("HCAPTCHA_SECRET","").strip()

# antispam configs
app.config["SPAM_SIMILARITY_THRESHOLD"] = float(environ.get("SPAM_SIMILARITY_THRESHOLD", 0.5))
app.config["SPAM_SIMILAR_COUNT_THRESHOLD"] = int(environ.get("SPAM_SIMILAR_COUNT_THRESHOLD", 5))
app.config["SPAM_URL_SIMILARITY_THRESHOLD"] = float(environ.get("SPAM_URL_SIMILARITY_THRESHOLD", 0.5))
app.config["COMMENT_SPAM_SIMILAR_THRESHOLD"] = float(environ.get("COMMENT_SPAM_SIMILAR_THRESHOLD", 0.5))
app.config["COMMENT_SPAM_COUNT_THRESHOLD"] = int(environ.get("COMMENT_SPAM_COUNT_THRESHOLD", 0.5))

app.config["CACHE_REDIS_URL"] = environ.get("REDIS_URL").strip()
app.config["CACHE_DEFAULT_TIMEOUT"] = 60
app.config["CACHE_KEY_PREFIX"] = "flask_caching_"

app.config["REDIS_POOL_SIZE"] = 10

redispool=ConnectionPool(
	max_connections=app.config["REDIS_POOL_SIZE"],
	host=app.config["CACHE_REDIS_URL"][8:]
	) if app.config["CACHE_TYPE"]=="redis" else None
app.config["CACHE_OPTIONS"]={'connection_pool':redispool} if app.config["CACHE_TYPE"]=="redis" else {}

app.config["READ_ONLY"]=bool(int(environ.get("READ_ONLY", "0")))
app.config["BOT_DISABLE"]=bool(int(environ.get("BOT_DISABLE", False)))


Markdown(app)
cache = Cache(app)
Compress(app)

app.config["RATELIMIT_STORAGE_URL"] = environ.get("REDIS_URL").strip()
app.config["RATELIMIT_KEY_PREFIX"] = "flask_limiting_"
app.config["RATELIMIT_ENABLED"] = True
app.config["RATELIMIT_DEFAULTS_DEDUCT_WHEN"]=lambda:True
app.config["RATELIMIT_DEFAULTS_EXEMPT_WHEN"]=lambda:False
app.config["RATELIMIT_HEADERS_ENABLED"]=True


limiter = Limiter(
	app,
	key_func=get_ipaddr,
	#default_limits=["100/minute"],
	headers_enabled=True,
	strategy="fixed-window"
)

_engine=create_engine(
	app.config['DATABASE_URL'],
	poolclass=QueuePool,
	pool_size=int(environ.get("PG_POOL_SIZE",10)),
	pool_use_lifo=True
)

def retry(f):

	def wrapper(self, *args, **kwargs):
		try:
			return f(self, *args, **kwargs)
		except:
			self.session.rollback()
			return f(self, *args, **kwargs)

	wrapper.__name__=f.__name__
	return wrapper


class RetryingQuery(_Query):

	@retry
	def all(self):
		return super().all()

	@retry
	def count(self):
		return super().count()

	@retry
	def first(self):
		return super().first()

db_session=scoped_session(sessionmaker(bind=_engine, query_cls=RetryingQuery))

Base = declarative_base()


#set the shared redis cache for misc stuff

r=redis.Redis(
	host=app.config["CACHE_REDIS_URL"][8:], 
	decode_responses=True, 
	ssl_cert_reqs=None,
	connection_pool=redispool
	) if app.config["CACHE_REDIS_URL"] else None

local_ban_cache={}

UA_BAN_CACHE_TTL = int(environ.get("UA_BAN_CACHE_TTL", 3600))



# import and bind all routing functions
import files.classes
from files.routes import *
import files.helpers.jinja2

@cache.memoize(UA_BAN_CACHE_TTL)
def get_useragent_ban_response(user_agent_str):
	"""
	Given a user agent string, returns a tuple in the form of:
	(is_user_agent_banned, (insult, status_code))
	"""
	#if request.path.startswith("/socket.io/"):
	#	return False, (None, None)

	result = g.db.query(
		files.classes.Agent).filter(
		files.classes.Agent.kwd.in_(
			user_agent_str.split())).first()
	if result:
		return True, (result.mock or "Follow the robots.txt, dumbass",
					  result.status_code or 418)
	return False, (None, None)

def drop_connection():

	g.db.close()
	gevent.getcurrent().kill()


# enforce https
@app.before_request
def before_request():

	if request.method.lower() != "get" and app.config["READ_ONLY"]:
		return {"error":f"{app.config['SITE_NAME']} is currently in read-only mode."}, 500

	if app.config["BOT_DISABLE"] and request.headers.get("X-User-Type")=="Bot":
		abort(503)

	g.db = db_session()

	g.timestamp = int(time.time())

	#do not access session for static files
	if not request.path.startswith("/assets"):
		session.permanent = True

		if not session.get("session_id"):
			session["session_id"] = secrets.token_hex(16)

	ua_banned, response_tuple = get_useragent_ban_response(
		request.headers.get("User-Agent", "NoAgent"))
	if ua_banned and request.path != "/robots.txt":
		return response_tuple

	if app.config["FORCE_HTTPS"] and request.url.startswith(
			"http://") and "localhost" not in app.config["SERVER_NAME"]:
		url = request.url.replace("http://", "https://", 1)
		return redirect(url, code=301)

	ua=request.headers.get("User-Agent","")
	if "CriOS/" in ua:
		g.system="ios/chrome"
	elif "Version/" in ua:
		g.system="android/webview"
	elif "Mobile Safari/" in ua:
		g.system="android/chrome"
	elif "Safari/" in ua:
		g.system="ios/safari"
	elif "Mobile/" in ua:
		g.system="ios/webview"
	else:
		g.system="other/other"

@app.after_request
def after_request(response):

	try:
		g.db.commit()
		g.db.close()
	except Exception as e:
		g.db.rollback()
		g.db.close()
		print(e)
		abort(500)

	response.headers.add("Strict-Transport-Security", "max-age=31536000")
	response.headers.add("Referrer-Policy", "same-origin")

	response.headers.add("Feature-Policy", "geolocation 'none'; midi 'none'; notifications 'none'; push 'none'; sync-xhr 'none'; microphone 'none'; camera 'none'; magnetometer 'none'; gyroscope 'none'; vibrate 'none'; fullscreen 'none'; payment 'none';")
	response.headers.add("X-Frame-Options", "deny")

	return response
