from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base

class UserBlock(Base):

	__tablename__ = "userblocks"
	user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
	target_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

	user = relationship("User", primaryjoin="User.id==UserBlock.user_id", back_populates="blocking")
	target = relationship("User", primaryjoin="User.id==UserBlock.target_id", back_populates="blocked")

	def __repr__(self):
		return f"<UserBlock(user={self.user_id}, target={self.target_id})>"