from __future__ import unicode_literals
from files.helpers.alerts import *
from files.helpers.sanitize import *
from files.helpers.filters import filter_comment_html
from files.helpers.markdown import *
from files.helpers.discord import remove_user, set_nick
from files.helpers.const import *
from files.mail import *
from files.__main__ import app, cache, limiter
import youtube_dl
from .front import frontlist
import os
from .posts import filter_title
from files.helpers.discord import add_role
from shutil import copyfile
import requests

valid_username_regex = re.compile("^[a-zA-Z0-9_\-]{3,25}$")
valid_password_regex = re.compile("^.{8,100}$")

YOUTUBE_KEY = environ.get("YOUTUBE_KEY", "").strip()
COINS_NAME = environ.get("COINS_NAME").strip()
GUMROAD_TOKEN = environ.get("GUMROAD_TOKEN", "").strip()

tiers={
	"(Paypig)": 1,
	"(Renthog)": 2,
	"(Landchad)": 3,
	"(Terminally online turboautist)": 4,
	"(Footpig)": 5,
	}

@app.post("/settings/removebackground")
@limiter.limit("1/second")
@auth_required
def removebackground(v):
	v.background = None
	g.db.add(v)
	g.db.commit()
	return {"message": "Background removed!"}

@app.post("/settings/profile")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def settings_profile_post(v):
	if request.content_length > 4 * 1024 * 1024: return "Max file size is 4 MB.", 413

	updated = False

	if request.values.get("background", v.background) != v.background:
		updated = True
		v.background = request.values.get("background", None)

	if request.values.get("slurreplacer", v.slurreplacer) != v.slurreplacer:
		updated = True
		v.slurreplacer = request.values.get("slurreplacer", None) == 'true'

	if request.values.get("hidevotedon", v.hidevotedon) != v.hidevotedon:
		updated = True
		v.hidevotedon = request.values.get("hidevotedon", None) == 'true'

	if request.values.get("cardview", v.cardview) != v.cardview:
		updated = True
		v.cardview = request.values.get("cardview", None) == 'true'

	if request.values.get("highlightcomments", v.highlightcomments) != v.highlightcomments:
		updated = True
		v.highlightcomments = request.values.get("highlightcomments", None) == 'true'

	if request.values.get("newtab", v.newtab) != v.newtab:
		updated = True
		v.newtab = request.values.get("newtab", None) == 'true'

	if request.values.get("newtabexternal", v.newtabexternal) != v.newtabexternal:
		updated = True
		v.newtabexternal = request.values.get("newtabexternal", None) == 'true'

	if request.values.get("oldreddit", v.oldreddit) != v.oldreddit:
		updated = True
		v.oldreddit = request.values.get("oldreddit", None) == 'true'

	if request.values.get("nitter", v.nitter) != v.nitter:
		updated = True
		v.nitter = request.values.get("nitter", None) == 'true'

	if request.values.get("controversial", v.controversial) != v.controversial:
		updated = True
		v.controversial = request.values.get("controversial", None) == 'true'

	if request.values.get("over18", v.over_18) != v.over_18:
		updated = True
		v.over_18 = request.values.get("over18", None) == 'true'
		
	if request.values.get("private", v.is_private) != v.is_private:
		updated = True
		v.is_private = request.values.get("private", None) == 'true'

	if request.values.get("nofollow", v.is_nofollow) != v.is_nofollow:
		updated = True
		v.is_nofollow = request.values.get("nofollow", None) == 'true'

	if request.values.get("bio"):
		bio = request.values.get("bio")[:1500]

		for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|webp|PNG|JPG|JPEG|GIF|WEBP|9999))', bio, re.MULTILINE):
			if "wikipedia" not in i.group(1): bio = bio.replace(i.group(1), f'![]({i.group(1)})')
		bio = re.sub('([^\n])\n([^\n])', r'\1\n\n\2', bio)

		if request.files.get('file') and request.headers.get("cf-ipcountry") != "T1":
			
			file = request.files['file']
			if not file.content_type.startswith('image/'):
				if request.headers.get("Authorization"): return {"error": f"Image files only"}, 400
				else: return render_template("settings_profile.html", v=v, error=f"Image files only."), 400

			name = f'/images/{int(time.time())}{secrets.token_urlsafe(2)}.gif'
			file.save(name)
			url = request.host_url[:-1] + process_image(name)

			bio += f"\n\n![]({url})"

		bio_html = CustomRenderer().render(mistletoe.Document(bio))
		bio_html = sanitize(bio_html)
		bans = filter_comment_html(bio_html)

		if len(bio_html) > 10000:
			return render_template("settings_profile.html",
								   v=v,
								   error="Your bio is too long")

		if bans:
			ban = bans[0]
			reason = f"Remove the {ban.domain} link from your bio and try again."
			if ban.reason:
				reason += f" {ban.reason}"
				
			if any([x.reason==4 for x in bans]):
				v.ban(days=30, reason="Digitally malicious content is not allowed.")
			return {"error": reason}, 401

		if len(bio_html) > 10000: abort(400)

		v.bio = bio[:1500]
		v.bio_html=bio_html
		g.db.add(v)
		g.db.commit()
		return render_template("settings_profile.html",
							   v=v,
							   msg="Your bio has been updated.")

	if request.values.get("filters"):

		filters=request.values.get("filters")[:1000].strip()

		if filters==v.custom_filter_list:
			return render_template("settings_profile.html",
								   v=v,
								   error="You didn't change anything")

		v.custom_filter_list=filters
		g.db.add(v)
		g.db.commit()
		return render_template("settings_profile.html",
							   v=v,
							   msg="Your custom filters have been updated.")



	frontsize = request.values.get("frontsize")
	if frontsize:
		if frontsize in ["25", "50", "100"]:
			v.frontsize = int(frontsize)
			updated = True
			cache.delete_memoized(frontlist)
		else: abort(400)

	defaultsortingcomments = request.values.get("defaultsortingcomments")
	if defaultsortingcomments:
		if defaultsortingcomments in ["new", "old", "controversial", "top", "bottom"]:
			v.defaultsortingcomments = defaultsortingcomments
			updated = True
		else: abort(400)

	defaultsorting = request.values.get("defaultsorting")
	if defaultsorting:
		if defaultsorting in ["hot", "new", "old", "comments", "controversial", "top", "bottom"]:
			v.defaultsorting = defaultsorting
			updated = True
		else: abort(400)

	defaulttime = request.values.get("defaulttime")
	if defaulttime:
		if defaulttime in ["hour", "day", "week", "month", "year", "all"]:
			v.defaulttime = defaulttime
			updated = True
		else: abort(400)

	theme = request.values.get("theme")
	if theme:
		v.theme = theme
		updated = True

	quadrant = request.values.get("quadrant")
	if quadrant and 'pcmemes.net' in request.host.lower():
		v.quadrant = quadrant
		v.customtitle = quadrant
		if quadrant=="Centrist":
			v.namecolor = "7f8fa6"
			v.titlecolor = "7f8fa6"
		elif quadrant=="LibLeft":
			v.namecolor = "62ca56"
			v.titlecolor = "62ca56"
		elif quadrant=="LibRight":
			v.namecolor = "f8db58"
			v.titlecolor = "f8db58"
		elif quadrant=="AuthLeft":
			v.namecolor = "ff0000"
			v.titlecolor = "ff0000"
		elif quadrant=="AuthRight":
			v.namecolor = "2a96f3"
			v.titlecolor = "2a96f3"
		elif quadrant=="LibCenter":
			v.namecolor = "add357"
			v.titlecolor = "add357"
		elif quadrant=="AuthCenter":
			v.namecolor = "954b7a"
			v.titlecolor = "954b7a"
		elif quadrant=="Left":
			v.namecolor = "b1652b"
			v.titlecolor = "b1652b"
		elif quadrant=="Right":
			v.namecolor = "91b9A6"
			v.titlecolor = "91b9A6"

		updated = True

	if updated:
		g.db.add(v)
		g.db.commit()

		return {"message": "Your settings have been updated."}

	else:
		return {"error": "You didn't change anything."}, 400

@app.post("/changelogsub")
@auth_required
@validate_formkey
def changelogsub(v):
	v.changelogsub = not v.changelogsub
	g.db.add(v)

	cache.delete_memoized(frontlist)

	g.db.commit()
	if v.changelogsub: return {"message": "You have subscribed to the changelog!"}
	else: return {"message": "You have unsubscribed from the changelog!"}

@app.post("/settings/namecolor")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def namecolor(v):
	color = str(request.values.get("color", "")).strip()
	if color.startswith('#'): color = color[1:]
	if len(color) != 6: return render_template("settings_security.html", v=v, error="Invalid color code")
	v.namecolor = color
	g.db.add(v)
	g.db.commit()
	return redirect("/settings/profile")
	
@app.post("/settings/themecolor")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def themecolor(v):
	themecolor = str(request.values.get("themecolor", "")).strip()
	if themecolor.startswith('#'): themecolor = themecolor[1:]
	if len(themecolor) != 6: return render_template("settings_security.html", v=v, error="Invalid color code")
	v.themecolor = themecolor
	g.db.add(v)
	g.db.commit()
	return redirect("/settings/profile")

@app.post("/settings/gumroad")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def gumroad(v):
	if 'rdrama' in request.host: patron = 'Paypig'
	else: patron = 'Patron'

	if not (v.email and v.is_activated): return {"error": f"You must have a verified email to verify {patron} status and claim your rewards"}, 400

	data = {
		'access_token': GUMROAD_TOKEN,
		'email': v.email
	}
	response = requests.get('https://api.gumroad.com/v2/sales', data=data).json()["sales"]

	if len(response) == 0: return {"error": "Email not found"}, 404

	response = response[0]
	tier = tiers[response["variants_and_quantity"]]
	if v.patron == tier: return {"error": f"{patron} rewards already claimed"}, 400

	v.patron = tier
	g.db.add(v)

	grant_awards = {}
	if tier == 1:
		if v.discord_id: add_role(v, "1")
		grant_awards["shit"] = 1
		grant_awards["fireflies"] = 1
	elif tier == 2:
		if v.discord_id: add_role(v, "2")
		grant_awards["shit"] = 3
		grant_awards["fireflies"] = 3
	elif tier == 3:
		if v.discord_id: add_role(v, "3")
		grant_awards["shit"] = 5
		grant_awards["fireflies"] = 5
		grant_awards["ban"] = 1
	elif tier == 4:
		if v.discord_id: add_role(v, "4")
		grant_awards["shit"] = 10
		grant_awards["fireflies"] = 10
		grant_awards["ban"] = 3
	elif tier == 5 or tier == 8:
		if v.discord_id: add_role(v, "5")
		grant_awards["shit"] = 20
		grant_awards["fireflies"] = 20
		grant_awards["ban"] = 6

	thing = g.db.query(AwardRelationship).order_by(AwardRelationship.id.desc()).first().id

	for name in grant_awards:
		for count in range(grant_awards[name]):

			thing += 1

			award = AwardRelationship(
				id=thing,
				user_id=v.id,
				kind=name
			)

			g.db.add(award)

	if not v.has_badge(20+tier):
		new_badge = Badge(badge_id=20+tier,
						user_id=v.id,
						)
		g.db.add(new_badge)

	g.db.commit()

	return {"message": f"{patron} rewards claimed!"}

@app.post("/settings/titlecolor")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def titlecolor(v):
	titlecolor = str(request.values.get("titlecolor", "")).strip()
	if titlecolor.startswith('#'): titlecolor = titlecolor[1:]
	if len(titlecolor) != 6: return render_template("settings_security.html", v=v, error="Invalid color code")
	v.titlecolor = titlecolor
	g.db.add(v)
	g.db.commit()

	return redirect("/settings/profile")

@app.post("/settings/security")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def settings_security_post(v):
	if request.values.get("new_password"):
		if request.values.get(
				"new_password") != request.values.get("cnf_password"):
			return redirect("/settings/security?error=" +
							escape("Passwords do not match."))

		if not re.match(valid_password_regex, request.values.get("new_password")):
			return redirect("/settings/security?error=" + 
							escape("Password must be between 8 and 100 characters."))

		if not v.verifyPass(request.values.get("old_password")):
			return render_template(
				"settings_security.html", v=v, error="Incorrect password")

		v.passhash = v.hash_password(request.values.get("new_password"))

		g.db.add(v)

		g.db.commit()

		return redirect("/settings/security?msg=" +
						escape("Your password has been changed."))

	if request.values.get("new_email"):

		if not v.verifyPass(request.values.get('password')):
			return redirect("/settings/security?error=" +
							escape("Invalid password."))

		new_email = request.values.get("new_email","").strip()
		if new_email == v.email:
			return redirect("/settings/security?error=That email is already yours!")

		existing = g.db.query(User).options(lazyload('*')).filter(User.id != v.id,
										   func.lower(User.email) == new_email.lower()).first()
		if existing:
			return redirect("/settings/security?error=" +
							escape("That email address is already in use."))

		url = f"https://{app.config['SERVER_NAME']}/activate"

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

		return redirect("/settings/security?msg=" + escape(
			"Check your email and click the verification link to complete the email change."))

	if request.values.get("2fa_token", ""):

		if not v.verifyPass(request.values.get('password')):
			return redirect("/settings/security?error=" +
							escape("Invalid password or token."))

		secret = request.values.get("2fa_secret")
		x = pyotp.TOTP(secret)
		if not x.verify(request.values.get("2fa_token"), valid_window=1):
			return redirect("/settings/security?error=" +
							escape("Invalid password or token."))

		v.mfa_secret = secret
		g.db.add(v)

		g.db.commit()

		return redirect("/settings/security?msg=" +
						escape("Two-factor authentication enabled."))

	if request.values.get("2fa_remove", ""):

		if not v.verifyPass(request.values.get('password')):
			return redirect("/settings/security?error=" +
							escape("Invalid password or token."))

		token = request.values.get("2fa_remove")

		if not v.validate_2fa(token):
			return redirect("/settings/security?error=" +
							escape("Invalid password or token."))

		v.mfa_secret = None
		g.db.add(v)

		g.db.commit()

		return redirect("/settings/security?msg=" +
						escape("Two-factor authentication disabled."))

@app.post("/settings/log_out_all_others")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def settings_log_out_others(v):

	submitted_password = request.values.get("password", "")

	if not v.verifyPass(submitted_password): return render_template("settings_security.html", v=v, error="Incorrect Password"), 401

	v.login_nonce += 1

	session["login_nonce"] = v.login_nonce

	g.db.add(v)

	g.db.commit()

	return render_template("settings_security.html", v=v, msg="All other devices have been logged out")


@app.post("/settings/images/profile")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def settings_images_profile(v):
	if request.content_length > 4 * 1024 * 1024: return "Max file size is 4 MB.", 413

	if request.headers.get("cf-ipcountry") == "T1": return "Image uploads are not allowed through TOR.", 403

	file = request.files["profile"]

	name = f'/images/{int(time.time())}{secrets.token_urlsafe(2)}.gif'
	file.save(name)
	highres = request.host_url[:-1] + process_image(name)

	if not highres: abort(400)

	name2 = name.replace('.gif', 'r.gif')
	copyfile(name, name2)
	imageurl = request.host_url[:-1] + process_image(name2, True)

	if not imageurl: abort(400)

	v.highres = highres
	v.profileurl = imageurl
	g.db.add(v)

	g.db.commit()

	return render_template("settings_profile.html", v=v, msg="Profile picture successfully updated.")


@app.post("/settings/images/banner")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def settings_images_banner(v):
	if request.content_length > 4 * 1024 * 1024: return "Max file size is 4 MB.", 413

	if request.headers.get("cf-ipcountry") == "T1": return "Image uploads are not allowed through TOR.", 403

	file = request.files["banner"]

	name = f'/images/{int(time.time())}{secrets.token_urlsafe(2)}.gif'
	file.save(name)
	imageurl = request.host_url[:-1] + process_image(name)

	if imageurl:
		v.bannerurl = imageurl
		g.db.add(v)
		g.db.commit()

	return render_template("settings_profile.html", v=v, msg="Banner successfully updated.")


@app.post("/settings/delete/profile")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def settings_delete_profile(v):
	v.highres = None
	v.profileurl = None
	g.db.add(v)
	g.db.commit()
	return render_template("settings_profile.html", v=v,
						   msg="Profile picture successfully removed.")

@app.post("/settings/delete/banner")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def settings_delete_banner(v):

	v.bannerurl = None
	g.db.add(v)
	g.db.commit()

	return render_template("settings_profile.html", v=v,
						   msg="Banner successfully removed.")


@app.get("/settings/blocks")
@auth_required
def settings_blockedpage(v):

	return render_template("settings_blocks.html", v=v)

@app.get("/settings/css")
@auth_required
def settings_css_get(v):

	return render_template("settings_css.html", v=v)

@app.post("/settings/css")
@limiter.limit("1/second")
@auth_required
def settings_css(v):
	css = request.values.get("css").replace('\\', '')[:50000]

	if not v.agendaposter:
		v.css = css
	else:
		v.css = 'body *::before, body *::after { content: "Trans rights are human rights!"; }'
	g.db.add(v)
	g.db.commit()

	return render_template("settings_css.html", v=v)

@app.get("/settings/profilecss")
@auth_required
def settings_profilecss_get(v):

	if v.coins < 1000 and not v.patron and v.admin_level < 6: return f"You must have +1000 {COINS_NAME} or be a patron to set profile css."
	return render_template("settings_profilecss.html", v=v)

@app.post("/settings/profilecss")
@limiter.limit("1/second")
@auth_required
def settings_profilecss(v):
	if v.coins < 1000 and not v.patron: return f"You must have +1000 {COINS_NAME} or be a patron to set profile css."
	profilecss = request.values.get("profilecss").replace('\\', '')[:50000]
	v.profilecss = profilecss
	g.db.add(v)
	g.db.commit()

	return render_template("settings_profilecss.html", v=v)

@app.post("/settings/block")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def settings_block_user(v):

	user = get_user(request.values.get("username"), graceful=True)

	if not user:
		return {"error": "That user doesn't exist."}, 404

	if user.id == v.id:
		return {"error": "You can't block yourself."}, 409

	if v.has_block(user):
		return {"error": f"You have already blocked @{user.username}."}, 409

	if user.id == NOTIFICATIONS_ACCOUNT:
		return {"error": "You can't block this user."}, 409

	new_block = UserBlock(user_id=v.id,
						  target_id=user.id,
						  )
	g.db.add(new_block)

	

	existing = g.db.query(Notification).options(lazyload('*')).filter_by(blocksender=v.id, user_id=user.id).first()
	if not existing: send_block_notif(v.id, user.id, f"@{v.username} has blocked you!")

	cache.delete_memoized(frontlist)

	g.db.commit()

	if v.admin_level == 1: return {"message": f"@{user.username} banned!"}
	else: return {"message": f"@{user.username} blocked."}


@app.post("/settings/unblock")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def settings_unblock_user(v):

	user = get_user(request.values.get("username"))

	x = v.has_block(user)
	
	if not x: abort(409)

	g.db.delete(x)

	

	existing = g.db.query(Notification).options(lazyload('*')).filter_by(unblocksender=v.id, user_id=user.id).first()
	if not existing: send_unblock_notif(v.id, user.id, f"@{v.username} has unblocked you!")

	cache.delete_memoized(frontlist)

	g.db.commit()

	if v.admin_level == 1: return {"message": f"@{user.username} unbanned!"}

	return {"message": f"@{user.username} unblocked."}


@app.get("/settings/apps")
@auth_required
def settings_apps(v):

	return render_template("settings_apps.html", v=v)


@app.post("/settings/remove_discord")
@limiter.limit("1/second")
@auth_required
@validate_formkey
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
@limiter.limit("1/second")
@auth_required
@validate_formkey
def settings_name_change(v):

	new_name=request.values.get("name").strip()

	if new_name==v.username:
		return render_template("settings_profile.html",
						   v=v,
						   error="You didn't change anything")

	if not re.match(valid_username_regex, new_name):
		return render_template("settings_profile.html",
						   v=v,
						   error=f"This isn't a valid username.")

	name=new_name.replace('_','\_')

	x= g.db.query(User).options(
		lazyload('*')
		).filter(
		or_(
			User.username.ilike(name),
			User.original_username.ilike(name)
			)
		).first()

	if x and x.id != v.id:
		return render_template("settings_profile.html",
						   v=v,
						   error=f"Username `{new_name}` is already in use.")

	v=g.db.query(User).with_for_update().options(lazyload('*')).filter_by(id=v.id).first()

	v.username=new_name
	v.name_changed_utc=int(time.time())

	set_nick(v, new_name)

	g.db.add(v)

	g.db.commit()

	return redirect("/settings/profile")

@app.post("/settings/song_change")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def settings_song_change(v):
	song=request.values.get("song").strip()

	if song == "" and v.song and path.isfile(f"/songs/{v.song}.mp3") and g.db.query(User.id).options(lazyload('*')).filter_by(song=v.song).count() == 1:
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
		return render_template("settings_profile.html",
					v=v,
					error=f"Not a youtube link.")

	if "?" in id: id = id.split("?")[0]
	if "&" in id: id = id.split("&")[0]

	if path.isfile(f'/songs/{id}.mp3'): 
		v.song = id
		g.db.add(v)
		g.db.commit()
		return redirect("/settings/profile")
		
	
	req = requests.get(f"https://www.googleapis.com/youtube/v3/videos?id={id}&key={YOUTUBE_KEY}&part=contentDetails").json()
	duration = req['items'][0]['contentDetails']['duration']
	if "H" in duration:
		return render_template("settings_profile.html",
					v=v,
					error=f"Duration of the video must not exceed 10 minutes.")

	if "M" in duration:
		duration = int(duration.split("PT")[1].split("M")[0])
		if duration > 10: 
			return render_template("settings_profile.html",
						v=v,
						error=f"Duration of the video must not exceed 10 minutes.")


	if v.song and path.isfile(f"/songs/{v.song}.mp3") and g.db.query(User.id).options(lazyload('*')).filter_by(song=v.song).count() == 1:
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
						   error=f"Age-restricted videos aren't allowed.")

	files = os.listdir("/songs/")
	paths = [path.join("/songs/", basename) for basename in files]
	songfile = max(paths, key=path.getctime)
	os.rename(songfile, f"/songs/{id}.mp3")

	v.song = id
	g.db.add(v)

	g.db.commit()

	return redirect("/settings/profile")

@app.post("/settings/title_change")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def settings_title_change(v):

	if v.flairchanged: abort(403)
	
	new_name=request.values.get("title").strip()[:100].replace("𒐪","")

	if new_name==v.customtitle:
		return render_template("settings_profile.html",
						   v=v,
						   error="You didn't change anything")

	v.customtitleplain = new_name

	v.customtitle = filter_title(new_name)

	g.db.add(v)
	g.db.commit()

	return redirect("/settings/profile")