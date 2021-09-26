from sqlalchemy import *
from files.__main__ import Base

class BannedDomain(Base):

	__tablename__ = "banneddomains"
	id = Column(Integer, primary_key=True)
	domain = Column(String(255))
	reason = Column(String(255))


class BadLink(Base):

	__tablename__ = "badlinks"
	id = Column(Integer, primary_key=True)
	link = Column(String(512))
	reason = Column(String(255))
	autoban = Column(Boolean, default=False)