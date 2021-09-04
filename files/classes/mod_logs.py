from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from .mix_ins import *
import time

class ModAction(Base, Stndrd, Age_times):
	__tablename__ = "modactions"
	id = Column(BigInteger, primary_key=True)

	user_id = Column(Integer, ForeignKey("users.id"))
	kind = Column(String(32))
	target_user_id = Column(Integer, ForeignKey("users.id"), default=0)
	target_submission_id = Column(Integer, ForeignKey("submissions.id"), default=0)
	target_comment_id = Column(Integer, ForeignKey("comments.id"), default=0)
	_note=Column(String(256), default=None)
	created_utc = Column(Integer, default=0)


	user = relationship("User", lazy="joined", primaryjoin="User.id==ModAction.user_id")
	target_user = relationship("User", lazy="joined", primaryjoin="User.id==ModAction.target_user_id")
	target_post = relationship("Submission", lazy="joined")
	target_comment = relationship("Comment", lazy="joined")


	def __init__(self, *args, **kwargs):
		if "created_utc" not in kwargs:
			kwargs["created_utc"] = int(time.time())

		if "note" in kwargs:
			kwargs["_note"]=kwargs["note"]

		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<ModAction(id={self.id})>"

	@property
	def actiontype(self):
		return ACTIONTYPES[self.kind]

	@property
	def note(self):

		if self.kind=="exile_user":
			if self.target_post:
				return f'for <a href="{self.target_post.permalink}">post</a>'
			elif self.target_comment:
				return f'for <a href="{self.target_comment.permalink}">comment</a>'
			else: return self._note
		else:
			return self._note or ""

	@note.setter
	def note(self, x):
		self._note=x

	@property
	def string(self):

		output =  self.actiontype["str"].format(self=self)

		if self.note:
			output += f" <i>({self.note})</i>"

		return output

	@property
	def target_link(self):
		if self.target_user:
			return f'<a href="{self.target_user.url}">{self.target_user.username}</a>'
		elif self.target_post:
			return f'<a href="{self.target_post.permalink}">{self.target_post.title}</a>'
		elif self.target_comment:
			return f'<a href="{self.target_comment.permalink}">comment</a>'

		else:
			return ''

	@property
	def json(self):
		data={
			"id":self.id,
			"kind": self.kind,
			"created_utc": self.created_utc,
			"mod": self.user.username,
		}

		if self.target_user_id:
			data["target_user_id"]=self.target_user.id
			data["target_user"]=self.target_user.username

		if self.target_comment_id:
			data["target_comment_id"]=self.target_comment.id

		if self.target_submission_id:
			data["target_submission_id"]=self.target_submission.id

		if self._note:
			data["note"]=self._note

		return data
	



	@property
	def icon(self):
		return self.actiontype['icon']

	@property
	def color(self):
		return self.actiontype['color']

	@property
	def permalink(self):
		return f"/log/{self.id}"
	@property
	def title_text(self):
		return f"@{self.user.username} {self.actiontype['title'].format(self=self)}"
	
	


ACTIONTYPES={
	"kick_post":{
		"str":'kicked post {self.target_link}',
		"icon":"fa-sign-out fa-flip-horizontal",
		"color": "bg-danger",
		"title": 'kicked post {self.target_post.title}'
	},
	"approve_post":{
		"str":'approved post {self.target_link}',
		"icon":"fa-check",
		"color": "bg-success",
		"title": 'approved post {self.target_post.title}'
	},	
	"yank_post":{
		"str":'yanked post {self.target_link}',
		"icon":"fa-hand-lizard",
		"color": "bg-muted",
		"title": 'yanked post {self.target_post.title}'
	},
	"exile_user":{
		"str":'banned user {self.target_link}',
		"icon":"fa-user-slash",
		"color": "bg-danger",
		"title": 'banned user {self.target_user.username}'
	},
	"unexile_user":{
		"str":'unbanned user {self.target_link}',
		"icon": "fa-user-slash",
		"color": "bg-muted",
		"title": 'unbanned user {self.target_user.username}'
	},
	"nuke_user":{
		"str":'removed all content of {self.target_link}',
		"icon":"fa-user-slash",
		"color": "bg-danger",
		"title": 'removed all content of {self.target_user.username}'
	},
	"unnuke_user":{
		"str":'approved all content of {self.target_link}',
		"icon": "fa-user-slash",
		"color": "bg-muted",
		"title": 'approved all content of {self.target_user.username}'
	},
	"shadowban": {
		"str": 'shadowbanned {self.target_link}',
		"icon": "fa-user-slash",
		"color": "bg-danger",
		"title": 'shadowbanned {self.target_user.username}'
	},
	"unshadowban": {
		"str": 'unshadowbanned {self.target_link}',
		"icon": "fa-user-slash",
		"color": "bg-muted",
		"title": 'unshadowbanned {self.target_user.username}'
	},
	"agendaposter": {
		"str": "set agendaposter theme on {self.target_link}",
		"icon": "fa-user-slash",
		"color": "bg-muted",
		"title": "set agendaposter theme on {self.target_link}"
	},
	"unagendaposter": {
		"str": "removed agendaposter theme from {self.target_link}",
		"icon": "fa-user-slash",
		"color": "bg-muted",
		"title": "removed agendaposter theme from {self.target_link}"
	},
	"set_flair_locked":{
		"str":"set {self.target_link}'s flair (locked)",
		"icon": "fa-user-slash",
		"color": "bg-muted",
		"title": "set {self.target_link}'s flair (locked)"
	},
	"set_flair_notlocked":{
		"str":"set {self.target_link}'s flair (not locked)",
		"icon": "fa-user-slash",
		"color": "bg-muted",
		"title": "set {self.target_link}'s flair (not locked)"
	},
	"contrib_user":{
		"str":'added contributor {self.target_link}',
		"icon": "fa-user-check",
		"color": "bg-info",
		"title": 'added contributor {self.target_user.username}'
	},
	"uncontrib_user":{
		"str":'removed contributor {self.target_link}',
		"icon": "fa-user-check",
		"color": "bg-muted",
		"title": 'removed user {self.target_user.username}'
	},
	"herald_comment":{
		"str":'heralded their {self.target_link}',
		"icon": "fa-crown",
		"color": "bg-warning",
		"title": 'heralded their comment'
	},
	"herald_post":{
		"str":'heralded their post {self.target_link}',
		"icon": "fa-crown",
		"color": "bg-warning",
		"title": 'heralded their post {self.target_post.title}'
	},
	"unherald_comment":{
		"str":'un-heralded their {self.target_link}',
		"icon": "fa-crown",
		"color": "bg-muted",
		"title": 'un-heralded their comment'
		},
	"unherald_post":{
		"str":'un-heralded their post {self.target_link}',
		"icon": "fa-crown",
		"color": "bg-muted",
		"title": 'un-heralded their post {self.target_post.title}'
	},
	"pin_comment":{
		"str":'pinned a {self.target_link}',
		"icon":"fa-thumbtack fa-rotate--45",
		"color": "bg-info",
		"title": 'pinned a comment'
	},
	"unpin_comment":{
		"str":'un-pinned a {self.target_link}',
		"icon":"fa-thumbtack fa-rotate--45",
		"color": "bg-muted",
		"title": 'un-pinned a comment'
	},
	"pin_post":{
		"str":'pinned post {self.target_link}',
		"icon":"fa-thumbtack fa-rotate--45",
		"color": "bg-success",
		"title": 'pinned post {self.target_post.title}'
	},
	"unpin_post":{
		"str":'un-pinned post {self.target_link}',
		"icon":"fa-thumbtack fa-rotate--45",
		"color": "bg-muted",
		"title": 'un-pinned post {self.target_post.title}'
	},
	"invite_mod":{
		"str":'invited admin {self.target_link}',
		"icon":"fa-user-crown",
		"color": "bg-info",
		"title": 'invited admin @{self.target_user.username}'
	},
	"uninvite_mod":{
		"str":'rescinded admin invitation to {self.target_link}',
		"icon":"fa-user-crown",
		"color": "bg-muted",
		"title": 'rescinded admin invitation to @{self.target_user.username}'
	},
	"accept_mod_invite":{
		"str":'accepted admin invitation',
		"icon":"fa-user-crown",
		"color": "bg-warning",
		"title": 'accepted admin invitation'
	},
	"remove_mod":{
		"str":'removed admin {self.target_link}',
		"icon":"fa-user-crown",
		"color": "bg-danger",
		"title": 'removed admin @{self.target_user.username}'
	},
	"dethrone_self":{
		"str":'stepped down as guildmaster',
		"icon":"fa-user-crown",
		"color": "bg-danger",
		"title": 'stepped down as guildmaster'
	},
	"add_mod":{
		"str":'added admin {self.target_link}',
		"icon":"fa-user-crown",
		"color": "bg-success",
		"title": 'added admin @{self.target_user.username}'
	},
	"update_settings":{
		"str":'updated setting',
		"icon":"fa-cog",
		"color": "bg-info",
		"title": 'updated settings'
	},
	"update_appearance":{
		"str":'updated appearance',
		"icon":"fa-palette",
		"color": "bg-info",
		"title": 'updated appearance'
	},
	"set_nsfw":{
		"str":'set nsfw on post {self.target_link}',
		"icon":"fa-eye-evil",
		"color": "bg-danger",
		"title": 'set nsfw on post {self.target_post.title}'
	},
	"unset_nsfw":{
		"str":'un-set nsfw on post {self.target_link}',
		"icon":"fa-eye-evil",
		"color": "bg-muted",
		"title": 'un-set nsfw on post {self.target_post.title}'
	},
	"set_nsfl":{
		"str":'set nsfl on post {self.target_link}',
		"icon":"fa-skull",
		"color": "bg-black",
		"title": 'set nsfl on post {self.target_post.title}'
	},
	"unset_nsfl":{
		"str":'un-set nsfl on post {self.target_link}',
		"icon":"fa-skull",
		"color": "bg-muted",
		"title": 'un-set nsfw on post {self.target_post.title}'
	},
	"ban_post":{
		"str": 'removed post {self.target_link}',
		"icon":"fa-feather-alt",
		"color": "bg-danger",
		"title": "removed post {self.target_post.title}"
	},
	"unban_post":{
		"str": 'reinstated post {self.target_link}',
		"icon":"fa-feather-alt",
		"color": "bg-muted",
		"title": "reinstated post {self.target_post.title}"
	},
	"ban_comment":{
		"str": 'removed {self.target_link}',
		"icon":"fa-comment",
		"color": "bg-danger",
		"title": "removed comment"
	},
	"unban_comment":{
		"str": 'reinstated {self.target_link}',
		"icon":"fa-comment",
		"color": "bg-muted",
		"title": "reinstated comment"
	},
	"change_perms":{
		"str": 'changed permissions on admin {self.target_link}',
		"icon":"fa-user-cog",
		"color": "bg-info",
		"title": "changed permissions on {self.target_user.username}"
	},
	"change_invite":{
		"str": 'changed  permissions on admin invitation to {self.target_link}',
		"icon":"fa-user-cog",
		"color": "bg-muted",
		"title": "changed permissions on invitation to {self.target_user.username}"
	},
	"create_guild":{
		"str": 'created +{self.board.name}',
		"icon": "fa-chess-rook",
		"color": "bg-primary",
		"title": "created +{self.board.name}"
	}
}