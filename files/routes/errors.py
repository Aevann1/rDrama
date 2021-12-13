import jinja2.exceptions

from files.helpers.wrappers import *
from files.helpers.session import *
from flask import *
from urllib.parse import quote, urlencode
import time
from files.__main__ import app, limiter

# Errors



@app.errorhandler(400)
@admin_level_required(2)
def error_400(e, v):
	if request.headers.get("Authorization"): return {"error": "400 Bad Request"}, 400
	else: return render_template('errors/400.html', v=v), 400

@app.errorhandler(401)
def error_401(e):

	path = request.path
	qs = urlencode(dict(request.values))
	argval = quote(f"{path}?{qs}", safe='')
	output = f"/login?redirect={argval}"

	if request.headers.get("Authorization"): return {"error": "401 Not Authorized"}, 401
	else: return redirect(output)


@app.errorhandler(403)
@admin_level_required(2)
def error_403(e, v):
	if request.headers.get("Authorization"): return {"error": "403 Forbidden"}, 403
	else: return render_template('errors/403.html', v=v), 403


@app.errorhandler(404)
@admin_level_required(2)
def error_404(e, v):
	if request.headers.get("Authorization"): return {"error": "404 Not Found"}, 404
	else: return render_template('errors/404.html', v=v), 404


@app.errorhandler(405)
@admin_level_required(2)
def error_405(e, v):
	if request.headers.get("Authorization"): return {"error": "405 Method Not Allowed"}, 405
	else: return render_template('errors/405.html', v=v), 405


@app.errorhandler(429)
@admin_level_required(2)
def error_429(e, v):
	if request.headers.get("Authorization"): return {"error": "429 Too Many Requests"}, 429
	else: return render_template('errors/429.html', v=v), 429


@app.errorhandler(500)
@admin_level_required(2)
def error_500(e, v):
	g.db.rollback()

	if request.headers.get("Authorization"): return {"error": "500 Internal Server Error"}, 500
	else: return render_template('errors/500.html', v=v), 500


@app.post("/allow_nsfw")
def allow_nsfw():

	session["over_18"] = int(time.time()) + 3600
	return redirect(request.values.get("redir", "/"))


@app.get("/error/<error>")
@admin_level_required(2)
def error_all_preview(error, v):

	try:
		return render_template(f"errors/{error}.html", v=v)
	except jinja2.exceptions.TemplateNotFound:
		abort(400)

