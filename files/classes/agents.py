from sqlalchemy import *
from files.__main__ import Base

class Agent(Base):

	__tablename__ = "useragents"

	id = Column(Integer, primary_key=True)
	kwd = Column(String(64))
	reason = Column(String(256))
	banned_by = Column(Boolean, ForeignKey("users.id"), default=True)
	mock = Column(String(256))
	status_code = Column(Integer, default=418)
