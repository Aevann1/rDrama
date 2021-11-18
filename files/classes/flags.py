from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from files.helpers.lazy import lazy
import time

class Flag(Base):

	__tablename__ = "flags"

	id = Column(Integer, primary_key=True)
	post_id = Column(Integer, ForeignKey("submissions.id"))
	user_id = Column(Integer, ForeignKey("users.id"))
	reason = Column(String)
	
	user = relationship("User", primaryjoin = "Flag.user_id == User.id", uselist = False, viewonly=True)

	def __repr__(self):

		return f"<Flag(id={self.id})>"

	@property
	@lazy
	def created_date(self):
		return time.strftime("%d %B %Y", time.gmtime(self.created_utc))

	@property
	@lazy
	def created_datetime(self):
		return str(time.strftime("%d/%B/%Y %H:%M:%S UTC", time.gmtime(self.created_utc)))


class CommentFlag(Base):

	__tablename__ = "commentflags"

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey("users.id"))
	comment_id = Column(Integer, ForeignKey("comments.id"))
	reason = Column(String)
	
	user = relationship("User", primaryjoin = "CommentFlag.user_id == User.id", uselist = False, viewonly=True)

	def __repr__(self):

		return f"<CommentFlag(id={self.id})>"

	@property
	@lazy
	def created_date(self):
		return time.strftime("%d %B %Y", time.gmtime(self.created_utc))

	@property
	@lazy
	def created_datetime(self):
		return str(time.strftime("%d/%B/%Y %H:%M:%S UTC", time.gmtime(self.created_utc)))