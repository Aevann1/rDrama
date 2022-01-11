from files.helpers.wrappers import *
from flask import *
from urllib.parse import quote, urlencode
import time
from files.__main__ import app, limiter


@app.errorhandler(400)
def error_400(e):
	if request.headers.get("Authorization"): return {"error": "400 Bad Request"}, 400
	else: return render_template('errors/400.html', error=True), 400

@app.errorhandler(401)
def error_401(e):

	path = request.path
	qs = urlencode(dict(request.values))
	argval = quote(f"{path}?{qs}", safe='')
	output = f"/login?redirect={argval}"

	if request.headers.get("Authorization"): return {"error": "401 Not Authorized"}, 401
	else: return redirect(output)


@app.errorhandler(403)
def error_403(e):
	if request.headers.get("Authorization"): return {"error": "403 Forbidden"}, 403
	else: return render_template('errors/403.html', error=True), 403


@app.errorhandler(404)
def error_404(e):
	if request.headers.get("Authorization"): return {"error": "404 Not Found"}, 404
	else: return render_template('errors/404.html', error=True), 404


@app.errorhandler(405)
def error_405(e):
	if request.headers.get("Authorization"): return {"error": "405 Method Not Allowed"}, 405
	else: return render_template('errors/405.html', error=True), 405


@app.errorhandler(429)
def error_429(e):
	if request.headers.get("Authorization"): return {"error": "429 Too Many Requests"}, 429
	else: return render_template('errors/429.html', error=True), 429


@app.errorhandler(500)
def error_500(e):
	g.db.rollback()

	if request.headers.get("Authorization"): return {"error": "500 Internal Server Error"}, 500
	else: return render_template('errors/500.html', error=True), 500


@app.post("/allow_nsfw")
@auth_required
def allow_nsfw(v):
	session["over_18"] = int(time.time()) + 3600
	return redirect(request.values.get("redir", "/"))