from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base

class Sub(Base):

	__tablename__ = "subs"
	name = Column(String, primary_key=True)
	sidebar = Column(String)
	sidebar_html = Column(String)

	def __repr__(self):
		return f"<Sub(name={self.name})>"