from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base


class Subscription(Base):
	__tablename__ = "subscriptions"
	id = Column(BigInteger, primary_key=True)
	user_id = Column(BigInteger, ForeignKey("users.id"))
	submission_id = Column(BigInteger, default=0)
	
	user = relationship("User", uselist=False, viewonly=True)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<Subscription(id={self.id})>"


class Follow(Base):
	__tablename__ = "follows"
	id = Column(BigInteger, primary_key=True)
	user_id = Column(BigInteger, ForeignKey("users.id"))
	target_id = Column(BigInteger, ForeignKey("users.id"))

	user = relationship("User", uselist=False, primaryjoin="User.id==Follow.user_id", viewonly=True)
	target = relationship("User", primaryjoin="User.id==Follow.target_id", viewonly=True)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<Follow(id={self.id})>"