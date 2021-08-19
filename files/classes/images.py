from sqlalchemy import *
from flask import g
from files.__main__ import Base
from os import environ

site = environ.get("DOMAIN").strip()
site_name = environ.get("SITE_NAME").strip()

class Image(Base):
	__tablename__ = "images"
	id = Column(BigInteger, primary_key=True)
	state = Column(String(8))
	number = Column(Integer)
	text = Column(String(64))
	deletehash = Column(String(64))
	

	@property
	def path(self): return f"/assets/images/{site_name}/cover.png"



def random_image():
	n=g.db.query(Image).count()
	return g.db.query(Image).order_by(Image.id.asc()).first()



class BadPic(Base):

	#Class for tracking fuzzy hashes of banned csam images

	__tablename__="badpics"
	id = Column(BigInteger, primary_key=True)
	description=Column(String(255))
	phash=Column(String(64))
	ban_reason=Column(String(64))
	ban_time=Column(Integer)

	