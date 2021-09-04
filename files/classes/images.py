from sqlalchemy import *
from files.__main__ import Base

class Image(Base):
	__tablename__ = "images"
	id = Column(BigInteger, primary_key=True)
	state = Column(String(8))
	number = Column(Integer)
	text = Column(String(64))
	deletehash = Column(String(64))


class BadPic(Base):

	#Class for tracking fuzzy hashes of banned csam images

	__tablename__="badpics"
	id = Column(BigInteger, primary_key=True)
	description=Column(String(255))
	phash=Column(String(64))
	ban_reason=Column(String(64))
	ban_time=Column(Integer)

	