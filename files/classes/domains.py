from sqlalchemy import *
from files.__main__ import Base

class BannedDomain(Base):

	__tablename__ = "banneddomains"
	domain = Column(String, primary_key=True)
	reason = Column(String)

	def __repr__(self):
		return f"<BannedDomain(domain={self.domain})>"