from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from os import environ
from files.helpers.lazy import lazy
from files.helpers.const import *

class AwardRelationship(Base):

	__tablename__ = "award_relationships"

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey("users.id"))
	submission_id = Column(Integer, ForeignKey("submissions.id"))
	comment_id = Column(Integer, ForeignKey("comments.id"))
	kind = Column(String)
	awarded_utc = Column(Integer)

	user = relationship("User", primaryjoin="AwardRelationship.user_id==User.id", back_populates="awards")
	post = relationship("Submission", primaryjoin="AwardRelationship.submission_id==Submission.id", back_populates="awards")
	comment = relationship("Comment", primaryjoin="AwardRelationship.comment_id==Comment.id", back_populates="awards")

	def __repr__(self):
		return f"<AwardRelationship(id={self.id})>"

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
