from __future__ import unicode_literals
from files.helpers.alerts import *
from files.helpers.sanitize import *
from files.helpers.discord import remove_user, set_nick
from files.helpers.const import *
from files.mail import *
from files.__main__ import app, cache, limiter
import youtube_dl
from .front import frontlist
import os
from files.helpers.sanitize import filter_emojis_only
from files.helpers.discord import add_role
from shutil import copyfile
import requests
import tldextract

GUMROAD_TOKEN = environ.get("GUMROAD_TOKEN", "").strip()
GUMROAD_ID = environ.get("GUMROAD_ID", "tfcvri").strip()

tiers={
	"(Paypig)": 1,
	"(Renthog)": 2,
	"(Landchad)": 3,
	"(Terminally online turboautist)": 4,
	"(Marsey's Sugar Daddy)": 5,
	"(JIDF Bankroller)": 6,
	"(Rich Bich)": 7,
	"(LlamaBean)": 1,
	}

@app.post("/settings/removebackground")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def removebackground(v):
	v.background = None
	g.db.add(v)
	g.db.commit()
	return {"message": "Background removed!"}

@app.post("/settings/profile")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def settings_profile_post(v):
	updated = False

	if request.values.get("background", v.background) != v.background:
		updated = True
		v.background = request.values.get("background")

	elif request.values.get("reddit", v.reddit) != v.reddit:
		reddit = request.values.get("reddit")
		if reddit in {'old.reddit.com', 'reddit.com', 'i.reddit.com', 'teddit.net', 'libredd.it', 'unddit.com'}:
			updated = True
			v.reddit = reddit

	elif request.values.get("slurreplacer", v.slurreplacer) != v.slurreplacer:
		updated = True
		v.slurreplacer = request.values.get("slurreplacer") == 'true'

	elif request.values.get("hidevotedon", v.hidevotedon) != v.hidevotedon:
		updated = True
		v.hidevotedon = request.values.get("hidevotedon") == 'true'

	elif request.values.get("cardview", v.cardview) != v.cardview:
		updated = True
		v.cardview = request.values.get("cardview") == 'true'

	elif request.values.get("highlightcomments", v.highlightcomments) != v.highlightcomments:
		updated = True
		v.highlightcomments = request.values.get("highlightcomments") == 'true'

	elif request.values.get("newtab", v.newtab) != v.newtab:
		updated = True
		v.newtab = request.values.get("newtab") == 'true'

	elif request.values.get("newtabexternal", v.newtabexternal) != v.newtabexternal:
		updated = True
		v.newtabexternal = request.values.get("newtabexternal") == 'true'

	elif request.values.get("nitter", v.nitter) != v.nitter:
		updated = True
		v.nitter = request.values.get("nitter") == 'true'

	elif request.values.get("controversial", v.controversial) != v.controversial:
		updated = True
		v.controversial = request.values.get("controversial") == 'true'

	elif request.values.get("sigs_disabled", v.sigs_disabled) != v.sigs_disabled:
		updated = True
		v.sigs_disabled = request.values.get("sigs_disabled") == 'true'

	elif request.values.get("over18", v.over_18) != v.over_18:
		updated = True
		v.over_18 = request.values.get("over18") == 'true'
		
	elif request.values.get("private", v.is_private) != v.is_private:
		updated = True
		v.is_private = request.values.get("private") == 'true'

	elif request.values.get("nofollow", v.is_nofollow) != v.is_nofollow:
		updated = True
		v.is_nofollow = request.values.get("nofollow") == 'true'

	elif request.values.get("bio") == "":
		v.bio = None
		v.bio_html = None
		g.db.add(v)
		g.db.commit()
		return render_template("settings_profile.html", v=v, msg="Your bio has been updated.")

	elif request.values.get("sig") == "":
		v.sig = None
		v.sig_html = None
		g.db.add(v)
		g.db.commit()
		return render_template("settings_profile.html", v=v, msg="Your sig has been updated.")

	elif request.values.get("friends") == "":
		v.friends = None
		v.friends_html = None
		g.db.add(v)
		g.db.commit()
		return render_template("settings_profile.html", v=v, msg="Your friends list has been updated.")

	elif request.values.get("enemies") == "":
		v.enemies = None
		v.enemies_html = None
		g.db.add(v)
		g.db.commit()
		return render_template("settings_profile.html", v=v, msg="Your enemies list has been updated.")

	elif (v.patron or v.id == MOOSE_ID) and request.values.get("sig"):
		sig = request.values.get("sig")[:200]

		sig_html = sanitize(sig)

		if len(sig_html) > 1000:
			return render_template("settings_profile.html",
								   v=v,
								   error="Your sig is too long")

		v.sig = sig[:200]
		v.sig_html=sig_html
		g.db.add(v)
		g.db.commit()
		return render_template("settings_profile.html",
							   v=v,
							   msg="Your sig has been updated.")




	elif request.values.get("friends"):
		friends = request.values.get("friends")[:500]

		friends_html = sanitize(friends)

		if len(friends_html) > 2000:
			return render_template("settings_profile.html",
								   v=v,
								   error="Your friends list is too long")


		notify_users = NOTIFY_USERS(friends, v)

		if notify_users:
			cid = notif_comment(f"@{v.username} has added you to their friends list!")
			for x in notify_users:
				add_notif(cid, x)

		v.friends = friends[:500]
		v.friends_html=friends_html
		g.db.add(v)
		g.db.commit()
		return render_template("settings_profile.html",
							   v=v,
							   msg="Your friends list has been updated.")


	elif request.values.get("enemies"):
		enemies = request.values.get("enemies")[:500]

		enemies_html = sanitize(enemies)

		if len(enemies_html) > 2000:
			return render_template("settings_profile.html",
								   v=v,
								   error="Your enemies list is too long")


		notify_users = NOTIFY_USERS(enemies, v)

		if notify_users:
			cid = notif_comment(f"@{v.username} has added you to their enemies list!")
			for x in notify_users:
				add_notif(cid, x)

		v.enemies = enemies[:500]
		v.enemies_html=enemies_html
		g.db.add(v)
		g.db.commit()
		return render_template("settings_profile.html",
							   v=v,
							   msg="Your enemies list has been updated.")


	elif request.values.get("bio") or request.files.get('file') and request.headers.get("cf-ipcountry") != "T1":
		bio = request.values.get("bio")[:1500]

		if request.files.get('file'):
			file = request.files['file']
			if file.content_type.startswith('image/'):
				name = f'/images/{time.time()}'.replace('.','') + '.webp'
				file.save(name)
				url = process_image(v.patron, name)
				bio += f"\n\n![]({url})"
			elif file.content_type.startswith('video/'):
				file.save("video.mp4")
				with open("video.mp4", 'rb') as f:
					try: req = requests.request("POST", "https://pomf2.lain.la/upload.php", files={'files[]': f}, timeout=5).json()
					except requests.Timeout: return {"error": "Video upload timed out, please try again!"}
					try: url = req['files'][0]['url']
					except: return {"error": req['description']}, 400
				bio += f"\n\n{url}"
			else:
				if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": "Image/Video files only"}, 400
				return render_template("settings_profile.html", v=v, error="Image/Video files only."), 400
		
		bio_html = sanitize(bio)

		if len(bio_html) > 10000:
			return render_template("settings_profile.html",
								   v=v,
								   error="Your bio is too long")

		if len(bio_html) > 10000: abort(400)

		v.bio = bio[:1500]
		v.bio_html=bio_html
		g.db.add(v)
		g.db.commit()
		return render_template("settings_profile.html",
							   v=v,
							   msg="Your bio has been updated.")


	frontsize = request.values.get("frontsize")
	if frontsize:
		if frontsize in {"15", "25", "50", "100"}:
			v.frontsize = int(frontsize)
			updated = True
			cache.delete_memoized(frontlist)
		else: abort(400)

	defaultsortingcomments = request.values.get("defaultsortingcomments")
	if defaultsortingcomments:
		if defaultsortingcomments in {"new", "old", "controversial", "top", "bottom"}:
			v.defaultsortingcomments = defaultsortingcomments
			updated = True
		else: abort(400)

	defaultsorting = request.values.get("defaultsorting")
	if defaultsorting:
		if defaultsorting in {"hot", "bump", "new", "old", "comments", "controversial", "top", "bottom"}:
			v.defaultsorting = defaultsorting
			updated = True
		else: abort(400)

	defaulttime = request.values.get("defaulttime")
	if defaulttime:
		if defaulttime in {"hour", "day", "week", "month", "year", "all"}:
			v.defaulttime = defaulttime
			updated = True
		else: abort(400)

	theme = request.values.get("theme")
	if theme:
		if theme in {"dramblr", "reddit", "classic", "classic_dark", "transparent", "win98", "dark", "light", "coffee", "tron", "4chan", "midnight"}:
			if theme == "transparent" and not v.background: 
				return {"error": "You need to set a background to use the transparent theme!"}
			v.theme = theme
			if theme == "win98": v.themecolor = "30409f"
			updated = True
		else: abort(400)

	house = request.values.get("house")
	if house and house in ("None","Furry","Femboy","Vampire","Racist"):
		if v.house: cost = 2000
		else: cost = 500

		if v.coins >= cost: v.coins -= cost
		elif v.procoins >= cost: v.procoins -= cost
		else: abort(403)

		if house == "None": house = None 
		v.house = house

		if v.house == "Vampire":
			send_repeatable_notification(DAD_ID, f"@{v.username} has joined House Vampire!")

		updated = True

	if updated:
		g.db.add(v)
		g.db.commit()

		return {"message": "Your settings have been updated."}

	else:
		return {"error": "You didn't change anything."}, 400


@app.post("/settings/filters")
@auth_required
def filters(v):
	filters=request.values.get("filters")[:1000].strip()

	if filters == v.custom_filter_list:
		return render_template("settings_filters.html", v=v, error="You didn't change anything")

	v.custom_filter_list=filters
	g.db.add(v)
	g.db.commit()
	return render_template("settings_filters.html", v=v, msg="Your custom filters have been updated.")

@app.post("/changelogsub")
@auth_required
def changelogsub(v):
	v.changelogsub = not v.changelogsub
	g.db.add(v)

	cache.delete_memoized(frontlist)

	g.db.commit()
	if v.changelogsub: return {"message": "You have subscribed to the changelog!"}
	else: return {"message": "You have unsubscribed from the changelog!"}

@app.post("/settings/namecolor")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def namecolor(v):

	color = str(request.values.get("color", "")).strip()
	if color.startswith('#'): color = color[1:]
	if len(color) != 6: return render_template("settings_security.html", v=v, error="Invalid color code")
	v.namecolor = color
	g.db.add(v)
	g.db.commit()
	return redirect("/settings/profile")
	
@app.post("/settings/themecolor")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def themecolor(v):

	themecolor = str(request.values.get("themecolor", "")).strip()
	if themecolor.startswith('#'): themecolor = themecolor[1:]
	if len(themecolor) != 6: return render_template("settings_security.html", v=v, error="Invalid color code")
	v.themecolor = themecolor
	g.db.add(v)
	g.db.commit()
	return redirect("/settings/profile")

@app.post("/settings/gumroad")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def gumroad(v):
	if not (v.email and v.is_activated):
		return {"error": f"You must have a verified email to verify {patron} status and claim your rewards"}, 400

	data = {'access_token': GUMROAD_TOKEN, 'email': v.email}
	response = requests.get('https://api.gumroad.com/v2/sales', data=data, timeout=5).json()["sales"]

	if len(response) == 0: return {"error": "Email not found"}, 404

	response = response[0]
	tier = tiers[response["variants_and_quantity"]]
	if v.patron == tier: return {"error": f"{patron} rewards already claimed"}, 400

	procoins = procoins_li[tier] - procoins_li[v.patron]
	if procoins < 0: return {"error": f"{patron} rewards already claimed"}, 400

	existing = g.db.query(User.id).filter(User.email == v.email, User.is_activated == True, User.patron >= tier).one_or_none()
	if existing: return {"error": f"{patron} rewards already claimed on another account"}, 400

	v.patron = tier
	if v.discord_id: add_role(v, f"{tier}")

	v.procoins += procoins
	send_repeatable_notification(v.id, f"You have received {procoins} Marseybux! You can use them to buy awards in the [shop](/shop).")

	if v.patron > 1 and v.verified == None: v.verified = "Verified"

	g.db.add(v)

	if not v.has_badge(20+tier):
		new_badge = Badge(badge_id=20+tier, user_id=v.id)
		g.db.add(new_badge)
		g.db.flush()
		send_notification(v.id, f"@AutoJanny has given you the following profile badge:\n\n![]({new_badge.path})\n\n{new_badge.name}")
	
	g.db.commit()

	return {"message": f"{patron} rewards claimed!"}

@app.post("/settings/titlecolor")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def titlecolor(v):

	titlecolor = str(request.values.get("titlecolor", "")).strip()
	if titlecolor.startswith('#'): titlecolor = titlecolor[1:]
	if len(titlecolor) != 6: return render_template("settings_profile.html", v=v, error="Invalid color code")
	v.titlecolor = titlecolor
	g.db.add(v)
	g.db.commit()
	return redirect("/settings/profile")

@app.post("/settings/verifiedcolor")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def verifiedcolor(v):
	verifiedcolor = str(request.values.get("verifiedcolor", "")).strip()
	if verifiedcolor.startswith('#'): verifiedcolor = verifiedcolor[1:]
	if len(verifiedcolor) != 6: return render_template("settings_profile.html", v=v, error="Invalid color code")
	v.verifiedcolor = verifiedcolor
	g.db.add(v)
	g.db.commit()
	return redirect("/settings/profile")

@app.post("/settings/security")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def settings_security_post(v):
	if request.values.get("new_password"):
		if request.values.get("new_password") != request.values.get("cnf_password"):
			return render_template("settings_security.html", v=v, error="Passwords do not match.")

		if not valid_password_regex.fullmatch(request.values.get("new_password")):
			return render_template("settings_security.html", v=v, error="Password must be between 8 and 100 characters.")

		if not v.verifyPass(request.values.get("old_password")):
			return render_template("settings_security.html", v=v, error="Incorrect password")

		v.passhash = v.hash_password(request.values.get("new_password"))

		g.db.add(v)

		g.db.commit()

		return render_template("settings_security.html", v=v, msg="Your password has been changed.")

	if request.values.get("new_email"):

		if not v.verifyPass(request.values.get('password')):
			return render_template("settings_security.html", v=v, error="Invalid password.")

		new_email = request.values.get("new_email","").strip().lower()

		if new_email == v.email:
			return render_template("settings_security.html", v=v, error="That email is already yours!")

		url = f"{SITE_FULL}/activate"

		now = int(time.time())

		token = generate_hash(f"{new_email}+{v.id}+{now}")
		params = f"?email={quote(new_email)}&id={v.id}&time={now}&token={token}"

		link = url + params

		send_mail(to_address=new_email,
				  subject="Verify your email address.",
				  html=render_template("email/email_change.html",
									   action_url=link,
									   v=v)
				  )

		return render_template("settings_security.html", v=v, msg="Check your email and click the verification link to complete the email change.")

	if request.values.get("2fa_token"):
		if not v.verifyPass(request.values.get('password')):
			return render_template("settings_security.html", v=v, error="Invalid password or token.")

		secret = request.values.get("2fa_secret")
		x = pyotp.TOTP(secret)
		if not x.verify(request.values.get("2fa_token"), valid_window=1):
			return render_template("settings_security.html", v=v, error="Invalid password or token.")

		v.mfa_secret = secret
		g.db.add(v)

		g.db.commit()

		return render_template("settings_security.html", v=v, msg="Two-factor authentication enabled.")

	if request.values.get("2fa_remove"):

		if not v.verifyPass(request.values.get('password')):
			return render_template("settings_security.html", v=v, error="Invalid password or token.")

		token = request.values.get("2fa_remove")

		if not v.validate_2fa(token):
			return render_template("settings_security.html", v=v, error="Invalid password or token.")

		v.mfa_secret = None
		g.db.add(v)

		g.db.commit()

		return render_template("settings_security.html", v=v, msg="Two-factor authentication disabled.")

@app.post("/settings/log_out_all_others")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def settings_log_out_others(v):

	submitted_password = request.values.get("password", "").strip()

	if not v.verifyPass(submitted_password):
		return render_template("settings_security.html", v=v, error="Incorrect Password"), 401

	v.login_nonce += 1

	session["login_nonce"] = v.login_nonce

	g.db.add(v)

	g.db.commit()

	return render_template("settings_security.html", v=v, msg="All other devices have been logged out")


@app.post("/settings/images/profile")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def settings_images_profile(v):
	if request.headers.get("cf-ipcountry") == "T1": return {"error":"Image uploads are not allowed through TOR."}, 403

	file = request.files["profile"]

	name = f'/images/{time.time()}'.replace('.','') + '.webp'
	file.save(name)
	highres = process_image(v.patron, name)

	if not highres: abort(400)

	name2 = name.replace('.webp', 'r.webp')
	copyfile(name, name2)
	imageurl = process_image(v.patron, name2, resize=100)

	if not imageurl: abort(400)

	if v.highres and '/images/' in v.highres:
		fpath = '/images/' + v.highres.split('/images/')[1]
		if path.isfile(fpath): os.remove(fpath)
	if v.profileurl and '/images/' in v.profileurl:
		fpath = '/images/' + v.profileurl.split('/images/')[1]
		if path.isfile(fpath): os.remove(fpath)
	v.highres = highres
	v.profileurl = imageurl
	g.db.add(v)

	g.db.commit()

	return render_template("settings_profile.html", v=v, msg="Profile picture successfully updated.")


@app.post("/settings/images/banner")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def settings_images_banner(v):
	if request.headers.get("cf-ipcountry") == "T1": return {"error":"Image uploads are not allowed through TOR."}, 403

	file = request.files["banner"]

	name = f'/images/{time.time()}'.replace('.','') + '.webp'
	file.save(name)
	bannerurl = process_image(v.patron, name)

	if bannerurl:
		if v.bannerurl and '/images/' in v.bannerurl:
			fpath = '/images/' + v.bannerurl.split('/images/')[1]
			if path.isfile(fpath): os.remove(fpath)
		v.bannerurl = bannerurl
		g.db.add(v)
		g.db.commit()

	return render_template("settings_profile.html", v=v, msg="Banner successfully updated.")


@app.get("/settings/blocks")
@auth_required
def settings_blockedpage(v):

	return render_template("settings_blocks.html", v=v)

@app.get("/settings/css")
@auth_required
def settings_css_get(v):

	return render_template("settings_css.html", v=v)

@app.post("/settings/css")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def settings_css(v):
	if v.agendaposter: return {"error": "Agendapostered users can't edit css!"}

	css = request.values.get("css").strip().replace('\\', '').strip()[:4000]
	v.css = css
	g.db.add(v)
	g.db.commit()

	return render_template("settings_css.html", v=v)

@app.get("/settings/profilecss")
@auth_required
def settings_profilecss_get(v):
	return render_template("settings_profilecss.html", v=v)

@app.post("/settings/profilecss")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def settings_profilecss(v):
	profilecss = request.values.get("profilecss").strip().replace('\\', '').strip()[:4000]


	urls = list(css_regex.finditer(profilecss)) + list(css_regex2.finditer(profilecss))
	for i in urls:
		url = i.group(1)
		if url.startswith('/'): continue
		domain = tldextract.extract(url).registered_domain
		if domain not in approved_embed_hosts:
			error = f"The domain '{domain}' is not allowed, please use one of these domains\n\n{approved_embed_hosts}."
			return render_template("settings_profilecss.html", error=error, v=v)


	v.profilecss = profilecss
	g.db.add(v)
	g.db.commit()
	return render_template("settings_profilecss.html", v=v)

@app.post("/settings/block")
@limiter.limit("1/second;10/day")
@limiter.limit("1/second;10/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def settings_block_user(v):

	user = get_user(request.values.get("username"), graceful=True)

	if not user: return {"error": "That user doesn't exist."}, 404
	
	if user.unblockable:
		send_notification(user.id, f"@{v.username} has tried to block you and failed because of your unblockable status!")
		g.db.commit()
		return {"error": "This user is unblockable."}, 403

	if user.id == v.id:
		return {"error": "You can't block yourself."}, 409

	if v.is_blocking(user):
		return {"error": f"You have already blocked @{user.username}."}, 409

	if user.id == NOTIFICATIONS_ID:
		return {"error": "You can't block this user."}, 409

	new_block = UserBlock(user_id=v.id,
						  target_id=user.id,
						  )
	g.db.add(new_block)

	send_notification(user.id, f"@{v.username} has blocked you!")

	cache.delete_memoized(frontlist)

	g.db.commit()

	return {"message": f"@{user.username} blocked."}


@app.post("/settings/unblock")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def settings_unblock_user(v):

	user = get_user(request.values.get("username"))

	x = v.is_blocking(user)
	
	if not x: abort(409)

	g.db.delete(x)

	send_notification(user.id, f"@{v.username} has unblocked you!")

	cache.delete_memoized(frontlist)

	g.db.commit()

	return {"message": f"@{user.username} unblocked."}


@app.get("/settings/apps")
@auth_required
def settings_apps(v):

	return render_template("settings_apps.html", v=v)


@app.post("/settings/remove_discord")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def settings_remove_discord(v):

	remove_user(v)

	v.discord_id=None
	g.db.add(v)

	g.db.commit()

	return redirect("/settings/profile")

@app.get("/settings/content")
@auth_required
def settings_content_get(v):

	return render_template("settings_filters.html", v=v)

@app.post("/settings/name_change")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@is_not_permabanned
def settings_name_change(v):

	new_name=request.values.get("name").strip()

	if new_name==v.username:
		return render_template("settings_profile.html",
						   v=v,
						   error="You didn't change anything")

	if not valid_username_regex.fullmatch(new_name):
		return render_template("settings_profile.html",
						   v=v,
						   error="This isn't a valid username.")

	search_name = new_name.replace('\\', '').replace('_','\_').replace('%','')

	x= g.db.query(User).filter(
		or_(
			User.username.ilike(search_name),
			User.original_username.ilike(search_name)
			)
		).one_or_none()

	if x and x.id != v.id:
		return render_template("settings_profile.html",
						   v=v,
						   error=f"Username `{new_name}` is already in use.")

	v=g.db.query(User).filter_by(id=v.id).one_or_none()

	v.username=new_name
	v.name_changed_utc=int(time.time())

	set_nick(v, new_name)

	g.db.add(v)

	g.db.commit()

	return redirect("/settings/profile")

@app.post("/settings/song_change")
@limiter.limit("2/second;10/day")
@limiter.limit("2/second;10/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def settings_song_change(v):
	song=request.values.get("song").strip()

	if song == "" and v.song:
		if path.isfile(f"/songs/{v.song}.mp3") and g.db.query(User).filter_by(song=v.song).count() == 1:
			os.remove(f"/songs/{v.song}.mp3")
		v.song = None
		g.db.add(v)
		g.db.commit()
		return redirect("/settings/profile")

	song = song.replace("https://music.youtube.com", "https://youtube.com")
	if song.startswith(("https://www.youtube.com/watch?v=", "https://youtube.com/watch?v=", "https://m.youtube.com/watch?v=")):
		id = song.split("v=")[1]
	elif song.startswith("https://youtu.be/"):
		id = song.split("https://youtu.be/")[1]
	else:
		return render_template("settings_profile.html", v=v, error="Not a youtube link.")

	if "?" in id: id = id.split("?")[0]
	if "&" in id: id = id.split("&")[0]

	if path.isfile(f'/songs/{id}.mp3'): 
		v.song = id
		g.db.add(v)
		g.db.commit()
		return redirect("/settings/profile")
		
	
	req = requests.get(f"https://www.googleapis.com/youtube/v3/videos?id={id}&key={YOUTUBE_KEY}&part=contentDetails", timeout=5).json()
	duration = req['items'][0]['contentDetails']['duration']
	if duration == 'P0D':
		return render_template("settings_profile.html", v=v, error="Can't use a live youtube video!")

	if "H" in duration:
		return render_template("settings_profile.html", v=v, error="Duration of the video must not exceed 15 minutes.")

	if "M" in duration:
		duration = int(duration.split("PT")[1].split("M")[0])
		if duration > 15: 
			return render_template("settings_profile.html", v=v, error="Duration of the video must not exceed 15 minutes.")


	if v.song and path.isfile(f"/songs/{v.song}.mp3") and g.db.query(User).filter_by(song=v.song).count() == 1:
		os.remove(f"/songs/{v.song}.mp3")

	ydl_opts = {
		'outtmpl': '/songs/%(title)s.%(ext)s',
		'format': 'bestaudio/best',
		'postprocessors': [{
			'key': 'FFmpegExtractAudio',
			'preferredcodec': 'mp3',
			'preferredquality': '192',
		}],
	}

	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		try: ydl.download([f"https://youtube.com/watch?v={id}"])
		except Exception as e:
			print(e)
			return render_template("settings_profile.html",
						   v=v,
						   error="Age-restricted videos aren't allowed.")

	files = os.listdir("/songs/")
	paths = [path.join("/songs/", basename) for basename in files]
	songfile = max(paths, key=path.getctime)
	os.rename(songfile, f"/songs/{id}.mp3")

	v.song = id
	g.db.add(v)

	g.db.commit()

	return redirect("/settings/profile")

@app.post("/settings/title_change")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@auth_required
def settings_title_change(v):

	if v.flairchanged: abort(403)
	
	new_name=request.values.get("title").strip()[:100].replace("𒐪","")

	if new_name==v.customtitle: return render_template("settings_profile.html", v=v, error="You didn't change anything")

	v.customtitleplain = new_name

	v.customtitle = filter_emojis_only(new_name)

	if len(v.customtitle) < 1000:
		g.db.add(v)
		g.db.commit()

	return redirect("/settings/profile")


@app.get("/settings")
@auth_required
def settings(v):
	return redirect("/settings/profile")


@app.get("/settings/profile")
@auth_required
def settings_profile(v):
	return render_template("settings_profile.html", v=v)