from flask import render_template, g
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred
import re, random
from urllib.parse import urlparse
from files.helpers.lazy import lazy
from files.helpers.const import SLURS
from files.__main__ import Base
from .flags import *
from os import environ
import time

site = environ.get("DOMAIN").strip()
site_name = environ.get("SITE_NAME").strip()


class Submission(Base):

	__tablename__ = "submissions"

	id = Column(BigInteger, primary_key=True)
	author_id = Column(BigInteger, ForeignKey("users.id"))
	edited_utc = Column(BigInteger, default=0)
	created_utc = Column(BigInteger, default=0)
	thumburl = Column(String(255))
	is_banned = Column(Boolean, default=False)
	removed_by = Column(Integer)
	bannedfor = Column(Boolean)
	processing = Column(Boolean, default=False)
	views = Column(Integer, default=0)
	deleted_utc = Column(Integer, default=0)
	distinguish_level = Column(Integer, default=0)
	created_str = Column(String(255))
	stickied = Column(String(255))
	is_pinned = Column(Boolean, default=False)
	private = Column(Boolean, default=False)
	club = Column(Boolean, default=False)
	comment_count = Column(Integer, default=0)
	comments = relationship("Comment", primaryjoin="Comment.parent_submission==Submission.id", viewonly=True)
	flags = relationship("Flag", lazy="dynamic", viewonly=True)
	is_approved = Column(Integer, ForeignKey("users.id"), default=0)
	over_18 = Column(Boolean, default=False)
	author = relationship("User", primaryjoin="Submission.author_id==User.id")
	is_bot = Column(Boolean, default=False)
	upvotes = Column(Integer, default=1)
	downvotes = Column(Integer, default=0)
	app_id=Column(Integer, ForeignKey("oauth_apps.id"))
	title = Column(String(500))
	title_html = Column(String(500))
	url = Column(String(500))
	body = deferred(Column(String(10000)))
	body_html = deferred(Column(String(20000)))
	ban_reason = Column(String(128))
	embed_url = Column(String(256))

	oauth_app = relationship("OauthApp", viewonly=True)
	approved_by = relationship("User", uselist=False, primaryjoin="Submission.is_approved==User.id", viewonly=True)
	awards = relationship("AwardRelationship", viewonly=True)

	def __init__(self, *args, **kwargs):

		if "created_utc" not in kwargs:
			kwargs["created_utc"] = int(time.time())
			kwargs["created_str"] = time.strftime(
				"%I:%M %p on %d %b %Y", time.gmtime(
					kwargs["created_utc"]))


		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<Submission(id={self.id})>"


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

		# compute number of months
		months = now.tm_mon - ctd.tm_mon + 12 * (now.tm_year - ctd.tm_year)
		# remove a month count if current day of month < creation day of month
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

		if not self.edited_utc: return "never"

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

		if months < 12:
			return f"{months}mo ago"
		else:
			years = now.tm_year - ctd.tm_year
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
		return f"https://{site}/post/{self.id}"

	@property
	@lazy
	def permalink(self):
		if self.club: return f"/post/{self.id}"

		output = self.title.lower()

		output = re.sub('&\w{2,3};', '', output)

		output = [re.sub('\W', '', word) for word in output.split()]
		output = [x for x in output if x][:6]

		output = '-'.join(output)

		if not output: output = '-'

		return f"/post/{self.id}/{output}"

	@lazy
	def rendered_page(self, sort=None, last_view_utc=None, comment=None, comment_info=None, v=None):

		if self.is_banned and not (v and (v.admin_level >= 3 or self.author_id == v.id)): template = "submission_banned.html"
		else: template = "submission.html"

		self.tree_comments(comment=comment)

		return render_template(template,
							   v=v,
							   p=self,
							   last_view_utc=last_view_utc,
							   sort=sort,
							   linked_comment=comment,
							   comment_info=comment_info,
							   render_replies=True
							   )

	@property
	@lazy
	def domain(self):

		if not self.url: return "text post"
		domain = urlparse(self.url).netloc
		if domain.startswith("www."): domain = domain.split("www.")[1]
		return domain.replace("old.reddit.com", "reddit.com")

	def tree_comments(self, comment=None, v=None):

		comments = self.__dict__.get('preloaded_comments', [])
		if not comments: return

		pinned_comment=[]

		index = {}
		for c in comments:

			if c.is_pinned and c.parent_fullname==self.fullname:
				pinned_comment += [c]
				continue

			if c.parent_fullname in index: index[c.parent_fullname].append(c)
			else: index[c.parent_fullname] = [c]

		for c in comments: c.__dict__["replies"] = index.get(c.fullname, [])

		if comment: self.__dict__["replies"] = [comment]
		else: self.__dict__["replies"] = pinned_comment + index.get(self.fullname, [])

	@property
	@lazy
	def thumb_url(self):
		if self.over_18: return f"https://{site}/assets/images/nsfw.webp"
		elif not self.url: return f"https://{site}/assets/images/{site_name}/default_thumb_text.webp"
		elif self.thumburl: return self.thumburl
		elif "youtu.be" in self.domain or "youtube.com" in self.domain: return f"https://{site}/assets/images/default_thumb_yt.webp"
		else: return f"https://{site}/assets/images/default_thumb_link.webp"

	@property
	@lazy
	def json_raw(self):
		flags = {}
		for f in self.flags: flags[f.user.username] = f.reason

		data = {'author_name': self.author.username,
				'permalink': self.permalink,
				'is_banned': bool(self.is_banned),
				'deleted_utc': self.deleted_utc,
				'created_utc': self.created_utc,
				'id': self.id,
				'title': self.title,
				'is_nsfw': self.over_18,
				'is_bot': self.is_bot,
				'thumb_url': self.thumb_url,
				'domain': self.domain,
				'url': self.url,
				'body': self.body,
				'body_html': self.body_html,
				'created_utc': self.created_utc,
				'edited_utc': self.edited_utc or 0,
				'comment_count': self.comment_count,
				'score': self.score,
				'upvotes': self.upvotes,
				'downvotes': self.downvotes,
				'stickied': self.stickied,
				'distinguish_level': self.distinguish_level,
				#'award_count': self.award_count,
				'voted': self.voted if hasattr(self, 'voted') else 0,
				'flags': flags,
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
		
		if self.deleted_utc > 0 or self.is_banned:
			return data

		data["author"]=self.author.json_core
		data["comment_count"]=self.comment_count

	
		if "replies" in self.__dict__:
			data["replies"]=[x.json_core for x in self.replies]

		if "voted" in self.__dict__:
			data["voted"] = self.voted

		return data

	def award_count(self, kind) -> int:
		return len([x for x in self.awards if x.kind == kind])

	@lazy
	def realurl(self, v):
		if v and v.agendaposter and random.randint(1, 10) < 4:
			return 'https://secure.actblue.com/donate/ms_blm_homepage_2019'
		elif v and self.url and self.url.startswith("https://old.reddit.com/"):
			url = self.url
			if not v.oldreddit: url = self.url.replace("old.reddit.com", "reddit.com")
			if v.controversial and '/comments/' in url and "sort=" not in url:
				if "?" in url: url += "&sort=controversial" 
				else: url += "?sort=controversial"
			return url
		elif self.url:
			if v and v.nitter: return self.url.replace("www.twitter.com", "nitter.net").replace("twitter.com", "nitter.net")
			return self.url
		else: return ""
 
	def realbody(self, v):
		if self.club and not (v and v.paid_dues): return "COUNTRY CLUB ONLY"
		body = self.body_html

		if not v or v.slurreplacer: 
			for s,r in SLURS.items(): 
				body = body.replace(s, r) 

		if v and not v.oldreddit: body = body.replace("old.reddit.com", "reddit.com")
		if v and v.nitter: body = body.replace("www.twitter.com", "nitter.net").replace("twitter.com", "nitter.net")
		return body

	@lazy
	def realtitle(self, v):
		if self.club and not (v and v.paid_dues) and not (v and v.admin_level == 6): return 'COUNTRY CLUB MEMBERS ONLY'
		elif self.title_html: title = self.title_html
		else: title = self.title

		if not v or v.slurreplacer:
			for s,r in SLURS.items(): title = title.replace(s, r) 

		return title

	@property
	@lazy
	def is_image(self):
		if self.url: return self.url.lower().endswith('.webp') or self.url.lower().endswith('.jpg') or self.url.lower().endswith('.png') or self.url.lower().endswith('.gif') or self.url.lower().endswith('.jpeg') or self.url.lower().endswith('?maxwidth=9999')
		else: return False

	@property
	@lazy
	def is_video(self) -> bool:
		if self.url:
			return self.url.startswith("https://i.imgur.com") and self.url.lower().endswith('.mp4')
		else:
			return False

	@property
	@lazy
	def active_flags(self): return self.flags.count()

	@property
	@lazy
	def ordered_flags(self): return self.flags.order_by(Flag.id).all()


class SaveRelationship(Base):

	__tablename__="save_relationship"

	id=Column(Integer, primary_key=true)
	user_id=Column(Integer, ForeignKey("users.id"))
	submission_id=Column(Integer, ForeignKey("submissions.id"))
	type=Column(Integer)