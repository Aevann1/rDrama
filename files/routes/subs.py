from files.__main__ import app, limiter, mail
from files.helpers.alerts import *
from files.helpers.wrappers import *
from files.classes import *
from .front import frontlist







@app.post("/exile/post/<pid>")
@is_not_permabanned
def exile_post(v, pid):
	try: pid = int(pid)
	except: abort(400)

	p = get_post(pid)
	sub = p.sub
	if not sub: abort(400)

	if not v.mods(sub): abort(403)

	u = p.author

	if u.admin_level < 2 and not u.exiled_from(sub):
		exile = Exile(user_id=u.id, sub=sub, exiler_id=v.id)
		g.db.add(exile)

		send_notification(u.id, f"@{v.username} has exiled you from /s/{sub} for [{p.title}]({p.shortlink})")

		g.db.commit()
	
	return {"message": "User exiled successfully!"}



@app.post("/unexile/post/<pid>")
@is_not_permabanned
def unexile_post(v, pid):
	try: pid = int(pid)
	except: abort(400)

	p = get_post(pid)
	sub = p.sub
	if not sub: abort(400)

	if not v.mods(sub): abort(403)

	u = p.author

	if u.exiled_from(sub):
		exile = g.db.query(Exile).filter_by(user_id=u.id, sub=sub).one_or_none()
		g.db.delete(exile)

		send_notification(u.id, f"@{v.username} has revoked your exile from /s/{sub}")

		g.db.commit()
	
	return {"message": "User unexiled successfully!"}




@app.post("/exile/comment/<cid>")
@is_not_permabanned
def exile_comment(v, cid):
	try: cid = int(cid)
	except: abort(400)

	c = get_comment(cid)
	sub = c.post.sub
	if not sub: abort(400)

	if not v.mods(sub): abort(403)

	u = c.author

	if u.admin_level < 2 and not u.exiled_from(sub):
		exile = Exile(user_id=u.id, sub=sub, exiler_id=v.id)
		g.db.add(exile)

		send_notification(u.id, f"@{v.username} has exiled you from /s/{sub} for [{c.permalink}]({c.shortlink})")

		g.db.commit()
	
	return {"message": "User exiled successfully!"}




@app.post("/unexile/comment/<cid>")
@is_not_permabanned
def unexile_comment(v, cid):
	try: cid = int(cid)
	except: abort(400)

	c = get_comment(cid)
	sub = c.post.sub
	if not sub: abort(400)

	if not v.mods(sub): abort(403)

	u = c.author

	if u.exiled_from(sub):
		exile = g.db.query(Exile).filter_by(user_id=u.id, sub=sub).one_or_none()
		g.db.delete(exile)

		send_notification(u.id, f"@{v.username} has revoked your exile from /s/{sub}")

		g.db.commit()
	
	return {"message": "User unexiled successfully!"}






@app.post("/s/<sub>/block")
@auth_required
def block_sub(v, sub):
	sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	if not sub: abort(404)
	sub = sub.name

	# if v.mods(sub): return {"error": "You can't block subs you mod!"}

	existing = g.db.query(SubBlock).filter_by(user_id=v.id, sub=sub).one_or_none()

	if not existing:
		block = SubBlock(user_id=v.id, sub=sub)
		g.db.add(block)
		g.db.commit()
		cache.delete_memoized(frontlist)

	return {"message": "Sub blocked successfully!"}


@app.post("/s/<sub>/unblock")
@auth_required
def unblock_sub(v, sub):
	sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	if not sub: abort(404)
	sub = sub.name

	block = g.db.query(SubBlock).filter_by(user_id=v.id, sub=sub).one_or_none()

	if block:
		g.db.delete(block)
		g.db.commit()
		cache.delete_memoized(frontlist)

	return {"message": "Sub unblocked successfully!"}

@app.get("/s/<sub>/mods")
@auth_required
def mods(v, sub):
	sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	if not sub: abort(404)

	users = g.db.query(User, Mod).join(Mod, Mod.user_id==User.id).filter_by(sub=sub.name).order_by(Mod.created_utc).all()

	return render_template("sub/mods.html", v=v, sub=sub, users=users)


@app.get("/s/<sub>/exilees")
@auth_required
def exilees(v, sub):
	sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	if not sub: abort(404)

	users = g.db.query(User, Exile).join(Exile, Exile.user_id==User.id).filter_by(sub=sub.name).all()

	return render_template("sub/exilees.html", v=v, sub=sub, users=users)


@app.get("/s/<sub>/blockers")
@auth_required
def blockers(v, sub):
	sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	if not sub: abort(404)

	users = g.db.query(User).join(SubBlock, SubBlock.user_id==User.id).filter_by(sub=sub.name).all()

	return render_template("sub/blockers.html", v=v, sub=sub, users=users)



@app.post("/s/<sub>/add_mod")
@limiter.limit("1/second;5/day")
@is_not_permabanned
def add_mod(v, sub):
	sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	if not sub: abort(404)
	sub = sub.name

	if not v.mods(sub): abort(403)

	user = request.values.get('user')

	if not user: abort(400)

	user = get_user(user)

	existing = g.db.query(Mod).filter_by(user_id=user.id, sub=sub).one_or_none()

	if not existing:
		mod = Mod(user_id=user.id, sub=sub)
		g.db.add(mod)

		if v.id != user.id:
			send_repeatable_notification(user.id, f"@{v.username} has added you as a mod to /s/{sub}")

		g.db.commit()
	
	return redirect(f'/s/{sub}/mods')


@app.post("/s/<sub>/remove_mod")
@is_not_permabanned
def remove_mod(v, sub):
	sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	if not sub: abort(404)
	sub = sub.name

	if not v.mods(sub): abort(403)

	uid = request.values.get('uid')

	if not uid: abort(400)

	try: uid = int(uid)
	except: abort(400)

	user = g.db.query(User).filter_by(id=uid).one_or_none()

	if not user: abort(404)

	mod = g.db.query(Mod).filter_by(user_id=user.id, sub=sub).one_or_none()
	if not mod: abort(400)

	if not (v.id == user.id or v.mod_date(sub) and v.mod_date(sub) < mod.created_utc): abort(403)

	g.db.delete(mod)

	if v.id != user.id:
		send_repeatable_notification(user.id, f"@{v.username} has removed you as a mod from /s/{sub}")

	g.db.commit()
	
	return redirect(f'/s/{sub}/mods')

@app.get("/create_sub")
@is_not_permabanned
def create_sub(v):
	if SITE_NAME == 'Drama' and v.id not in (AEVANN_ID, CARP_ID): abort(403)

	if v.id == MENTION_ID: cost = 0
	else:
		num = v.subs_created + 1
		for a in v.alts:
			num += a.subs_created
		cost = num * 100
	
	return render_template("sub/create_sub.html", v=v, cost=cost)


@app.post("/create_sub")
@is_not_permabanned
def create_sub2(v):
	if SITE_NAME == 'Drama' and v.id not in (AEVANN_ID, CARP_ID): abort(403)

	name = request.values.get('name')
	if not name: abort(400)
	name = name.strip().lower()

	if v.id == MENTION_ID: cost = 0
	else:
		num = v.subs_created + 1
		for a in v.alts:
			num += a.subs_created
		cost = num * 100

	if not valid_sub_regex.fullmatch(name):
		return render_template("sub/create_sub.html", v=v, cost=cost, error="Sub name not allowed."), 400

	sub = g.db.query(Sub).filter_by(name=name).one_or_none()
	if not sub:
		if v.coins < cost:
			return render_template("sub/create_sub.html", v=v, cost=cost, error="You don't have enough coins!"), 403

		v.coins -= cost

		v.subs_created += 1
		g.db.add(v)

		sub = Sub(name=name)
		g.db.add(sub)
		g.db.flush()
		mod = Mod(user_id=v.id, sub=sub.name)
		g.db.add(mod)
		g.db.commit()

	return redirect(f'/s/{sub.name}')

@app.post("/kick/<pid>")
@is_not_permabanned
def kick(v, pid):
	try: pid = int(pid)
	except: abort(400)

	post = get_post(pid)

	if not post.sub: abort(403)
	if not v.mods(post.sub): abort(403)

	post.sub = 'general'
	g.db.add(post)
	g.db.commit()

	cache.delete_memoized(frontlist)

	return {"message": "Post kicked successfully!"}


@app.get('/s/<sub>/settings')
@is_not_permabanned
def sub_settings(v, sub):
	sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	if not sub: abort(404)

	if not v.mods(sub.name): abort(403)

	return render_template('sub/settings.html', v=v, sidebar=sub.sidebar, sub=sub)


@app.post('/s/<sub>/sidebar')
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@is_not_permabanned
def post_sub_sidebar(v, sub):
	sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	if not sub: abort(404)
	
	if not v.mods(sub.name): abort(403)

	sub.sidebar = request.values.get('sidebar', '').strip()[:500]
	sub.sidebar_html = sanitize(sub.sidebar)
	if len(sub.sidebar_html) > 1000: return "Sidebar is too big!"

	g.db.add(sub)

	g.db.commit()

	return redirect(f'/s/{sub.name}/settings')


@app.post('/s/<sub>/css')
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@is_not_permabanned
def post_sub_css(v, sub):
	sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	if not sub: abort(404)
	
	if not v.mods(sub.name): abort(403)

	sub.css = request.values.get('css', '').strip()
	g.db.add(sub)

	g.db.commit()

	return redirect(f'/s/{sub.name}/settings')


@app.get("/s/<sub>/css")
def get_sub_css(sub):
	sub = g.db.query(Sub).filter_by(name=sub.strip().lower()).one_or_none()
	if not sub: abort(404)
	resp=make_response(sub.css or "")
	resp.headers.add("Content-Type", "text/css")
	return resp


@app.post("/s/<sub>/banner")
@limiter.limit("1/second;10/day")
@is_not_permabanned
def sub_banner(v, sub):
	if v and v.patron:
		if request.content_length > 8 * 1024 * 1024: return {"error":"Max file size is 4 MB (8 MB for paypigs)."}, 413
	elif request.content_length > 4 * 1024 * 1024: return {"error":"Max file size is 4 MB (8 MB for paypigs)."}, 413

	if request.headers.get("cf-ipcountry") == "T1": return {"error":"Image uploads are not allowed through TOR."}, 403

	sub = g.db.query(Sub).filter_by(name=sub.lower().strip()).one_or_none()
	if not sub: abort(404)

	if not v.mods(sub.name): abort(403)

	file = request.files["banner"]

	name = f'/images/{time.time()}'.replace('.','')[:-5] + '.webp'
	file.save(name)
	bannerurl = process_image(name)

	if bannerurl:
		if sub.bannerurl and '/images/' in sub.bannerurl:
			fpath = '/images/' + sub.bannerurl.split('/images/')[1]
			if path.isfile(fpath): os.remove(fpath)
		sub.bannerurl = bannerurl
		g.db.add(sub)
		g.db.commit()

	return redirect(f'/s/{sub.name}/settings')

@app.post("/s/<sub>/sidebar_image")
@limiter.limit("1/second;10/day")
@is_not_permabanned
def sub_sidebar(v, sub):
	if v and v.patron:
		if request.content_length > 8 * 1024 * 1024: return {"error":"Max file size is 4 MB (8 MB for paypigs)."}, 413
	elif request.content_length > 4 * 1024 * 1024: return {"error":"Max file size is 4 MB (8 MB for paypigs)."}, 413

	if request.headers.get("cf-ipcountry") == "T1": return {"error":"Image uploads are not allowed through TOR."}, 403

	sub = g.db.query(Sub).filter_by(name=sub.lower().strip()).one_or_none()
	if not sub: abort(404)

	if not v.mods(sub.name): abort(403)
	
	file = request.files["sidebar"]
	name = f'/images/{time.time()}'.replace('.','')[:-5] + '.webp'
	file.save(name)
	sidebarurl = process_image(name)

	if sidebarurl:
		if sub.sidebarurl and '/images/' in sub.sidebarurl:
			fpath = '/images/' + sub.sidebarurl.split('/images/')[1]
			if path.isfile(fpath): os.remove(fpath)
		sub.sidebarurl = sidebarurl
		g.db.add(sub)
		g.db.commit()

	return redirect(f'/s/{sub.name}/settings')


@app.get("/sub_toggle/<mode>")
def sub_toggle(mode):
	if mode in ('Exclude subs', 'Include subs', 'View subs only'): session["subs"] = mode

	if request.referrer and len(request.referrer) > 1 and request.referrer.startswith(SITE_FULL):
		return redirect(request.referrer)

	return redirect('/')


@app.get("/subs")
@auth_desired
def subs(v):
	subs = g.db.query(Submission.sub, func.count(Submission.sub)).group_by(Submission.sub).order_by(func.count(Submission.sub).desc()).all()[:-1]
	return render_template('sub/subs.html', v=v, subs=subs)