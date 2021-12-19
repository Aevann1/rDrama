import gevent.monkey
gevent.monkey.patch_all()
from os import environ
import secrets
from flask import *
from flask_caching import Cache
from flask_limiter import Limiter
from flask_compress import Compress
from flask_limiter.util import get_ipaddr
from flask_mail import Mail

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import *
import gevent
from werkzeug.middleware.proxy_fix import ProxyFix
import redis

app = Flask(__name__, template_folder='templates')

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=3)
app.url_map.strict_slashes = False
app.jinja_env.cache = {}
app.jinja_env.auto_reload = True
import faulthandler
faulthandler.enable()

app.config["SITE_NAME"]=environ.get("SITE_NAME").strip()
app.config["COINS_NAME"]=environ.get("COINS_NAME").strip()
app.config["GUMROAD_LINK"]=environ.get("GUMROAD_LINK", "https://marsey1.gumroad.com/l/tfcvri").strip()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DATABASE_URL'] = environ.get("DATABASE_URL")
app.config['SECRET_KEY'] = environ.get('MASTER_KEY')
app.config["SERVER_NAME"] = environ.get("DOMAIN").strip()
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400
app.config["SESSION_COOKIE_NAME"] = "session_" + environ.get("DOMAIN")
app.config["VERSION"] = "1.0.0"
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
app.config["SESSION_COOKIE_SECURE"] = bool(int(environ.get("FORCE_HTTPS", 1)))
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 365
app.config["SESSION_REFRESH_EACH_REQUEST"] = True
app.config["SLOGAN"] = environ.get("SLOGAN", "").strip()
app.config["DEFAULT_COLOR"] = environ.get("DEFAULT_COLOR", "ff0000").strip()
app.config["DEFAULT_THEME"] = environ.get("DEFAULT_THEME", "midnight").strip()
app.config["FORCE_HTTPS"] = int(environ.get("FORCE_HTTPS", 1)) if ("localhost" not in app.config["SERVER_NAME"] and "localhost" not in app.config["SERVER_NAME"]) else 0
app.config["UserAgent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
app.config["HCAPTCHA_SITEKEY"] = environ.get("HCAPTCHA_SITEKEY","").strip()
app.config["HCAPTCHA_SECRET"] = environ.get("HCAPTCHA_SECRET","").strip()
app.config["SPAM_SIMILARITY_THRESHOLD"] = float(environ.get("SPAM_SIMILARITY_THRESHOLD", 0.5))
app.config["SPAM_SIMILAR_COUNT_THRESHOLD"] = int(environ.get("SPAM_SIMILAR_COUNT_THRESHOLD", 5))
app.config["SPAM_URL_SIMILARITY_THRESHOLD"] = float(environ.get("SPAM_URL_SIMILARITY_THRESHOLD", 0.5))
app.config["COMMENT_SPAM_SIMILAR_THRESHOLD"] = float(environ.get("COMMENT_SPAM_SIMILAR_THRESHOLD", 0.5))
app.config["COMMENT_SPAM_COUNT_THRESHOLD"] = int(environ.get("COMMENT_SPAM_COUNT_THRESHOLD", 0.5))
app.config["READ_ONLY"]=bool(int(environ.get("READ_ONLY", "0")))
app.config["BOT_DISABLE"]=bool(int(environ.get("BOT_DISABLE", False)))
app.config["RATELIMIT_KEY_PREFIX"] = "flask_limiting_"
app.config["RATELIMIT_ENABLED"] = True
app.config["RATELIMIT_DEFAULTS_DEDUCT_WHEN"]=lambda:True
app.config["RATELIMIT_DEFAULTS_EXEMPT_WHEN"]=lambda:False
app.config["RATELIMIT_HEADERS_ENABLED"]=True
app.config["CACHE_TYPE"] = "filesystem"
app.config["CACHE_DIR"] = "cache"
app.config["RATELIMIT_STORAGE_URL"] = environ.get("REDIS_URL", "redis://localhost")
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = environ.get("MAIL_USERNAME", "").strip()
app.config['MAIL_PASSWORD'] = environ.get("MAIL_PASSWORD", "").strip()

r=redis.Redis(host=environ.get("REDIS_URL", "redis://localhost"),  decode_responses=True, ssl_cert_reqs=None)

limiter = Limiter(
	app,
	key_func=get_ipaddr,
	default_limits=["3/second;30/minute;100/hour"],
	headers_enabled=True,
	strategy="fixed-window"
)

Base = declarative_base()

engine = create_engine(app.config['DATABASE_URL'])

db_session = scoped_session(sessionmaker(bind=engine, autoflush=False))

cache = Cache(app)
Compress(app)
mail = Mail(app)

@app.before_request
def before_request():

	if request.method.lower() != "get" and app.config["READ_ONLY"]: return {"error":f"{app.config['SITE_NAME']} is currently in read-only mode."}, 500

	if app.config["BOT_DISABLE"] and request.headers.get("Authorization"): abort(503)

	g.db = db_session()

	g.timestamp = int(time.time())

	if not request.path.startswith("/assets") and not request.path.startswith("/images") and not request.path.startswith("/hostedimages"):
		session.permanent = True
		if not session.get("session_id"): session["session_id"] = secrets.token_hex(16)

	if app.config["FORCE_HTTPS"] and request.url.startswith("http://") and "localhost" not in app.config["SERVER_NAME"]:
		url = request.url.replace("http://", "https://", 1)
		return redirect(url, code=301)

	ua=request.headers.get("User-Agent","")
	if "CriOS/" in ua: g.system="ios/chrome"
	elif "Version/" in ua: g.system="android/webview"
	elif "Mobile Safari/" in ua: g.system="android/chrome"
	elif "Safari/" in ua: g.system="ios/safari"
	elif "Mobile/" in ua: g.system="ios/webview"
	else: g.system="other/other"

@app.get('/tw')
def get_tailwind():
	return render_template('tailwind.html')

@app.teardown_appcontext
def teardown_request(error):
	if hasattr(g, 'db') and g.db:
		g.db.close()

@app.after_request
def after_request(response):

	response.headers.add("Strict-Transport-Security", "max-age=31536000")
	response.headers.add("X-Frame-Options", "deny")
	return response


from files.routes import *