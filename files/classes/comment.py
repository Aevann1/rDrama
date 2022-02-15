from os import environ
import re
import time
from urllib.parse import urlencode, urlparse, parse_qs
from flask import *
from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from files.classes.votes import CommentVote
from files.helpers.const import *
from files.helpers.lazy import lazy
from .flags import CommentFlag
from random import randint
from .votes import CommentVote

class Comment(Base):

	__tablename__ = "comments"

	id = Column(Integer, primary_key=True)
	author_id = Column(Integer, ForeignKey("users.id"))
	parent_submission = Column(Integer, ForeignKey("submissions.id"))
	created_utc = Column(Integer)
	edited_utc = Column(Integer, default=0)
	is_banned = Column(Boolean, default=False)
	ghost = Column(Boolean)
	bannedfor = Column(Boolean)
	distinguish_level = Column(Integer, default=0)
	deleted_utc = Column(Integer, default=0)
	is_approved = Column(Integer, ForeignKey("users.id"))
	level = Column(Integer, default=0)
	parent_comment_id = Column(Integer, ForeignKey("comments.id"))
	top_comment_id = Column(Integer)
	over_18 = Column(Boolean, default=False)
	is_bot = Column(Boolean, default=False)
	is_pinned = Column(String)
	is_pinned_utc = Column(Integer)
	sentto = Column(Integer, ForeignKey("users.id"))
	app_id = Column(Integer, ForeignKey("oauth_apps.id"))
	upvotes = Column(Integer, default=1)
	downvotes = Column(Integer, default=0)
	realupvotes = Column(Integer, default=1)
	body = Column(String)
	body_html = Column(String)
	ban_reason = Column(String)
	slots_result = Column(String)
	blackjack_result = Column(String)
	wordle_result = Column(String)
	treasure_amount = Column(String)

	oauth_app = relationship("OauthApp", viewonly=True)
	post = relationship("Submission", viewonly=True)
	author = relationship("User", primaryjoin="User.id==Comment.author_id")
	senttouser = relationship("User", primaryjoin="User.id==Comment.sentto", viewonly=True)
	parent_comment = relationship("Comment", remote_side=[id], viewonly=True)
	child_comments = relationship("Comment", remote_side=[parent_comment_id], viewonly=True)
	awards = relationship("AwardRelationship", viewonly=True)
	reports = relationship("CommentFlag", viewonly=True)
	
	def __init__(self, *args, **kwargs):
		if "created_utc" not in kwargs: kwargs["created_utc"] = int(time.time())
		super().__init__(*args, **kwargs)

	def __repr__(self):

		return f"<Comment(id={self.id})>"

	@property
	@lazy
	def top_comment(self):
		return g.db.query(Comment).filter_by(id=self.top_comment_id).one_or_none()

	@property
	@lazy
	def flags(self):
		return g.db.query(CommentFlag).filter_by(comment_id=self.id).order_by(CommentFlag.id)

	@lazy
	def poll_voted(self, v):
		if v:
			vote = g.db.query(CommentVote.vote_type).filter_by(user_id=v.id, comment_id=self.id).one_or_none()
			if vote: return vote[0]
		return None

	@property
	@lazy
	def options(self):
		return tuple(x for x in self.child_comments if x.author_id == AUTOPOLLER_ID)

	@property
	@lazy
	def choices(self):
		return tuple(x for x in self.child_comments if x.author_id == AUTOCHOICE_ID)

	def total_poll_voted(self, v):
		if v:
			for option in self.options:
				if option.poll_voted(v): return True
		return False

	def total_choice_voted(self, v):
		if v:
			return g.db.query(CommentVote).filter(CommentVote.user_id == v.id, CommentVote.comment_id.in_(tuple(x.id for x in self.choices))).all()
		return False

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
	def age_string(self):
		if not self.created_utc: return None
		
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
		if self.replies2 != None:  return [x for x in self.replies2 if not x.author.shadowbanned]
		return sorted((x for x in self.child_comments if x.author and not x.author.shadowbanned and x.author_id not in (AUTOPOLLER_ID, AUTOBETTER_ID, AUTOCHOICE_ID)), key=lambda x: x.realupvotes, reverse=True)

	@property
	def replies3(self):
		if self.replies2 != None: return self.replies2
		return sorted((x for x in self.child_comments if x.author_id not in (AUTOPOLLER_ID, AUTOBETTER_ID, AUTOCHOICE_ID)), key=lambda x: x.realupvotes, reverse=True)

	@property
	def replies2(self):
		return self.__dict__.get("replies2", None)

	@replies2.setter
	def replies2(self, value):
		self.__dict__["replies2"] = value

	@property
	@lazy
	def shortlink(self):
		return f"{SITE_FULL}/comment/{self.id}#context"

	@property
	@lazy
	def shortlink_context(self):
		return f"/comment/{self.id}?context=8#context"

	@property
	@lazy
	def author_name(self):
		if self.ghost: return '👻'
		else: return self.author.username

	@property
	@lazy
	def permalink(self):
		return f"{SITE_FULL}/comment/{self.id}?context=8#context"

	@property
	@lazy
	def json_raw(self):
		flags = {}
		for f in self.flags: flags[f.user.username] = f.reason

		data= {
			'id': self.id,
			'level': self.level,
			'author_name': self.author_name,
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
			'post_id': self.post.id if self.post else 0,
			'score': self.score,
			'upvotes': self.upvotes,
			'downvotes': self.downvotes,
			'is_bot': self.is_bot,
			'flags': flags,
			}

		if self.ban_reason:
			data["ban_reason"]=self.ban_reason

		return data

	def award_count(self, kind):
		return len([x for x in self.awards if x.kind == kind])

	@property
	@lazy
	def json_core(self):
		if self.is_banned:
			data= {'is_banned': True,
					'ban_reason': self.ban_reason,
					'id': self.id,
					'post': self.post.id if self.post else 0,
					'level': self.level,
					'parent': self.parent_fullname
					}
		elif self.deleted_utc:
			data= {'deleted_utc': self.deleted_utc,
					'id': self.id,
					'post': self.post.id if self.post else 0,
					'level': self.level,
					'parent': self.parent_fullname
					}
		else:

			data=self.json_raw

			if self.level>=2: data['parent_comment_id']= self.parent_comment_id

		if "replies" in self.__dict__:
			data['replies']=[x.json_core for x in self.replies]

		return data

	@property
	@lazy
	def json(self):
	
		data=self.json_core

		if self.deleted_utc or self.is_banned:
			return data

		data["author"]='👻' if self.ghost else self.author.json_core
		data["post"]=self.post.json_core if self.post else ''

		if self.level >= 2:
			data["parent"]=self.parent.json_core


		return data

	def realbody(self, v):
		if self.post and self.post.club and not (v and (v.paid_dues or v.id in [self.author_id, self.post.author_id])): return f"<p>{CC} ONLY</p>"

		body = self.body_html or ""

		if body:
			body = censor_slurs(body, v)

			if v:
				if v.teddit: body = body.replace("old.reddit.com", "teddit.net")
				elif not v.oldreddit: body = body.replace("old.reddit.com", "reddit.com")

				if v.nitter and not '/i/' in body: body = body.replace("www.twitter.com", "nitter.net").replace("twitter.com", "nitter.net")

			if v and v.controversial:
				for i in re.finditer('(/comments/.*?)"', body):
					url = i.group(1)
					p = urlparse(url).query
					p = parse_qs(p)

					if 'sort' not in p: p['sort'] = ['controversial']

					url_noquery = url.split('?')[0]
					body = body.replace(url, f"{url_noquery}?{urlencode(p, True)}")

			if v and v.shadowbanned and v.id == self.author_id and 86400 > time.time() - self.created_utc > 60:
				ti = max(int((time.time() - self.created_utc)/60), 1)
				maxupvotes = min(ti, 6)
				rand = randint(0, maxupvotes)
				if self.upvotes < rand:
					amount = randint(0, 1)
					if amount == 1:
						self.upvotes += amount
						g.db.add(self)
						g.db.commit()

		for c in self.options:
			body += f'<div class="custom-control"><input type="checkbox" class="custom-control-input" id="{c.id}" name="option"'
			if c.poll_voted(v): body += " checked"
			if v: body += f''' onchange="poll_vote('{c.id}', '{self.id}')"'''
			else: body += f''' onchange="poll_vote_no_v('{c.id}', '{self.id}')"'''
			body += f'''><label class="custom-control-label" for="{c.id}">{c.body_html}<span class="presult-{self.id}'''
			if not self.total_poll_voted(v): body += ' d-none'	
			body += f'"> - <a href="/votes?link=t3_{c.id}"><span id="poll-{c.id}">{c.upvotes}</span> votes</a></span></label></div>'

		curr = self.total_choice_voted(v)
		if curr: curr = " value=" + str(curr[0].comment_id)
		else: curr = ''
		body += f'<input class="d-none" id="current-{self.id}"{curr}>'

		for c in self.choices:
			body += f'''<div class="custom-control"><input name="choice-{self.id}" autocomplete="off" class="custom-control-input" type="radio" id="{c.id}" onchange="choice_vote('{c.id}','{self.id}')"'''
			if c.poll_voted(v): body += " checked "
			body += f'''><label class="custom-control-label" for="{c.id}">{c.body_html}<span class="presult-{self.id}'''
			if not self.total_choice_voted(v): body += ' d-none'	
			body += f'"> - <a href="/votes?link=t3_{c.id}"><span id="choice-{c.id}">{c.upvotes}</span> votes</a></span></label></div>'

		if self.author.sig_html and not self.ghost and (self.author_id == MOOSE_ID or not (v and v.sigs_disabled)):
			body += f"<hr>{self.author.sig_html}"

		return body

	def plainbody(self, v):
		if self.post and self.post.club and not (v and (v.paid_dues or v.id in [self.author_id, self.post.author_id])): return f"<p>{CC} ONLY</p>"

		body = self.body

		if not body: return ""

		body = censor_slurs(body, v)

		if v and not v.oldreddit: body = body.replace("old.reddit.com", "reddit.com")

		if v and v.nitter and not '/i/' in body: body = body.replace("www.twitter.com", "nitter.net").replace("twitter.com", "nitter.net")

		if v and v.controversial:
			for i in re.finditer('(/comments/.*?)"', body):
				url = i.group(1)
				p = urlparse(url).query
				p = parse_qs(p)

				if 'sort' not in p: p['sort'] = ['controversial']

				url_noquery = url.split('?')[0]
				body = body.replace(url, f"{url_noquery}?{urlencode(p, True)}")

		return body

	def print(self):
		print(f'post: {self.id}, comment: {self.author_id}', flush=True)
		return ''

	@lazy
	def collapse_for_user(self, v, path):
		if v and self.author_id == v.id: return False

		if path == '/admin/removed/comments': return False

		if self.over_18 and not (v and v.over_18) and not (self.post and self.post.over_18): return True

		if self.is_banned: return True

		if path.startswith('/post') and (self.slots_result or self.blackjack_result) and (not self.body or len(self.body) <= 50) and self.level > 1: return True
			
		if v and v.filter_words and self.body and any(x in self.body for x in v.filter_words): return True
		
		return False

	@property
	@lazy
	def is_op(self): return self.author_id==self.post.author_id
	
	@property
	@lazy
	def active_flags(self): return self.flags.count()

class Notification(Base):

	__tablename__ = "notifications"

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey("users.id"))
	comment_id = Column(Integer, ForeignKey("comments.id"))
	read = Column(Boolean, default=False)

	comment = relationship("Comment", viewonly=True)
	user = relationship("User", viewonly=True)

	def __repr__(self):

		return f"<Notification(id={self.id})>"
