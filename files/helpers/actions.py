from flask import g
from files.classes.badges import Badge
from files.helpers.alerts import send_repeatable_notification

def badge_grant(user, badge_id):

	if user.has_badge(badge_id): return

	badge = Badge(
		badge_id=int(badge_id), 
		user_id=user.id
	)

	g.db.add(badge)
	g.db.flush()

	send_repeatable_notification(user.id, f"@AutoJanny has given you the following profile badge:\n\n![]({badge.path})\n\n{badge.name}")
