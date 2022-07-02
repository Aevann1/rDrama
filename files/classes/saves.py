from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base


class SaveRelationship(Base):

	__tablename__="save_relationship"

	user_id=Column(Integer, ForeignKey("users.id"), primary_key=True)
	submission_id=Column(Integer, ForeignKey("submissions.id"), primary_key=True)

	def __repr__(self):
		return f"<SaveRelationship(user_id={self.user_id}, submission_id={self.submission_id})>"


class CommentSaveRelationship(Base):

	__tablename__="comment_save_relationship"

	user_id=Column(Integer, ForeignKey("users.id"), primary_key=True)
	comment_id=Column(Integer, ForeignKey("comments.id"), primary_key=True)

	def __repr__(self):
		return f"<CommentSaveRelationship(user_id={self.user_id}, comment_id={self.comment_id})>"