from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base
from files.helpers.lazy import *
import time

class ViewerRelationship(Base):

	__tablename__ = "viewers"

	user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
	viewer_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
	last_view_utc = Column(Integer)

	viewer = relationship("User", primaryjoin="ViewerRelationship.viewer_id == User.id")

	def __init__(self, **kwargs):

		if 'last_view_utc' not in kwargs:
			kwargs['last_view_utc'] = int(time.time())

		super().__init__(**kwargs)

	def __repr__(self):
		return f"<ViewerRelationship(user_id={self.user_id}, viewer_id={self.viewer_id})>"

	@property
	@lazy
	def last_view_since(self):

		return int(time.time()) - self.last_view_utc

	@property
	@lazy
	def last_view_string(self):

		age = self.last_view_since

		if age < 60:
			return "just now"
		elif age < 3600:
			minutes = int(age / 60)
			return f"{minutes}m ago"
		elif age < 86400:
			hours = int(age / 3600)
			return f"{hours}hr ago"
		elif age < 2678400:
			days = int(age / 86400)
			return f"{days}d ago"

		now = time.gmtime()
		ctd = time.gmtime(self.last_view_utc)

		months = now.tm_mon - ctd.tm_mon + 12 * (now.tm_year - ctd.tm_year)
		if now.tm_mday < ctd.tm_mday:
			months -= 1

		if months < 12:
			return f"{months}mo ago"
		else:
			years = int(months / 12)
			return f"{years}yr ago"
