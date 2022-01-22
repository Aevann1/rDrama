from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
import time
from files.helpers.lazy import lazy
from os import environ
from copy import deepcopy
from files.helpers.const import *

class ModAction(Base):
	__tablename__ = "modactions"
	id = Column(BigInteger, primary_key=True)

	user_id = Column(Integer, ForeignKey("users.id"))
	kind = Column(String)
	target_user_id = Column(Integer, ForeignKey("users.id"), default=0)
	target_submission_id = Column(Integer, ForeignKey("submissions.id"), default=0)
	target_comment_id = Column(Integer, ForeignKey("comments.id"), default=0)
	_note=Column(String)
	created_utc = Column(Integer, default=0)

	user = relationship("User", primaryjoin="User.id==ModAction.user_id", viewonly=True)
	target_user = relationship("User", primaryjoin="User.id==ModAction.target_user_id", viewonly=True)
	target_post = relationship("Submission", viewonly=True)

	def __init__(self, *args, **kwargs):
		if "created_utc" not in kwargs: kwargs["created_utc"] = int(time.time())
		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<ModAction(id={self.id})>"

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
	def note(self):

		if self.kind=="ban_user":
			if self.target_post: return f'for <a href="{self.target_post.permalink}">post</a>'
			elif self.target_comment_id: return f'for <a href="/comment/{self.target_comment_id}">comment</a>'
			else: return self._note
		else:
			return self._note or ""

	@note.setter
	def note(self, x):
		self._note=x

	@property
	@lazy
	def string(self):

		output =  ACTIONTYPES[self.kind]["str"].format(self=self)

		if self.note: output += f" <i>({self.note})</i>"

		return output

	@property
	@lazy
	def target_link(self):
		if self.target_user: return f'<a href="{self.target_user.url}">{self.target_user.username}</a>'
		elif self.target_post:
			if self.target_post.club: return f'<a href="{self.target_post.permalink}">{CC} ONLY</a>'
			return f'<a href="{self.target_post.permalink}">{self.target_post.title.replace("<","")}</a>'
		elif self.target_comment_id: return f'<a href="/comment/{self.target_comment_id}?context=9#context">comment</a>'

	@property
	@lazy
	def icon(self):
		return ACTIONTYPES[self.kind]['icon']

	@property
	@lazy
	def color(self):
		return ACTIONTYPES[self.kind]['color']

	@property
	@lazy
	def permalink(self):
		return f"/log/{self.id}"	

ACTIONTYPES={
	"grant_awards": {
		"str": "granted awards to {self.target_link}",
		"icon": "fa-user",
		"color": "bg-primary",
	},
	"check": {
		"str": "gave {self.target_link} a checkmark",
		"icon": "fa-user",
		"color": "bg-success",
	},
	"uncheck": {
		"str": "removed checkmark from {self.target_link}",
		"icon": "fa-user-slash",
		"color": "bg-danger",
	},
	"ban_domain": {
		"str": "banned a domain",
		"icon": "fa-globe",
		"color": "bg-danger",
	},
	"unban_domain": {
		"str": "unbanned a domain",
		"icon": "fa-globe",
		"color": "bg-success",
	},
	"approve_app": {
		"str": "approved an application by {self.target_link}",
		"icon": "fa-robot",
		"color": "bg-success",
	},
	"revoke_app": {
		"str": "revoked an application by {self.target_link}",
		"icon": "fa-robot",
		"color": "bg-danger",
	},
	"reject_app": {
		"str": "rejected an application request by {self.target_link}",
		"icon": "fa-robot",
		"color": "bg-danger",
	},
	"change_rules": {
		"str": "changed the <a href='/rules'>rules</a>",
		"icon": "fa-balance-scale",
		"color": "bg-primary",
	},
	"change_sidebar": {
		"str": "changed the sidebar",
		"icon": "fa-columns",
		"color": "bg-primary",
	},
	"disable_signups": {
		"str": "disabled signups",
		"icon": "fa-user-slash",
		"color": "bg-danger",
	},
	"enable_signups": {
		"str": "enabled signups",
		"icon": "fa-user",
		"color": "bg-success",
	},
	"disable_under_attack": {
		"str": "disabled under attack mode",
		"icon": "fa-shield",
		"color": "bg-danger",
	},
	"enable_under_attack": {
		"str": "enabled under attack mode",
		"icon": "fa-shield",
		"color": "bg-success",
	},
	"ban_user":{
		"str":'banned user {self.target_link}',
		"icon":"fa-user-slash",
		"color": "bg-danger",
	},
	"unban_user":{
		"str":'unbanned user {self.target_link}',
		"icon": "fa-user-slash",
		"color": "bg-success",
	},
	"nuke_user":{
		"str":'removed all content of {self.target_link}',
		"icon":"fa-user-slash",
		"color": "bg-danger",
	},
	"unnuke_user":{
		"str":'approved all content of {self.target_link}',
		"icon": "fa-user-slash",
		"color": "bg-success",
	},
	"shadowban": {
		"str": 'shadowbanned {self.target_link}',
		"icon": "fa-user-slash",
		"color": "bg-danger",
	},
	"unshadowban": {
		"str": 'unshadowbanned {self.target_link}',
		"icon": "fa-user-slash",
		"color": "bg-success",
	},
	"agendaposter": {
		"str": "set agendaposter theme on {self.target_link}",
		"icon": "fa-user-slash",
		"color": "bg-danger",
	},
	"unagendaposter": {
		"str": "removed agendaposter theme from {self.target_link}",
		"icon": "fa-user-slash",
		"color": "bg-success",
	},
	"set_flair_locked":{
		"str":"set {self.target_link}'s flair (locked)",
		"icon": "fa-user-slash",
		"color": "bg-primary",
	},
	"set_flair_notlocked":{
		"str":"set {self.target_link}'s flair (not locked)",
		"icon": "fa-user-slash",
		"color": "bg-primary",
	},
	"pin_comment":{
		"str":'pinned a {self.target_link}',
		"icon":"fa-thumbtack fa-rotate--45",
		"color": "bg-success",
	},
	"unpin_comment":{
		"str":'un-pinned a {self.target_link}',
		"icon":"fa-thumbtack fa-rotate--45",
		"color": "bg-danger",
	},
	"pin_post":{
		"str":'pinned post {self.target_link}',
		"icon":"fa-thumbtack fa-rotate--45",
		"color": "bg-success",
	},
	"unpin_post":{
		"str":'un-pinned post {self.target_link}',
		"icon":"fa-thumbtack fa-rotate--45",
		"color": "bg-danger",
	},
	"set_nsfw":{
		"str":'set nsfw on post {self.target_link}',
		"icon":"fa-eye-evil",
		"color": "bg-danger",
	},
	"unset_nsfw":{
		"str":'un-set nsfw on post {self.target_link}',
		"icon":"fa-eye-evil",
		"color": "bg-success",
	},
	"ban_post":{
		"str": 'removed post {self.target_link}',
		"icon":"fa-feather-alt",
		"color": "bg-danger",
	},
	"unban_post":{
		"str": 'reinstated post {self.target_link}',
		"icon":"fa-feather-alt",
		"color": "bg-success",
	},
	"ban_comment":{
		"str": 'removed {self.target_link}',
		"icon":"fa-comment",
		"color": "bg-danger",
	},
	"unban_comment":{
		"str": 'reinstated {self.target_link}',
		"icon":"fa-comment",
		"color": "bg-success",
	},
}

ACTIONTYPES2 = deepcopy(ACTIONTYPES)
ACTIONTYPES2.pop("shadowban")
ACTIONTYPES2.pop("unshadowban")