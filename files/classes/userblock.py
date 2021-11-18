from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base

class UserBlock(Base):

	__tablename__ = "userblocks"
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey("users.id"))
	target_id = Column(Integer, ForeignKey("users.id"))

	user = relationship("User", primaryjoin="User.id==UserBlock.user_id", viewonly=True)
	target = relationship("User", primaryjoin="User.id==UserBlock.target_id", viewonly=True)

	def __repr__(self):
		return f"<UserBlock(user={self.user_id}, target={self.target_id})>"