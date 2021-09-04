import re
from urllib.parse import urlencode, urlparse, parse_qs
from flask import *
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred
from files.helpers.lazy import lazy
from files.helpers.const import SLURS
from files.__main__ import Base
from .mix_ins import *
from .flags import CommentFlag

class CommentAux(Base):

	__tablename__ = "comments_aux"

	key_id = Column(Integer, primary_key=True)
	id = Column(Integer, ForeignKey("comments.id"))
	body = Column(String(10000))
	body_html = Column(String(20000))
	ban_reason = Column(String(256), default='')


class Comment(Base, Age_times, Scores, Stndrd, Fuzzing):

	__tablename__ = "comments"

	id = Column(Integer, primary_key=True)
	comment_aux = relationship(
		"CommentAux",
		lazy="joined",
		uselist=False,
		innerjoin=True,
		primaryjoin="Comment.id==CommentAux.id")
	author_id = Column(Integer, ForeignKey("users.id"))
	parent_submission = Column(Integer, ForeignKey("submissions.id"))
	# this column is foreignkeyed to comment(id) but we can't do that yet as
	# "comment" class isn't yet defined
	created_utc = Column(Integer, default=0)
	edited_utc = Column(Integer, default=0)
	is_banned = Column(Boolean, default=False)
	bannedfor = Column(Boolean)
	distinguish_level = Column(Integer, default=0)
	deleted_utc = Column(Integer, default=0)
	is_approved = Column(Integer, default=0)
	level = Column(Integer, default=0)
	parent_comment_id = Column(Integer, ForeignKey("comments.id"))

	over_18 = Column(Boolean, default=False)
	is_bot = Column(Boolean, default=False)
	is_pinned = Column(Boolean, default=False)
	sentto=Column(Integer)

	app_id = Column(Integer, ForeignKey("oauth_apps.id"))
	oauth_app=relationship("OauthApp")

	post = relationship("Submission")
	flags = relationship("CommentFlag", lazy="dynamic")
	author = relationship(
		"User",
		lazy="joined",
		innerjoin=True,
		primaryjoin="User.id==Comment.author_id")

	upvotes = Column(Integer, default=1)
	downvotes = Column(Integer, default=0)

	parent_comment = relationship("Comment", remote_side=[id])
	child_comments = relationship("Comment", remote_side=[parent_comment_id])

	awards = relationship("AwardRelationship", lazy="joined")

	def __init__(self, *args, **kwargs):

		if "created_utc" not in kwargs:
			kwargs["created_utc"] = int(time.time())

		super().__init__(*args, **kwargs)

	def __repr__(self):

		return f"<Comment(id={self.id})>"

	@property
	@lazy
	def score(self):
		return self.upvotes - self.downvotes

	@property
	@lazy
	def fullname(self):
		return f"t3_{self.id}"

	@property
	@lazy
	def score_disputed(self):
		return (self.upvotes+1) * (self.downvotes+1)

	@property
	@lazy
	def parent(self):

		if not self.parent_submission: return None

		if self.level == 1: return self.post

		else: return g.db.query(Comment).get(self.parent_comment_id)

	@property
	@lazy
	def parent_fullname(self):
		if self.parent_comment_id: return f"t3_{self.parent_comment_id}"
		elif self.parent_submission: return f"t2_{self.parent_submission}"

	@property
	@lazy
	def replies(self):
		r = self.__dict__.get("replies", None)
		if r: r = [x for x in r if not x.author.shadowbanned]
		if not r and r != []:  r = sorted([x for x in self.child_comments if not x.author.shadowbanned], key=lambda x: x.score, reverse=True)
		return r

	@replies.setter
	def replies(self, value):
		self.__dict__["replies"] = value

	@property
	def replies2(self):
		return self.__dict__.get("replies2", [])

	@replies2.setter
	def replies2(self, value):
		self.__dict__["replies2"] = value

	@property
	@lazy
	def replies3(self):
		r = self.__dict__.get("replies", None)
		if not r and r != []:  r = sorted([x for x in self.child_comments], key=lambda x: x.score, reverse=True)
		return r

	@property
	@lazy
	def permalink(self):
		if self.post: return f"{self.post.permalink}/{self.id}/"
		else: return f"/comment/{self.id}/"

	@property
	def json_raw(self):
		flags = {}
		for f in self.flags: flags[f.user.username] = f.reason

		data= {
			'id': self.id,
			'level': self.level,
			'author_name': self.author.username,
			'body': self.body,
			'body_html': self.body_html,
			'is_bot': self.is_bot,
			'created_utc': self.created_utc,
			'edited_utc': self.edited_utc or 0,
			'is_banned': bool(self.is_banned),
			'deleted_utc': self.deleted_utc,
			'is_nsfw': self.over_18,
			'permalink': self.permalink,
			'is_pinned': self.is_pinned,
			'distinguish_level': self.distinguish_level,
			'post_id': self.post.id,
			'score': self.score_fuzzed,
			'upvotes': self.upvotes_fuzzed,
			'downvotes': self.downvotes_fuzzed,
			#'award_count': self.award_count,
			'is_bot': self.is_bot,
			'flags': flags,
			}

		if self.ban_reason:
			data["ban_reason"]=self.ban_reason

		return data

	def award_count(self, kind) -> int:
		return len([x for x in self.awards if x.kind == kind])

	@property
	def json_core(self):
		if self.is_banned:
			data= {'is_banned': True,
					'ban_reason': self.ban_reason,
					'id': self.id,
					'post': self.post.id,
					'level': self.level,
					'parent': self.parent_fullname
					}
		elif self.deleted_utc > 0:
			data= {'deleted_utc': self.deleted_utc,
					'id': self.id,
					'post': self.post.id,
					'level': self.level,
					'parent': self.parent_fullname
					}
		else:

			data=self.json_raw

			if self.level>=2: data['parent_comment_id']= self.parent_comment_id,

		if "replies" in self.__dict__:
			data['replies']=[x.json_core for x in self.replies]

		return data

	@property
	def json(self):
	
		data=self.json_core

		if self.deleted_utc > 0 or self.is_banned:
			return data

		data["author"]=self.author.json_core
		data["post"]=self.post.json_core

		if self.level >= 2:
			data["parent"]=self.parent.json_core


		return data

	@property
	def is_blocking(self):
		return self.__dict__.get('_is_blocking', 0)

	@property
	def is_blocked(self):
		return self.__dict__.get('_is_blocked', 0)

	@property
	def body(self):
		if self.comment_aux: return self.comment_aux.body
		else: return ""

	@body.setter
	def body(self, x):
		self.comment_aux.body = x
		g.db.add(self.comment_aux)

	@property
	def body_html(self):
		return self.comment_aux.body_html

	@body_html.setter
	def body_html(self, x):
		self.comment_aux.body_html = x
		g.db.add(self.comment_aux)

	def realbody(self, v):
		body = self.comment_aux.body_html

		if not v or v.slurreplacer: 
			for s,r in SLURS.items(): body = body.replace(s, r) 

		if v and not v.oldreddit: body = body.replace("old.reddit.com", "reddit.com")

		if v and v.controversial:
			for i in re.finditer('(/comments/.*?)"', body):
				url = i.group(1)
				p = urlparse(url).query
				p = parse_qs(p)

				if 'sort' not in p:
					p['sort'] = ['controversial']

				url_noquery = url.split('?')[0]
				body = body.replace(url, f"{url_noquery}?{urlencode(p, True)}")

		return body

	@property
	def ban_reason(self):
		return self.comment_aux.ban_reason

	@ban_reason.setter
	def ban_reason(self, x):
		self.comment_aux.ban_reason = x
		g.db.add(self.comment_aux)

	#@property
	#def award_count(self):
		#return len(self.awards)

	def collapse_for_user(self, v):

		if self.over_18 and not (v and v.over_18) and not self.post.over_18:
			return True

		if not v:
			return False
			
		if any([x in self.body for x in v.filter_words]):
			return True
		
		if self.is_banned: return True
		
		return False

	@property
	@lazy
	def is_op(self): return self.author_id==self.post.author_id
	
	@property
	@lazy
	def active_flags(self): return self.flags.count()

	@property
	@lazy
	def ordered_flags(self): return self.flags.order_by(CommentFlag.id).all()



class Notification(Base):

	__tablename__ = "notifications"

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey("users.id"))
	comment_id = Column(Integer, ForeignKey("comments.id"))
	read = Column(Boolean, default=False)
	followsender = Column(Integer)
	unfollowsender = Column(Integer)
	blocksender = Column(Integer)
	unblocksender = Column(Integer)

	comment = relationship("Comment", lazy="joined", innerjoin=True)
	user=relationship("User", innerjoin=True)

	def __repr__(self):

		return f"<Notification(id={self.id})>"
