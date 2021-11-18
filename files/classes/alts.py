from sqlalchemy import *
from files.__main__ import Base


class Alt(Base):
	__tablename__ = "alts"

	id = Column(Integer, primary_key=True)
	user1 = Column(Integer, ForeignKey("users.id"))
	user2 = Column(Integer, ForeignKey("users.id"))
	is_manual = Column(Boolean, default=False)

	def __repr__(self):

		return f"<Alt(id={self.id})>"
