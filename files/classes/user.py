from sqlalchemy.orm import deferred, contains_eager, aliased
from secrets import token_hex
import pyotp

from files.helpers.discord import delete_role
from files.helpers.images import *
from files.helpers.const import *
from .alts import Alt
from .submission import SaveRelationship
from .comment import Notification
from .award import AwardRelationship
from .subscriptions import *
from .userblock import *
from .badges import *
from .clients import *
from files.__main__ import Base, cache
from files.helpers.security import *

site = environ.get("DOMAIN").strip()
defaulttheme = environ.get("DEFAULT_THEME", "light").strip()
defaultcolor = environ.get("DEFAULT_COLOR", "fff").strip()
class User(Base, Stndrd, Age_times):
	__tablename__ = "users"
	id = Column(Integer, primary_key=True)
	username = Column(String)
	namecolor = Column(String, default=defaultcolor)
	background = Column(String)
	customtitle = Column(String)
	customtitleplain = Column(String)
	titlecolor = Column(String, default=defaultcolor)
	theme = Column(String, default=defaulttheme)
	themecolor = Column(String, default=defaultcolor)
	song = Column(String)
	highres = Column(String)
	profileurl = Column(String)
	bannerurl = Column(String)
	patron = Column(Integer, default=0)
	verified = Column(Boolean)
	email = Column(String)
	css = deferred(Column(String))
	profilecss = deferred(Column(String))
	passhash = deferred(Column(String))
	post_count = Column(Integer, default=0)
	comment_count = Column(Integer, default=0)
	created_utc = Column(Integer, default=0)
	suicide_utc = Column(Integer, default=0)
	rent_utc = Column(Integer, default=0)
	admin_level = Column(Integer, default=0)
	agendaposter = Column(Boolean, default=False)
	agendaposter_expires_utc = Column(Integer, default=0)
	changelogsub = Column(Boolean, default=False)
	is_activated = Column(Boolean, default=False)
	shadowbanned = Column(Boolean, default=False)
	over_18 = Column(Boolean, default=False)
	hidevotedon = Column(Boolean, default=False)
	slurreplacer = Column(Boolean, default=True)
	flairchanged = Column(Boolean, default=False)
	newtab = Column(Boolean, default=False)
	newtabexternal = Column(Boolean, default=True)
	oldreddit = Column(Boolean, default=False)
	controversial = Column(Boolean, default=False)
	submissions = relationship(
		"Submission",
		lazy="dynamic",
		primaryjoin="Submission.author_id==User.id")
	comments = relationship(
		"Comment",
		lazy="dynamic",
		primaryjoin="Comment.author_id==User.id")
	bio = Column(String)
	bio_html = Column(String)
	badges = relationship("Badge", lazy="dynamic")
	notifications = relationship(
		"Notification",
		lazy="dynamic")

	is_banned = Column(Integer, default=0)
	unban_utc = Column(Integer, default=0)
	ban_reason = Column(String)
	login_nonce = Column(Integer, default=0)
	reserved = Column(String(256))
	coins = Column(Integer, default=0)
	coins_spent = Column(Integer, default=0)
	mfa_secret = deferred(Column(String(16)))
	is_private = Column(Boolean, default=False)
	stored_subscriber_count = Column(Integer, default=0)
	defaultsortingcomments = Column(String, default="top")
	defaultsorting = Column(String, default="hot")
	defaulttime = Column(String, default="day")

	is_nofollow = Column(Boolean, default=False)
	custom_filter_list = Column(String(1000))
	discord_id = Column(String(64))
	ban_evade = Column(Integer, default=0)
	original_username = deferred(Column(String(255)))
	subscriptions = relationship("Subscription")

	following = relationship("Follow", primaryjoin="Follow.user_id==User.id")
	followers = relationship("Follow", primaryjoin="Follow.target_id==User.id")

	viewers = relationship("ViewerRelationship", primaryjoin="User.id == ViewerRelationship.user_id")

	blocking = relationship("UserBlock", lazy="dynamic", primaryjoin="User.id==UserBlock.user_id")
	blocked = relationship("UserBlock", lazy="dynamic", primaryjoin="User.id==UserBlock.target_id")

	_applications = relationship("OauthApp", lazy="dynamic")
	authorizations = relationship("ClientAuth", lazy="dynamic")

	awards = relationship(
		"AwardRelationship",
		lazy="dynamic",
		primaryjoin="User.id==AwardRelationship.user_id"
	)

	referred_by = Column(Integer, ForeignKey("users.id"))

	referrals = relationship(
		"User",
		lazy="joined"
	)

	def __init__(self, **kwargs):

		if "password" in kwargs:
			kwargs["passhash"] = self.hash_password(kwargs["password"])
			kwargs.pop("password")

		kwargs["created_utc"] = int(time.time())

		super().__init__(**kwargs)

	@property
	@lazy
	def referral_count(self):
		return len(self.referrals)

	def has_block(self, target):

		return g.db.query(UserBlock).filter_by(
			user_id=self.id, target_id=target.id).first()

	def any_block_exists(self, other):

		return g.db.query(UserBlock).filter(
			or_(and_(UserBlock.user_id == self.id, UserBlock.target_id == other.id), and_(
				UserBlock.user_id == other.id, UserBlock.target_id == self.id))).first()

	def validate_2fa(self, token):

		x = pyotp.TOTP(self.mfa_secret)
		return x.verify(token, valid_window=1)

	@property
	def age(self):
		return int(time.time()) - self.created_utc

	@property
	def strid(self):
		return str(self.id)

	@cache.memoize()
	def userpagelisting(self, v=None, page=1, sort="new", t="all"):

		submissions = g.db.query(Submission).options(lazyload('*')).filter_by(author_id=self.id, is_pinned=False)

		if not (v and (v.admin_level >= 3 or v.id == self.id)):
			submissions = submissions.filter_by(deleted_utc=0)
			submissions = submissions.filter_by(is_banned=False)

		now = int(time.time())
		if t == 'hour':
			cutoff = now - 3600
		elif t == 'day':
			cutoff = now - 86400
		elif t == 'week':
			cutoff = now - 604800
		elif t == 'month':
			cutoff = now - 2592000
		elif t == 'year':
			cutoff = now - 31536000
		else:
			cutoff = 0
		submissions = submissions.filter(Submission.created_utc >= cutoff)

		if sort == "new":
			submissions = submissions.order_by(Submission.created_utc.desc()).all()
		elif sort == "old":
			submissions = submissions.order_by(Submission.created_utc.asc()).all()
		elif sort == "controversial":
			submissions = sorted(submissions.all(), key=lambda x: x.score_disputed, reverse=True)
		elif sort == "top":
			submissions = sorted(submissions.all(), key=lambda x: x.score, reverse=True)
		elif sort == "bottom":
			submissions = sorted(submissions.all(), key=lambda x: x.score)
		elif sort == "comments":
			submissions = submissions.order_by(Submission.comment_count.desc()).all()

		firstrange = 25 * (page - 1)
		secondrange = firstrange + 26
		listing = [x.id for x in submissions[firstrange:secondrange]]
		return listing

	@cache.memoize()
	def commentlisting(self, v=None, page=1, sort="new", t="all"):
		comments = self.comments.options(lazyload('*')).filter(Comment.parent_submission != None).join(Comment.post)

		if (not v) or (v.id != self.id and v.admin_level == 0):
			comments = comments.filter(Comment.deleted_utc == 0)
			comments = comments.filter(Comment.is_banned == False)

		comments = comments.options(contains_eager(Comment.post))

		now = int(time.time())
		if t == 'hour':
			cutoff = now - 3600
		elif t == 'day':
			cutoff = now - 86400
		elif t == 'week':
			cutoff = now - 604800
		elif t == 'month':
			cutoff = now - 2592000
		elif t == 'year':
			cutoff = now - 31536000
		else:
			cutoff = 0
		comments = comments.filter(Comment.created_utc >= cutoff)

		if sort == "new":
			comments = comments.order_by(Comment.created_utc.desc()).all()
		elif sort == "old":
			comments = comments.order_by(Comment.created_utc.asc()).all()
		elif sort == "controversial":
			comments = sorted(comments.all(), key=lambda x: x.score_disputed, reverse=True)
		elif sort == "top":
			comments = sorted(comments.all(), key=lambda x: x.score, reverse=True)
		elif sort == "bottom":
			comments = sorted(comments.all(), key=lambda x: x.score)

		firstrange = 25 * (page - 1)
		secondrange = firstrange + 26
		return [x.id for x in comments[firstrange:secondrange]]

	@property
	def fullname(self):
		return f"t1_{self.id}"

	@property
	def banned_by(self):

		if not self.is_banned: return None
		return g.db.query(User).filter_by(id=self.is_banned).first()

	def has_badge(self, badgedef_id):
		return self.badges.filter_by(badge_id=badgedef_id).first()

	def hash_password(self, password):
		return generate_password_hash(
			password, method='pbkdf2:sha512', salt_length=8)

	def verifyPass(self, password):
		return check_password_hash(self.passhash, password)

	@property
	def formkey(self):

		if "session_id" not in session:
			session["session_id"] = token_hex(16)

		msg = f"{session['session_id']}+{self.id}+{self.login_nonce}"

		return generate_hash(msg)

	def validate_formkey(self, formkey):

		return validate_hash(f"{session['session_id']}+{self.id}+{self.login_nonce}", formkey)

	@property
	def url(self):
		return f"/@{self.username}"

	def __repr__(self):
		return f"<User(username={self.username})>"

	@property
	def unban_string(self):
		if self.unban_utc == 0:
			return "permanently banned"

		wait = self.unban_utc - int(time.time())

		if wait < 60:
			text = f"{wait}s"
		else:
			days = wait//(24*60*60)
			wait -= days*24*60*60

			hours = wait//(60*60)
			wait -= hours*60*60

			mins = wait//60

			text = f"{days}d {hours:02d}h {mins:02d}m"

		return f"Unban in {text}"

	@property
	@lazy
	def display_awards(self):

		awards = {}
		active_awards = [x for x in self.awards if not x.given]

		for a in active_awards:
			if a.kind in awards:
				awards[a.kind]['count'] += 1
			else:
				awards[a.kind] = a.type
				awards[a.kind]['count'] = 1

		return sorted(list(awards.values()), key=lambda x: x['kind'], reverse=True)

	@property
	@lazy
	def received_awards(self):

		awards = {}

		posts_idlist = g.db.query(Submission.id).filter_by(author_id=self.id).subquery()
		comments_idlist = g.db.query(Comment.id).filter_by(author_id=self.id).subquery()

		post_awards = g.db.query(AwardRelationship).filter(AwardRelationship.submission_id.in_(posts_idlist)).all()
		comment_awards = g.db.query(AwardRelationship).filter(AwardRelationship.comment_id.in_(comments_idlist)).all()

		total_awards = post_awards + comment_awards

		for a in total_awards:
			if a.kind in awards:
				awards[a.kind]['count'] += 1
			else:
				awards[a.kind] = a.type
				awards[a.kind]['count'] = 1

		return sorted(list(awards.values()), key=lambda x: x['kind'], reverse=True)

	@property
	@lazy
	def post_notifications_count(self):
		return self.notifications.filter(Notification.read == False).join(Notification.comment).filter(
			Comment.author_id == AUTOJANNY_ACCOUNT).count()

	def notification_subscriptions(self, page=1, all_=False):

		notifications = self.notifications.join(Notification.comment).filter(Comment.author_id == AUTOJANNY_ACCOUNT)

		notifications = notifications.options(
			contains_eager(Notification.comment)
		)

		notifications = notifications.order_by(Notification.id.desc()).offset(25 * (page - 1)).limit(26)

		output = []
		for x in notifications:
			x.read = True
			g.db.add(x)
			output.append(x.comment_id)

		return output

	def notification_commentlisting(self, page=1, all_=False):

		notifications = self.notifications.join(Notification.comment).filter(
			Comment.is_banned == False,
			Comment.deleted_utc == 0,
			Comment.author_id != AUTOJANNY_ACCOUNT,
		)

		if not all_:
			notifications = notifications.filter(Notification.read == False)

		notifications = notifications.options(
			contains_eager(Notification.comment)
		)

		notifications = notifications.order_by(
			Notification.id.desc()).offset(25 * (page - 1)).limit(26)

		output = []
		for x in notifications:
			x.read = True
			g.db.add(x)
			output.append(x.comment_id)
		return output

	@property
	@lazy
	def notifications_count(self):

		return self.notifications.join(Notification.comment).filter(Notification.read == False,
																	Comment.is_banned == False,
																	Comment.deleted_utc == 0).count()

	@property
	@lazy
	def alts(self):

		subq = g.db.query(Alt).filter(
			or_(
				Alt.user1 == self.id,
				Alt.user2 == self.id
			)
		).subquery()

		data = g.db.query(
			User,
			aliased(Alt, alias=subq)
		).join(
			subq,
			or_(
				subq.c.user1 == User.id,
				subq.c.user2 == User.id
			)
		).filter(
			User.id != self.id
		).order_by(User.username.asc()).all()

		data = [x for x in data]
		output = []
		for x in data:
			user = x[0]
			user._is_manual = x[1].is_manual
			output.append(user)

		return output

	def alts_threaded(self, db):

		subq = db.query(Alt).filter(
			or_(
				Alt.user1 == self.id,
				Alt.user2 == self.id
			)
		).subquery()

		data = db.query(
			User,
			aliased(Alt, alias=subq)
		).join(
			subq,
			or_(
				subq.c.user1 == User.id,
				subq.c.user2 == User.id
			)
		).filter(
			User.id != self.id
		).order_by(User.username.asc()).all()

		data = [x for x in data]
		output = []
		for x in data:
			user = x[0]
			user._is_manual = x[1].is_manual
			output.append(user)

		return output

	def has_follower(self, user):

		return g.db.query(Follow).filter_by(target_id=self.id, user_id=user.id).first()


	@property
	def banner_url(self):
		if self.bannerurl: return self.bannerurl
		else: return f"https://{site}/assets/images/default_bg.gif"

	@cache.memoize()
	def defaultpicture(self):
		pic = random.randint(1, 150)
		return f"https://{site}/assets/images/defaultpictures/{pic}.gif"

	@property
	def profile_url(self):
		if self.profileurl: return self.profileurl
		elif "rdrama" in site: return self.defaultpicture()
		else: return f"https://{site}/assets/images/default-profile-pic.gif"

	@property
	def json_raw(self):
		data = {'username': self.username,
				'url': self.url,
				'is_banned': bool(self.is_banned),
				'created_utc': self.created_utc,
				'id': self.id,
				'is_private': self.is_private,
				'profile_url': self.profile_url,
				'banner_url': self.banner_url,
				'bio': self.bio,
				'bio_html': self.bio_html,
				'flair': self.customtitle
				}

		return data

	@property
	def json_core(self):

		now = int(time.time())
		if self.is_banned and (not self.unban_utc or now < self.unban_utc):
			return {'username': self.username,
					'url': self.url,
					'is_banned': True,
					'is_permanent_ban': not bool(self.unban_utc),
					'ban_reason': self.ban_reason,
					'id': self.id
					}
		return self.json_raw

	@property
	def json(self):
		data = self.json_core

		data["badges"] = [x.json_core for x in self.badges]
		data['coins'] = int(self.coins)
		data['post_count'] = self.post_count
		data['comment_count'] = self.comment_count

		return data

	def ban(self, admin=None, reason=None, days=0):

		if days > 0:
			ban_time = int(time.time()) + (days * 86400)
			self.unban_utc = ban_time

		else:
			self.bannerurl = None
			self.profileurl = None
			delete_role(self, "linked")

		self.is_banned = admin.id if admin else AUTOJANNY_ACCOUNT
		if reason: self.ban_reason = reason

		g.db.add(self)

	def unban(self):

		self.is_banned = 0
		self.unban_utc = 0

		g.db.add(self)

	@property
	def is_suspended(self):
		return (self.is_banned and (not self.unban_utc or self.unban_utc > time.time()))

	@property
	def is_blocking(self):
		return self.__dict__.get('_is_blocking', 0)

	@property
	def is_blocked(self):
		return self.__dict__.get('_is_blocked', 0)

	def refresh_selfset_badges(self):

		# check self-setting badges
		badge_types = g.db.query(BadgeDef).filter(
			BadgeDef.qualification_expr.isnot(None)).all()
		for badge in badge_types:
			if eval(badge.qualification_expr, {}, {'v': self}):
				if not self.has_badge(badge.id):
					new_badge = Badge(user_id=self.id,
									  badge_id=badge.id,
									  )
					g.db.add(new_badge)

			else:
				bad_badge = self.has_badge(badge.id)
				if bad_badge:
					g.db.delete(bad_badge)

		try:
			g.db.add(self)
		except:
			pass

	@property
	def applications(self):
		return [x for x in self._applications.order_by(
			OauthApp.id.asc()).all()]

	def subscribed_idlist(self, page=1):
		posts = g.db.query(Subscription.submission_id).filter_by(user_id=self.id).all()
		return [x[0] for x in posts]

	def saved_idlist(self, page=1):

		posts = g.db.query(Submission.id).options(lazyload('*')).filter_by(is_banned=False,
																		   deleted_utc=0
																		   )

		saved = g.db.query(SaveRelationship.submission_id).filter(SaveRelationship.user_id == self.id).subquery()
		posts = posts.filter(Submission.id.in_(saved))

		if self.admin_level == 0:
			blocking = g.db.query(
				UserBlock.target_id).filter_by(
				user_id=self.id).subquery()
			blocked = g.db.query(
				UserBlock.user_id).filter_by(
				target_id=self.id).subquery()

			posts = posts.filter(
				Submission.author_id.notin_(blocking),
				Submission.author_id.notin_(blocked)
			)

		posts = posts.order_by(Submission.created_utc.desc())

		return [x[0] for x in posts.offset(25 * (page - 1)).limit(26).all()]

	def saved_comment_idlist(self, page=1):

		comments = g.db.query(Comment.id).options(lazyload('*')).filter_by(is_banned=False, deleted_utc=0)

		saved = g.db.query(SaveRelationship.submission_id).filter(SaveRelationship.user_id == self.id).subquery()
		comments = comments.filter(Comment.id.in_(saved))

		if self.admin_level == 0:
			blocking = g.db.query(
				UserBlock.target_id).filter_by(
				user_id=self.id).subquery()
			blocked = g.db.query(
				UserBlock.user_id).filter_by(
				target_id=self.id).subquery()

			comments = comments.filter(
				Comment.author_id.notin_(blocking),
				Comment.author_id.notin_(blocked)
			)

		comments = comments.order_by(Comment.created_utc.desc())

		return [x[0] for x in comments.offset(25 * (page - 1)).limit(26).all()]

	@property
	def filter_words(self):
		l = [i.strip() for i in self.custom_filter_list.split('\n')] if self.custom_filter_list else []
		l = [i for i in l if i]
		return l


class ViewerRelationship(Base):

	__tablename__ = "viewers"

	id = Column(Integer, Sequence('viewers_id_seq'), primary_key=True)
	user_id = Column(Integer, ForeignKey('users.id'))
	viewer_id = Column(Integer, ForeignKey('users.id'))
	last_view_utc = Column(Integer)

	user = relationship("User", lazy="joined", primaryjoin="ViewerRelationship.user_id == User.id")
	viewer = relationship("User", lazy="joined", primaryjoin="ViewerRelationship.viewer_id == User.id")

	def __init__(self, **kwargs):

		if 'last_view_utc' not in kwargs:
			kwargs['last_view_utc'] = int(time.time())

		super().__init__(**kwargs)

	@property
	def last_view_since(self):

		return int(time.time()) - self.last_view_utc

	@property
	def last_view_string(self):

		age = self.last_view_since

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
