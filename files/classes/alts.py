from sqlalchemy import *
from files.__main__ import Base


class Alt(Base):
	__tablename__ = "alts"

	user1 = Column(Integer, ForeignKey("users.id"), primary_key=True)
	user2 = Column(Integer, ForeignKey("users.id"), primary_key=True)
	is_manual = Column(Boolean, default=False)

	def __repr__(self):

		return f"<Alt(id={self.id})>"
