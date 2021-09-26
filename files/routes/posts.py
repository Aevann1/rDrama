import time
from urllib.parse import urlparse
import mistletoe
import urllib.parse
import gevent
import traceback

from files.helpers.wrappers import *
from files.helpers.sanitize import *
from files.helpers.filters import *
from files.helpers.markdown import *
from files.helpers.session import *
from files.helpers.thumbs import *
from files.helpers.alerts import send_notification
from files.helpers.discord import send_message
from files.helpers.const import *
from files.classes import *
from flask import *
from io import BytesIO
from files.__main__ import app, limiter, cache, db_session
from PIL import Image as PILimage
from .front import frontlist, changeloglist


site = environ.get("DOMAIN").strip()

with open("snappy.txt", "r") as f: snappyquotes = f.read().split("{[para]}")


@app.post("/toggle_club/<pid>")
@auth_required
def toggle_club(pid, v):

	post = get_post(pid)

	if post.author_id != v.id or not v.paid_dues: abort(403)

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
@auth_required
@validate_formkey
def publish(pid, v):
	post = get_post(pid)
	if not post.author_id == v.id: abort(403)
	post.private = False
	g.db.add(post)
	
	cache.delete_memoized(frontlist)

	for follow in v.followers:
		user = get_account(follow.user_id)
		send_notification(AUTOJANNY_ACCOUNT, user, f"@{v.username} has made a new post: [{post.title}](https://{site}{post.permalink})")

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

	if v and request.full_path.startswith('/logged_out'): v = None

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

	if post.club and not (v and v.paid_dues): abort(403)

	if v:
		votes = g.db.query(CommentVote).options(lazyload('*')).filter_by(user_id=v.id).subquery()

		blocking = v.blocking.subquery()

		blocked = v.blocked.subquery()

		if not (v and v.shadowbanned) and not (v and v.admin_level == 6):
			shadowbanned = [x[0] for x in g.db.query(User.id).options(lazyload('*')).filter(User.shadowbanned == True).all()]
			comments = g.db.query(Comment).filter(Comment.author_id.notin_(shadowbanned))

		comments = g.db.query(
			Comment,
			votes.c.vote_type,
			blocking.c.id,
			blocked.c.id,
		)
		
		if not (v and v.shadowbanned) and not (v and v.admin_level == 6):
			shadowbanned = [x[0] for x in g.db.query(User.id).options(lazyload('*')).filter(User.shadowbanned == True).all()]
			comments = comments.filter(Comment.author_id.notin_(shadowbanned))

		if v.admin_level >=4:
			comments=comments.options(joinedload(Comment.oauth_app))
 
		comments=comments.filter(
			Comment.parent_submission == post.id
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
			comments = comments.order_by(-1 * Comment.upvotes * (Comment.downvotes+1))
		elif sort == "top":
			comments = comments.order_by(Comment.downvotes - Comment.upvotes)
		elif sort == "bottom":
			comments = comments.order_by(Comment.upvotes - Comment.downvotes)

		output = []
		for c in comments.all():
			comment = c[0]
			comment.voted = c[1] or 0
			comment.is_blocking = c[2] or 0
			comment.is_blocked = c[3] or 0
			output.append(comment)

		post.preloaded_comments = output

	else:
		shadowbanned = [x[0] for x in g.db.query(User.id).options(lazyload('*')).filter(User.shadowbanned == True).all()]
		comments = g.db.query(Comment).filter(Comment.parent_submission == post.id, Comment.author_id.notin_(shadowbanned))

		if sort == "new":
			comments = comments.order_by(Comment.created_utc.desc())
		elif sort == "old":
			comments = comments.order_by(Comment.created_utc.asc())
		elif sort == "controversial":
			comments = comments.order_by(-1 * Comment.upvotes * (Comment.downvotes+1))
		elif sort == "top":
			comments = comments.order_by(Comment.downvotes - Comment.upvotes)
		elif sort == "bottom":
			comments = comments.order_by(Comment.upvotes - Comment.downvotes)

		post.preloaded_comments = comments.all()

	if not v or v.highlightcomments:
		last_view_utc = session.get(str(post.id))
		if last_view_utc: last_view_utc = int(last_view_utc)
		session[str(post.id)] = int(time.time())

		keys = []
		for key, val in session.items():
			if type(val) is int and key not in ['login_nonce','user_id']:
				if time.time() - val > 86400: keys.append(key)
		
		for key in keys: session.pop(key)

	post.views += 1
	g.db.add(post)
	if isinstance(session.get('over_18', 0), dict): session["over_18"] = 0
	if post.over_18 and not (v and v.over_18) and not session.get('over_18', 0) >= int(time.time()):
		if request.headers.get("Authorization"): return {"error":"Must be 18+ to view"}, 451
		else: return render_template("errors/nsfw.html", v=v)

	g.db.commit()
	if request.headers.get("Authorization"): return post.json
	else:
		if not v or v.highlightcomments: return post.rendered_page(v=v, last_view_utc=last_view_utc, sort=sort)
		else: return post.rendered_page(v=v, sort=sort)


@app.post("/edit_post/<pid>")
@auth_required
@validate_formkey
def edit_post(pid, v):

	p = get_post(pid)

	if not p.author_id == v.id: abort(403)

	title = request.values.get("title")
	body = request.values.get("body", "")

	if title != p.title:
		p.title = title
		p.title_html = filter_title(title)

	if body != p.body:
		for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|webp|PNG|JPG|JPEG|GIF|WEBP|9999))', body, re.MULTILINE):
			if "wikipedia" not in i.group(1): body = body.replace(i.group(1), f'![]({i.group(1)})')
		body = re.sub('([^\n])\n([^\n])', r'\1\n\n\2', body)
		body_md = CustomRenderer().render(mistletoe.Document(body))
		body_html = sanitize(body_md)

		# Run safety filter
		bans = filter_comment_html(body_html)
		if bans:
			ban = bans[0]
			reason = f"Remove the {ban.domain} link from your post and try again."
			if ban.reason:
				reason += f" {ban.reason}"
				
			#auto ban for digitally malicious content
			if any([x.reason==4 for x in bans]):
				v.ban(days=30, reason="Digitally malicious content is not allowed.")
				abort(403)
				
			return {"error": reason}, 403

		# check spam
		soup = BeautifulSoup(body_html, features="html.parser")
		links = [x['href'] for x in soup.find_all('a') if x.get('href')]

		for link in links:
			parse_link = urlparse(link)
			check_url = ParseResult(scheme="https",
									netloc=parse_link.netloc,
									path=parse_link.path,
									params=parse_link.params,
									query=parse_link.query,
									fragment='')
			check_url = urlunparse(check_url)

			badlink = g.db.query(BadLink).options(lazyload('*')).filter(
				literal(check_url).contains(
					BadLink.link)).first()
			if badlink:
				if badlink.autoban:
					text = "Your account has been suspended for 1 day for the following reason:\n\n> Too much spam!"
					send_notification(NOTIFICATIONS_ACCOUNT, v, text)
					v.ban(days=1, reason="spam")

					return redirect('/notifications')
				else:

					return {"error": f"The link `{badlink.link}` is not allowed. Reason: {badlink.reason}"}

		p.body = body
		p.body_html = body_html

		if "rdrama" in request.host and "ivermectin" in body_html.lower():

			p.is_banned = True
			p.ban_reason = "ToS Violation"

			g.db.add(p)

			body = VAXX_MSG.format(username=v.username)

			body_md = CustomRenderer().render(mistletoe.Document(body))

			body_jannied_html = sanitize(body_md)


			c_jannied = Comment(author_id=AUTOJANNY_ACCOUNT,
				parent_submission=p.id,
				level=1,
				over_18=False,
				is_bot=True,
				app_id=None,
				is_pinned=True,
				distinguish_level=6,
				body_html=body_jannied_html,
				body=body
				)

			g.db.add(c_jannied)
			g.db.flush()


			n = Notification(comment_id=c_jannied.id, user_id=v.id)
			g.db.add(n)


		if v.agendaposter and "trans lives matter" not in body_html.lower():

			p.is_banned = True
			p.ban_reason = "ToS Violation"

			g.db.add(p)

			body = AGENDAPOSTER_MSG.format(username=v.username)

			body_md = CustomRenderer().render(mistletoe.Document(body))

			body_jannied_html = sanitize(body_md)

			c_jannied = Comment(author_id=AUTOJANNY_ACCOUNT,
				parent_submission=p.id,
				level=1,
				over_18=False,
				is_bot=True,
				app_id=None,
				is_pinned=True,
				distinguish_level=6,
				body_html=body_jannied_html,
				body=body
				)

			g.db.add(c_jannied)
			g.db.flush()

			n = Notification(comment_id=c_jannied.id, user_id=v.id)
			g.db.add(n)
		

		notify_users = set()
		
		soup = BeautifulSoup(body_html, features="html.parser")
		for mention in soup.find_all("a", href=re.compile("^/@(\w+)")):
			username = mention["href"].split("@")[1]
			user = g.db.query(User).options(lazyload('*')).filter_by(username=username).first()
			if user and not v.any_block_exists(user) and user.id != v.id: notify_users.add(user)
			
		for x in notify_users: send_notification(NOTIFICATIONS_ACCOUNT, x, f"@{v.username} has mentioned you: https://{site}{p.permalink}")


	if title != p.title or body != p.body:
		if int(time.time()) - p.created_utc > 60 * 3: p.edited_utc = int(time.time())
		g.db.add(p)

	g.db.commit()

	return redirect(p.permalink)

@app.get("/submit/title")
@limiter.limit("6/minute")
@auth_required
def get_post_title(v):

	url = request.values.get("url", None)
	if not url:
		return abort(400)

	#mimic chrome browser agent
	headers = {"User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36"}
	try:
		x = requests.get(url, headers=headers)
	except BaseException:
		return {"error": "Could not reach page"}, 400


	if not x.status_code == 200:
		return {"error": f"Page returned {x.status_code}"}, x.status_code


	try:
		soup = BeautifulSoup(x.content, 'html.parser')

		data = {"url": url,
				"title": soup.find('title').string
				}

		return data
	except BaseException:
		return {"error": f"Could not find a title"}, 400

def archiveorg(url):
	try: requests.get(f'https://web.archive.org/save/{url}', headers={'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}, timeout=100)
	except Exception as e: print(e)

def filter_title(title):
	title = title.strip()
	title = title.replace("\n", "")
	title = title.replace("\r", "")
	title = title.replace("\t", "")

	# sanitize title
	title = bleach.clean(title, tags=[])

	for i in re.finditer(':(.{1,30}?):', title):
		if path.isfile(f'./files/assets/images/emojis/{i.group(1)}.webp'):
			title = title.replace(f':{i.group(1)}:', f'<img loading="lazy" data-bs-toggle="tooltip" title="{i.group(1)}" delay="0" height=20 src="https://{site}/assets/images/emojis/{i.group(1)}.webp">')

	return title


IMGUR_KEY = environ.get("IMGUR_KEY", "").strip()


def check_processing_thread(v, post, link):

	image_id = link.split('/')[-1].rstrip('.mp4')
	headers = {"Authorization": f"Client-ID {IMGUR_KEY}"}

	while True:
		# break on error to prevent zombie threads
		try:
			time.sleep(15)

			req = requests.get(f"https://api.imgur.com/3/image/{image_id}", headers=headers)

			status = req.json()['data']['processing']['status']
			if status == 'completed':
				post.processing = False
				g.db.add(post)

				send_notification(
					NOTIFICATIONS_ACCOUNT,
					v,
					f"Your video has finished processing and your [post](/post/{post.id}) is now live."
				)

				g.db.commit()
				break
			# just in case
			elif status == 'failed':
				print(f"video upload for post {post.id} failed")
				break
		except Exception as e:
			traceback.print_exc()
			print("retard. aborting thread")
			break


def thumbnail_thread(pid):

	db = db_session()

	post = db.query(Submission).filter_by(id=pid).first()
	
	if not post:
		time.sleep(5)
		post = db.query(Submission).filter_by(id=pid).first()

	fetch_url=post.url

	#mimic chrome browser agent
	headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36"}

	try:
		x=requests.get(fetch_url, headers=headers)
	except:
		db.close()
		return

	if x.status_code != 200:
		db.close()
		return
	

	#if content is image, stick with that. Otherwise, parse html.

	if x.headers.get("Content-Type","").startswith("text/html"):
		#parse html, find image, load image
		soup=BeautifulSoup(x.content, 'html.parser')
		#parse html

		#create list of urls to check
		thumb_candidate_urls=[]

		#iterate through desired meta tags
		meta_tags = [
			"ruqqus:thumbnail",
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

		#parse html doc for <img> elements
		for tag in soup.find_all("img", attrs={'src':True}):
			thumb_candidate_urls.append(expand_url(post.url, tag['src']))


		#now we have a list of candidate urls to try
		for url in thumb_candidate_urls:

			try:
				image_req=requests.get(url, headers=headers)
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
			#getting here means we are out of candidate urls (or there never were any)
			db.close()
			return



	elif x.headers.get("Content-Type","").startswith("image/"):
		#image is originally loaded fetch_url
		image_req=x
		image = PILimage.open(BytesIO(x.content))

	else:
		db.close()
		return

	with open("image.webp", "wb") as file:
		for chunk in image_req.iter_content(1024):
			file.write(chunk)

	post.thumburl = upload_ibb(resize=True)
	db.add(post)
	db.commit()
	db.close()
	return


@app.post("/submit")
@limiter.limit("6/minute")
@is_not_banned
@validate_formkey
def submit_post(v):
	if request.content_length > 16 * 1024 * 1024: abort(413)

	title = request.values.get("title", "")
	url = request.values.get("url", "")

	if url:
		if "/i.imgur.com/" in url: url = url.replace(".png", ".webp").replace(".jpg", ".webp").replace(".jpeg", ".webp")
		elif "/media.giphy.com/" in url or "/c.tenor.com/" in url: url = url.replace(".gif", ".webp")
		elif "/i.ibb.com/" in url: url = url.replace(".png", ".webp").replace(".jpg", ".webp").replace(".jpeg", ".webp").replace(".gif", ".webp")

		for rd in ["https://reddit.com/", "https://new.reddit.com/", "https://www.reddit.com/", "https://redd.it/"]:
			url = url.replace(rd, "https://old.reddit.com/")
				
		url = url.replace("https://mobile.twitter.com", "https://twitter.com")
		if url.startswith("https://streamable.com/") and not url.startswith("https://streamable.com/e/"):
			url = url.replace("https://streamable.com/", "https://streamable.com/e/")

		repost = g.db.query(Submission).options(lazyload('*')).filter(
			Submission.url.ilike(url),
			Submission.deleted_utc == 0,
			Submission.is_banned == False
		).first()
	else:
		repost = None
	
	if repost:
		return redirect(repost.permalink)

	if not title:
		if request.headers.get("Authorization"): return {"error": "Please enter a better title"}, 400
		else: return render_template("submit.html", v=v, error="Please enter a better title.", title=title, url=url, body=request.values.get("body", "")), 400


	elif len(title) > 500:
		if request.headers.get("Authorization"): return {"error": "500 character limit for titles"}, 400
		else: render_template("submit.html", v=v, error="500 character limit for titles.", title=title[:500], url=url, body=request.values.get("body", "")), 400

	parsed_url = urlparse(url)
	if not (parsed_url.scheme and parsed_url.netloc) and not request.values.get(
			"body") and not request.files.get("file", None):

		if request.headers.get("Authorization"): return {"error": "`url` or `body` parameter required."}, 400
		else: return render_template("submit.html", v=v, error="Please enter a url or some text.", title=title, url=url, body=request.values.get("body", "")), 400


	# Force https for submitted urls

	if request.values.get("url"):
		new_url = ParseResult(scheme="https",
							  netloc=parsed_url.netloc,
							  path=parsed_url.path,
							  params=parsed_url.params,
							  query=parsed_url.query,
							  fragment=parsed_url.fragment)
		url = urlunparse(new_url)
	else:
		url = ""
	
	body = request.values.get("body", "")
	# check for duplicate
	dup = g.db.query(Submission).options(lazyload('*')).filter(

		Submission.author_id == v.id,
		Submission.deleted_utc == 0,
		Submission.title == title,
		Submission.url == url,
		Submission.body == body
	).first()

	if dup:
		return redirect(dup.permalink)


	# check for domain specific rules

	parsed_url = urlparse(url)

	domain = parsed_url.netloc

	# check ban status
	domain_obj = get_domain(domain)
	if domain_obj:		  
		if domain_obj.reason==4:
			v.ban(days=30, reason="Digitally malicious content")
		elif domain_obj.reason==7:
			v.ban(reason="Sexualizing minors")

		if request.headers.get("Authorization"): return {"error":"ToS violation"}, 400
		else: return render_template("submit.html", v=v, error="ToS Violation", title=title, url=url, body=request.values.get("body", "")), 400

	if "twitter.com" in domain:
		try: embed = requests.get("https://publish.twitter.com/oembed", params={"url":url, "omit_script":"t"}).json()["html"]
		except: embed = None

	elif "youtu" in domain:
		try:
			yt_id = re.match(re.compile("^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|shorts\/|\&v=)([^#\&\?]*).*"), url).group(2)
			params = parse_qs(urlparse(url).query)
			t = params.get('t', params.get('start', [0]))[0]
			if t: embed = f"https://youtube.com/embed/{yt_id}?start={t}"
			else: embed = f"https://youtube.com/embed/{yt_id}"
		except: embed = None

	elif app.config['SERVER_NAME'] in domain and "/post/" in url and "context" not in url:
		id = url.split("/post/")[1]
		if "/" in id: id = id.split("/")[0]
		embed = id

	else: embed = None

	# similarity check
	now = int(time.time())
	cutoff = now - 60 * 60 * 24


	similar_posts = g.db.query(Submission).options(
		lazyload('*')
		).filter(
			#or_(
			#	and_(
					Submission.author_id == v.id,
					Submission.title.op('<->')(title) < app.config["SPAM_SIMILARITY_THRESHOLD"],
					Submission.created_utc > cutoff
			#	),
			#	and_(
			#		Submission.title.op('<->')(title) < app.config["SPAM_SIMILARITY_THRESHOLD"]/2,
			#		Submission.created_utc > cutoff
			#	)
			#)
	).all()

	if url:
		similar_urls = g.db.query(Submission).options(
			lazyload('*')
		).filter(
			#or_(
			#	and_(
					Submission.author_id == v.id,
					Submission.url.op('<->')(url) < app.config["SPAM_URL_SIMILARITY_THRESHOLD"],
					Submission.created_utc > cutoff
			#	),
			#	and_(
			#		Submission.url.op('<->')(url) < app.config["SPAM_URL_SIMILARITY_THRESHOLD"]/2,
			#		Submission.created_utc > cutoff
			#	)
			#)
		).all()
	else:
		similar_urls = []

	threshold = app.config["SPAM_SIMILAR_COUNT_THRESHOLD"]
	if v.age >= (60 * 60 * 24 * 7):
		threshold *= 3
	elif v.age >= (60 * 60 * 24):
		threshold *= 2

	if max(len(similar_urls), len(similar_posts)) >= threshold:

		text = "Your account has been suspended for 1 day for the following reason:\n\n> Too much spam!"
		send_notification(NOTIFICATIONS_ACCOUNT, v, text)

		v.ban(reason="Spamming.",
			  days=1)

		for alt in v.alts:
			if not alt.is_suspended:
				alt.ban(reason="Spamming.", days=1)

		for post in similar_posts + similar_urls:
			post.is_banned = True
			post.is_pinned = False
			post.ban_reason = "Automatic spam removal. This happened because the post's creator submitted too much similar content too quickly."
			g.db.add(post)
			ma=ModAction(
					user_id=AUTOJANNY_ACCOUNT,
					target_submission_id=post.id,
					kind="ban_post",
					note="spam"
					)
			g.db.add(ma)
		return redirect("/notifications")

	# catch too-long body
	if len(str(body)) > 10000:

		if request.headers.get("Authorization"): return {"error":"10000 character limit for text body."}, 400
		else: return render_template("submit.html", v=v, error="10000 character limit for text body.", title=title, url=url, body=request.values.get("body", "")), 400

	if len(url) > 2048:

		if request.headers.get("Authorization"): return {"error":"2048 character limit for URLs."}, 400
		else: return render_template("submit.html", v=v, error="2048 character limit for URLs.", title=title, url=url,body=request.values.get("body", "")), 400

	# render text
	for i in re.finditer('^(https:\/\/.*\.(png|jpg|jpeg|gif|webp|PNG|JPG|JPEG|GIF|WEBP|9999))', body, re.MULTILINE):
		if "wikipedia" not in i.group(1): body = body.replace(i.group(1), f'![]({i.group(1)})')
	body = re.sub('([^\n])\n([^\n])', r'\1\n\n\2', body)
	body_md = CustomRenderer().render(mistletoe.Document(body))
	body_html = sanitize(body_md)

	if len(body_html) > 20000: abort(400)

	# Run safety filter
	bans = filter_comment_html(body_html)
	if bans:
		ban = bans[0]
		reason = f"Remove the {ban.domain} link from your post and try again."
		if ban.reason:
			reason += f" {ban.reason}"
			
		#auto ban for digitally malicious content
		if any([x.reason==4 for x in bans]):
			v.ban(days=30, reason="Digitally malicious content is not allowed.")
			abort(403)
			
		if request.headers.get("Authorization"): return {"error": reason}, 403
		else: return render_template("submit.html", v=v, error=reason, title=title, url=url, body=request.values.get("body", "")), 403

	# check spam
	soup = BeautifulSoup(body_html, features="html.parser")
	links = [x['href'] for x in soup.find_all('a') if x.get('href')]

	if url:
		links = [url] + links

	for link in links:
		parse_link = urlparse(link)
		check_url = ParseResult(scheme="https",
								netloc=parse_link.netloc,
								path=parse_link.path,
								params=parse_link.params,
								query=parse_link.query,
								fragment='')
		check_url = urlunparse(check_url)

		badlink = g.db.query(BadLink).options(lazyload('*')).filter(
			literal(check_url).contains(
				BadLink.link)).first()
		if badlink:
			if badlink.autoban:
				text = "Your account has been suspended for 1 day for the following reason:\n\n> Too much spam!"
				send_notification(NOTIFICATIONS_ACCOUNT, v, text)
				v.ban(days=1, reason="spam")

				return redirect('/notifications')
			else:
				if request.headers.get("Authorization"): return {"error": f"The link `{badlink.link}` is not allowed. Reason: {badlink.reason}"}, 400
				else: return render_template("submit.html", v=v, error=f"The link `{badlink.link}` is not allowed. Reason: {badlink.reason}.", title=title, url=url, body=request.values.get("body", "")), 400

	# check for embeddable video
	domain = parsed_url.netloc

	if v.paid_dues: club = bool(request.values.get("club",""))
	else: club = False

	new_post = Submission(
		private=bool(request.values.get("private","")),
		club=club,
		author_id=v.id,
		over_18=bool(request.values.get("over_18","")),
		app_id=v.client.application.id if v.client else None,
		is_bot = request.headers.get("X-User-Type","").lower()=="bot",
		url=url,
		body=body,
		body_html=body_html,
		embed_url=embed,
		title=title,
		title_html=filter_title(title)
	)

	g.db.add(new_post)
	g.db.flush()
	
	vote = Vote(user_id=v.id,
				vote_type=1,
				submission_id=new_post.id
				)
	g.db.add(vote)
	g.db.flush()

	g.db.refresh(new_post)

	# check for uploaded image
	if request.files.get('file') and request.headers.get("cf-ipcountry") != "T1":

		file = request.files['file']
		#if not file.content_type.startswith('image/'):
		#	if request.headers.get("Authorization"): return {"error": f"Image files only"}, 400
		#	else: return render_template("submit.html", v=v, error=f"Image files only.", title=title, body=request.values.get("body", "")), 400

		if not file.content_type.startswith(('image/', 'video/')):
			if request.headers.get("Authorization"): return {"error": f"File type not allowed"}, 400
			else: return render_template("submit.html", v=v, error=f"File type not allowed.", title=title, body=request.values.get("body", "")), 400

		if file.content_type.startswith('video/') and v.coins < app.config["VIDEO_COIN_REQUIREMENT"] and v.admin_level < 1:
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
			new_post.url = upload_ibb(file=file)
		else:
			try:
				post_url = upload_video(file)
				if not post_url.endswith('.mp4'):
					post_url += 'mp4'
				new_post.url = post_url
				new_post.processing = True
				gevent.spawn(check_processing_thread, v.id, new_post, post_url)
			except UploadException as e:
				if request.headers.get("Authorization"):
					return {
						"error": str(e),
					}, 400
				else:
					return render_template(
						"submit.html",
						v=v,
						error=str(e),
						title=title,
						body=request.values.get("body", "")
					), 400

		g.db.add(new_post)
	
	g.db.flush()




	if (new_post.url or request.files.get('file')) and (v.is_activated or request.headers.get('cf-ipcountry')!="T1"):
		gevent.spawn( thumbnail_thread, new_post.id)

	notify_users = set()
	
	soup = BeautifulSoup(body_html, features="html.parser")
	for mention in soup.find_all("a", href=re.compile("^/@(\w+)")):
		username = mention["href"].split("@")[1]
		user = g.db.query(User).options(lazyload('*')).filter_by(username=username).first()
		if user and not v.any_block_exists(user) and user.id != v.id: notify_users.add(user)
		
	for x in notify_users: send_notification(NOTIFICATIONS_ACCOUNT, x, f"@{v.username} has mentioned you: https://{site}{new_post.permalink}")
		
	if not new_post.private:
		for follow in v.followers:
			user = get_account(follow.user_id)
			send_notification(AUTOJANNY_ACCOUNT, user, f"@{v.username} has made a new post: [{title}](https://{site}{new_post.permalink})")

	g.db.add(new_post)
	g.db.flush()


	if "rdrama" in request.host and "ivermectin" in new_post.body_html.lower():

		new_post.is_banned = True
		new_post.ban_reason = "ToS Violation"

		g.db.add(new_post)


		body = VAXX_MSG.format(username=v.username)

		body_md = CustomRenderer().render(mistletoe.Document(body))

		body_jannied_html = sanitize(body_md)


		c_jannied = Comment(author_id=AUTOJANNY_ACCOUNT,
			parent_submission=new_post.id,
			level=1,
			over_18=False,
			is_bot=True,
			app_id=None,
			is_pinned=True,
			distinguish_level=6,
			body_html=body_jannied_html,
			body=body,
		)

		g.db.add(c_jannied)
		g.db.flush()


		n = Notification(comment_id=c_jannied.id, user_id=v.id)
		g.db.add(n)


	if v.agendaposter and "trans lives matter" not in new_post.body_html.lower():

		new_post.is_banned = True
		new_post.ban_reason = "ToS Violation"

		g.db.add(new_post)

		body = AGENDAPOSTER_MSG.format(username=v.username)

		body_md = CustomRenderer().render(mistletoe.Document(body))

		body_jannied_html = sanitize(body_md)



		c_jannied = Comment(author_id=AUTOJANNY_ACCOUNT,
			parent_submission=new_post.id,
			level=1,
			over_18=False,
			is_bot=True,
			app_id=None,
			is_pinned=True,
			distinguish_level=6,
			body_html=body_jannied_html,
			body=body,
		)

		g.db.add(c_jannied)
		g.db.flush()



		n = Notification(comment_id=c_jannied.id, user_id=v.id)
		g.db.add(n)

	if "rdrama" in request.host or (new_post.url and not "weebzone" in request.host and not "marsey.tech" in request.host):
		new_post.comment_count = 1
		g.db.add(new_post)

		if "rdrama" in request.host:
			if v.id == 995:
				if random.random() < 0.02: body = "i love you carp"
				else: body = "fuck off carp"
			elif v.id == 3833:
				if random.random() < 0.5: body = "wow, this lawlzpost sucks!"
				else: body = "wow, a good lawlzpost for once!"
			else: body = random.choice(snappyquotes)
			body += "\n\n---\n\n"
		else: body = ""
		if new_post.url:
			body += f"Snapshots:\n\n* [reveddit.com](https://reveddit.com/{new_post.url})\n* [archive.org](https://web.archive.org/{new_post.url})\n* [archive.ph](https://archive.ph/?url={urllib.parse.quote(new_post.url)}&run=1) (click to archive)"
			gevent.spawn(archiveorg, new_post.url)
		body_md = CustomRenderer().render(mistletoe.Document(body))
		body_html = sanitize(body_md)


		c = Comment(author_id=261,
			distinguish_level=6,
			parent_submission=new_post.id,
			level=1,
			over_18=False,
			is_bot=True,
			app_id=None,
			body_html=body_html,
			body=body,
			)

		g.db.add(c)
		g.db.flush()


		n = Notification(comment_id=c.id, user_id=v.id)
		g.db.add(n)
		g.db.flush()
	
	v.post_count = v.submissions.filter_by(is_banned=False, deleted_utc=0).count()
	g.db.add(v)

	cache.delete_memoized(frontlist)
	cache.delete_memoized(User.userpagelisting)
	if "[changelog]" in new_post.title or "(changelog)" in new_post.title:
		send_message(f"https://{site}{new_post.permalink}")
		cache.delete_memoized(changeloglist)

	g.db.commit()

	if request.headers.get("Authorization"): return new_post.json
	else: return redirect(new_post.permalink)


@app.post("/delete_post/<pid>")
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

	comment = g.db.query(Comment).options(lazyload('*')).filter_by(id=cid).first()
	if not comment.author_id == v.id and not v.admin_level >= 3: abort(403)
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

	if not post.author_id == v.id and not v.admin_level >= 3:
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
@auth_required
@validate_formkey
def save_post(pid, v):

	post=get_post(pid)

	save = g.db.query(SaveRelationship).options(lazyload('*')).filter_by(user_id=v.id, submission_id=post.id, type=1).first()

	if not save:
		new_save=SaveRelationship(user_id=v.id, submission_id=post.id, type=1)
		g.db.add(new_save)
		g.db.commit()

	return {"message": "Post saved!"}

@app.post("/unsave_post/<pid>")
@auth_required
@validate_formkey
def unsave_post(pid, v):

	post=get_post(pid)

	save = g.db.query(SaveRelationship).options(lazyload('*')).filter_by(user_id=v.id, submission_id=post.id, type=1).first()

	if save:
		g.db.delete(save)
		g.db.commit()

	return {"message": "Post unsaved!"}
