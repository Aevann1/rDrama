from os import environ
import re
import time
from urllib.parse import urlencode, urlparse, parse_qs
from flask import *
from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from files.classes.votes import CommentVote
from files.helpers.const import AUTOPOLLER_ID, censor_slurs
from files.helpers.lazy import lazy
from .flags import CommentFlag
from random import randint

site = environ.get("DOMAIN").strip()
if site == 'pcmemes.net': cc = "splash mountain"
else: cc = "country club"

class Comment(Base):

	__tablename__ = "comments"

	id = Column(Integer, primary_key=True)
	author_id = Column(Integer, ForeignKey("users.id"))
	parent_submission = Column(Integer, ForeignKey("submissions.id"))
	created_utc = Column(Integer, default=0)
	edited_utc = Column(Integer, default=0)
	is_banned = Column(Boolean, default=False)
	removed_by = Column(Integer)
	bannedfor = Column(Boolean)
	distinguish_level = Column(Integer, default=0)
	deleted_utc = Column(Integer, default=0)
	is_approved = Column(Integer, default=0)
	level = Column(Integer, default=0)
	parent_comment_id = Column(Integer, ForeignKey("comments.id"))
	over_18 = Column(Boolean, default=False)
	is_bot = Column(Boolean, default=False)
	is_pinned = Column(String)
	sentto=Column(Integer, ForeignKey("users.id"))
	notifiedto=Column(Integer)
	app_id = Column(Integer, ForeignKey("oauth_apps.id"))
	oauth_app = relationship("OauthApp", viewonly=True)
	upvotes = Column(Integer, default=1)
	downvotes = Column(Integer, default=0)
	body = Column(String)
	body_html = Column(String)
	ban_reason = Column(String)

	post = relationship("Submission", viewonly=True)
	author = relationship("User", primaryjoin="User.id==Comment.author_id")
	senttouser = relationship("User", primaryjoin="User.id==Comment.sentto", viewonly=True)
	parent_comment = relationship("Comment", remote_side=[id], viewonly=True)
	child_comments = relationship("Comment", remote_side=[parent_comment_id], viewonly=True)
	awards = relationship("AwardRelationship", viewonly=True)
	
	def __init__(self, *args, **kwargs):

		if "created_utc" not in kwargs:
			kwargs["created_utc"] = int(time.time())

		super().__init__(*args, **kwargs)

	def __repr__(self):

		return f"<Comment(id={self.id})>"

	@property
	@lazy
	def flags(self):
		return g.db.query(CommentFlag).filter_by(comment_id=self.id)

	@lazy
	def poll_voted(self, v):
		if v:
			vote = g.db.query(CommentVote).filter_by(user_id=v.id, comment_id=self.id).first()
			if vote: return vote.vote_type
			else: return None
		else: return None

	@property
	@lazy
	def options(self):
		return [x for x in self.child_comments if x.author_id == AUTOPOLLER_ID]

	def total_poll_voted(self, v):
		if v:
			for option in self.options:
				if option.poll_voted(v): return True
		return False

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

		if not self.edited_utc:
			return "never"

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
	def score(self):
		return self.upvotes - self.downvotes

	@property
	@lazy
	def fullname(self):
		return f"t3_{self.id}"

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
	def replies(self):
		r = self.__dict__.get("replies", None)
		if r: r = [x for x in r if not x.author.shadowbanned]
		if not r and r != []: r = sorted([x for x in self.child_comments if not x.author.shadowbanned and x.author_id != AUTOPOLLER_ID], key=lambda x: x.score, reverse=True)
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
	def replies3(self):
		r = self.__dict__.get("replies", None)
		if not r and r != []: r = sorted([x for x in self.child_comments if x.author_id != AUTOPOLLER_ID], key=lambda x: x.score, reverse=True)
		return r

	@property
	@lazy
	def shortlink(self):
		return f"http://{site}/comment/{self.id}#context"

	@property
	@lazy
	def permalink(self):
		if self.post and self.post.club: return f"/comment/{self.id}?context=9#context"

		if self.post: return f"{self.post.permalink}/{self.id}?context=9#context"
		else: return f"/comment/{self.id}?context=9#context"

	@property
	@lazy
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
			'score': self.score,
			'upvotes': self.upvotes,
			'downvotes': self.downvotes,
			'is_bot': self.is_bot,
			'flags': flags,
			}

		if self.ban_reason:
			data["ban_reason"]=self.ban_reason

		return data

	def award_count(self, kind) -> int:
		return len([x for x in self.awards if x.kind == kind])

	@property
	@lazy
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
	@lazy
	def json(self):
	
		data=self.json_core

		if self.deleted_utc > 0 or self.is_banned:
			return data

		data["author"]=self.author.json_core
		data["post"]=self.post.json_core

		if self.level >= 2:
			data["parent"]=self.parent.json_core


		return data

	def realbody(self, v):
		if self.post and self.post.club and not (v and v.paid_dues): return f"<p>{cc} ONLY</p>"

		body = self.body_html

		if not body: return ""

		body = censor_slurs(body, v)

		if v and not v.oldreddit: body = body.replace("old.reddit.com", "reddit.com")

		if v and v.nitter: body = body.replace("www.twitter.com", "nitter.net").replace("twitter.com", "nitter.net")

		if v and v.controversial:
			for i in re.finditer('(/comments/.*?)"', body):
				url = i.group(1)
				p = urlparse(url).query
				p = parse_qs(p)

				if 'sort' not in p: p['sort'] = ['controversial']

				url_noquery = url.split('?')[0]
				body = body.replace(url, f"{url_noquery}?{urlencode(p, True)}")

		if v and v.shadowbanned and v.id == self.author_id and 86400 > time.time() - self.created_utc > 600:
			rand = randint(1,16)
			if self.upvotes < rand:
				self.upvotes = rand
				g.db.add(self)
				g.db.commit()

		return body

	def plainbody(self, v):
		if self.post and self.post.club and not (v and v.paid_dues): return f"<p>{cc} ONLY</p>"

		body = self.body

		if not body: return ""

		body = censor_slurs(body, v)

		if v and not v.oldreddit: body = body.replace("old.reddit.com", "reddit.com")

		if v and v.nitter: body = body.replace("www.twitter.com", "nitter.net").replace("twitter.com", "nitter.net")

		if v and v.controversial:
			for i in re.finditer('(/comments/.*?)"', body):
				url = i.group(1)
				p = urlparse(url).query
				p = parse_qs(p)

				if 'sort' not in p: p['sort'] = ['controversial']

				url_noquery = url.split('?')[0]
				body = body.replace(url, f"{url_noquery}?{urlencode(p, True)}")

		return body

	@lazy
	def collapse_for_user(self, v):

		if self.over_18 and not (v and v.over_18) and not (self.post and self.post.over_18): return True

		if not v: return False
			
		if v.filter_words and self.body and any([x in self.body for x in v.filter_words]): return True
		
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
	removefollowsender = Column(Integer)
	blocksender = Column(Integer)
	unblocksender = Column(Integer)

	comment = relationship("Comment", viewonly=True)
	user = relationship("User", viewonly=True)

	def __repr__(self):

		return f"<Notification(id={self.id})>"
