from flask import *
from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from files.helpers.lazy import lazy
import time

class Vote(Base):

	__tablename__ = "votes"

	submission_id = Column(Integer, ForeignKey("submissions.id"), primary_key=True)
	user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
	vote_type = Column(Integer)
	app_id = Column(Integer, ForeignKey("oauth_apps.id"))
	real = Column(Boolean, default=True)
	created_utc = Column(Integer)

	user = relationship("User", lazy="subquery")
	post = relationship("Submission", lazy="subquery")

	def __init__(self, *args, **kwargs):
		if "created_utc" not in kwargs: kwargs["created_utc"] = int(time.time())
		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<Vote(id={self.id})>"

	@property
	@lazy
	def json_core(self):
		data={
			"user_id": self.user_id,
			"submission_id":self.submission_id,
			"vote_type":self.vote_type
			}
		return data

	@property
	@lazy
	def json(self):
		data=self.json_core
		data["user"]=self.user.json_core
		data["post"]=self.post.json_core
	
		return data

	@property
	def created_datetime(self):
		return str(time.strftime("%d/%B/%Y %H:%M:%S UTC", time.gmtime(self.created_utc)))


class CommentVote(Base):

	__tablename__ = "commentvotes"

	comment_id = Column(Integer, ForeignKey("comments.id"), primary_key=True)
	user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
	vote_type = Column(Integer)
	app_id = Column(Integer, ForeignKey("oauth_apps.id"))
	real = Column(Boolean, default=True)
	created_utc = Column(Integer)

	user = relationship("User", lazy="subquery")
	comment = relationship("Comment", lazy="subquery")

	def __init__(self, *args, **kwargs):
		if "created_utc" not in kwargs: kwargs["created_utc"] = int(time.time())
		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<CommentVote(id={self.id})>"

	@property
	@lazy
	def json_core(self):
		data={
			"user_id": self.user_id,
			"comment_id":self.comment_id,
			"vote_type":self.vote_type
			}
		return data

	@property
	@lazy
	def json(self):
		data=self.json_core
		data["user"]=self.user.json_core
		data["comment"]=self.comment.json_core
	
		return data

	@property
	def created_datetime(self):
		return str(time.strftime("%d/%B/%Y %H:%M:%S UTC", time.gmtime(self.created_utc)))