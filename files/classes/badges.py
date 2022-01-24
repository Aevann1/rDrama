from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base, app
from os import environ
from files.helpers.lazy import lazy
from files.helpers.const import *
from datetime import datetime
from json import loads

class BadgeDef(Base):
	__tablename__ = "badge_defs"

	id = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(String)
	description = Column(String)

	def __repr__(self):
		return f"<BadgeDef(id={self.id})>"


class Badge(Base):

	__tablename__ = "badges"

	id = Column(Integer, primary_key=True)

	user_id = Column(Integer, ForeignKey('users.id'))
	badge_id = Column(Integer)
	description = Column(String)
	url = Column(String)
	user = relationship("User", viewonly=True)
	badge = relationship("BadgeDef", primaryjoin="foreign(Badge.badge_id) == remote(BadgeDef.id)", viewonly=True)

	def __repr__(self):
		return f"<Badge(user_id={self.user_id}, badge_id={self.badge_id})>"

	@property
	@lazy
	def text(self):
		if self.name == "Agendaposter":
			ti = self.user.agendaposter_expires_utc
			if ti: text = self.badge.description + " until " + datetime.utcfromtimestamp(ti).strftime('%Y-%m-%d %H:%M:%S')
			else: text = self.badge.description + " permanently"
		elif self.badge_id in (94,95,96,97,98):
			if self.badge_id == 94: ti = self.user.progressivestack
			elif self.badge_id == 95: ti = self.user.bird
			elif self.badge_id == 96: ti = self.user.flairchanged
			elif self.badge_id == 97: ti = self.user.longpost
			else: ti = self.user.marseyawarded
			text = self.badge.description + " until " + datetime.utcfromtimestamp(ti).strftime('%Y-%m-%d %H:%M:%S')
		elif self.description: text = self.description
		elif self.badge.description: text = self.badge.description
		else: return ''
		return f'{self.name} - {text}'

	@property
	@lazy
	def name(self):
		try: return self.badge.name
		except Exception as e:
			print(e)
			print(self.badge_id)
			return ""

	@property
	@lazy
	def path(self):
		return f"/static/assets/images/badges/{self.badge_id}.webp?a=1008"

	@property
	@lazy
	def json(self):
		return {'text': self.text,
				'name': self.name,
				'url': self.url,
				'icon_url':f"{SITE_FULL}{self.path}"
				}
