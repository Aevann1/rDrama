from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base, app
from os import environ
from files.helpers.lazy import lazy
from files.helpers.const import *
from datetime import datetime
from json import loads
import time

class BadgeDef(Base):
	__tablename__ = "badge_defs"

	id = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(String)
	description = Column(String)

	def __repr__(self):
		return f"<BadgeDef(id={self.id})>"


class Badge(Base):

	__tablename__ = "badges"

	user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
	badge_id = Column(Integer,  ForeignKey('badge_defs.id'), primary_key=True)
	description = Column(String)
	url = Column(String)
	created_utc = Column(Integer)

	user = relationship("User", back_populates="badges")
	badge = relationship("BadgeDef", primaryjoin="foreign(Badge.badge_id) == remote(BadgeDef.id)")

	def __init__(self, *args, **kwargs):
		if "created_utc" not in kwargs:
			kwargs["created_utc"] = int(time.time())
		super().__init__(*args, **kwargs)

	def __repr__(self):
		return f"<Badge(user_id={self.user_id}, badge_id={self.badge_id})>"

	@property
	@lazy
	def text(self):
		if self.name == "Chud":
			ti = self.user.agendaposter
			if ti: text = self.badge.description + " until " + datetime.utcfromtimestamp(ti).strftime('%Y-%m-%d %H:%M:%S')
			else: text = self.badge.description + " permanently"
		elif self.badge_id in {94,95,96,97,98,109}:
			if self.badge_id == 94: ti = self.user.progressivestack
			elif self.badge_id == 95: ti = self.user.bird
			elif self.badge_id == 96: ti = self.user.flairchanged
			elif self.badge_id == 97: ti = self.user.longpost
			elif self.badge_id == 98: ti = self.user.marseyawarded
			elif self.badge_id == 109: ti = self.user.rehab
			text = self.badge.description + " until " + datetime.utcfromtimestamp(ti).strftime('%Y-%m-%d %H:%M:%S')
		elif self.description: text = self.description
		elif self.badge.description: text = self.badge.description
		else: return self.name
		return f'{self.name} - {text}'

	@property
	@lazy
	def name(self):
		return self.badge.name

	@property
	@lazy
	def path(self):
		return f"/i/badges/{self.badge_id}.webp"

	@property
	@lazy
	def json(self):
		return {'text': self.text,
				'name': self.name,
				'url': self.url,
				'icon_url':self.path
				}
