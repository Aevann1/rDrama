from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from files.helpers.lazy import lazy
import time

class SubmissionOption(Base):

	__tablename__ = "submission_options"

	id = Column(Integer, primary_key=True)
	submission_id = Column(Integer, ForeignKey("submissions.id"))
	body_html = Column(Text)
	exclusive = Column(Boolean)

	votes = relationship("SubmissionOptionVote")
	post = relationship("Submission", back_populates="options")

	def __repr__(self):
		return f"<SubmissionOption(id={self.id})>"

	@property
	@lazy
	def upvotes(self):
		return len(self.votes)

	@lazy
	def voted(self, v):
		return v.id in [x.user_id for x in self.votes]


class SubmissionOptionVote(Base):

	__tablename__ = "submission_option_votes"

	option_id = Column(Integer, ForeignKey("submission_options.id"), primary_key=True)
	user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
	created_utc = Column(Integer)
	submission_id = Column(Integer, ForeignKey("submissions.id"))

	user = relationship("User")
	option = relationship("SubmissionOption")

	def __init__(self, *args, **kwargs):
		if "created_utc" not in kwargs: kwargs["created_utc"] = int(time.time())
		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<SubmissionOptionVote(option_id={self.option_id}, user_id={self.user_id})>"

	@property
	def created_datetime(self):
		return str(time.strftime("%d/%B/%Y %H:%M:%S UTC", time.gmtime(self.created_utc)))



class CommentOption(Base):

	__tablename__ = "comment_options"

	id = Column(Integer, primary_key=True)
	comment_id = Column(Integer, ForeignKey("comments.id"))
	body_html = Column(Text)
	exclusive = Column(Boolean)

	votes = relationship("CommentOptionVote")
	post = relationship("Comment", back_populates="options")

	def __repr__(self):
		return f"<CommentOption(id={self.id})>"

	@property
	@lazy
	def upvotes(self):
		return len(self.votes)

	@lazy
	def voted(self, v):
		return v.id in [x.user_id for x in self.votes]


class CommentOptionVote(Base):

	__tablename__ = "comment_option_votes"

	option_id = Column(Integer, ForeignKey("comment_options.id"), primary_key=True)
	user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
	created_utc = Column(Integer)
	comment_id = Column(Integer, ForeignKey("comments.id"))

	user = relationship("User")
	option = relationship("CommentOption")

	def __init__(self, *args, **kwargs):
		if "created_utc" not in kwargs: kwargs["created_utc"] = int(time.time())
		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<CommentOptionVote(option_id={self.option_id}, user_id={self.user_id})>"

	@property
	def created_datetime(self):
		return str(time.strftime("%d/%B/%Y %H:%M:%S UTC", time.gmtime(self.created_utc)))