from sqlalchemy.orm import deferred, aliased
from secrets import token_hex
import pyotp
from files.helpers.discord import remove_user
from files.helpers.images import *
from files.helpers.const import *
from .alts import Alt
from .saves import *
from .notifications import Notification
from .award import AwardRelationship
from .follows import *
from .subscriptions import *
from .userblock import *
from .badges import *
from .clients import *
from .mod_logs import *
from .mod import *
from .exiles import *
from .sub_block import *
from files.__main__ import Base, cache
from files.helpers.security import *
import random
from os import environ, remove, path

defaulttheme = environ.get("DEFAULT_THEME", "midnight").strip()
defaulttimefilter = environ.get("DEFAULT_TIME_FILTER", "all").strip()
cardview = bool(int(environ.get("CARD_VIEW", 1)))

if SITE_NAME in ('Cringetopia', 'WPD'): patron_default = 7
else: patron_default = 0

class User(Base):
	__tablename__ = "users"

	if SITE == "pcmemes.net":
		basedcount = Column(Integer, default=0)
		pills = deferred(Column(String, default=""))

	id = Column(Integer, primary_key=True)
	username = Column(String)
	namecolor = Column(String, default=DEFAULT_COLOR)
	background = Column(String)
	customtitle = Column(String)
	customtitleplain = deferred(Column(String))
	titlecolor = Column(String, default=DEFAULT_COLOR)
	theme = Column(String, default=defaulttheme)
	themecolor = Column(String, default=DEFAULT_COLOR)
	cardview = Column(Boolean, default=cardview)
	song = Column(String)
	highres = Column(String)
	profileurl = Column(String)
	bannerurl = Column(String)
	house = Column(String)
	patron = Column(Integer, default=patron_default)
	patron_utc = Column(Integer, default=0)
	verified = Column(String)
	verifiedcolor = Column(String)
	marseyawarded = Column(Integer)
	rehab = Column(Integer)
	longpost = Column(Integer)
	winnings = Column(Integer, default=0)
	unblockable = Column(Boolean)
	bird = Column(Integer)
	email = deferred(Column(String))
	css = deferred(Column(String))
	profilecss = deferred(Column(String))
	passhash = deferred(Column(String))
	post_count = Column(Integer, default=0)
	comment_count = Column(Integer, default=0)
	received_award_count = Column(Integer, default=0)
	created_utc = Column(Integer)
	admin_level = Column(Integer, default=0)
	coins_spent = Column(Integer, default=0)
	lootboxes_bought = Column(Integer, default=0)
	agendaposter = Column(Integer, default=0)
	changelogsub = Column(Boolean, default=False)
	is_activated = Column(Boolean, default=False)
	shadowbanned = Column(String)
	over_18 = Column(Boolean, default=False)
	hidevotedon = Column(Boolean, default=False)
	highlightcomments = Column(Boolean, default=True)
	slurreplacer = Column(Boolean, default=True)
	flairchanged = Column(Integer)
	newtab = Column(Boolean, default=False)
	newtabexternal = Column(Boolean, default=True)
	reddit = Column(String, default='old.reddit.com')
	nitter = Column(Boolean)
	mute = Column(Boolean)
	unmutable = Column(Boolean)
	eye = Column(Boolean)
	alt = Column(Boolean)
	frontsize = Column(Integer, default=25)
	controversial = Column(Boolean, default=False)
	bio = deferred(Column(String))
	bio_html = Column(String)
	sig = deferred(Column(String))
	sig_html = Column(String)
	fp = Column(String)
	sigs_disabled = Column(Boolean)
	fish = Column(Boolean)
	progressivestack = Column(Integer)
	deflector = Column(Integer)
	friends = deferred(Column(String))
	friends_html = deferred(Column(String))
	enemies = deferred(Column(String))
	enemies_html = deferred(Column(String))
	is_banned = Column(Integer, default=0)
	unban_utc = Column(Integer, default=0)
	ban_reason = deferred(Column(String))
	club_allowed = Column(Boolean)
	login_nonce = Column(Integer, default=0)
	reserved = deferred(Column(String))
	coins = Column(Integer, default=0)
	truecoins = Column(Integer, default=0)
	procoins = Column(Integer, default=0)
	mfa_secret = deferred(Column(String))
	is_private = Column(Boolean, default=False)
	stored_subscriber_count = Column(Integer, default=0)
	defaultsortingcomments = Column(String, default="top")
	defaultsorting = Column(String, default="hot")
	defaulttime = Column(String, default=defaulttimefilter)
	is_nofollow = Column(Boolean, default=False)
	custom_filter_list = Column(String)
	discord_id = Column(String)
	ban_evade = Column(Integer, default=0)
	original_username = deferred(Column(String))
	referred_by = Column(Integer, ForeignKey("users.id"))
	subs_created = Column(Integer, default=0)

	badges = relationship("Badge", viewonly=True)
	subscriptions = relationship("Subscription", viewonly=True)
	following = relationship("Follow", primaryjoin="Follow.user_id==User.id", viewonly=True)
	followers = relationship("Follow", primaryjoin="Follow.target_id==User.id", viewonly=True)
	viewers = relationship("ViewerRelationship", primaryjoin="User.id == ViewerRelationship.user_id", viewonly=True)
	blocking = relationship("UserBlock", lazy="dynamic", primaryjoin="User.id==UserBlock.user_id", viewonly=True)
	blocked = relationship("UserBlock", lazy="dynamic", primaryjoin="User.id==UserBlock.target_id", viewonly=True)
	authorizations = relationship("ClientAuth", viewonly=True)
	awards = relationship("AwardRelationship", primaryjoin="User.id==AwardRelationship.user_id", viewonly=True)
	referrals = relationship("User", viewonly=True)

	def __init__(self, **kwargs):

		if "password" in kwargs:
			kwargs["passhash"] = self.hash_password(kwargs["password"])
			kwargs.pop("password")

		if "created_utc" not in kwargs: kwargs["created_utc"] = int(time.time())

		super().__init__(**kwargs)


	@lazy
	def mods(self, sub):
		return self.admin_level == 3 or bool(g.db.query(Mod.user_id).filter_by(user_id=self.id, sub=sub).one_or_none())

	@lazy
	def exiled_from(self, sub):
		return self.admin_level < 2 and bool(g.db.query(Exile.user_id).filter_by(user_id=self.id, sub=sub).one_or_none())

	@property
	@lazy
	def all_blocks(self):
		return [x[0] for x in g.db.query(SubBlock.sub).filter_by(user_id=self.id).all()]

	@lazy
	def blocks(self, sub):
		return g.db.query(SubBlock).filter_by(user_id=self.id, sub=sub).one_or_none()

	@lazy
	def mod_date(self, sub):
		if self.id == AEVANN_ID: return 1
		mod = g.db.query(Mod).filter_by(user_id=self.id, sub=sub).one_or_none()
		if not mod: return None
		return mod.created_utc

	@property
	@lazy
	def csslazy(self):
		return self.css

	@property
	@lazy
	def created_date(self):

		return time.strftime("%d %b %Y", time.gmtime(self.created_utc))


	@property
	@lazy
	def is_cakeday(self):
		if time.time() - self.created_utc > 363 * 86400:
			date = time.strftime("%d %b", time.gmtime(self.created_utc))
			now = time.strftime("%d %b", time.gmtime())
			if date == now:
				if not self.has_badge(134):
					new_badge = Badge(badge_id=134, user_id=self.id)
					g.db.add(new_badge)
					g.db.commit()
				return True
		return False

	@property
	@lazy
	def discount(self):
		if self.patron == 1: discount = 0.90
		elif self.patron == 2: discount = 0.85
		elif self.patron == 3: discount = 0.80
		elif self.patron == 4: discount = 0.75
		elif self.patron == 5: discount = 0.70
		elif self.patron == 6: discount = 0.65
		elif self.patron == 7: discount = 0.60
		else: discount = 1

		for badge in [69,70,71,72,73]:
			if self.has_badge(badge): discount -= discounts[badge]

		return discount
		

	@property
	@lazy
	def user_awards(self):

		return_value = list(AWARDS2.values())

		user_awards = g.db.query(AwardRelationship).filter_by(user_id=self.id)

		for val in return_value: val['owned'] = user_awards.filter_by(kind=val['kind'], submission_id=None, comment_id=None).count()

		return return_value

	@property
	def referral_count(self):
		return len(self.referrals)

	def is_blocking(self, target):
		return g.db.query(UserBlock).filter_by(user_id=self.id, target_id=target.id).one_or_none()

	@property
	@lazy
	def paid_dues(self):
		return not self.shadowbanned and not (self.is_banned and not self.unban_utc) and (self.admin_level or self.club_allowed or (self.club_allowed != False and self.truecoins > dues))

	@lazy
	def any_block_exists(self, other):

		return g.db.query(UserBlock).filter(
			or_(and_(UserBlock.user_id == self.id, UserBlock.target_id == other.id), and_(
				UserBlock.user_id == other.id, UserBlock.target_id == self.id))).first()

	def validate_2fa(self, token):

		x = pyotp.TOTP(self.mfa_secret)
		return x.verify(token, valid_window=1)

	@property
	@lazy
	def age(self):
		return int(time.time()) - self.created_utc

	@property
	@lazy
	def ban_reason_link(self):
		if self.ban_reason:
			if self.ban_reason.startswith("/post/"): return self.ban_reason.split(None, 1)[0]
			if self.ban_reason.startswith("/comment/"): return self.ban_reason.split(None, 1)[0] + "?context=8#context"

	@property
	@lazy
	def alts_unique(self):
		alts = []
		for u in self.alts:
			if u not in alts: alts.append(u)
		return alts

	@property
	@lazy
	def alts_patron(self):
		for u in self.alts_unique:
			if u.patron: return True
		return False

	@cache.memoize(timeout=86400)
	def userpagelisting(self, site=None, v=None, page=1, sort="new", t="all"):

		if self.shadowbanned and not (v and (v.admin_level > 1 or v.id == self.id)): return []

		posts = g.db.query(Submission.id).filter_by(author_id=self.id, is_pinned=False)

		if not (v and (v.admin_level > 1 or v.id == self.id)):
			posts = posts.filter_by(deleted_utc=0, is_banned=False, private=False, ghost=False)

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
		posts = posts.filter(Submission.created_utc >= cutoff)

		if sort == "new":
			posts = posts.order_by(Submission.created_utc.desc())
		elif sort == "old":
			posts = posts.order_by(Submission.created_utc)
		elif sort == "controversial":
			posts = posts.order_by((Submission.upvotes+1)/(Submission.downvotes+1) + (Submission.downvotes+1)/(Submission.upvotes+1), Submission.downvotes.desc())
		elif sort == "top":
			posts = posts.order_by(Submission.downvotes - Submission.upvotes)
		elif sort == "bottom":
			posts = posts.order_by(Submission.upvotes - Submission.downvotes)
		elif sort == "comments":
			posts = posts.order_by(Submission.comment_count.desc())

		posts = posts.offset(25 * (page - 1)).limit(26).all()

		return [x[0] for x in posts]

	@property
	@lazy
	def follow_count(self):
		return g.db.query(Follow).filter_by(user_id=self.id).count()

	@property
	@lazy
	def bio_html_eager(self):
		if self.bio_html == None: return ''
		return self.bio_html.replace('data-src', 'src').replace('src="/assets/images/loading.webp"', '')

	@property
	@lazy
	def fullname(self):
		return f"t1_{self.id}"

	@property
	@lazy
	def banned_by(self):
		if not self.is_suspended: return None
		return g.db.query(User).filter_by(id=self.is_banned).one_or_none()

	def has_badge(self, badge_id):
		return g.db.query(Badge).filter_by(user_id=self.id, badge_id=badge_id).one_or_none()

	def hash_password(self, password):
		return generate_password_hash(
			password, method='pbkdf2:sha512', salt_length=8)

	def verifyPass(self, password):
		return check_password_hash(self.passhash, password)

	@property
	@lazy
	def formkey(self):

		msg = f"{session['session_id']}+{self.id}+{self.login_nonce}"

		return generate_hash(msg)

	def validate_formkey(self, formkey):

		return validate_hash(f"{session['session_id']}+{self.id}+{self.login_nonce}", formkey)

	@property
	@lazy
	def url(self):
		return f"/@{self.username}"

	def __repr__(self):
		return f"<User(id={self.id})>"

	@property
	@lazy
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
	def received_awards(self):

		awards = {}

		posts_idlist = [x[0] for x in g.db.query(Submission.id).filter_by(author_id=self.id).all()]
		comments_idlist = [x[0] for x in g.db.query(Comment.id).filter_by(author_id=self.id).all()]

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
	def modaction_num(self):
		if self.admin_level < 2: return 0
		return g.db.query(ModAction).filter_by(user_id=self.id).count()

	@property
	@lazy
	def notifications_count(self):
		notifs = g.db.query(Notification.user_id).join(Comment).filter(Notification.user_id == self.id, Notification.read == False, Comment.is_banned == False, Comment.deleted_utc == 0)
		
		if not self.shadowbanned and self.admin_level < 3:
			notifs = notifs.join(User, User.id == Comment.author_id).filter(User.shadowbanned == None)
		
		return notifs.count()

	@property
	@lazy
	def post_notifications_count(self):
		return g.db.query(Notification).join(Comment).filter(Notification.user_id == self.id, Notification.read == False, Comment.author_id == AUTOJANNY_ID).count()

	@property
	@lazy
	def reddit_notifications_count(self):
		return g.db.query(Notification).join(Comment).filter(Notification.user_id == self.id, Notification.read == False, Comment.is_banned == False, Comment.deleted_utc == 0, Comment.body_html.like('%<p>New site mention: <a href="https://old.reddit.com/r/%'), Comment.parent_submission == None, Comment.author_id == NOTIFICATIONS_ID).count()

	@property
	@lazy
	def normal_count(self):
		return self.notifications_count - self.post_notifications_count - self.reddit_notifications_count

	@property
	@lazy
	def do_posts(self):
		return self.post_notifications_count and self.notifications_count-self.reddit_notifications_count == self.post_notifications_count

	@property
	@lazy
	def do_reddit(self):
		return self.notifications_count == self.reddit_notifications_count

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
		).order_by(User.username).all()

		data = [x for x in data]
		output = []
		for x in data:
			user = x[0]
			user._is_manual = x[1].is_manual
			output.append(user)

		return output

	@property
	@lazy
	def moderated_subs(self):
		modded_subs = g.db.query(Mod.sub).filter_by(user_id=self.id).all()
		return modded_subs

	def has_follower(self, user):

		return g.db.query(Follow).filter_by(target_id=self.id, user_id=user.id).one_or_none()

	@property
	@lazy
	def banner_url(self):
		if self.bannerurl: return self.bannerurl
		else: return f"/assets/images/{SITE_NAME}/site_preview.webp?v=1015"

	@property
	@lazy
	def profile_url(self):
		if self.agendaposter: return f"{SITE_FULL}/assets/images/astolfo.webp?v=1"
		if self.profileurl: 
			if self.profileurl.startswith('/'): return SITE_FULL + self.profileurl
			return self.profileurl
		return f"{SITE_FULL}/assets/images/default-profile-pic.webp?v=1008"

	@lazy
	def json_popover(self, v):
		data = {'username': self.username,
				'url': self.url,
				'id': self.id,
				'profile_url': self.profile_url,
				'bannerurl': self.banner_url,
				'bio_html': self.bio_html_eager,
				'coins': self.coins,
				'post_count': 0 if self.shadowbanned and not (v and (v.shadowbanned or v.admin_level > 2)) else self.post_count,
				'comment_count': 0 if self.shadowbanned and not (v and (v.shadowbanned or v.admin_level > 2)) else self.comment_count,
				'badges': [x.path for x in self.badges],
				}

		return data

	@property
	@lazy
	def json_raw(self):
		data = {'username': self.username,
				'url': self.url,
				'is_banned': bool(self.is_banned),
				'created_utc': self.created_utc,
				'id': self.id,
				'is_private': self.is_private,
				'profile_url': self.profile_url,
				'bannerurl': self.banner_url,
				'bio': self.bio,
				'bio_html': self.bio_html_eager,
				'flair': self.customtitle
				}

		return data

	@property
	@lazy
	def json_core(self):

		now = int(time.time())
		if self.is_suspended:
			return {'username': self.username,
					'url': self.url,
					'is_banned': True,
					'is_permanent_ban': not bool(self.unban_utc),
					'ban_reason': self.ban_reason,
					'id': self.id
					}
		return self.json_raw

	@property
	@lazy
	def json(self):
		data = self.json_core

		data["badges"] = [x.json for x in self.badges]
		data['coins'] = self.coins
		data['post_count'] = self.post_count
		data['comment_count'] = self.comment_count

		return data


	def ban(self, admin=None, reason=None, days=0):
		if days:
			self.unban_utc = int(time.time()) + (days * 86400)
			g.db.add(self)
		elif self.discord_id: remove_user(self)

		self.is_banned = admin.id if admin else AUTOJANNY_ID
		if reason: self.ban_reason = reason



	@property
	def is_suspended(self):
		return (self.is_banned and (self.unban_utc == 0 or self.unban_utc > time.time()))


	@property
	@lazy
	def applications(self):
		return g.db.query(OauthApp).filter_by(author_id=self.id).order_by(OauthApp.id)

	@property
	@lazy
	def created_datetime(self):
		return str(time.strftime("%d/%B/%Y %H:%M:%S UTC", time.gmtime(self.created_utc)))

	@lazy
	def subscribed_idlist(self, page=1):
		posts = g.db.query(Subscription.submission_id).filter_by(user_id=self.id).all()
		return [x[0] for x in posts]

	@property
	@lazy
	def userblocks(self):
		return [x[0] for x in g.db.query(UserBlock.target_id).filter_by(user_id=self.id).all()] + [x[0] for x in g.db.query(UserBlock.user_id).filter_by(target_id=self.id).all()]

	@lazy
	def saved_idlist(self, page=1):

		saved = [x[0] for x in g.db.query(SaveRelationship.submission_id).filter_by(user_id=self.id).all()]
		posts = g.db.query(Submission.id).filter(Submission.id.in_(saved), Submission.is_banned == False, Submission.deleted_utc == 0)

		if self.admin_level < 2:
			posts = posts.filter(Submission.author_id.notin_(self.userblocks))

		return [x[0] for x in posts.order_by(Submission.created_utc.desc()).offset(25 * (page - 1)).all()]

	@lazy
	def saved_comment_idlist(self, page=1):

		saved = [x[0] for x in g.db.query(CommentSaveRelationship.comment_id).filter_by(user_id=self.id).all()]
		comments = g.db.query(Comment.id).filter(Comment.id.in_(saved), Comment.is_banned == False, Comment.deleted_utc == 0)

		if self.admin_level < 2:
			comments = comments.filter(Comment.author_id.notin_(self.userblocks))

		return [x[0] for x in comments.order_by(Comment.created_utc.desc()).offset(25 * (page - 1)).all()]

	@property
	@lazy
	def saved_count(self):
		return len(self.saved_idlist())

	@property
	@lazy
	def saved_comment_count(self):
		return len(self.saved_comment_idlist())

	@property
	@lazy
	def filter_words(self):
		l = [i.strip() for i in self.custom_filter_list.split('\n')] if self.custom_filter_list else []
		l = [i for i in l if i]
		return l