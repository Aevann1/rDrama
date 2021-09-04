from flask import render_template, g
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred
import re, random
from urllib.parse import urlparse
from files.helpers.lazy import lazy
from files.helpers.const import SLURS
from files.__main__ import Base
from .mix_ins import *
from .flags import *
from os import environ

site = environ.get("DOMAIN").strip()
site_name = environ.get("SITE_NAME").strip()

class SubmissionAux(Base):

	__tablename__ = "submissions_aux"

	key_id = Column(BigInteger, primary_key=True)
	id = Column(BigInteger, ForeignKey("submissions.id"))
	title = Column(String(500))
	title_html = Column(String(500))
	url = Column(String(500))
	body = Column(String(10000))
	body_html = Column(String(20000))
	ban_reason = Column(String(128))
	embed_url = Column(String(256))


class Submission(Base, Stndrd, Age_times, Scores, Fuzzing):

	__tablename__ = "submissions"

	id = Column(BigInteger, primary_key=True)
	submission_aux = relationship(
		"SubmissionAux",
		lazy="joined",
		uselist=False,
		innerjoin=True,
		primaryjoin="Submission.id==SubmissionAux.id")
	author_id = Column(BigInteger, ForeignKey("users.id"))
	edited_utc = Column(BigInteger, default=0)
	created_utc = Column(BigInteger, default=0)
	thumburl = Column(String)
	is_banned = Column(Boolean, default=False)
	bannedfor = Column(Boolean)
	views = Column(Integer, default=0)
	deleted_utc = Column(Integer, default=0)
	distinguish_level = Column(Integer, default=0)
	created_str = Column(String(255))
	stickied = Column(Boolean, default=False)
	is_pinned = Column(Boolean, default=False)
	private = Column(Boolean, default=False)
	comment_count = Column(Integer, default=0)
	comments = relationship(
		"Comment",
		lazy="joined",
		primaryjoin="Comment.parent_submission==Submission.id",
		)
	flags = relationship("Flag", lazy="dynamic")
	is_approved = Column(Integer, ForeignKey("users.id"), default=0)
	over_18 = Column(Boolean, default=False)
	author = relationship(
		"User",
		lazy="joined",
		innerjoin=True,
		primaryjoin="Submission.author_id==User.id")
	is_pinned = Column(Boolean, default=False)
	is_bot = Column(Boolean, default=False)

	upvotes = Column(Integer, default=1)
	downvotes = Column(Integer, default=0)

	app_id=Column(Integer, ForeignKey("oauth_apps.id"))
	oauth_app=relationship("OauthApp")

	approved_by = relationship(
		"User",
		uselist=False,
		primaryjoin="Submission.is_approved==User.id")

	awards = relationship("AwardRelationship", lazy="joined")

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
	def score(self):
		return self.upvotes - self.downvotes

	@property
	@lazy
	def hotscore(self):
		return 10000000*(self.upvotes - self.downvotes + 1)/(((self.age+3600)/1000)**(1.35))

	@property
	@lazy
	def score_disputed(self):
		return (self.upvotes+1) * (self.downvotes+1)


	@property
	@lazy
	def fullname(self):
		return f"t2_{self.id}"	
		
	@property
	@lazy
	def permalink(self):

		output = self.title.lower()

		output = re.sub('&\w{2,3};', '', output)

		output = [re.sub('\W', '', word) for word in output.split()]
		output = [x for x in output if x][:6]

		output = '-'.join(output)

		if not output:
			output = '-'

		return f"/post/{self.id}/{output}"

	def rendered_page(self, sort=None, comment=None, comment_info=None, v=None):

		# check for banned
		if v and (v.admin_level >= 3 or self.author_id == v.id):
			template = "submission.html"
		elif self.is_banned:
			template = "submission_banned.html"
		else:
			template = "submission.html"

		# load and tree comments
		# calling this function with a comment object will do a comment
		# permalink thing
		if "replies" not in self.__dict__ and "preloaded_comments" in self.__dict__:
			self.tree_comments(comment=comment)

		return render_template(template,
							   v=v,
							   p=self,
							   sort=sort,
							   linked_comment=comment,
							   comment_info=comment_info,
							   render_replies=True,
							   )

	@property
	@lazy
	def domain(self):

		if not self.url: return "text post"
		domain = urlparse(self.url).netloc
		if domain.startswith("www."): domain = domain.split("www.")[1]
		return domain.replace("old.reddit.com", "reddit.com")

	def tree_comments(self, comment=None, v=None):

		comments = self.__dict__.get('preloaded_comments',[])
		if not comments:
			return

		pinned_comment=[]

		index = {}
		for c in comments:

			if c.is_pinned and c.parent_fullname==self.fullname:
				pinned_comment+=[c]
				continue

			if c.parent_fullname in index:
				index[c.parent_fullname].append(c)
			else:
				index[c.parent_fullname] = [c]

		for c in comments:
			c.__dict__["replies"] = index.get(c.fullname, [])

		if comment:
			self.__dict__["replies"] = [comment]
		else:
			self.__dict__["replies"] = pinned_comment + index.get(self.fullname, [])

	@property
	@lazy
	def thumb_url(self):
		if self.over_18: return f"https://{site}/assets/images/nsfw.gif"
		elif not self.url: return f"https://{site}/assets/images/{site_name}/default_thumb_text.gif"
		elif self.thumburl: return self.thumburl
		elif "youtu.be" in self.domain or "youtube.com" in self.domain: return f"https://{site}/assets/images/default_thumb_yt.gif"
		else: return f"https://{site}/assets/images/default_thumb_link.gif"

	@property

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
				'score': self.score_fuzzed,
				'upvotes': self.upvotes_fuzzed,
				'downvotes': self.downvotes_fuzzed,
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

	@property
	def title(self):
		return self.submission_aux.title

	@title.setter
	def title(self, x):
		self.submission_aux.title = x
		g.db.add(self.submission_aux)

	@property
	def url(self):
		return self.submission_aux.url

	@url.setter
	def url(self, x):
		self.submission_aux.url = x
		g.db.add(self.submission_aux)

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
		elif self.url: return self.url
		else: return ""
 
	@property
	def body(self):
		return self.submission_aux.body

	@body.setter
	def body(self, x):
		self.submission_aux.body = x
		g.db.add(self.submission_aux)

	@property
	def body_html(self):
		return self.submission_aux.body_html

	@body_html.setter
	def body_html(self, x):
		self.submission_aux.body_html = x
		g.db.add(self.submission_aux)

	def realbody(self, v):
		body = self.submission_aux.body_html

		if not v or v.slurreplacer: 
			for s,r in SLURS.items(): 
				body = body.replace(s, r) 

		if v and not v.oldreddit: body = body.replace("old.reddit.com", "reddit.com")
		return body

	@property
	def title_html(self):
		return self.submission_aux.title_html

	@title_html.setter
	def title_html(self, x):
		self.submission_aux.title_html = x
		g.db.add(self.submission_aux)

	def realtitle(self, v):
		if self.title_html: title = self.title_html
		else: title = self.title

		if not v or v.slurreplacer: 
			for s,r in SLURS.items(): title = title.replace(s, r) 

		return title

	@property
	def ban_reason(self):
		return self.submission_aux.ban_reason

	@ban_reason.setter
	def ban_reason(self, x):
		self.submission_aux.ban_reason = x
		g.db.add(self.submission_aux)

	@property
	def embed_url(self):
		return self.submission_aux.embed_url

	@embed_url.setter
	def embed_url(self, x):
		self.submission_aux.embed_url = x
		g.db.add(self.submission_aux)
	
	@property
	def is_blocked(self):
		return self.__dict__.get('_is_blocked', False)

	@property
	def is_blocking(self):
		return self.__dict__.get('_is_blocking', False)

	#@property
	#def award_count(self):
		#return len(self.awards)

	@property
	def is_image(self):
		if self.url: return self.url.lower().endswith('.jpg') or self.url.lower().endswith('.png') or self.url.lower().endswith('.gif') or self.url.lower().endswith('.jpeg') or self.url.lower().endswith('?maxwidth=9999')
		else: return False

	@property
	@lazy
	def active_flags(self): return self.flags.count()

	@property
	@lazy
	def ordered_flags(self): return self.flags.order_by(Flag.id).all()


class SaveRelationship(Base, Stndrd):

	__tablename__="save_relationship"

	id=Column(Integer, primary_key=true)
	user_id=Column(Integer, ForeignKey("users.id"))
	submission_id=Column(Integer, ForeignKey("submissions.id"))
	type=Column(Integer)
