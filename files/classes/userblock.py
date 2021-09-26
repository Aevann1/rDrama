from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from files.helpers.lazy import lazy
import time

class UserBlock(Base):

	__tablename__ = "userblocks"
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey("users.id"))
	target_id = Column(Integer, ForeignKey("users.id"))

	user = relationship("User", primaryjoin="User.id==UserBlock.user_id", viewonly=True)
	target = relationship("User", primaryjoin="User.id==UserBlock.target_id", viewonly=True)

	def __repr__(self):

		return f"<UserBlock(user={user.username}, target={target.username})>"

	@property
	@lazy
	def created_date(self):
		return time.strftime("%d %b %Y", time.gmtime(self.created_utc))