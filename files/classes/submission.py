from os import environ
import random
import re
import time
from urllib.parse import urlparse
from flask import render_template
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred
from files.__main__ import Base
from files.helpers.const import *
from files.helpers.regex import *
from files.helpers.lazy import lazy
from .flags import Flag
from .comment import Comment, normalize_urls_runtime
from .saves import SaveRelationship
from .sub import *
from .subscriptions import *
from .votes import CommentVote
from .polls import *
from flask import g

def sort_posts(sort, posts):
	if sort == "new":
		return posts.order_by(Submission.created_utc.desc())
	elif sort == "old":
		return posts.order_by(Submission.created_utc)
	elif sort == "controversial":
		return posts.order_by((Submission.upvotes+1)/(Submission.downvotes+1) + (Submission.downvotes+1)/(Submission.upvotes+1), Submission.downvotes.desc(), Submission.created_utc.desc())
	elif sort == "bottom":
		return posts.order_by(Submission.upvotes - Submission.downvotes, Submission.created_utc.desc())
	elif sort == "comments":
		return posts.order_by(Submission.comment_count.desc(), Submission.created_utc.desc())
	else:
		return posts.order_by(Submission.downvotes - Submission.upvotes, Submission.created_utc.desc())

class Submission(Base):
	__tablename__ = "submissions"

	id = Column(Integer, primary_key=True)
	author_id = Column(Integer, ForeignKey("users.id"))
	edited_utc = Column(Integer, default=0)
	created_utc = Column(Integer)
	thumburl = Column(String)
	is_banned = Column(Boolean, default=False)
	bannedfor = Column(String)
	ghost = Column(Boolean, default=False)
	views = Column(Integer, default=0)
	deleted_utc = Column(Integer, default=0)
	distinguish_level = Column(Integer, default=0)
	stickied = Column(String)
	stickied_utc = Column(Integer)
	hole_pinned = Column(String)
	sub = Column(String, ForeignKey("subs.name"))
	is_pinned = Column(Boolean, default=False)
	private = Column(Boolean, default=False)
	club = Column(Boolean, default=False)
	comment_count = Column(Integer, default=0)
	is_approved = Column(Integer, ForeignKey("users.id"))
	over_18 = Column(Boolean, default=False)
	is_bot = Column(Boolean, default=False)
	upvotes = Column(Integer, default=1)
	downvotes = Column(Integer, default=0)
	realupvotes = Column(Integer, default=1)
	app_id=Column(Integer, ForeignKey("oauth_apps.id"))
	title = Column(String)
	title_html = Column(String)
	url = Column(String)
	body = Column(String)
	body_html = Column(String)
	flair = Column(String)
	ban_reason = Column(String)
	embed_url = Column(String)
	new = Column(Boolean)

	author = relationship("User", primaryjoin="Submission.author_id==User.id")
	oauth_app = relationship("OauthApp")
	approved_by = relationship("User", uselist=False, primaryjoin="Submission.is_approved==User.id")
	awards = relationship("AwardRelationship", order_by="AwardRelationship.awarded_utc.desc()", back_populates="post")
	flags = relationship("Flag", order_by="Flag.created_utc")
	comments = relationship("Comment", primaryjoin="Comment.parent_submission==Submission.id", back_populates="post")
	subr = relationship("Sub", primaryjoin="foreign(Submission.sub)==remote(Sub.name)")
	options = relationship("SubmissionOption", order_by="SubmissionOption.id")

	bump_utc = deferred(Column(Integer, server_default=FetchedValue()))

	def __init__(self, *args, **kwargs):
		if "created_utc" not in kwargs: kwargs["created_utc"] = int(time.time())
		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<Submission(id={self.id})>"

	@property
	@lazy
	def controversial(self):
		if self.downvotes > 5 and 0.25 < self.upvotes / self.downvotes < 4: return True
		return False


	@property
	@lazy
	def created_datetime(self):
		return str(time.strftime("%d/%B/%Y %H:%M:%S UTC", time.gmtime(self.created_utc)))

	@property
	@lazy
	def created_datetime(self):
		return str(time.strftime("%d/%B/%Y %H:%M:%S UTC", time.gmtime(self.created_utc)))

	@property
	@lazy
	def age_string(self):

		age = int(time.time()) - self.created_utc

		if age < 60:
			return "just now"
		elif age < 3600:
			minutes = int(age / 60)
			return f"{minutes}m ago"
		elif age < 86400:
			hours = int(age / 3600)
			return f"{hours}hr ago"
		elif age < 2678400:
			days = int(age / 86400)
			return f"{days}d ago"

		now = time.gmtime()
		ctd = time.gmtime(self.created_utc)

		months = now.tm_mon - ctd.tm_mon + 12 * (now.tm_year - ctd.tm_year)
		if now.tm_mday < ctd.tm_mday:
			months -= 1

		if months < 12:
			return f"{months}mo ago"
		else:
			years = int(months / 12)
			return f"{years}yr ago"

	@property
	@lazy
	def edited_string(self):

		age = int(time.time()) - self.edited_utc

		if age < 60:
			return "just now"
		elif age < 3600:
			minutes = int(age / 60)
			return f"{minutes}m ago"
		elif age < 86400:
			hours = int(age / 3600)
			return f"{hours}hr ago"
		elif age < 2678400:
			days = int(age / 86400)
			return f"{days}d ago"

		now = time.gmtime()
		ctd = time.gmtime(self.edited_utc)
		months = now.tm_mon - ctd.tm_mon + 12 * (now.tm_year - ctd.tm_year)
		if now.tm_mday < ctd.tm_mday:
			months -= 1

		if months < 12:
			return f"{months}mo ago"
		else:
			years = int(months / 12)
			return f"{years}yr ago"


	@property
	@lazy
	def edited_datetime(self):
		return str(time.strftime("%d/%B/%Y %H:%M:%S UTC", time.gmtime(self.edited_utc)))


	@property
	@lazy
	def score(self):
		return self.upvotes - self.downvotes

	@property
	@lazy
	def fullname(self):
		return f"t2_{self.id}"	


	@property
	@lazy
	def shortlink(self):
		link = f"/post/{self.id}"
		if self.sub: link = f"/h/{self.sub}{link}"

		if self.club: return link + '/-'

		output = title_regex.sub('', self.title.lower())
		output = output.split()[:6]
		output = '-'.join(output)

		if not output: output = '-'

		return f"{link}/{output}"

	@property
	@lazy
	def permalink(self):
		return SITE_FULL + self.shortlink

	@property
	@lazy
	def domain(self):
		if not self.url: return None
		if self.url.startswith('/'): return SITE
		domain = urlparse(self.url).netloc
		if domain.startswith("www."): domain = domain.split("www.")[1]
		return domain.replace("old.reddit.com", "reddit.com")

	@property
	@lazy
	def author_name(self):
		if self.ghost: return '👻'
		else: return self.author.username

	@property
	@lazy
	def is_youtube(self):
		return self.domain == "youtube.com" and self.embed_url and self.embed_url.startswith('<lite-youtube') 

	@property
	@lazy
	def thumb_url(self):
		if self.over_18: return f"{SITE_FULL}/assets/images/nsfw.webp?v=1"
		elif not self.url: return f"{SITE_FULL}/assets/images/{SITE_NAME}/default_text.webp?v=1"
		elif self.thumburl: 
			if self.thumburl.startswith('/'): return SITE_FULL + self.thumburl
			return self.thumburl
		elif self.is_youtube or self.is_video: return f"{SITE_FULL}/assets/images/default_thumb_video.webp?v=1"
		elif self.is_audio: return f"{SITE_FULL}/assets/images/default_thumb_audio.webp?v=1"
		elif self.domain == SITE: return f"{SITE_FULL}/assets/images/{SITE_NAME}/site_preview.webp?v=1" 
		else: return f"{SITE_FULL}/assets/images/default_thumb_link.webp?v=1"

	@property
	@lazy
	def json_raw(self):
		flags = {}
		for f in self.flags: flags[f.user.username] = f.reason

		data = {'author_name': self.author_name if self.author else '',
				'permalink': self.permalink,
				'shortlink': self.shortlink,
				'is_banned': bool(self.is_banned),
				'deleted_utc': self.deleted_utc,
				'created_utc': self.created_utc,
				'id': self.id,
				'title': self.title,
				'is_nsfw': self.over_18,
				'is_bot': self.is_bot,
				'thumb_url': self.thumb_url,
				'domain': self.domain,
				'url': self.realurl(None),
				'body': self.body,
				'body_html': self.body_html,
				'created_utc': self.created_utc,
				'edited_utc': self.edited_utc or 0,
				'comment_count': self.comment_count,
				'score': self.score,
				'upvotes': self.upvotes,
				'downvotes': self.downvotes,
				'stickied': self.stickied,
				'private' : self.private,
				'distinguish_level': self.distinguish_level,
				'voted': self.voted if hasattr(self, 'voted') else 0,
				'flags': flags,
				'club': self.club,
				}

		if self.ban_reason:
			data["ban_reason"]=self.ban_reason

		return data

	@property
	@lazy
	def json_core(self):

		if self.is_banned:
			return {'is_banned': True,
					'deleted_utc': self.deleted_utc,
					'ban_reason': self.ban_reason,
					'id': self.id,
					'title': self.title,
					'permalink': self.permalink,
					}
		elif self.deleted_utc:
			return {'is_banned': bool(self.is_banned),
					'deleted_utc': True,
					'id': self.id,
					'title': self.title,
					'permalink': self.permalink,
					}

		return self.json_raw

	@property
	@lazy
	def json(self):

		data=self.json_core
		
		if self.deleted_utc or self.is_banned:
			return data

		data["author"]='👻' if self.ghost else self.author.json_core
		data["comment_count"]=self.comment_count

	
		if "replies" in self.__dict__:
			data["replies"]=[x.json_core for x in self.replies]

		if "voted" in self.__dict__:
			data["voted"] = self.voted

		return data

	@lazy
	def award_count(self, kind, v):
		if v and v.poor: return 0
		return len([x for x in self.awards if x.kind == kind])

	@lazy
	def realurl(self, v):
		url = self.url

		if not url: return ''

		if url.startswith('/'): return SITE_FULL + url

		url = normalize_urls_runtime(url, v)

		if url.startswith("https://old.reddit.com/r/") and '/comments/' in url and "sort=" not in url:
			if "?" in url: url += "&context=9" 
			else: url += "?context=8"
			if v and v.controversial: url += "&sort=controversial"

		return url

	@lazy
	def realbody(self, v, listing=False):
		if self.club and not (v and (v.paid_dues or v.id == self.author_id)): return f"<p>{CC} ONLY</p>"

		body = self.body_html or ""

		body = censor_slurs(body, v)

		body = normalize_urls_runtime(body, v)

		if v and v.shadowbanned and v.id == self.author_id and 86400 > time.time() - self.created_utc > 20:
			ti = max(int((time.time() - self.created_utc)/60), 1)
			maxupvotes = min(ti, 11)
			rand = random.randint(0, maxupvotes)
			if self.upvotes < rand:
				amount = random.randint(0, 3)
				if amount == 1:
					self.views += amount*random.randint(3, 5)
					self.upvotes += amount
					g.db.add(self)


		if self.options:
			curr = [x for x in self.options if x.exclusive and x.voted(v)]
			if curr: curr = " value=" + str(curr[0].id)
			else: curr = ''
			body += f'<input class="d-none" id="current-{self.id}"{curr}>'

		for c in self.options:
			if c.exclusive:
				body += f'''<div class="custom-control"><input name="choice-{self.id}" autocomplete="off" class="custom-control-input" type="radio" id="{c.id}" onchange="choice_vote('{c.id}','{self.id}','post')"'''
				if c.voted(v): body += " checked "
				body += f'''><label class="custom-control-label" for="{c.id}">{c.body_html}<span class="presult-{self.id}'''
				body += f'"> - <a href="/votes/post/option/{c.id}"><span id="choice-{c.id}">{c.upvotes}</span> votes</a></span></label></div>'
			else:
				body += f'<div class="custom-control"><input type="checkbox" class="custom-control-input" id="{c.id}" name="option"'
				if c.voted(v): body += " checked"
				if v: body += f''' onchange="poll_vote('{c.id}', 'post')"'''
				else: body += f''' onchange="poll_vote_no_v('{c.id}', '{self.id}')"'''
				body += f'''><label class="custom-control-label" for="{c.id}">{c.body_html}<span class="presult-{self.id}'''
				body += f'"> - <a href="/votes/post/option/{c.id}"><span id="poll-{c.id}">{c.upvotes}</span> votes</a></span></label></div>'



		if not listing and self.author.sig_html and (self.author_id == MOOSE_ID or (not self.ghost and not (v and (v.sigs_disabled or v.poor)))):
			body += f"<hr>{self.author.sig_html}"

		return body

	@lazy
	def plainbody(self, v):
		if self.club and not (v and (v.paid_dues or v.id == self.author_id)): return f"<p>{CC} ONLY</p>"

		body = self.body

		if not body: return ""

		body = censor_slurs(body, v)

		body = normalize_urls_runtime(body, v)
		return body

	@lazy
	def realtitle(self, v):
		if self.club and not (v and (v.paid_dues or v.id == self.author_id)):
			if v: return random.choice(TROLLTITLES).format(username=v.username)
			elif dues == -2: return f'Please make an account to see this post'
			else: return f'{CC} MEMBERS ONLY'
		elif self.title_html: title = self.title_html
		else: title = self.title

		title = censor_slurs(title, v)

		return title

	@lazy
	def plaintitle(self, v):
		if self.club and not (v and (v.paid_dues or v.id == self.author_id)):
			if v: return random.choice(TROLLTITLES).format(username=v.username)
			else: return f'{CC} MEMBERS ONLY'
		else: title = self.title

		title = censor_slurs(title, v)

		return title

	@property
	@lazy
	def is_video(self):
		return self.url and any((self.url.lower().endswith(x) for x in ('.mp4','.webm','.mov'))) and is_safe_url(self.url)

	@property
	@lazy
	def is_audio(self):
		return self.url and any((self.url.lower().endswith(x) for x in ('.mp3','.wav','.ogg','.aac','.m4a','.flac'))) and is_safe_url(self.url)

	@property
	@lazy
	def is_image(self):
		if self.url and (self.url.lower().endswith('.webp') or self.url.lower().endswith('.jpg') or self.url.lower().endswith('.png') or self.url.lower().endswith('.gif') or self.url.lower().endswith('.jpeg') or self.url.lower().endswith('?maxwidth=9999') or self.url.lower().endswith('&fidelity=high')) and is_safe_url(self.url):
			return True
		return False

	@property
	@lazy
	def active_flags(self):
		return len(self.flags)