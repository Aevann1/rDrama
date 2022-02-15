from sqlalchemy import *
from files.__main__ import Base

class BannedDomain(Base):

	__tablename__ = "banneddomains"
	domain = Column(String, primary_key=True)
	reason = Column(String)