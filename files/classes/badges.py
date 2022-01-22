from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base, app
from os import environ
from files.helpers.lazy import lazy
from files.helpers.const import *
from datetime import datetime
from json import loads

class Badge(Base):

	__tablename__ = "badges"

	id = Column(Integer, primary_key=True)

	user_id = Column(Integer, ForeignKey('users.id'))
	badge_id = Column(Integer)
	description = Column(String)
	url = Column(String)
	user = relationship("User", viewonly=True)

	def __repr__(self):
		return f"<Badge(user_id={self.user_id}, badge_id={self.badge_id})>"

	@property
	@lazy
	def badge(self):
		with open("badges.json", 'r') as f:
			return loads(f.read().replace("'",'"'))[str(self.badge_id)]

	@property
	@lazy
	def text(self):
		if self.name == "Agendaposter":
			ti = self.user.agendaposter_expires_utc
			if ti: text = self.badge["description"] + " until " + datetime.utcfromtimestamp(ti).strftime('%Y-%m-%d %H:%M:%S')
			else: text = self.badge["description"] + " permanently"
		elif self.badge_id in (94,95,96,97,98):
			if self.badge_id == 94: ti = self.user.progressivestack
			elif self.badge_id == 95: ti = self.user.bird
			elif self.badge_id == 96: ti = self.user.flairchanged
			elif self.badge_id == 97: ti = self.user.longpost
			else: ti = self.user.marseyawarded
			text = self.badge["description"] + " until " + datetime.utcfromtimestamp(ti).strftime('%Y-%m-%d %H:%M:%S')
		elif self.description: text = self.description
		elif self.badge["description"]: text = self.badge["description"]
		else: return ''
		return f' - {text}'

	@property
	@lazy
	def name(self):
		return self.badge["name"]

	@property
	@lazy
	def path(self):
		return f"/static/assets/images/badges/{self.badge_id}.webp?a=6"

	@property
	@lazy
	def json(self):
		return {'text': self.text,
				'name': self.name,
				'url': self.url,
				'icon_url':f"{SITE_FULL}{self.path}"
				}