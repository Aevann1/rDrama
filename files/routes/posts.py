import time
import mistletoe
import gevent
import requests
from files.helpers.wrappers import *
from files.helpers.sanitize import *
from files.helpers.filters import *
from files.helpers.markdown import *
from files.helpers.session import *
from files.helpers.alerts import send_notification
from files.helpers.discord import send_message
from files.helpers.const import *
from files.classes import *
from flask import *
from io import BytesIO
from files.__main__ import app, limiter, cache, db_session
from PIL import Image as PILimage
from .front import frontlist, changeloglist
from urllib.parse import ParseResult, urlunparse, urlparse, quote

site = environ.get("DOMAIN").strip()
CATBOX_KEY = environ.get("CATBOX_KEY").strip()

with open("snappy.txt", "r") as f: snappyquotes = f.read().split("{[para]}")

if site == 'pcmemes.net' or site == 'ashithole.com': snappyquotes = [x for x in snappyquotes if 'drama' not in x.lower()]

@app.post("/toggle_club/<pid>")
@auth_required
def toggle_club(pid, v):

	post = get_post(pid)

	if post.author_id != v.id and v.admin_level == 0: abort(403)

	post.club = not post.club
	g.db.add(post)

	if post.author_id!=v.id:
		ma=ModAction(
			kind="club" if post.club else "unclub",
			user_id=v.id,
			target_submission_id=post.id,
			)
		g.db.add(ma)

	g.db.commit()

	if post.club: return {"message": "Post has been marked as club-only!"}
	else: return {"message": "Post has been unmarked as club-only!"}


@app.post("/publish/<pid>")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def publish(pid, v):
	post = get_post(pid)
	if not post.author_id == v.id: abort(403)
	post.private = False
	g.db.add(post)
	
	notify_users = set()
	soup = BeautifulSoup(post.body_html, features="html.parser")
	for mention in soup.find_all("a", href=re.compile("^/@(\w+)")):
		username = mention["href"].split("@")[1]
		user = g.db.query(User).filter_by(username=username).first()
		if user and not v.any_block_exists(user) and user.id != v.id: notify_users.add(user.id)
		
	if request.host == 'rdrama.net':
		if 'aevann' in f'{post.body_html}{post.title}'.lower() and 1 not in notify_users: notify_users.add(1)
		if 'joan' in f'{post.body_html}{post.title}'.lower() and 28 not in notify_users: notify_users.add(28)
		if 'carp' in f'{post.body_html}{post.title}'.lower() and 995 not in notify_users:
			notify_users.add(995)
			notify_users.add(541)
		if ('idio3' in f'{post.body_html}{post.title}'.lower() or 'idio ' in f'{post.body_html}{post.title}'.lower()) and 30 not in notify_users: notify_users.add(30)

	for x in notify_users: send_notification(x, f"@{v.username} has mentioned you: http://{site}{post.permalink}")

	for follow in v.followers:
		user = get_account(follow.user_id)
		if post.club and not user.club_allowed: continue
		send_notification(user.id, f"@{v.username} has made a new post: [{post.title}](http://{site}{post.permalink})", True)

	cache.delete_memoized(frontlist)

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

	if not v and not request.path.startswith('/logged_out') and not request.headers.get("Authorization"): return redirect(f"/logged_out{request.full_path}")

	if v and request.path.startswith('/logged_out'): v = None

	try: pid = int(pid)
	except Exception as e: pass

	if v: defaultsortingcomments = v.defaultsortingcomments
	else: defaultsortingcomments = "top"
	sort=request.values.get("sort", defaultsortingcomments)

	try: pid = int(pid)
	except:
		try: pid = int(pid, 36)
		except: abort(404)

	post = get_post(pid, v=v)

	if post.club and not (v and v.paid_dues) or post.private and not (v and (v.id == post.author_id or v.admin_level > 1)): abort(403)

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
 
		comments=comments.filter(
			Comment.parent_submission == post.id,
			Comment.author_id != AUTOPOLLER_ID,
		).join(
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

		if sort == "new":
			comments = comments.order_by(Comment.created_utc.desc())
		elif sort == "old":
			comments = comments.order_by(Comment.created_utc.asc())
		elif sort == "controversial":
			comments = comments.order_by(-1 * Comment.upvotes * Comment.downvotes * Comment.downvotes)
		elif sort == "top":
			comments = comments.order_by(-Comment.upvotes - Comment.downvotes)
		elif sort == "bottom":
			comments = comments.order_by(Comment.upvotes - Comment.downvotes)

		output = []
		for c in comments.all():
			comment = c[0]
			comment.voted = c[1] or 0
			comment.is_blocking = c[2] or 0
			comment.is_blocked = c[3] or 0
			output.append(comment)

		post.replies = [x for x in output if x.is_pinned] + [x for x in output if x.level == 1 and not x.is_pinned]

	else:
		comments = g.db.query(Comment).join(User, User.id == Comment.author_id).filter(User.shadowbanned == None, Comment.parent_submission == post.id, Comment.author_id != AUTOPOLLER_ID)

		if sort == "new":
			comments = comments.order_by(Comment.created_utc.desc())
		elif sort == "old":
			comments = comments.order_by(Comment.created_utc.asc())
		elif sort == "controversial":
			comments = comments.order_by(-1 * Comment.upvotes * Comment.downvotes * Comment.downvotes)
		elif sort == "top":
			comments = comments.order_by(-Comment.upvotes - Comment.downvotes)
		elif sort == "bottom":
			comments = comments.order_by(Comment.upvotes - Comment.downvotes)

		post.replies = comments.filter(Comment.is_pinned != None).all() + comments.filter(Comment.level == 1, Comment.is_pinned == None).all()

	post.views += 1
	g.db.add(post)
	if isinstance(session.get('over_18', 0), dict): session["over_18"] = 0
	if post.over_18 and not (v and v.over_18) and not session.get('over_18', 0) >= int(time.time()):
		if request.headers.get("Authorization"): return {"error":"Must be 18+ to view"}, 451
		else: return render_template("errors/nsfw.html", v=v)

	g.db.commit()
	if request.headers.get("Authorization"): return post.json
	else:
		if post.is_banned and not (v and (v.admin_level > 1 or post.author_id == v.id)): template = "submission_banned.html"
		else: template = "submission.html"
		return render_template(template, v=v, p=post, sort=sort, render_replies=True)


@app.post("/edit_post/<pid>")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def edit_post(pid, v):

	p = get_post(pid)

	if p.author_id != v.id and not (v.admin_level > 1 and v.admin_level > 2): abort(403)

	title = request.values.get("title", "").strip()
	body = request.values.get("body", "").strip()

	if len(body) > 10000: return {"error":"Character limit is 10000!"}, 403

	if v.marseyawarded:
		if time.time() > v.marseyawarded:
			v.marseyawarded = None
			g.db.add(v)
		else:
			marregex = list(re.finditer("^(:!?m\w+:\s*)+$", title))
			if len(marregex) == 0: return {"error":"You can only type marseys!"}, 403
			if body:
				marregex = list(re.finditer("^(:!?m\w+:\s*)+$", body))
				if len(marregex) == 0: return {"error":"You can only type marseys!"}, 403

	if v.longpost:
		if time.time() > v.longpost:
			v.longpost = None
			g.db.add(v)
		elif len(body) < 280: return {"error":"You have to type more than 280 characters!"}, 403

	if title != p.title:
		title_html = filter_title(title)
		if v.marseyawarded and len(list(re.finditer('>[^<\s+]|[^>\s+]<', title_html))) > 0: return {"error":"You can only type marseys!"}, 403
		p.title = title
		p.title_html = title_html

	if body != p.body:
		for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|webp|PNG|JPG|JPEG|GIF|WEBP|9999))', body, re.MULTILINE):
			if "wikipedia" not in i.group(1): body = body.replace(i.group(1), f'![]({i.group(1)})')
		body_md = CustomRenderer().render(mistletoe.Document(body))
		body_html = sanitize(body_md)

		bans = filter_comment_html(body_html)
		if bans:
			ban = bans[0]
			reason = f"Remove the {ban.domain} link from your post and try again."
			if ban.reason:
				reason += f" {ban.reason}"
								
			return {"error": reason}, 403

		p.body = body
		if v.marseyawarded and len(list(re.finditer('>[^<\s+]|[^>\s+]<', body_html))) > 0: return {"error":"You can only type marseys!"}, 40

		if v.longpost and len(body) < 280: return {"error":"You have to type more than 280 characters!"}, 403

		p.body_html = body_html

		if "rama" in request.host and "ivermectin" in body_html.lower():

			p.is_banned = True
			p.ban_reason = "AutoJanny"

			g.db.add(p)

			body = VAXX_MSG.format(username=v.username)

			body_md = CustomRenderer().render(mistletoe.Document(body))

			body_jannied_html = sanitize(body_md)


			c_jannied = Comment(author_id=AUTOJANNY_ID,
				parent_submission=p.id,
				level=1,
				over_18=False,
				is_bot=True,
				app_id=None,
				is_pinned=True,
				distinguish_level=6,
				body_html=body_jannied_html,
				)

			g.db.add(c_jannied)
			g.db.flush()


			n = Notification(comment_id=c_jannied.id, user_id=v.id)
			g.db.add(n)


		if v.agendaposter and not v.marseyawarded and "trans lives matter" not in body_html.lower():

			p.is_banned = True
			p.ban_reason = "AutoJanny"

			g.db.add(p)

			body = AGENDAPOSTER_MSG.format(username=v.username)

			body_md = CustomRenderer().render(mistletoe.Document(body))

			body_jannied_html = sanitize(body_md)

			c_jannied = Comment(author_id=AUTOJANNY_ID,
				parent_submission=p.id,
				level=1,
				over_18=False,
				is_bot=True,
				app_id=None,
				is_pinned=True,
				distinguish_level=6,
				body_html=body_jannied_html,
				)

			g.db.add(c_jannied)
			g.db.flush()

			n = Notification(comment_id=c_jannied.id, user_id=v.id)
			g.db.add(n)
		

		notify_users = set()
		
		soup = BeautifulSoup(body_html, features="html.parser")
		for mention in soup.find_all("a", href=re.compile("^/@(\w+)")):
			username = mention["href"].split("@")[1]
			user = g.db.query(User).filter_by(username=username).first()
			if user and not v.any_block_exists(user) and user.id != v.id: notify_users.add(user.id)
			
		message = f"@{v.username} has mentioned you: http://{site}{p.permalink}"

		if request.host == 'rdrama.net':
			if 'aevann' in f'{body_html}{title}'.lower() and 1 not in notify_users: notify_users.add(1)
			if 'joan' in f'{body_html}{title}'.lower() and 28 not in notify_users: notify_users.add(28)
			if 'carp' in f'{body_html}{title}'.lower() and 995 not in notify_users:
				notify_users.add(995)
				notify_users.add(541)
			if ('idio3' in f'{body_html}{title}'.lower() or 'idio ' in f'{body_html}{title}'.lower()) and 30 not in notify_users: notify_users.add(30)

		for x in notify_users:
			existing = g.db.query(Comment.id).filter(Comment.author_id == NOTIFICATIONS_ID, Comment.body == message, Comment.notifiedto == x).first()
			if not existing: send_notification(x, message)


	if (title != p.title or body != p.body) and v.id == p.author_id:
		if int(time.time()) - p.created_utc > 60 * 3: p.edited_utc = int(time.time())
		g.db.add(p)

	g.db.commit()

	return redirect(p.permalink)

@app.get("/submit/title")
@limiter.limit("6/minute")
@auth_required
def get_post_title(v):

	url = request.values.get("url", None)
	if not url: return abort(400)

	headers = {"User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36"}
	try: x = requests.get(url, headers=headers, timeout=5)
	except BaseException: return {"error": "Could not reach page"}, 400

	if not x.status_code == 200: return {"error": f"Page returned {x.status_code}"}, x.status_code

	try:
		soup = BeautifulSoup(x.content, 'html.parser')
		return {"url": url, "title": soup.find('title').string}
	except BaseException:
		return {"error": f"Could not find a title"}, 400

def archiveorg(url):
	try: requests.get(f'https://web.archive.org/save/{url}', headers={'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}, timeout=100)
	except Exception as e: print(e)


def thumbnail_thread(pid):

	def expand_url(post_url, fragment_url):

		if fragment_url.startswith("https://"):
			return fragment_url
		elif fragment_url.startswith("http://"):
			return f"https://{fragment_url.split('http://')[1]}"
		elif fragment_url.startswith('//'):
			return f"https:{fragment_url}"
		elif fragment_url.startswith('/'):
			parsed_url = urlparse(post_url)
			return f"https://{parsed_url.netloc}{fragment_url}"
		else:
			return f"{post_url}{'/' if not post_url.endswith('/') else ''}{fragment_url}"

	db = db_session()

	post = db.query(Submission).filter_by(id=pid).first()
	
	if not post:
		time.sleep(5)
		post = db.query(Submission).filter_by(id=pid).first()

	fetch_url=post.url

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

	name = f'/images/{int(time.time())}{secrets.token_urlsafe(2)}.webp'

	with open(name, "wb") as file:
		for chunk in image_req.iter_content(1024):
			file.write(chunk)

	post.thumburl = "https://" + site + process_image(name, True)
	db.add(post)
	db.commit()
	db.close()
	return


@app.post("/submit")
@limiter.limit("1/second")
@limiter.limit("6/minute")
@is_not_banned
@validate_formkey
def submit_post(v):
	if v and v.patron:
		if request.content_length > 8 * 1024 * 1024: return "Max file size is 8 MB.", 413
	elif request.content_length > 4 * 1024 * 1024: return "Max file size is 4 MB.", 413

	title = request.values.get("title", "").strip()
	url = request.values.get("url", "").strip()
	title_html = filter_title(title)
	body = request.values.get("body", "").strip()

	if v.marseyawarded and len(list(re.finditer('>[^<\s+]|[^>\s+]<', title_html))) > 0: return {"error":"You can only type marseys!"}, 40

	if v.longpost and len(body) < 280: return {"error":"You have to type more than 280 characters!"}, 403

	if url:
		if "/i.imgur.com/" in url: url = url.replace(".png", ".webp").replace(".jpg", ".webp").replace(".jpeg", ".webp")
		elif "/media.giphy.com/" in url or "/c.tenor.com/" in url: url = url.replace(".gif", ".webp")
		elif "/i.ibb.com/" in url: url = url.replace(".png", ".webp").replace(".jpg", ".webp").replace(".jpeg", ".webp").replace(".gif", ".webp")

		for rd in ["https://reddit.com/", "https://new.reddit.com/", "https://www.reddit.com/", "https://redd.it/"]:
			url = url.replace(rd, "https://old.reddit.com/")
		
		url = url.replace("old.reddit.com/gallery", "new.reddit.com/gallery")

		url = url.replace("https://mobile.twitter.com", "https://twitter.com")
		if url.startswith("https://streamable.com/") and not url.startswith("https://streamable.com/e/"): url = url.replace("https://streamable.com/", "https://streamable.com/e/")

		parsed_url = urlparse(url)

		domain = parsed_url.netloc

		qd = parse_qs(parsed_url.query)
		filtered = dict((k, v) for k, v in qd.items() if not k.startswith('utm_'))

		new_url = ParseResult(scheme="https",
							netloc=parsed_url.netloc,
							path=parsed_url.path,
							params=parsed_url.params,
							query=urlencode(filtered, doseq=True),
							fragment=parsed_url.fragment)
		url = urlunparse(new_url)

		repost = g.db.query(Submission).filter(
			Submission.url.ilike(url),
			Submission.deleted_utc == 0,
			Submission.is_banned == False
		).first()

		if repost: return redirect(repost.permalink)

		domain_obj = get_domain(domain)
		if domain_obj:
			if request.headers.get("Authorization"): return {"error":domain_obj.reason}, 400
			else: return render_template("submit.html", v=v, error=domain_obj.reason, title=title, url=url, body=request.values.get("body", "")), 400
		elif "twitter.com" in domain:
			try: embed = requests.get("https://publish.twitter.com/oembed", timeout=5, params={"url":url, "omit_script":"t"}).json()["html"]
			except: embed = None
		elif "youtu" in domain:
			yt_id = re.match(re.compile("^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|shorts\/|\&v=)([^#\&\?]*).*"), url).group(2)
			params = parse_qs(urlparse(url).query)
			t = params.get('t', params.get('start', [0]))[0]
			if isinstance(t, str): t = t.replace('s','')
			if t: embed = f"https://youtube.com/embed/{yt_id}?start={t}"
			else: embed = f"https://youtube.com/embed/{yt_id}"
		elif app.config['SERVER_NAME'] in domain and "/post/" in url and "context" not in url:
			id = url.split("/post/")[1]
			if "/" in id: id = id.split("/")[0]
			embed = id
		else: embed = None
	else: embed = None

	if not url and not request.values.get("body") and not request.files.get("file", None):
		if request.headers.get("Authorization"): return {"error": "`url` or `body` parameter required."}, 400
		else: return render_template("submit.html", v=v, error="Please enter a url or some text.", title=title, url=url, body=request.values.get("body", "")), 400

	if not title:
		if request.headers.get("Authorization"): return {"error": "Please enter a better title"}, 400
		else: return render_template("submit.html", v=v, error="Please enter a better title.", title=title, url=url, body=request.values.get("body", "")), 400


	elif len(title) > 500:
		if request.headers.get("Authorization"): return {"error": "500 character limit for titles"}, 400
		else: render_template("submit.html", v=v, error="500 character limit for titles.", title=title[:500], url=url, body=request.values.get("body", "")), 400

	if v.marseyawarded:
		if time.time() > v.marseyawarded:
			v.marseyawarded = None
			g.db.add(v)
		else:
			marregex = list(re.finditer("^(:!?m\w+:\s*)+$", title))
			if len(marregex) == 0: return {"error":"You can only type marseys!"}, 403
			if body:
				marregex = list(re.finditer("^(:!?m\w+:\s*)+$", body))
				if len(marregex) == 0: return {"error":"You can only type marseys!"}, 403

	if v.longpost:
		if time.time() > v.longpost:
			v.longpost = None
			g.db.add(v)
		elif len(body) < 280: return {"error":"You have to type more than 280 characters!"}, 403

	dup = g.db.query(Submission).filter(
		Submission.author_id == v.id,
		Submission.deleted_utc == 0,
		Submission.title == title,
		Submission.url == url,
		Submission.body == body
	).first()

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
		send_notification(v.id, text)

		v.ban(reason="Spamming.",
			  days=1)

		for alt in v.alts:
			if not alt.is_suspended:
				alt.ban(reason="Spamming.", days=1)

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
		return redirect("/notifications")

	if len(str(body)) > 10000:

		if request.headers.get("Authorization"): return {"error":"10000 character limit for text body."}, 400
		else: return render_template("submit.html", v=v, error="10000 character limit for text body.", title=title, url=url, body=request.values.get("body", "")), 400

	if len(url) > 2048:

		if request.headers.get("Authorization"): return {"error":"2048 character limit for URLs."}, 400
		else: return render_template("submit.html", v=v, error="2048 character limit for URLs.", title=title, url=url,body=request.values.get("body", "")), 400

	for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|webp|PNG|JPG|JPEG|GIF|WEBP|9999))', body, re.MULTILINE):
		if "wikipedia" not in i.group(1): body = body.replace(i.group(1), f'![]({i.group(1)})')

	options = []
	for i in re.finditer('\s*\$\$([^\$\n]+)\$\$\s*', body):
		options.append(i.group(1))
		body = body.replace(i.group(0), "")

	body_md = CustomRenderer().render(mistletoe.Document(body))
	body_html = sanitize(body_md)

	if v.marseyawarded and len(list(re.finditer('>[^<\s+]|[^>\s+]<', body_html))) > 0: return {"error":"You can only type marseys!"}, 400

	if v.longpost and len(body) < 280: return {"error":"You have to type more than 280 characters!"}, 403

	if len(body_html) > 20000: return {"error":"Submission body too long!"}, 400

	bans = filter_comment_html(body_html)
	if bans:
		ban = bans[0]
		reason = f"Remove the {ban.domain} link from your post and try again."
		if ban.reason: reason += f" {ban.reason}"
		if request.headers.get("Authorization"): return {"error": reason}, 403
		else: return render_template("submit.html", v=v, error=reason, title=title, url=url, body=request.values.get("body", "")), 403

	if v.paid_dues: club = bool(request.values.get("club",""))
	else: club = False

	new_post = Submission(
		private=bool(request.values.get("private","")),
		club=club,
		author_id=v.id,
		over_18=request.host == 'pcmemes.net' and v.id == 1578 or bool(request.values.get("over_18","")),
		app_id=v.client.application.id if v.client else None,
		is_bot = request.headers.get("Authorization"),
		url=url,
		body=body[:10000],
		body_html=body_html,
		embed_url=embed,
		title=title,
		title_html=title_html
	)

	g.db.add(new_post)
	g.db.flush()
	
	for option in options:
		c = Comment(author_id=AUTOPOLLER_ID,
			parent_submission=new_post.id,
			level=1,
			body_html=filter_title(option),
			upvotes=0
			)

		g.db.add(c)

	vote = Vote(user_id=v.id,
				vote_type=1,
				submission_id=new_post.id
				)
	g.db.add(vote)
	g.db.flush()

	if request.files.get('file') and request.headers.get("cf-ipcountry") != "T1":

		file = request.files['file']

		if not file.content_type.startswith(('image/', 'video/')):
			if request.headers.get("Authorization"): return {"error": f"File type not allowed"}, 400
			else: return render_template("submit.html", v=v, error=f"File type not allowed.", title=title, body=request.values.get("body", "")), 400

		if file.content_type.startswith('video/') and v.truecoins < app.config["VIDEO_COIN_REQUIREMENT"] and v.admin_level < 1:
			if request.headers.get("Authorization"):
				return {
					"error": f"You need at least {app.config['VIDEO_COIN_REQUIREMENT']} coins to upload videos"
				}, 403
			else:
				return render_template(
					"submit.html",
					v=v,
					error=f"You need at least {app.config['VIDEO_COIN_REQUIREMENT']} coins to upload videos.",
					title=title,
					body=request.values.get("body", "")
				), 403

		if file.content_type.startswith('image/'):
			name = f'/images/{int(time.time())}{secrets.token_urlsafe(2)}.webp'
			file.save(name)
			new_post.url = request.host_url[:-1] + process_image(name)
			
		elif file.content_type.startswith('video/'):
			file.save("video.mp4")
			with open("video.mp4", 'rb') as f:
				new_post.url = requests.post('https://catbox.moe/user/api.php', timeout=5, data={'userhash':CATBOX_KEY, 'reqtype':'fileupload'}, files={'fileToUpload':f}).text

		g.db.add(new_post)
	
	g.db.flush()




	if (new_post.url or request.files.get('file')) and request.headers.get('cf-ipcountry')!="T1":
		gevent.spawn( thumbnail_thread, new_post.id)

	if not new_post.private:

		notify_users = set()
		soup = BeautifulSoup(body_html, features="html.parser")
		for mention in soup.find_all("a", href=re.compile("^/@(\w+)")):
			username = mention["href"].split("@")[1]
			user = g.db.query(User).filter_by(username=username).first()
			if user and not v.any_block_exists(user) and user.id != v.id: notify_users.add(user.id)
		
		if request.host == 'rdrama.net':
			if 'aevann' in f'{body_html}{title}'.lower() and 1 not in notify_users: notify_users.add(1)
			if 'joan' in f'{body_html}{title}'.lower() and 28 not in notify_users: notify_users.add(28)
			if 'carp' in f'{body_html}{title}'.lower() and 995 not in notify_users:
				notify_users.add(995)
				notify_users.add(541)
			if ('idio3' in f'{body_html}{title}'.lower() or 'idio ' in f'{body_html}{title}'.lower()) and 30 not in notify_users: notify_users.add(30)

		for x in notify_users: send_notification(x, f"@{v.username} has mentioned you: http://{site}{new_post.permalink}")
		
		for follow in v.followers:
			user = get_account(follow.user_id)
			if new_post.club and not user.club_allowed: continue
			send_notification(user.id, f"@{v.username} has made a new post: [{title}](http://{site}{new_post.permalink})", True)

	g.db.add(new_post)
	g.db.flush()


	if "rama" in request.host and "ivermectin" in new_post.body_html.lower():

		new_post.is_banned = True
		new_post.ban_reason = "AutoJanny"

		g.db.add(new_post)


		body = VAXX_MSG.format(username=v.username)

		body_md = CustomRenderer().render(mistletoe.Document(body))

		body_jannied_html = sanitize(body_md)


		c_jannied = Comment(author_id=AUTOJANNY_ID,
			parent_submission=new_post.id,
			level=1,
			over_18=False,
			is_bot=True,
			app_id=None,
			is_pinned=True,
			distinguish_level=6,
			body_html=body_jannied_html,
		)

		g.db.add(c_jannied)
		g.db.flush()


		n = Notification(comment_id=c_jannied.id, user_id=v.id)
		g.db.add(n)


	if v.agendaposter and not v.marseyawarded and "trans lives matter" not in new_post.body_html.lower():

		new_post.is_banned = True
		new_post.ban_reason = "AutoJanny"

		g.db.add(new_post)

		body = AGENDAPOSTER_MSG.format(username=v.username)

		body_md = CustomRenderer().render(mistletoe.Document(body))

		body_jannied_html = sanitize(body_md)



		c_jannied = Comment(author_id=AUTOJANNY_ID,
			parent_submission=new_post.id,
			level=1,
			over_18=False,
			is_bot=True,
			app_id=None,
			is_pinned=True,
			distinguish_level=6,
			body_html=body_jannied_html,
		)

		g.db.add(c_jannied)
		g.db.flush()



		n = Notification(comment_id=c_jannied.id, user_id=v.id)
		g.db.add(n)

	if "rama" in request.host or "pcmemes.net" in request.host or "shithole" in request.host or new_post.url:
		new_post.comment_count = 1
		g.db.add(new_post)

		if "rama" in request.host or "pcmemes.net" in request.host or "shithole" in request.host:
			if v.id == RED_ID: body = "fuck off red"
			if v.id == CARP_ID:
				if random.random() < 0.02: body = "i love you carp"
				else: body = "![](/assets/images/emojis/fuckoffcarp.webp)"
			elif v.id == LAWLZ_ID:
				if random.random() < 0.5: body = "wow, this lawlzpost sucks!"
				else: body = "wow, a good lawlzpost for once!"
			else: body = random.choice(snappyquotes)
			body += "\n\n"
		else: body = ""

		if new_post.url:
			if new_post.url.startswith('https://old.reddit.com/r/'):
				rev = new_post.url.replace('https://old.reddit.com/', '')
				rev = f"* [reveddit.com](https://reveddit.com/{rev})\n"
			else: rev = ''
			body += f"Snapshots:\n\n{rev}* [archive.org](https://web.archive.org/{new_post.url})\n* [archive.ph](https://archive.ph/?url={quote(new_post.url)}&run=1) (click to archive)\n\n"			
			gevent.spawn(archiveorg, new_post.url)

		url_regex = '<a (target=\"_blank\"  )?(rel=\"nofollow noopener noreferrer\" )?href=\"(https?://[a-z]{1,20}\.[^\"]+)\"( rel=\"nofollow noopener noreferrer\" target=\"_blank\")?>([^\"]+)</a>'
		for url_match in re.finditer(url_regex, new_post.body_html, flags=re.M|re.I):
			href = url_match.group(3)
			if not href: continue

			title = url_match.group(5)
			if "Snapshots:\n\n"	 not in body: body += "Snapshots:\n\n"			

			body += f'**[{title}]({href})**:\n\n'
			body += f'* [reveddit.com](https://reveddit.com/{href.replace("https://old.reddit.com/", "")})\n'
			body += f'* [archive.org](https://web.archive.org/{href})\n'
			body += f'* [archive.ph](https://archive.ph/?url={quote(href)}&run=1) (click to archive)\n\n'
			gevent.spawn(archiveorg, href)

		body_md = CustomRenderer().render(mistletoe.Document(body))
		body_html = sanitize(body_md)

		if len(body_html) < 20000:
			c = Comment(author_id=SNAPPY_ID,
				distinguish_level=6,
				parent_submission=new_post.id,
				level=1,
				over_18=False,
				is_bot=request.host!='pcmemes.net',
				app_id=None,
				body_html=body_html,
				)

			g.db.add(c)

			snappy = g.db.query(User).filter_by(id = SNAPPY_ID).first()
			snappy.comment_count += 1
			snappy.coins += 1
			g.db.add(snappy)

			g.db.flush()


			n = Notification(comment_id=c.id, user_id=v.id)
			g.db.add(n)
			g.db.flush()
	
	v.post_count = g.db.query(Submission.id).filter_by(author_id=v.id, is_banned=False, deleted_utc=0).count()
	g.db.add(v)

	cache.delete_memoized(frontlist)
	cache.delete_memoized(User.userpagelisting)
	if v.admin_level > 1 and ("[changelog]" in new_post.title or "(changelog)" in new_post.title):
		send_message(f"http://{site}{new_post.permalink}")
		cache.delete_memoized(changeloglist)

	g.db.commit()

	if request.headers.get("Authorization"): return new_post.json
	else: return redirect(new_post.permalink)


@app.post("/delete_post/<pid>")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def delete_post_pid(pid, v):

	post = get_post(pid)
	if not post.author_id == v.id:
		abort(403)

	post.deleted_utc = int(time.time())
	post.is_pinned = False
	post.stickied = None

	g.db.add(post)

	cache.delete_memoized(frontlist)

	g.db.commit()

	return {"message": "Post deleted!"}

@app.post("/undelete_post/<pid>")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def undelete_post_pid(pid, v):
	post = get_post(pid)
	if not post.author_id == v.id: abort(403)
	post.deleted_utc =0
	g.db.add(post)

	cache.delete_memoized(frontlist)

	g.db.commit()

	return {"message": "Post undeleted!"}


@app.post("/toggle_comment_nsfw/<cid>")
@auth_required
@validate_formkey
def toggle_comment_nsfw(cid, v):

	comment = g.db.query(Comment).filter_by(id=cid).first()
	if not comment.author_id == v.id and not v.admin_level > 1: abort(403)
	comment.over_18 = not comment.over_18
	g.db.add(comment)
	g.db.flush()

	g.db.commit()

	if comment.over_18: return {"message": "Comment has been marked as +18!"}
	else: return {"message": "Comment has been unmarked as +18!"}
	
@app.post("/toggle_post_nsfw/<pid>")
@auth_required
@validate_formkey
def toggle_post_nsfw(pid, v):

	post = get_post(pid)

	if not post.author_id == v.id and not v.admin_level > 1:
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
@limiter.limit("1/second")
@auth_required
@validate_formkey
def save_post(pid, v):

	post=get_post(pid)

	save = g.db.query(SaveRelationship).filter_by(user_id=v.id, submission_id=post.id, type=1).first()

	if not save:
		new_save=SaveRelationship(user_id=v.id, submission_id=post.id, type=1)
		g.db.add(new_save)
		g.db.commit()

	return {"message": "Post saved!"}

@app.post("/unsave_post/<pid>")
@limiter.limit("1/second")
@auth_required
@validate_formkey
def unsave_post(pid, v):

	post=get_post(pid)

	save = g.db.query(SaveRelationship).filter_by(user_id=v.id, submission_id=post.id, type=1).first()

	if save:
		g.db.delete(save)
		g.db.commit()

	return {"message": "Post unsaved!"}

@app.post("/pin/<post_id>")
@auth_required
def api_pin_post(post_id, v):

	post = g.db.query(Submission).filter_by(id=post_id).first()
	if post:
		post.is_pinned = not post.is_pinned
		g.db.add(post)
		g.db.commit()

		if post.is_pinned: return {"message": "Post pinned!"}
		else: return {"message": "Post unpinned!"}