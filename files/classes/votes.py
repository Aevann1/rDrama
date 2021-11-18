from flask import *
from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from files.helpers.lazy import lazy

class Vote(Base):

	__tablename__ = "votes"

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey("users.id"))
	vote_type = Column(Integer)
	submission_id = Column(Integer, ForeignKey("submissions.id"))
	app_id = Column(Integer, ForeignKey("oauth_apps.id"))

	user = relationship("User", lazy="subquery", viewonly=True)
	post = relationship("Submission", lazy="subquery", viewonly=True)

	def __init__(self, *args, **kwargs):

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


class CommentVote(Base):

	__tablename__ = "commentvotes"

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey("users.id"))
	vote_type = Column(Integer)
	comment_id = Column(Integer, ForeignKey("comments.id"))
	app_id = Column(Integer, ForeignKey("oauth_apps.id"))

	user = relationship("User", lazy="subquery", viewonly=True)
	comment = relationship("Comment", lazy="subquery", viewonly=True)

	def __init__(self, *args, **kwargs):

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