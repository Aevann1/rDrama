from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from files.helpers.lazy import *
from time import strftime, gmtime

class Mod(Base):

	__tablename__ = "mods"
	user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
	sub = Column(String, ForeignKey("subs.name"), primary_key=True)
	created_utc = Column(Integer)

	def __repr__(self):
		return f"<Mod(user_id={self.user_id}, sub={self.sub})>"

	@property
	@lazy
	def created_datetime(self):
		return str(strftime("%d/%B/%Y %H:%M:%S UTC", gmtime(self.created_utc)))