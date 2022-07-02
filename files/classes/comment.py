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
from files.helpers.regex import *
from files.helpers.regex import *
from files.helpers.lazy import lazy
from .flags import CommentFlag
from .votes import CommentVote
from .saves import CommentSaveRelationship
from random import randint
from math import floor


def normalize_urls_runtime(body, v):
	
	if v:
		body = body.replace("https://old.reddit.com/r/", f'https://{v.reddit}/r/')

		if v.nitter: body = twitter_to_nitter_regex.sub(r'https://nitter.net/\1', body)

	return body

def sort_comments(sort, comments):

	if sort == 'new':
		return comments.order_by(Comment.id.desc())
	elif sort == 'old':
		return comments.order_by(Comment.id)
	elif sort == 'controversial':
		return comments.order_by((Comment.upvotes+1)/(Comment.downvotes+1) + (Comment.downvotes+1)/(Comment.upvotes+1), Comment.downvotes.desc(), Comment.id.desc())
	elif sort == "bottom":
		return comments.order_by(Comment.upvotes - Comment.downvotes)
	else:
		return comments.order_by(Comment.realupvotes.desc(), Comment.id.desc())


class Comment(Base):

	__tablename__ = "comments"

	id = Column(Integer, primary_key=True)
	author_id = Column(Integer, ForeignKey("users.id"))
	parent_submission = Column(Integer, ForeignKey("submissions.id"))
	created_utc = Column(Integer)
	edited_utc = Column(Integer, default=0)
	is_banned = Column(Boolean, default=False)
	ghost = Column(Boolean, default=False)
	bannedfor = Column(String)
	distinguish_level = Column(Integer, default=0)
	deleted_utc = Column(Integer, default=0)
	is_approved = Column(Integer, ForeignKey("users.id"))
	level = Column(Integer, default=1)
	parent_comment_id = Column(Integer, ForeignKey("comments.id"))
	top_comment_id = Column(Integer)
	over_18 = Column(Boolean, default=False)
	is_bot = Column(Boolean, default=False)
	stickied = Column(String)
	stickied_utc = Column(Integer)
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

	oauth_app = relationship("OauthApp")
	post = relationship("Submission", back_populates="comments")
	author = relationship("User", primaryjoin="User.id==Comment.author_id")
	senttouser = relationship("User", primaryjoin="User.id==Comment.sentto")
	parent_comment = relationship("Comment", remote_side=[id], back_populates="child_comments")
	child_comments = relationship("Comment", remote_side=[parent_comment_id], back_populates="parent_comment")
	awards = relationship("AwardRelationship", order_by="AwardRelationship.awarded_utc.desc()", back_populates="comment")
	flags = relationship("CommentFlag", order_by="CommentFlag.created_utc")
	options = relationship("CommentOption", order_by="CommentOption.id")

	def __init__(self, *args, **kwargs):
		if "created_utc" not in kwargs:
			kwargs["created_utc"] = int(time.time())
		super().__init__(*args, **kwargs)

	def __repr__(self):

		return f"<Comment(id={self.id})>"

	@property
	@lazy
	def top_comment(self):
		return g.db.get(Comment, self.top_comment_id)


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
		notif_utc = self.__dict__.get("notif_utc")

		if notif_utc: timestamp = notif_utc
		elif self.created_utc: timestamp = self.created_utc
		else: return None
		
		age = int(time.time()) - timestamp

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
		ctd = time.gmtime(timestamp)

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

		else: return g.db.get(Comment, self.parent_comment_id)

	@property
	@lazy
	def parent_fullname(self):
		if self.parent_comment_id: return f"t3_{self.parent_comment_id}"
		elif self.parent_submission: return f"t2_{self.parent_submission}"

	@lazy
	def replies(self, sort=None):
		if self.replies2 != None: return [x for x in self.replies2 if not x.author.shadowbanned]
		if not self.parent_submission:
			return [x for x in self.child_comments.order_by(Comment.id) if not x.author.shadowbanned]

		comments = self.child_comments
		return [x for x in comments if not x.author.shadowbanned]
		

	@lazy
	def replies3(self, sort):
		if self.replies2 != None: return self.replies2
		if not self.parent_submission:
			return self.child_comments.order_by(Comment.id).all()

		return self.child_comments


	@property
	def replies2(self):
		return self.__dict__.get("replies2")

	@replies2.setter
	def replies2(self, value):
		self.__dict__["replies2"] = value

	@property
	@lazy
	def shortlink(self):
		return f"{self.post.shortlink}/{self.id}?context=8#context"

	@property
	@lazy
	def permalink(self):
		return f"{SITE_FULL}{self.shortlink}"

	@property
	@lazy
	def morecomments(self):
		return f"{self.post.permalink}/{self.id}#context"

	@property
	@lazy
	def author_name(self):
		if self.ghost: return '👻'
		else: return self.author.username

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
			'permalink': f'/comment/{self.id}',
			'stickied': self.stickied,
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

	@lazy
	def award_count(self, kind, v):
		if v and v.poor: return 0
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
			data['replies']=[x.json_core for x in self.replies(None)]

		return data

	@property
	def json(self):
	
		data=self.json_core

		if self.deleted_utc or self.is_banned:
			return data

		data["author"]='👻' if self.ghost else self.author.json_core
		data["post"]=self.post.json_core if self.post else ''

		if self.level >= 2:
			data["parent"]=self.parent.json_core


		return data

	@lazy
	def realbody(self, v):
		if self.post and self.post.club and not (v and (v.paid_dues or v.id in [self.author_id, self.post.author_id])): return f"<p>{CC} ONLY</p>"

		body = self.body_html or ""

		if body:
			body = censor_slurs(body, v)

			body = normalize_urls_runtime(body, v)


			if v and v.controversial:
				captured = []
				for i in controversial_regex.finditer(body):
					if i.group(1) in captured: continue
					captured.append(i.group(1))

					url = i.group(1)
					p = urlparse(url).query
					p = parse_qs(p)

					if 'sort' not in p: p['sort'] = ['controversial']

					url_noquery = url.split('?')[0]
					body = body.replace(url, f"{url_noquery}?{urlencode(p, True)}")

			if v and v.shadowbanned and v.id == self.author_id and 86400 > time.time() - self.created_utc > 60:
				ti = max(int((time.time() - self.created_utc)/60), 1)
				maxupvotes = min(ti, 13)
				rand = randint(0, maxupvotes)
				if self.upvotes < rand:
					amount = randint(0, 3)
					if amount == 1:
						self.upvotes += amount
						g.db.add(self)

		if self.options:
			curr = [x for x in self.options if x.exclusive and x.voted(v)]
			if curr: curr = " value=" + str(curr[0].id)
			else: curr = ''
			body += f'<input class="d-none" id="current-{self.id}"{curr}>'

		for c in self.options:
			if c.exclusive:
				body += f'''<div class="custom-control"><input name="choice-{self.id}" autocomplete="off" class="custom-control-input" type="radio" id="{c.id}" onchange="choice_vote('{c.id}','{self.id}','comment')"'''
				if c.voted(v): body += " checked "
				body += f'''><label class="custom-control-label" for="{c.id}">{c.body_html}<span class="presult-{self.id}'''
				body += f'"> - <a href="/votes/comment/option/{c.id}"><span id="choice-{c.id}">{c.upvotes}</span> votes</a></span></label></div>'
			else:
				body += f'<div class="custom-control"><input type="checkbox" class="custom-control-input" id="{c.id}" name="option"'
				if c.voted(v): body += " checked"
				if v: body += f''' onchange="poll_vote('{c.id}', 'comment')"'''
				else: body += f''' onchange="poll_vote_no_v('{c.id}', '{self.id}')"'''
				body += f'''><label class="custom-control-label" for="{c.id}">{c.body_html}<span class="presult-{self.id}'''
				body += f'"> - <a href="/votes/comment/option/{c.id}"><span id="poll-{c.id}">{c.upvotes}</span> votes</a></span></label></div>'

		if self.author.sig_html and (self.author_id == MOOSE_ID or (not self.ghost and not (v and (v.sigs_disabled or v.poor)))):
			body += f"<hr>{self.author.sig_html}"

		return body

	@lazy
	def plainbody(self, v):
		if self.post and self.post.club and not (v and (v.paid_dues or v.id in [self.author_id, self.post.author_id])): return f"<p>{CC} ONLY</p>"

		body = self.body

		if not body: return ""

		return censor_slurs(body, v)

	@lazy
	def collapse_for_user(self, v, path):
		if v and self.author_id == v.id: return False

		if path == '/admin/removed/comments': return False

		if f'/{self.id}' in path: return False

		if self.over_18 and not (v and v.over_18) and not (self.post and self.post.over_18): return True

		if self.is_banned: return True

		if (self.slots_result or self.blackjack_result or self.wordle_result) and (not self.body or len(self.body_html) <= 100) and 9 > self.level > 1: return True
			
		if v and v.filter_words and self.body and any(x in self.body for x in v.filter_words): return True
		
		return False

	@property
	@lazy
	def is_op(self): return self.author_id==self.post.author_id
	
	@property
	@lazy
	def active_flags(self): return len(self.flags)
	
	@lazy
	def wordle_html(self, v):
		if not self.wordle_result: return ''

		split_wordle_result = self.wordle_result.split('_')
		wordle_guesses = split_wordle_result[0]
		wordle_status = split_wordle_result[1]
		wordle_answer = split_wordle_result[2]

		body = f"<span id='wordle-{self.id}' class='ml-2'><small>{wordle_guesses}</small>"

		if wordle_status == 'active' and v and v.id == self.author_id:
			body += f'''<input autocomplete="off" id="guess_box" type="text" name="guess" class="form-control" maxsize="4" style="width: 200px;display: initial"placeholder="5-letter guess"></input><button class="action-{self.id} btn btn-success small" style="text-transform: uppercase; padding: 2px"onclick="handle_action('wordle','{self.id}',document.getElementById('guess_box').value)">Guess</button>'''
		elif wordle_status == 'won':
			body += "<strong class='ml-2'>Correct!</strong>"
		elif wordle_status == 'lost':
			body += f"<strong class='ml-2'>Lost. The answer was: {wordle_answer}</strong>"
		
		body += '</span>'
		return body

	@lazy
	def blackjack_html(self, v):
		if not self.blackjack_result: return ''

		split_result = self.blackjack_result.split('_')
		blackjack_status = split_result[3]
		player_hand = split_result[0].replace('X', '10')
		dealer_hand = split_result[1].split('/')[0] if blackjack_status == 'active' else split_result[1]
		dealer_hand = dealer_hand.replace('X', '10')
		wager = int(split_result[4])
		try: kind = split_result[5]
		except: kind = "coins"
		currency_kind = "Coins" if kind == "coins" else "Marseybux"

		try: is_insured = split_result[6]
		except: is_insured = "0"

		body = f"<span id='blackjack-{self.id}' class='ml-2'><em>{player_hand} vs. {dealer_hand}</em>"
		
		if blackjack_status == 'active' and v and v.id == self.author_id:
			body += f'''
			<button
				class="action-{self.id} btn btn-success small"
				style="text-transform: uppercase; padding: 2px"
				onclick="handle_action('blackjack','{self.id}','hit')">
					Hit
			</button>
			<button
				class="action-{self.id} btn btn-danger small"
				style="text-transform: uppercase; padding: 2px"
				onclick="handle_action('blackjack','{self.id}','stay')">
					Stay
			</button>
			<button
				class="action-{self.id} btn btn-secondary small"
				style="text-transform: uppercase; padding: 2px"
				onclick="handle_action('blackjack','{self.id}','doubledown')">
					Double Down
			</button>
			'''

			if dealer_hand[0][0] == 'A' and not is_insured == "1":
				body += f'''
				<button
					class="action-{self.id} btn btn-secondary small"
					style="text-transform: uppercase; padding: 2px"
					onclick="handle_action('blackjack','{self.id}','insurance')">
						Insure
				</button>
				'''

		elif blackjack_status == 'push':
			body += f"<strong class='ml-2'>Pushed. Refunded {wager} {currency_kind}.</strong>"
		elif blackjack_status == 'bust':
			body += f"<strong class='ml-2'>Bust. Lost {wager} {currency_kind}.</strong>"
		elif blackjack_status == 'lost':
			body += f"<strong class='ml-2'>Lost {wager} {currency_kind}.</strong>"
		elif blackjack_status == 'won':
			body += f"<strong class='ml-2'>Won {wager} {currency_kind}.</strong>"
		elif blackjack_status == 'blackjack':
			body += f"<strong class='ml-2'>Blackjack! Won {floor(wager * 3/2)} {currency_kind}.</strong>"

		if is_insured == "1":
			body += f" <em class='text-success'>Insured.</em>"

		body += '</span>'
		return body