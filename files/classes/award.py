from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from os import environ

site_name = environ.get("SITE_NAME").strip()

if site_name == "Drama":
	AWARDS = {
		"ban": {
			"kind": "ban",
			"title": "One-Day Ban",
			"description": "Ban the author for a day.",
			"icon": "fas fa-gavel",
			"color": "text-danger"
		},
		"shit": {
			"kind": "shit",
			"title": "Shitpost",
			"description": "Let OP know how much their post sucks ass. Flies will swarm their idiotic post. (flies only work on posts lol!!)",
			"icon": "fas fa-poop",
			"color": "text-black-50"
		},
		"gold": {
			"kind": "gold",
			"title": "Gold",
			"description": "A positive award because we need a positive award. Puts annoying sparkles in the post.",
			"icon": "fas fa-sparkles",
			"color": "text-warning"
		}
	}
else:
	AWARDS = {
		"shit": {
			"kind": "shit",
			"title": "Shitpost",
			"description": "Let OP know how much their post sucks ass. Flies will swarm their idiotic post. (flies only work on posts lol!!)",
			"icon": "fas fa-poop",
			"color": "text-black-50"
		},
		"gold": {
			"kind": "gold",
			"title": "Gold",
			"description": "A positive award because we need a positive award. Puts annoying sparkles in the post.",
			"icon": "fas fa-sparkles",
			"color": "text-warning"
		}
	}


class AwardRelationship(Base):

	__tablename__ = "award_relationships"

	id = Column(Integer, primary_key=True)

	user_id = Column(Integer, ForeignKey("users.id"))
	submission_id = Column(Integer, ForeignKey("submissions.id"), default=None)
	comment_id = Column(Integer, ForeignKey("comments.id"), default=None)
	kind = Column(String(20))

	user = relationship("User", primaryjoin="AwardRelationship.user_id==User.id", lazy="joined")
	post = relationship(
		"Submission",
		primaryjoin="AwardRelationship.submission_id==Submission.id",
		lazy="joined"
	)
	comment = relationship(
		"Comment",
		primaryjoin="AwardRelationship.comment_id==Comment.id",
		lazy="joined"
	)

	@property
	def given(self):
		return bool(self.submission_id) or bool(self.comment_id)

	@property
	def type(self):
		return AWARDS[self.kind]

	@property
	def title(self):
		return self.type['title']

	@property
	def class_list(self):
		return self.type['icon']+' '+self.type['color']
