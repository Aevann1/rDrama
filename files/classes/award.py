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
			"title": "1-Day Ban",
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
			"price": 500
		},
		"fireflies": {
			"kind": "fireflies",
			"title": "Fireflies",
			"description": "Puts stars on the post.",
			"icon": "fas fa-sparkles",
			"color": "text-warning",
			"price": 500
		},
		"grass": {
			"kind": "grass",
			"title": "Grass",
			"description": "Ban the author permanently (must provide a timestamped picture of them touching grass to the admins to get unbanned)",
			"icon": "fas fa-seedling",
			"color": "text-success",
			"price": 10000
		},
		"train": {
			"kind": "train",
			"title": "Train",
			"description": "Summons a train on the post.",
			"icon": "fas fa-train",
			"color": "text-pink",
			"price": 500
		},
		"pin": {
			"kind": "pin",
			"title": "1-Hour Pin",
			"description": "Pins the post.",
			"icon": "fas fa-thumbtack",
			"color": "text-warning",
			"price": 750
		},
	}
else:
	AWARDS = {
		"shit": {
			"kind": "shit",
			"title": "Shit",
			"description": "Makes flies swarm a post.",
			"icon": "fas fa-poop",
			"color": "text-black-50",
			"price": 500
		},
		"fireflies": {
			"kind": "fireflies",
			"title": "Fireflies",
			"description": "Puts stars on the post.",
			"icon": "fas fa-sparkles",
			"color": "text-warning",
			"price": 500
		},
		"train": {
			"kind": "train",
			"title": "Train",
			"description": "Summons a train on the post.",
			"icon": "fas fa-train",
			"color": "text-pink",
			"price": 500
		},
		"pin": {
			"kind": "pin",
			"title": "1-Hour Pin",
			"description": "Pins the post.",
			"icon": "fas fa-thumbtack",
			"color": "text-warning",
			"price": 750
		},
	}


class AwardRelationship(Base):

	__tablename__ = "award_relationships"

	id = Column(Integer, primary_key=True)

	user_id = Column(Integer, ForeignKey("users.id"))
	submission_id = Column(Integer, ForeignKey("submissions.id"))
	comment_id = Column(Integer, ForeignKey("comments.id"))
	kind = Column(String)

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
