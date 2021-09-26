from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base, app
from os import environ
from files.helpers.lazy import lazy

site_name = environ.get("SITE_NAME").strip()

class BadgeDef(Base):

	__tablename__ = "badge_defs"

	id = Column(BigInteger, primary_key=True)
	name = Column(String(64))
	description = Column(String(64))
	icon = Column(String(64))
	kind = Column(Integer, default=1)
	qualification_expr = Column(String(128))

	def __repr__(self):

		return f"<BadgeDef(badge_id={self.id})>"

	@property
	@lazy
	def path(self):

		return f"/assets/images/badges/{self.icon}"

	@property
	@lazy
	def json_core(self):
		return {
			"name": self.name,
			"description": self.description,
			"icon": self.icon
		}
	


class Badge(Base):

	__tablename__ = "badges"

	id = Column(Integer, primary_key=True)

	user_id = Column(Integer, ForeignKey('users.id'))
	badge_id = Column(Integer, ForeignKey("badge_defs.id"))
	description = Column(String(64))
	url = Column(String(256))
	badge = relationship("BadgeDef", viewonly=True)

	def __repr__(self):

		return f"<Badge(user_id={self.user_id}, badge_id={self.badge_id})>"

	@property
	@lazy
	def text(self):
		if self.description:
			return self.description
		else:
			return self.badge.description

	@property
	@lazy
	def type(self):
		return self.badge.id

	@property
	@lazy
	def name(self):
		return self.badge.name

	@property
	@lazy
	def path(self):
		return self.badge.path

	@property
	@lazy
	def json_core(self):

		return {'text': self.text,
				'name': self.name,
				'created_utc': self.created_utc,
				'url': self.url,
				'icon_url':f"https://{app.config['SERVER_NAME']}{self.path}"
				}

	@property
	@lazy
	def json(self):
		return self.json_core
