from sqlalchemy import *
from files.__main__ import Base

class Marsey(Base):
	__tablename__ = "marseys"

	name = Column(String, primary_key=True)
	author_id = Column(Integer, ForeignKey("users.id"))
	tags = Column(String)
	count = Column(Integer, default=0)

	def __repr__(self):
		return f"<Marsey(name={self.name})>"