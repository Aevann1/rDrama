from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from os import environ
from files.helpers.lazy import lazy

site_name = environ.get("SITE_NAME").strip()

if site_name == "Drama":
	AWARDS = {
		"ban": {
			"kind": "ban",
			"title": "One-Day Ban",
			"description": "Bans the author for a day.",
			"icon": "fas fa-gavel",
			"color": "text-danger",
			"price": 5000
		},
		"shit": {
			"kind": "shit",
			"title": "Shit",
			"description": "Makes flies swarm a post.",
			"icon": "fas fa-poop",
			"color": "text-black-50",
			"price": 1000
		},
		"fireflies": {
			"kind": "fireflies",
			"title": "Fireflies",
			"description": "Puts stars on the post.",
			"icon": "fas fa-sparkles",
			"color": "text-warning",
			"price": 1000
		}
	}
else:
	AWARDS = {
		"shit": {
			"kind": "shit",
			"title": "Shit",
			"description": "Makes flies swarm a post.",
			"icon": "fas fa-poop",
			"color": "text-black-50",
			"price": 1000
		},
		"fireflies": {
			"kind": "fireflies",
			"title": "Fireflies",
			"description": "Puts stars on the post.",
			"icon": "fas fa-sparkles",
			"color": "text-warning",
			"price": 1000
		}
	}


class AwardRelationship(Base):

	__tablename__ = "award_relationships"

	id = Column(Integer, primary_key=True)

	user_id = Column(Integer, ForeignKey("users.id"))
	submission_id = Column(Integer, ForeignKey("submissions.id"))
	comment_id = Column(Integer, ForeignKey("comments.id"))
	kind = Column(String(20))

	user = relationship("User", primaryjoin="AwardRelationship.user_id==User.id", viewonly=True)

	post = relationship("Submission", primaryjoin="AwardRelationship.submission_id==Submission.id", viewonly=True)
	comment = relationship("Comment", primaryjoin="AwardRelationship.comment_id==Comment.id", viewonly=True)


	@property
	@lazy
	def type(self):
		return AWARDS[self.kind]

	@property
	@lazy
	def title(self):
		return self.type['title']

	@property
	@lazy
	def class_list(self):
		return self.type['icon']+' '+self.type['color']
