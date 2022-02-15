from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base


class SaveRelationship(Base):

	__tablename__="save_relationship"

	user_id=Column(Integer, ForeignKey("users.id"), primary_key=True)
	submission_id=Column(Integer, ForeignKey("submissions.id"), primary_key=True)



class CommentSaveRelationship(Base):

	__tablename__="comment_save_relationship"

	user_id=Column(Integer, ForeignKey("users.id"), primary_key=True)
	comment_id=Column(Integer, ForeignKey("comments.id"), primary_key=True)