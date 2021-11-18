from sqlalchemy import *
from files.__main__ import Base

class BannedDomain(Base):

	__tablename__ = "banneddomains"
	id = Column(Integer, primary_key=True)
	domain = Column(String)
	reason = Column(String)