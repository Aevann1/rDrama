from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base

class Subscription(Base):
	__tablename__ = "subscriptions"
	user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
	submission_id = Column(Integer, ForeignKey("submissions.id"), primary_key=True)
	
	user = relationship("User", uselist=False)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<Subscription(id={self.id})>"