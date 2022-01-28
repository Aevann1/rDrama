import time
import gevent
import requests
from files.helpers.wrappers import *
from files.helpers.sanitize import *
from files.helpers.filters import *
from files.helpers.alerts import *
from files.helpers.discord import send_discord_message
from files.helpers.const import *
from files.classes import *
from flask import *
from io import BytesIO
from files.__main__ import app, limiter, cache, db_session
from PIL import Image as PILimage
from .front import frontlist, changeloglist
from urllib.parse import ParseResult, urlunparse, urlparse, quote, unquote
from os import path
import requests
from shutil import copyfile

db = db_session()
marseys = tuple(f':#{x[0]}:' for x in db.query(Marsey.name).all())
db.close()

if path.exists(f'snappy_{SITE_NAME}.txt'):
	with open(f'snappy_{SITE_NAME}.txt', "r") as f:
		if SITE == 'pcmemes.net': snappyquotes = tuple(f.read().split("{[para]}"))
		else: snappyquotes = tuple(f.read().split("{[para]}")) + marseys
else: snappyquotes = marseys

IMGUR_KEY = environ.get("IMGUR_KEY").strip()

CF_KEY = environ.get("CF_KEY", "").strip()
CF_ZONE = environ.get("CF_ZONE", "").strip()
CF_HEADERS = {"Authorization": f"Bearer {CF_KEY}", "Content-Type": "application/json"}

@app.post("/toggle_club/<pid>")
@auth_required
def toggle_club(pid, v):

	if v.club_allowed == False: abort(403)
	post = get_post(pid)
	if post.author_id != v.id and v.admin_level == 0: abort(403)

	post.club = not post.club
	g.db.add(post)

	g.db.commit()

	if post.club: return {"message": "Post has been marked as club-only!"}
	else: return {"message": "Post has been unmarked as club-only!"}


@app.post("/publish/<pid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def publish(pid, v):
	post = get_post(pid)
	if post.author_id != v.id: abort(403)
	post.private = False
	post.created_utc = int(time.time())
	g.db.add(post)
	
	notify_users = NOTIFY_USERS(post.body_html, v) | NOTIFY_USERS2(post.title, v)

	cid = notif_comment(f"@{v.username} has mentioned you: [{post.title}]({post.permalink})")
	for x in notify_users:
		add_notif(cid, x)

	
	cid = notif_comment(f"@{v.username} has made a new post: [{post.title}]({post.permalink})", autojanny=True)
	for follow in v.followers:
		user = get_account(follow.user_id)
		if post.club and not user.paid_dues: continue
		add_notif(cid, user.id)


	cache.delete_memoized(frontlist)
	cache.delete_memoized(User.userpagelisting)

	if v.admin_level > 0 and ("[changelog]" in post.title.lower() or "(changelog)" in post.title.lower()):
		send_discord_message(f"{SITE_FULL}{post.permalink}")
		cache.delete_memoized(changeloglist)

	g.db.commit()

	return {"message": "Post published!"}

@app.get("/submit")
@auth_required
def submit_get(v):
	return render_template("submit.html",
						   v=v)

@app.get("/post/<pid>")
@app.get("/post/<pid>/<anything>")
@app.get("/logged_out/post/<pid>")
@app.get("/logged_out/post/<pid>/<anything>")
@auth_desired
def post_id(pid, anything=None, v=None):
	if not v and not request.path.startswith('/logged_out') and not request.headers.get("Authorization"):
		return redirect(f"{SITE_FULL}/logged_out{request.full_path}")

	if v and request.path.startswith('/logged_out'): v = None


	try: pid = int(pid)
	except Exception as e: pass


	try: pid = int(pid)
	except:
		try: pid = int(pid, 36)
		except: abort(404)

	post = get_post(pid, v=v)

	if 'megathread' in post.title.lower(): defaultsortingcomments = 'new'
	elif v: defaultsortingcomments = v.defaultsortingcomments
	else: defaultsortingcomments = "top"
	sort = request.values.get("sort", defaultsortingcomments)

	if post.club and not (v and (v.paid_dues or v.id == post.author_id)): abort(403)

	if post.private and not (v and (v.admin_level > 1 or v.id == post.author.id)): abort(403)

	if v:
		votes = g.db.query(CommentVote).filter_by(user_id=v.id).subquery()

		blocking = v.blocking.subquery()

		blocked = v.blocked.subquery()

		comments = g.db.query(
			Comment,
			votes.c.vote_type,
			blocking.c.id,
			blocked.c.id,
		)
		
		if not (v and v.shadowbanned) and not (v and v.admin_level > 1):
			comments = comments.join(User, User.id == Comment.author_id).filter(User.shadowbanned == None)
 
		comments=comments.filter(Comment.parent_submission == post.id, Comment.author_id.notin_((AUTOPOLLER_ID, AUTOBETTER_ID))).join(
			votes,
			votes.c.comment_id == Comment.id,
			isouter=True
		).join(
			blocking,
			blocking.c.target_id == Comment.author_id,
			isouter=True
		).join(
			blocked,
			blocked.c.user_id == Comment.author_id,
			isouter=True
		)

		output = []
		for c in comments.all():
			comment = c[0]
			comment.voted = c[1] or 0
			comment.is_blocking = c[2] or 0
			comment.is_blocked = c[3] or 0
			output.append(comment)
		
		pinned = [c[0] for c in comments.filter(Comment.is_pinned != None).all()]
		
		comments = comments.filter(Comment.level == 1, Comment.is_pinned == None)

		if sort == "new":
			comments = comments.order_by(Comment.created_utc.desc())
		elif sort == "old":
			comments = comments.order_by(Comment.created_utc.asc())
		elif sort == "controversial":
			comments = comments.order_by(-1 * Comment.upvotes * Comment.downvotes * Comment.downvotes)
		elif sort == "top":
			comments = comments.order_by(Comment.realupvotes.desc())
		elif sort == "bottom":
			comments = comments.order_by(Comment.upvotes - Comment.downvotes)

		comments = [c[0] for c in comments.all()]
	else:
		pinned = g.db.query(Comment).filter(Comment.parent_submission == post.id, Comment.is_pinned != None).all()

		comments = g.db.query(Comment).join(User, User.id == Comment.author_id).filter(User.shadowbanned == None, Comment.parent_submission == post.id, Comment.author_id.notin_((AUTOPOLLER_ID, AUTOBETTER_ID)), Comment.level == 1, Comment.is_pinned == None)

		if sort == "new":
			comments = comments.order_by(Comment.created_utc.desc())
		elif sort == "old":
			comments = comments.order_by(Comment.created_utc.asc())
		elif sort == "controversial":
			comments = comments.order_by(-1 * Comment.upvotes * Comment.downvotes * Comment.downvotes)
		elif sort == "top":
			comments = comments.order_by(Comment.realupvotes.desc())
		elif sort == "bottom":
			comments = comments.order_by(Comment.upvotes - Comment.downvotes)

		comments = comments.all()

	offset = 0

	if post.comment_count > 60 and not request.headers.get("Authorization") and not request.values.get("all"):
		comments2 = []
		count = 0
		if post.created_utc > 1638672040:
			for comment in comments:
				comments2.append(comment)
				count += g.db.query(Comment.id).filter_by(parent_submission=post.id, top_comment_id=comment.id).count() + 1
				offset += 1
				if count > 50: break
		else:
			for comment in comments:
				comments2.append(comment)
				count += g.db.query(Comment.id).filter_by(parent_submission=post.id, parent_comment_id=comment.id).count() + 1
				offset += 1
				if count > 10: break

		if len(comments) == len(comments2): offset = None
		comments = comments2

	for pin in pinned:
		if pin.is_pinned_utc and int(time.time()) > pin.is_pinned_utc:
			pin.is_pinned = None
			pin.is_pinned_utc = None
			g.db.add(pin)
			pinned.remove(pin)

	post.replies = pinned + comments

	post.views += 1
	g.db.add(post)
	if request.host != 'old.rdrama.net' and post.over_18 and not (v and v.over_18) and session.get('over_18', 0) < int(time.time()):
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error":"Must be 18+ to view"}, 451
		return render_template("errors/nsfw.html", v=v)

	g.db.commit()
	if request.headers.get("Authorization"): return post.json
	else:
		if post.is_banned and not (v and (v.admin_level > 1 or post.author_id == v.id)): template = "submission_banned.html"
		else: template = "submission.html"
		return render_template(template, v=v, p=post, sort=sort, render_replies=True, offset=offset)

@app.post("/viewmore/<pid>/<sort>/<offset>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def viewmore(v, pid, sort, offset):
	offset = int(offset)
	if v:
		votes = g.db.query(CommentVote).filter_by(user_id=v.id).subquery()

		blocking = v.blocking.subquery()

		blocked = v.blocked.subquery()

		comments = g.db.query(
			Comment,
			votes.c.vote_type,
			blocking.c.id,
			blocked.c.id,
		)
		
		if not (v and v.shadowbanned) and not (v and v.admin_level > 1):
			comments = comments.join(User, User.id == Comment.author_id).filter(User.shadowbanned == None)
 
		comments=comments.filter(Comment.parent_submission == pid, Comment.author_id.notin_((AUTOPOLLER_ID, AUTOBETTER_ID)), Comment.is_pinned == None).join(
			votes,
			votes.c.comment_id == Comment.id,
			isouter=True
		).join(
			blocking,
			blocking.c.target_id == Comment.author_id,
			isouter=True
		).join(
			blocked,
			blocked.c.user_id == Comment.author_id,
			isouter=True
		)

		output = []
		for c in comments.all():
			comment = c[0]
			comment.voted = c[1] or 0
			comment.is_blocking = c[2] or 0
			comment.is_blocked = c[3] or 0
			output.append(comment)
				
		comments = comments.filter(Comment.level == 1)

		if sort == "new":
			comments = comments.order_by(Comment.created_utc.desc())
		elif sort == "old":
			comments = comments.order_by(Comment.created_utc.asc())
		elif sort == "controversial":
			comments = comments.order_by(-1 * Comment.upvotes * Comment.downvotes * Comment.downvotes)
		elif sort == "top":
			comments = comments.order_by(Comment.realupvotes.desc())
		elif sort == "bottom":
			comments = comments.order_by(Comment.upvotes - Comment.downvotes)

		comments = comments.offset(offset)

		comments = [c[0] for c in comments.all()]
	else:
		comments = g.db.query(Comment).join(User, User.id == Comment.author_id).filter(User.shadowbanned == None, Comment.parent_submission == pid, Comment.author_id.notin_((AUTOPOLLER_ID, AUTOBETTER_ID)), Comment.level == 1, Comment.is_pinned == None)

		if sort == "new":
			comments = comments.order_by(Comment.created_utc.desc())
		elif sort == "old":
			comments = comments.order_by(Comment.created_utc.asc())
		elif sort == "controversial":
			comments = comments.order_by(-1 * Comment.upvotes * Comment.downvotes * Comment.downvotes)
		elif sort == "top":
			comments = comments.order_by(Comment.realupvotes.desc())
		elif sort == "bottom":
			comments = comments.order_by(Comment.upvotes - Comment.downvotes)

		comments = comments.offset(offset)
		
		comments = comments.all()

	comments2 = []
	count = 0
	post = get_post(pid, v=v)
	if post.created_utc > 1638672040:
		for comment in comments:
			comments2.append(comment)
			count += g.db.query(Comment.id).filter_by(parent_submission=post.id, top_comment_id=comment.id).count() + 1
			offset += 1
			if count > 50: break
	else:
		for comment in comments:
			comments2.append(comment)
			count += g.db.query(Comment.id).filter_by(parent_submission=post.id, parent_comment_id=comment.id).count() + 1
			offset += 1
			if count > 10: break

	if len(comments) == len(comments2): offset = None
	comments = comments2

	return render_template("comments.html", v=v, comments=comments, render_replies=True, pid=pid, sort=sort, offset=offset)


@app.post("/morecomments/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def morecomments(v, cid):
	tcid = g.db.query(Comment.top_comment_id).filter_by(id=cid).one_or_none()[0]

	if v:
		votes = g.db.query(CommentVote).filter_by(user_id=v.id).subquery()

		blocking = v.blocking.subquery()

		blocked = v.blocked.subquery()

		comments = g.db.query(
			Comment,
			votes.c.vote_type,
			blocking.c.id,
			blocked.c.id,
		).filter(Comment.top_comment_id == tcid, Comment.level > 10).join(
			votes,
			votes.c.comment_id == Comment.id,
			isouter=True
		).join(
			blocking,
			blocking.c.target_id == Comment.author_id,
			isouter=True
		).join(
			blocked,
			blocked.c.user_id == Comment.author_id,
			isouter=True
		)

		output = []
		dump = []
		for c in comments.all():
			comment = c[0]
			comment.voted = c[1] or 0
			comment.is_blocking = c[2] or 0
			comment.is_blocked = c[3] or 0
			if c[0].parent_comment_id == int(cid): output.append(comment)
			else: dump.append(comment)
		comments = output
	else:
		c = g.db.query(Comment).filter_by(id=cid).one_or_none()
		comments = c.replies

	return render_template("comments.html", v=v, comments=comments, render_replies=True)

@app.post("/edit_post/<pid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def edit_post(pid, v):
	if v and v.patron:
		if request.content_length > 8 * 1024 * 1024: return {"error":"Max file size is 8 MB."}, 413
	elif request.content_length > 4 * 1024 * 1024: return {"error":"Max file size is 4 MB."}, 413

	p = get_post(pid)

	if p.author_id != v.id and not (v.admin_level > 1 and v.admin_level > 2): abort(403)

	title = request.values.get("title", "").strip().replace('‎','')

	body = request.values.get("body", "").strip().replace('‎','')

	if len(body) > 20000: return {"error":"Character limit is 20000!"}, 403

	if v.marseyawarded:
		marregex = list(re.finditer("^(:[!#]{0,2}m\w+:\s*)+$", title, flags=re.A))
		if len(marregex) == 0: return {"error":"You can only type marseys!"}, 403
		if body:
			marregex = list(re.finditer("^(:[!#]{0,2}m\w+:\s*)+$", body, flags=re.A))
			if len(marregex) == 0: return {"error":"You can only type marseys!"}, 403

	if v.longpost and len(body) < 280 or ' [](' in body or body.startswith('[]('): return {"error":"You have to type more than 280 characters!"}, 403
	elif v.bird and len(body) > 140: return {"error":"You have to type less than 140 characters!"}, 403

	if title != p.title:
		if v.agendaposter and not v.marseyawarded: title = torture_ap(title, v.username)

		title_html = filter_emojis_only(title, edit=True)
		if v.marseyawarded and len(list(re.finditer('>[^<\s+]|[^>\s+]<', title_html, flags=re.A))): return {"error":"You can only type marseys!"}, 403
		p.title = title[:500]
		p.title_html = title_html

	if request.files.get("file") and request.headers.get("cf-ipcountry") != "T1":
		file=request.files["file"]
		if file.content_type.startswith('image/'):
			name = f'/images/{time.time()}'.replace('.','')[:-5] + '.webp'
			file.save(name)
			url = process_image(name)
			body += f"\n\n![]({url})"
		elif file.content_type.startswith('video/'):
			file.save("video.mp4")
			with open("video.mp4", 'rb') as f:
				try: url = requests.request("POST", "https://api.imgur.com/3/upload", headers={'Authorization': f'Client-ID {IMGUR_KEY}'}, files=[('video', f)]).json()['data']['link']
				except: return {"error": "Imgur error"}, 400
			if url.endswith('.'): url += 'mp4'
			body += f"\n\n{url}"
		else: return {"error": "Image/Video files only"}, 400

	if body != p.body:
		for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|webp|PNG|JPG|JPEG|GIF|WEBP|9999))', body, re.MULTILINE):
			if "wikipedia" not in i.group(1): body = body.replace(i.group(1), f'![]({i.group(1)})')

		if v.agendaposter and not v.marseyawarded: body = torture_ap(body, v.username)

		if not p.options.count():
			for i in re.finditer('\s*\$\$([^\$\n]+)\$\$\s*', body, flags=re.A):
				body = body.replace(i.group(0), "")
				c = Comment(author_id=AUTOPOLLER_ID,
					parent_submission=p.id,
					level=1,
					body_html=filter_emojis_only(i.group(1)),
					upvotes=0,
					is_bot=True
					)
				g.db.add(c)

		body_html = sanitize(body, edit=True)

		bans = filter_comment_html(body_html)
		if bans:
			ban = bans[0]
			reason = f"Remove the {ban.domain} link from your post and try again."
			if ban.reason:
				reason += f" {ban.reason}"
								
			return {"error": reason}, 403

		p.body = body
		if v.marseyawarded and len(list(re.finditer('>[^<\s+]|[^>\s+]<', body_html, flags=re.A))): return {"error":"You can only type marseys!"}, 40

		if v.longpost:
			if len(body) < 280 or ' [](' in body or body.startswith('[]('): return {"error":"You have to type more than 280 characters!"}, 403
		elif v.bird:
			if len(body) > 140 : return {"error":"You have to type less than 140 characters!"}, 403

		if len(body_html) > 40000: return {"error":"Submission body too long!"}, 400

		p.body_html = body_html

		if v.agendaposter and not v.marseyawarded and AGENDAPOSTER_PHRASE not in f'{p.body}{p.title}'.lower():

			p.is_banned = True
			p.ban_reason = "AutoJanny"

			g.db.add(p)

			body = AGENDAPOSTER_MSG.format(username=v.username, type='post', AGENDAPOSTER_PHRASE=AGENDAPOSTER_PHRASE)

			body_jannied_html = sanitize(body)

			c_jannied = Comment(author_id=NOTIFICATIONS_ID,
				parent_submission=p.id,
				level=1,
				over_18=False,
				is_bot=True,
				app_id=None,
				is_pinned='AutoJanny',
				distinguish_level=6,
				body_html=body_jannied_html,
				)

			g.db.add(c_jannied)
			g.db.flush()

			n = Notification(comment_id=c_jannied.id, user_id=v.id)
			g.db.add(n)
		

		notify_users = NOTIFY_USERS(body_html, v) | NOTIFY_USERS2(title, v)
		
		soup = BeautifulSoup(body_html, features="html.parser")
			
		cid = notif_comment(f"@{v.username} has mentioned you: [{p.title}]({p.permalink})")
		for x in notify_users:
			add_notif(cid, x)



	if (title != p.title or body != p.body) and v.id == p.author_id:
		if int(time.time()) - p.created_utc > 60 * 3: p.edited_utc = int(time.time())
		g.db.add(p)

	g.db.commit()

	return redirect(p.permalink)

def archiveorg(url):
	try: requests.get(f'https://web.archive.org/save/{url}', headers={'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}, timeout=100)
	except Exception as e: print(e)


def thumbnail_thread(pid):

	db = db_session()

	def expand_url(post_url, fragment_url):

		if fragment_url.startswith("https://"):
			return fragment_url
		elif fragment_url.startswith("https://"):
			return f"https://{fragment_url.split('https://')[1]}"
		elif fragment_url.startswith('//'):
			return f"https:{fragment_url}"
		elif fragment_url.startswith('/'):
			parsed_url = urlparse(post_url)
			return f"https://{parsed_url.netloc}{fragment_url}"
		else:
			return f"{post_url}{'/' if not post_url.endswith('/') else ''}{fragment_url}"

	post = db.query(Submission).filter_by(id=pid).one_or_none()
	
	if not post or not post.url:
		time.sleep(5)
		post = db.query(Submission).filter_by(id=pid).one_or_none()

	if not post or not post.url: return
	
	fetch_url = post.url

	if fetch_url.startswith('/'): fetch_url = f"{SITE_FULL}{fetch_url}"

	headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36"}

	try:
		x=requests.get(fetch_url, headers=headers, timeout=5)
	except:
		db.close()
		return

	if x.status_code != 200:
		db.close()
		return
	


	if x.headers.get("Content-Type","").startswith("text/html"):
		soup=BeautifulSoup(x.content, 'html.parser')

		thumb_candidate_urls=[]

		meta_tags = [
			"drama:thumbnail",
			"twitter:image",
			"og:image",
			"thumbnail"
			]

		for tag_name in meta_tags:
			

			tag = soup.find(
				'meta', 
				attrs={
					"name": tag_name, 
					"content": True
					}
				)
			if not tag:
				tag = soup.find(
					'meta',
					attrs={
						'property': tag_name,
						'content': True
						}
					)
			if tag:
				thumb_candidate_urls.append(expand_url(post.url, tag['content']))

		for tag in soup.find_all("img", attrs={'src':True}):
			thumb_candidate_urls.append(expand_url(post.url, tag['src']))


		for url in thumb_candidate_urls:

			try:
				image_req=requests.get(url, headers=headers, timeout=5)
			except:
				continue

			if image_req.status_code >= 400:
				continue

			if not image_req.headers.get("Content-Type","").startswith("image/"):
				continue

			if image_req.headers.get("Content-Type","").startswith("image/svg"):
				continue

			image = PILimage.open(BytesIO(image_req.content))
			if image.width < 30 or image.height < 30:
				continue

			break

		else:
			db.close()
			return



	elif x.headers.get("Content-Type","").startswith("image/"):
		image_req=x
		image = PILimage.open(BytesIO(x.content))

	else:
		db.close()
		return

	name = f'/images/{time.time()}'.replace('.','')[:-5] + '.webp'

	with open(name, "wb") as file:
		for chunk in image_req.iter_content(1024):
			file.write(chunk)

	post.thumburl = process_image(name, resize=100)
	db.add(post)
	db.commit()
	db.close()
	return


@app.post("/submit")
@limiter.limit("1/second;6/minute;200/hour;1000/day")
@auth_required
def submit_post(v):
	if v.is_suspended: return {"error": "You can't perform this action while banned."}, 403
	
	if v and v.patron:
		if request.content_length > 8 * 1024 * 1024: return {"error": "Max file size is 8 MB."}, 413
	elif request.content_length > 4 * 1024 * 1024: return {"error": "Max file size is 4 MB."}, 413

	title = request.values.get("title", "").strip()[:500].replace('‎','')

	url = request.values.get("url", "").strip()

	if v.agendaposter and not v.marseyawarded: title = torture_ap(title, v.username)

	title_html = filter_emojis_only(title)
	body = request.values.get("body", "").strip().replace('‎','')

	if v.marseyawarded and len(list(re.finditer('>[^<\s+]|[^>\s+]<', title_html, flags=re.A))): return {"error":"You can only type marseys!"}, 40

	if v.longpost:
		if len(body) < 280 or ' [](' in body or body.startswith('[]('): return {"error":"You have to type more than 280 characters!"}, 403
	elif v.bird:
		if len(body) > 140 : return {"error":"You have to type less than 140 characters!"}, 403

	if url:
		if "/i.imgur.com/" in url: url = url.replace(".png", ".webp").replace(".jpg", ".webp").replace(".jpeg", ".webp")
		elif "/media.giphy.com/" in url or "/c.tenor.com/" in url: url = url.replace(".gif", ".webp")
		elif "/i.ibb.com/" in url: url = url.replace(".png", ".webp").replace(".jpg", ".webp").replace(".jpeg", ".webp").replace(".gif", ".webp")

		for rd in ["://reddit.com", "://new.reddit.com", "://www.reddit.com", "://redd.it", "://libredd.it"]:
			url = url.replace(rd, "://old.reddit.com")

		url = url.replace("old.reddit.com/gallery", "new.reddit.com/gallery").replace("https://youtu.be/", "https://youtube.com/watch?v=").replace("https://music.youtube.com/watch?v=", "https://youtube.com/watch?v=").replace("https://open.spotify.com/", "https://open.spotify.com/embed/").replace("https://streamable.com/", "https://streamable.com/e/").replace("https://youtube.com/shorts/", "https://youtube.com/watch?v=").replace("https://mobile.twitter", "https://twitter").replace("https://m.facebook", "https://facebook").replace("m.wikipedia.org", "wikipedia.org").replace("https://m.youtube", "https://youtube").replace("https://www.youtube", "https://youtube")

		if url.startswith("https://streamable.com/") and not url.startswith("https://streamable.com/e/"): url = url.replace("https://streamable.com/", "https://streamable.com/e/")

		parsed_url = urlparse(url)

		domain = parsed_url.netloc
		if domain == 'old.reddit.com':
			new_url = ParseResult(scheme="https",
					netloc=parsed_url.netloc,
					path=parsed_url.path,
					params=parsed_url.params,
					query=None,
					fragment=parsed_url.fragment)
		else:
			qd = parse_qs(parsed_url.query)
			filtered = {k: val for k, val in qd.items() if not k.startswith('utm_') and not k.startswith('ref_')}

			new_url = ParseResult(scheme="https",
								netloc=parsed_url.netloc,
								path=parsed_url.path,
								params=parsed_url.params,
								query=urlencode(filtered, doseq=True),
								fragment=parsed_url.fragment)
		
		url = urlunparse(new_url)

		if SITE != 'localhost':
			repost = g.db.query(Submission).filter(
				Submission.url.ilike(url),
				Submission.deleted_utc == 0,
				Submission.is_banned == False
			).one_or_none()

			if repost: return redirect(repost.permalink)

		domain_obj = get_domain(domain)
		if domain_obj:
			if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error":domain_obj.reason}, 400
			return render_template("submit.html", v=v, error=domain_obj.reason, title=title, url=url, body=request.values.get("body", "")), 400
		elif "twitter.com" == domain:
			try: embed = requests.get("https://publish.twitter.com/oembed", timeout=5, params={"url":url, "omit_script":"t"}).json()["html"]
			except: embed = None
		elif url.startswith('https://youtube.com/watch?v='):
			url = unquote(url).replace('?t', '&t')
			yt_id = url.split('https://youtube.com/watch?v=')[1].split('&')[0].split('%')[0]
			params = parse_qs(urlparse(url).query)
			t = params.get('t', params.get('start', [0]))[0]
			if isinstance(t, str): t = t.replace('s','')
			embed = f'<lite-youtube videoid="{yt_id}" params="autoplay=1&modestbranding=1'
			if t: embed += f'&start={t}'
			embed += '"></lite-youtube>'
		elif app.config['SERVER_NAME'] in domain and "/post/" in url and "context" not in url:
			id = url.split("/post/")[1]
			if "/" in id: id = id.split("/")[0]
			embed = id
		else: embed = None
	else: embed = None

	if not url and not request.values.get("body") and not request.files.get("file", None):
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": "`url` or `body` parameter required."}, 400
		return render_template("submit.html", v=v, error="Please enter a url or some text.", title=title, url=url, body=request.values.get("body", "")), 400

	if not title:
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": "Please enter a better title"}, 400
		return render_template("submit.html", v=v, error="Please enter a better title.", title=title, url=url, body=request.values.get("body", "")), 400


	elif len(title) > 500:
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": "500 character limit for titles"}, 400
		else: render_template("submit.html", v=v, error="500 character limit for titles.", title=title[:500], url=url, body=request.values.get("body", "")), 400

	if v.marseyawarded:
		marregex = list(re.finditer("^(:[!#]{0,2}m\w+:\s*)+$", title, flags=re.A))
		if len(marregex) == 0: return {"error":"You can only type marseys!"}, 403
		if body:
			marregex = list(re.finditer("^(:[!#]{0,2}m\w+:\s*)+$", body, flags=re.A))
			if len(marregex) == 0: return {"error":"You can only type marseys!"}, 403

	if v.longpost and len(body) < 280 or ' [](' in body or body.startswith('[]('): return {"error":"You have to type more than 280 characters!"}, 403
	elif v.bird and len(body) > 140: return {"error":"You have to type less than 140 characters!"}, 403

	dup = g.db.query(Submission).filter(
		Submission.author_id == v.id,
		Submission.deleted_utc == 0,
		Submission.title == title,
		Submission.url == url,
		Submission.body == body
	).one_or_none()

	if dup: return redirect(dup.permalink)

	now = int(time.time())
	cutoff = now - 60 * 60 * 24


	similar_posts = g.db.query(Submission).filter(
					Submission.author_id == v.id,
					Submission.title.op('<->')(title) < app.config["SPAM_SIMILARITY_THRESHOLD"],
					Submission.created_utc > cutoff
	).all()

	if url:
		similar_urls = g.db.query(Submission).filter(
					Submission.author_id == v.id,
					Submission.url.op('<->')(url) < app.config["SPAM_URL_SIMILARITY_THRESHOLD"],
					Submission.created_utc > cutoff
		).all()
	else: similar_urls = []

	threshold = app.config["SPAM_SIMILAR_COUNT_THRESHOLD"]
	if v.age >= (60 * 60 * 24 * 7): threshold *= 3
	elif v.age >= (60 * 60 * 24): threshold *= 2

	if max(len(similar_urls), len(similar_posts)) >= threshold:

		text = "Your account has been suspended for 1 day for the following reason:\n\n> Too much spam!"
		send_repeatable_notification(v.id, text)

		v.ban(reason="Spamming.",
			  days=1)

		for post in similar_posts + similar_urls:
			post.is_banned = True
			post.is_pinned = False
			post.ban_reason = "AutoJanny"
			g.db.add(post)
			ma=ModAction(
					user_id=AUTOJANNY_ID,
					target_submission_id=post.id,
					kind="ban_post",
					_note="spam"
					)
			g.db.add(ma)
		return redirect(f"{SITE_FULL}/notifications")

	if len(str(body)) > 20000:

		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error":"There's a 20000 character limit for text body."}, 400
		return render_template("submit.html", v=v, error="There's a 20000 character limit for text body.", title=title, url=url, body=request.values.get("body", "")), 400

	if len(url) > 2048:

		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error":"2048 character limit for URLs."}, 400
		return render_template("submit.html", v=v, error="2048 character limit for URLs.", title=title, url=url,body=request.values.get("body", "")), 400

	for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|webp|PNG|JPG|JPEG|GIF|WEBP|9999))', body, re.MULTILINE):
		if "wikipedia" not in i.group(1): body = body.replace(i.group(1), f'![]({i.group(1)})')

	if v and v.admin_level > 2:
		bet_options = []
		for i in re.finditer('\s*\$\$\$([^\$\n]+)\$\$\$\s*', body, flags=re.A):
			bet_options.append(i.group(1))
			body = body.replace(i.group(0), "")

	options = []
	for i in re.finditer('\s*\$\$([^\$\n]+)\$\$\s*', body, flags=re.A):
		options.append(i.group(1))
		body = body.replace(i.group(0), "")

	if v.agendaposter and not v.marseyawarded: body = torture_ap(body, v.username)

	if request.files.get("file2") and request.headers.get("cf-ipcountry") != "T1":
		file=request.files["file2"]
		if file.content_type.startswith('image/'):
			name = f'/images/{time.time()}'.replace('.','')[:-5] + '.webp'
			file.save(name)
			body += f"\n\n![]({process_image(name)})"
		elif file.content_type.startswith('video/'):
			file.save("video.mp4")
			with open("video.mp4", 'rb') as f:
				try: url = requests.request("POST", "https://api.imgur.com/3/upload", headers={'Authorization': f'Client-ID {IMGUR_KEY}'}, files=[('video', f)]).json()['data']['link']
				except: return {"error": "Imgur error"}, 400
			if url.endswith('.'): url += 'mp4'
			body += f"\n\n{url}"
		else:
			if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": "Image/Video files only"}, 400
			return render_template("submit.html", v=v, error=f"Image/Video files only."), 400

	if '#fortune' in body:
		body = body.replace('#fortune', '')
		body += '\n\n<p>' + random.choice(FORTUNE_REPLIES) + '</p>'

	body_html = sanitize(body)

	if v.marseyawarded and len(list(re.finditer('>[^<\s+]|[^>\s+]<', body_html, flags=re.A))): return {"error":"You can only type marseys!"}, 400

	if v.longpost:
		if len(body) < 280 or ' [](' in body or body.startswith('[]('): return {"error":"You have to type more than 280 characters!"}, 403
	elif v.bird:
		if len(body) > 140 : return {"error":"You have to type less than 140 characters!"}, 403

	if len(body_html) > 40000: return {"error":"Submission body too long!"}, 400

	bans = filter_comment_html(body_html)
	if bans:
		ban = bans[0]
		reason = f"Remove the {ban.domain} link from your post and try again."
		if ban.reason: reason += f" {ban.reason}"
		if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": reason}, 403
		return render_template("submit.html", v=v, error=reason, title=title, url=url, body=request.values.get("body", "")), 403

	if v.club_allowed == False: club = False
	else: club = bool(request.values.get("club",""))
	
	if embed and len(embed) > 1500: embed = None

	new_post = Submission(
		private=bool(request.values.get("private","")),
		club=club,
		author_id=v.id,
		over_18=bool(request.values.get("over_18","")),
		app_id=v.client.application.id if v.client else None,
		is_bot = request.headers.get("Authorization"),
		url=url,
		body=body[:20000],
		body_html=body_html,
		embed_url=embed,
		title=title[:500],
		title_html=title_html,
		created_utc=int(time.time())	
	)

	g.db.add(new_post)
	g.db.flush()

	if v and v.admin_level > 2:
		for option in bet_options:
			bet_option = Comment(author_id=AUTOBETTER_ID,
				parent_submission=new_post.id,
				level=1,
				body_html=filter_emojis_only(option),
				upvotes=0,
				is_bot=True
				)

			g.db.add(bet_option)

	for option in options:
		c = Comment(author_id=AUTOPOLLER_ID,
			parent_submission=new_post.id,
			level=1,
			body_html=filter_emojis_only(option),
			upvotes=0,
			is_bot=True
			)

		g.db.add(c)

	vote = Vote(user_id=v.id,
				vote_type=1,
				submission_id=new_post.id
				)
	g.db.add(vote)
	
	if request.files.get('file') and request.headers.get("cf-ipcountry") != "T1":

		file = request.files['file']

		if file.content_type.startswith('image/'):
			name = f'/images/{time.time()}'.replace('.','')[:-5] + '.webp'
			file.save(name)
			new_post.url = process_image(name)

			name2 = name.replace('.webp', 'r.webp')
			copyfile(name, name2)
			new_post.thumburl = process_image(name2, resize=100)	
		elif file.content_type.startswith('video/'):
			file.save("video.mp4")
			with open("video.mp4", 'rb') as f:
				try: url = requests.request("POST", "https://api.imgur.com/3/upload", headers={'Authorization': f'Client-ID {IMGUR_KEY}'}, files=[('video', f)]).json()['data']['link']
				except: return {"error": "Imgur error"}, 400
			if url.endswith('.'): url += 'mp4'
			new_post.url = url
		else:
			if request.headers.get("Authorization") or request.headers.get("xhr"): return {"error": "File type not allowed"}, 400
			return render_template("submit.html", v=v, error="File type not allowed.", title=title, body=request.values.get("body", "")), 400

		
	if not new_post.thumburl and new_post.url:
		if request.host in new_post.url or new_post.url.startswith('/') or request.host == 'rdrama.net' and 'rdrama' in new_post.domain:
			new_post.thumburl = f'/static/assets/images/{SITE_NAME}/site_preview.webp'
		elif request.headers.get('cf-ipcountry')!="T1":
			gevent.spawn( thumbnail_thread, new_post.id)

	if not new_post.private:

		notify_users = NOTIFY_USERS(body_html, v) | NOTIFY_USERS2(title, v)

		cid = notif_comment(f"@{v.username} has mentioned you: [{title}]({new_post.permalink})")
		for x in notify_users:
			add_notif(cid, x)

		cid = notif_comment(f"@{v.username} has made a new post: [{title}]({new_post.permalink})", autojanny=True)
		for follow in v.followers:
			user = get_account(follow.user_id)
			if new_post.club and not user.paid_dues: continue
			add_notif(cid, user.id)

	if v.agendaposter and not v.marseyawarded and AGENDAPOSTER_PHRASE not in f'{new_post.body}{new_post.title}'.lower():
		new_post.is_banned = True
		new_post.ban_reason = "AutoJanny"

		body = AGENDAPOSTER_MSG.format(username=v.username, type='post', AGENDAPOSTER_PHRASE=AGENDAPOSTER_PHRASE)

		body_jannied_html = sanitize(body)



		c_jannied = Comment(author_id=NOTIFICATIONS_ID,
			parent_submission=new_post.id,
			level=1,
			over_18=False,
			is_bot=True,
			app_id=None,
			is_pinned='AutoJanny',
			distinguish_level=6,
			body_html=body_jannied_html,
		)

		g.db.add(c_jannied)
		g.db.flush()

		n = Notification(comment_id=c_jannied.id, user_id=v.id)
		g.db.add(n)

	if v.id == CARP_ID:
		if random.random() < 0.02: body = "i love you carp"
		else: body = ":#marseyfuckoffcarp:"
	elif v.id == LAWLZ_ID:
		if random.random() < 0.5: body = "wow, this lawlzpost sucks!"
		else: body = "wow, a good lawlzpost for once!"
	else: body = random.choice(snappyquotes)
	body += "\n\n"

	if new_post.url:
		if new_post.url.startswith('https://old.reddit.com/r/'):
			rev = new_post.url.replace('https://old.reddit.com/', '')
			rev = f"* [unddit.com](https://unddit.com/{rev})\n"
		else: rev = ''
		newposturl = new_post.url
		if newposturl.startswith('/'): newposturl = f"{SITE_FULL}{newposturl}"
		body += f"Snapshots:\n\n{rev}* [archive.org](https://web.archive.org/{newposturl})\n* [archive.ph](https://archive.ph/?url={quote(newposturl)}&run=1) (click to archive)\n\n"			
		gevent.spawn(archiveorg, newposturl)

	url_regex = '<a href=\"(https?:\/\/[a-z]{1,20}\.[^\"]+)\" rel=\"nofollow noopener noreferrer\" target=\"_blank\">(.+)<\/a>'
	for url_match in re.finditer(url_regex, new_post.body_html):
		href = url_match.group(1)
		if not href: continue

		title = url_match.group(2)
		if "Snapshots:\n\n" not in body: body += "Snapshots:\n\n"			

		if f'**[{title}]({href})**:\n\n' not in body:
			body += f'**[{title}]({href})**:\n\n'
			if href.startswith('https://old.reddit.com/'):
				body += f'* [unddit.com](https://unddit.com/{href.replace("https://old.reddit.com/", "")})\n'
			body += f'* [archive.org](https://web.archive.org/{href})\n'
			body += f'* [archive.ph](https://archive.ph/?url={quote(href)}&run=1) (click to archive)\n\n'
			gevent.spawn(archiveorg, href)

	body_html = sanitize(body)

	if len(body_html) < 40000:
		c = Comment(author_id=SNAPPY_ID,
			distinguish_level=6,
			parent_submission=new_post.id,
			level=1,
			over_18=False,
			is_bot=True,
			app_id=None,
			body_html=body_html
			)

		g.db.add(c)

		snappy = g.db.query(User).filter_by(id = SNAPPY_ID).one_or_none()
		snappy.comment_count += 1
		snappy.coins += 1
		g.db.add(snappy)

		if not v.is_blocking(snappy):
			g.db.flush()
			n = Notification(comment_id=c.id, user_id=v.id)
			g.db.add(n)
		
		if body == '!slots1000':
			slots = Slots(g)
			slots.check_for_slots_command(body, snappy, c)

		new_post.comment_count += 1

	v.post_count = g.db.query(Submission.id).filter_by(author_id=v.id, is_banned=False, deleted_utc=0).count()
	g.db.add(v)

	cache.delete_memoized(frontlist)
	cache.delete_memoized(User.userpagelisting)
	if v.admin_level > 0 and ("[changelog]" in new_post.title.lower() or "(changelog)" in new_post.title.lower()) and not new_post.private:
		send_discord_message(f"{SITE_FULL}{new_post.permalink}")
		cache.delete_memoized(changeloglist)

	if v.id in (PIZZASHILL_ID, HIL_ID):
		autovote = Vote(user_id=CARP_ID, submission_id=new_post.id, vote_type=1)
		g.db.add(autovote)
		autovote = Vote(user_id=AEVANN_ID, submission_id=new_post.id, vote_type=1)
		g.db.add(autovote)
		autovote = Vote(user_id=CRAT_ID, submission_id=new_post.id, vote_type=1)
		g.db.add(autovote)
		v.coins += 3
		v.truecoins += 3
		g.db.add(v)
		new_post.upvotes += 3
		g.db.add(new_post)

	g.db.commit()

	if request.headers.get("Authorization"): return new_post.json
	else:
		new_post.voted = 1
		if 'megathread' in new_post.title.lower(): sort = 'new'
		else: sort = v.defaultsortingcomments
		if len(body_html) < 40000: new_post.replies = [c]
		return render_template('submission.html', v=v, p=new_post, sort=sort, render_replies=True, offset=0, success=True)


@app.post("/delete_post/<pid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def delete_post_pid(pid, v):

	post = get_post(pid)
	if post.author_id != v.id:
		abort(403)

	post.deleted_utc = int(time.time())
	post.is_pinned = False
	post.stickied = None

	g.db.add(post)

	cache.delete_memoized(frontlist)

	g.db.commit()

	return {"message": "Post deleted!"}

@app.post("/undelete_post/<pid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def undelete_post_pid(pid, v):
	post = get_post(pid)
	if post.author_id != v.id: abort(403)
	post.deleted_utc =0
	g.db.add(post)

	cache.delete_memoized(frontlist)

	g.db.commit()

	return {"message": "Post undeleted!"}


@app.post("/toggle_comment_nsfw/<cid>")
@auth_required
def toggle_comment_nsfw(cid, v):

	comment = g.db.query(Comment).filter_by(id=cid).one_or_none()
	if comment.author_id != v.id and not v.admin_level > 1: abort(403)
	comment.over_18 = not comment.over_18
	g.db.add(comment)

	g.db.commit()

	if comment.over_18: return {"message": "Comment has been marked as +18!"}
	else: return {"message": "Comment has been unmarked as +18!"}
	
@app.post("/toggle_post_nsfw/<pid>")
@auth_required
def toggle_post_nsfw(pid, v):

	post = get_post(pid)

	if post.author_id != v.id and not v.admin_level > 1:
		abort(403)

	post.over_18 = not post.over_18
	g.db.add(post)

	if post.author_id!=v.id:
		ma=ModAction(
			kind="set_nsfw" if post.over_18 else "unset_nsfw",
			user_id=v.id,
			target_submission_id=post.id,
			)
		g.db.add(ma)

	g.db.commit()

	if post.over_18: return {"message": "Post has been marked as +18!"}
	else: return {"message": "Post has been unmarked as +18!"}

@app.post("/save_post/<pid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def save_post(pid, v):

	post=get_post(pid)

	save = g.db.query(SaveRelationship).filter_by(user_id=v.id, submission_id=post.id, type=1).one_or_none()

	if not save:
		new_save=SaveRelationship(user_id=v.id, submission_id=post.id, type=1)
		g.db.add(new_save)
		g.db.commit()

	return {"message": "Post saved!"}

@app.post("/unsave_post/<pid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def unsave_post(pid, v):

	post=get_post(pid)

	save = g.db.query(SaveRelationship).filter_by(user_id=v.id, submission_id=post.id, type=1).one_or_none()

	if save:
		g.db.delete(save)
		g.db.commit()

	return {"message": "Post unsaved!"}

@app.post("/pin/<post_id>")
@auth_required
def api_pin_post(post_id, v):

	post = g.db.query(Submission).filter_by(id=post_id).one_or_none()
	if post:
		if v.id != post.author_id: return {"error": "Only the post author's can do that!"}
		post.is_pinned = not post.is_pinned
		g.db.add(post)

		cache.delete_memoized(User.userpagelisting)

		g.db.commit()
		if post.is_pinned: return {"message": "Post pinned!"}
		else: return {"message": "Post unpinned!"}