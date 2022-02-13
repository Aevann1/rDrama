from files.helpers.wrappers import *
from files.helpers.alerts import *
from files.helpers.get import *
from files.helpers.const import *
from files.classes import *
from flask import *
from files.__main__ import app, limiter

@app.get("/authorize")
@auth_required
def authorize_prompt(v):
	client_id = request.values.get("client_id")
	application = g.db.query(OauthApp).filter_by(client_id=client_id).one_or_none()
	if not application: return {"oauth_error": "Invalid `client_id`"}, 401
	return render_template("oauth.html", v=v, application=application)


@app.post("/authorize")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def authorize(v):

	client_id = request.values.get("client_id")
	application = g.db.query(OauthApp).filter_by(client_id=client_id).one_or_none()
	if not application: return {"oauth_error": "Invalid `client_id`"}, 401
	access_token = secrets.token_urlsafe(128)[:128]
	new_auth = ClientAuth(oauth_client = application.id, user_id = v.id, access_token=access_token)

	g.db.add(new_auth)

	g.db.commit()

	return redirect(f"{application.redirect_uri}?token={access_token}")


@app.post("/api_keys")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@is_not_permabanned
def request_api_keys(v):

	new_app = OauthApp(
		app_name=request.values.get('name').replace('<','').replace('>',''),
		redirect_uri=request.values.get('redirect_uri'),
		author_id=v.id,
		description=request.values.get("description")[:256]
	)

	g.db.add(new_app)

	body = f"{v.username} has requested API keys for `{request.values.get('name')}`. You can approve or deny the request [here](/admin/apps)."

	body_html = sanitize(body, noimages=True)

	send_admin(NOTIFICATIONS_ID, body_html)

	g.db.commit()

	return redirect(f'{SITE_FULL}/settings/apps')


@app.post("/delete_app/<aid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def delete_oauth_app(v, aid):

	aid = int(aid)
	app = g.db.query(OauthApp).filter_by(id=aid).one_or_none()

	if app.author_id != v.id: abort(403)

	for auth in g.db.query(ClientAuth).filter_by(oauth_client=app.id).all():
		g.db.delete(auth)

	g.db.delete(app)

	g.db.commit()

	return redirect(f'{SITE_FULL}/apps')


@app.post("/edit_app/<aid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@is_not_permabanned
def edit_oauth_app(v, aid):

	aid = int(aid)
	app = g.db.query(OauthApp).filter_by(id=aid).one_or_none()

	if app.author_id != v.id: abort(403)

	app.redirect_uri = request.values.get('redirect_uri')
	app.app_name = request.values.get('name')
	app.description = request.values.get("description")[:256]

	g.db.add(app)

	g.db.commit()

	return redirect(f'{SITE_FULL}/settings/apps')


@app.post("/admin/app/approve/<aid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(3)
def admin_app_approve(v, aid):

	app = g.db.query(OauthApp).filter_by(id=aid).one_or_none()
	user = app.author

	app.client_id = secrets.token_urlsafe(64)[:64]
	g.db.add(app)

	access_token = secrets.token_urlsafe(128)[:128]
	new_auth = ClientAuth(
		oauth_client = app.id,
		user_id = user.id,
		access_token=access_token
	)

	g.db.add(new_auth)

	send_repeatable_notification(user.id, f"Your application `{app.app_name}` has been approved. Here's your access token: `{access_token}`\nPlease check the guide [here](/api) if you don't know what to do next.")

	ma = ModAction(
		kind="approve_app",
		user_id=v.id,
		target_user_id=user.id,
	)
	g.db.add(ma)

	g.db.commit()

	return {"message": "Application approved"}


@app.post("/admin/app/revoke/<aid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def admin_app_revoke(v, aid):

	app = g.db.query(OauthApp).filter_by(id=aid).one_or_none()
	if app.id:
		for auth in g.db.query(ClientAuth).filter_by(oauth_client=app.id).all(): g.db.delete(auth)

		send_repeatable_notification(app.author.id, f"Your application `{app.app_name}` has been revoked.")

		g.db.delete(app)

		ma = ModAction(
			kind="revoke_app",
			user_id=v.id,
			target_user_id=app.author.id,
		)
		g.db.add(ma)

		g.db.commit()

	return {"message": "App revoked"}


@app.post("/admin/app/reject/<aid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def admin_app_reject(v, aid):

	app = g.db.query(OauthApp).filter_by(id=aid).one_or_none()

	for auth in g.db.query(ClientAuth).filter_by(oauth_client=app.id).all(): g.db.delete(auth)

	send_repeatable_notification(app.author.id, f"Your application `{app.app_name}` has been rejected.")

	g.db.delete(app)

	ma = ModAction(
		kind="reject_app",
		user_id=v.id,
		target_user_id=app.author.id,
	)
	g.db.add(ma)

	g.db.commit()

	return {"message": "App rejected"}


@app.get("/admin/app/<aid>")
@admin_level_required(2)
def admin_app_id(v, aid):

	aid=aid

	oauth = g.db.query(OauthApp).filter_by(id=aid).one_or_none()

	pids=oauth.idlist(page=int(request.values.get("page",1)))

	next_exists=len(pids)==101
	pids=pids[:100]

	posts=get_posts(pids, v=v)

	return render_template("admin/app.html",
						   v=v,
						   app=oauth,
						   listing=posts,
						   next_exists=next_exists
						   )

@app.get("/admin/app/<aid>/comments")
@admin_level_required(2)
def admin_app_id_comments(v, aid):

	aid=aid

	oauth = g.db.query(OauthApp).filter_by(id=aid).one_or_none()

	cids=oauth.comments_idlist(page=int(request.values.get("page",1)),
		)

	next_exists=len(cids)==101
	cids=cids[:100]

	comments=get_comments(cids, v=v)


	return render_template("admin/app.html",
						   v=v,
						   app=oauth,
						   comments=comments,
						   next_exists=next_exists,
						   standalone=True
						   )


@app.get("/admin/apps")
@admin_level_required(2)
def admin_apps_list(v):

	apps = g.db.query(OauthApp).order_by(OauthApp.id.desc()).all()

	return render_template("admin/apps.html", v=v, apps=apps)


@app.post("/oauth/reroll/<aid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def reroll_oauth_tokens(aid, v):

	aid = aid

	a = g.db.query(OauthApp).filter_by(id=aid).one_or_none()

	if a.author_id != v.id: abort(403)

	a.client_id = secrets.token_urlsafe(64)[:64]
	g.db.add(a)

	g.db.commit()

	return {"message": "Client ID Rerolled", "id": a.client_id}
