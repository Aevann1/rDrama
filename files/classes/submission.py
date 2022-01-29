from os import environ
import random
import re
import time
from urllib.parse import urlparse
from flask import render_template
from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from files.helpers.const import *
from files.helpers.lazy import lazy
from .flags import Flag
from .comment import Comment
from flask import g

class Submission(Base):
	__tablename__ = "submissions"

	id = Column(BigInteger, primary_key=True)
	author_id = Column(BigInteger, ForeignKey("users.id"))
	edited_utc = Column(BigInteger, default=0)
	created_utc = Column(BigInteger, default=0)
	thumburl = Column(String)
	is_banned = Column(Boolean, default=False)
	bannedfor = Column(Boolean)
	ghost = Column(Boolean)
	views = Column(Integer, default=0)
	deleted_utc = Column(Integer, default=0)
	distinguish_level = Column(Integer, default=0)
	stickied = Column(String)
	stickied_utc = Column(Integer)
	is_pinned = Column(Boolean, default=False)
	private = Column(Boolean, default=False)
	club = Column(Boolean, default=False)
	comment_count = Column(Integer, default=0)
	is_approved = Column(Integer, ForeignKey("users.id"), default=0)
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

	author = relationship("User", primaryjoin="Submission.author_id==User.id")
	oauth_app = relationship("OauthApp", viewonly=True)
	approved_by = relationship("User", uselist=False, primaryjoin="Submission.is_approved==User.id", viewonly=True)
	awards = relationship("AwardRelationship", viewonly=True)
	reports = relationship("Flag", viewonly=True)
	comments = relationship("Comment", primaryjoin="Comment.parent_submission==Submission.id")

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<Submission(id={self.id})>"

	@property
	@lazy
	def comments2(self):
		return g.db.query(Comment.author_id, Comment.created_utc, Comment.id).filter(Comment.parent_submission == self.id, Comment.author_id.notin_((AUTOPOLLER_ID,AUTOBETTER_ID))).all()

	@property
	@lazy
	def controversial(self):
		if self.downvotes > 5 and 0.25 < self.upvotes / self.downvotes < 4: return True
		return False

	@property
	@lazy
	def flags(self):
		return g.db.query(Flag).filter_by(post_id=self.id).order_by(Flag.id)

	@property
	@lazy
	def options(self):
		return g.db.query(Comment).filter_by(parent_submission = self.id, author_id = AUTOPOLLER_ID, level=1)

	@property
	@lazy
	def bet_options(self):
		return g.db.query(Comment).filter_by(parent_submission = self.id, author_id = AUTOBETTER_ID, level=1)

	def total_poll_voted(self, v):
		if v:
			for option in self.options:
				if option.poll_voted(v): return True
		return False

	def total_bet_voted(self, v):
		if "closed" in self.body.lower(): return True
		if v:
			for option in self.bet_options:
				if option.poll_voted(v): return True
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
		return f"/post/{self.id}"

	@property
	@lazy
	def permalink(self):
		if self.club: return f"{SITE_FULL}/post/{self.id}"

		output = self.title.lower()

		output = re.sub('&\w{2,3};', '', output, flags=re.A)

		output = [re.sub('\W', '', word, flags=re.A) for word in output.split()]
		output = [x for x in output if x][:6]

		output = '-'.join(output)

		if not output: output = '-'

		return f"{SITE_FULL}/post/{self.id}/{output}"

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
		if self.over_18: return f"{SITE_FULL}/static/assets/images/nsfw.webp"
		elif not self.url: return f"{SITE_FULL}/static/assets/images/{SITE_NAME}/default_text.webp"
		elif self.thumburl: 
			if self.thumburl.startswith('/'): return SITE_FULL + self.thumburl
			return self.thumburl
		elif self.is_youtube or self.is_video: return f"{SITE_FULL}/static/assets/images/default_thumb_yt.webp"
		else: return f"{SITE_FULL}/static/assets/images/default_thumb_link.webp"

	@property
	@lazy
	def json_raw(self):
		flags = {}
		for f in self.flags: flags[f.user.username] = f.reason

		data = {'author_name': self.author_name if self.author else '',
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

	def award_count(self, kind):
		return len([x for x in self.awards if x.kind == kind])

	@lazy
	def realurl(self, v):
		if v and self.url and self.url.startswith("https://old.reddit.com/"):
			url = self.url
			if v.teddit: url = self.url.replace("old.reddit.com", "teddit.net")
			elif not v.oldreddit: url = self.url.replace("old.reddit.com", "reddit.com")
			if '/comments/' in url and "sort=" not in url:
				if "?" in url: url += "&context=9" 
				else: url += "?context=9"
				if v.controversial: url += "&sort=controversial"
			return url
		elif self.url:
			if v and v.nitter: return self.url.replace("www.twitter.com", "nitter.net").replace("twitter.com", "nitter.net")
			if self.url.startswith('/'): return SITE_FULL + self.url
			return self.url
		else: return ""
 
	def realbody(self, v):
		if self.club and not (v and (v.paid_dues or v.id == self.author_id)): return f"<p>{CC} ONLY</p>"

		body = self.body_html or ""

		body = censor_slurs(body, v)

		if v:
			if v.teddit: body = body.replace("old.reddit.com", "teddit.net")
			elif not v.oldreddit: body = body.replace("old.reddit.com", "reddit.com")

			if v.nitter: body = body.replace("www.twitter.com", "nitter.net").replace("twitter.com", "nitter.net")

		if v and v.shadowbanned and v.id == self.author_id and 86400 > time.time() - self.created_utc > 20:
			ti = max(int((time.time() - self.created_utc)/60), 1)
			maxupvotes = min(ti, 27)
			rand = random.randint(0, maxupvotes)
			if self.upvotes < rand:
				amount = random.randint(0, 3)
				self.views += amount*random.randint(3, 5)
				self.upvotes += amount
				g.db.add(self)
				self.author.coins += amount
				g.db.add(self.author)
				g.db.commit()

		for o in self.options:
			body += f'<div class="custom-control"><input type="checkbox" class="custom-control-input" id="{o.id}" name="option"'
			if o.poll_voted(v): body += " checked"
			if v: body += f''' onchange="poll_vote('{o.id}', '{self.id}')"'''
			else: body += f''' onchange="poll_vote_no_v('{o.id}', '{self.id}')"'''
			body += f'''><label class="custom-control-label" for="{o.id}">{o.body_html}<span class="presult-{self.id}'''
			if not self.total_poll_voted(v): body += ' d-none'	
			body += f'"> - <a href="/votes?link=t3_{o.id}"><span id="poll-{o.id}">{o.upvotes}</span> votes</a></span></label></div>'


		for c in self.bet_options:
			body += f'''<div class="custom-control mt-3"><input autocomplete="off" class="custom-control-input bet" type="radio" id="{c.id}" onchange="bet_vote('{c.id}')"'''
			if c.poll_voted(v): body += " checked "
			if not (v and v.coins > 200) or self.total_bet_voted(v): body += " disabled "
			body += f'''><label class="custom-control-label" for="{c.id}">{c.body_html} - <a href="/votes?link=t3_{c.id}"><span id="bet-{c.id}">{c.upvotes}</span> bets</a>'''
			if not self.total_bet_voted(v):
				body += '''<span class="cost"> (cost of entry: 200 coins)</span>'''
			body += "</label>"
			if v and v.admin_level > 2:
				body += f'''<button class="btn btn-primary px-2 mx-2" style="font-size:10px;padding:2px;margin-top:-5px" onclick="post_toast('/distribute/{c.id}')">Declare winner</button>'''
			body += "</div>"


		if self.author.sig_html and not self.ghost and (self.author_id == MOOSE_ID or not (v and v.sigs_disabled)):
			body += f"<hr>{self.author.sig_html}"

		return body

	def plainbody(self, v):
		if self.club and not (v and (v.paid_dues or v.id == self.author_id)): return f"<p>{CC} ONLY</p>"

		body = self.body

		if not body: return ""

		body = censor_slurs(body, v)

		if v:
			if v.teddit: body = body.replace("old.reddit.com", "teddit.net")
			elif not v.oldreddit: body = body.replace("old.reddit.com", "reddit.com")

			if v.nitter: body = body.replace("www.twitter.com", "nitter.net").replace("twitter.com", "nitter.net")

		return body

	@lazy
	def realtitle(self, v):
		if self.club and not (v and (v.paid_dues or v.id == self.author_id)):
			if v: return random.choice(TROLLTITLES).format(username=v.username)
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
		return self.url and any((self.url.lower().endswith(x) for x in ('.mp4','.webm','.mov')))

	@property
	@lazy
	def is_image(self):
		if self.url: return self.url.lower().endswith('.webp') or self.url.lower().endswith('.jpg') or self.url.lower().endswith('.png') or self.url.lower().endswith('.gif') or self.url.lower().endswith('.jpeg') or self.url.lower().endswith('?maxwidth=9999') or self.url.lower().endswith('&fidelity=high')
		else: return False

	@property
	@lazy
	def active_flags(self): return self.flags.count()


class SaveRelationship(Base):

	__tablename__="save_relationship"

	id=Column(Integer, primary_key=True)
	user_id=Column(Integer)
	submission_id=Column(Integer)
	comment_id=Column(Integer)
	type=Column(Integer)