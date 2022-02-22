from files.classes import *
from flask import g
from .sanitize import *
from .const import *

def create_comment(text_html, autojanny=False):
	if autojanny: author_id = AUTOJANNY_ID
	else: author_id = NOTIFICATIONS_ID

	new_comment = Comment(author_id=author_id,
							parent_submission=None,
							distinguish_level=6,
							created_utc=0,
							body_html=text_html)
	g.db.add(new_comment)
	g.db.flush()
	return new_comment.id

def send_repeatable_notification(uid, text, autojanny=False):

	if autojanny: author_id = AUTOJANNY_ID
	else: author_id = NOTIFICATIONS_ID
	
	text_html = sanitize(text)

	existing_comment = g.db.query(Comment.id).filter_by(author_id=author_id, parent_submission=None, distinguish_level=6, body_html=text_html, created_utc=0).first()

	if existing_comment:
		cid = existing_comment[0]
		existing_notif = g.db.query(Notification.user_id).filter_by(user_id=uid, comment_id=cid).one_or_none()
		if existing_notif: cid = create_comment(text_html, autojanny)
	else: cid = create_comment(text_html, autojanny)

	notif = Notification(comment_id=cid, user_id=uid)
	g.db.add(notif)


def send_notification(uid, text, autojanny=False):

	cid = notif_comment(text, autojanny)
	add_notif(cid, uid)


def notif_comment(text, autojanny=False):

	if autojanny: author_id = AUTOJANNY_ID
	else: author_id = NOTIFICATIONS_ID

	text_html = sanitize(text, alert=True)

	existing = g.db.query(Comment.id).filter_by(author_id=author_id, parent_submission=None, distinguish_level=6, body_html=text_html, created_utc=0).first()
	
	if existing: return existing[0]
	else: return create_comment(text_html, autojanny)


def add_notif(cid, uid):
	existing = g.db.query(Notification.user_id).filter_by(comment_id=cid, user_id=uid).one_or_none()
	if not existing:
		notif = Notification(comment_id=cid, user_id=uid)
		g.db.add(notif)


def NOTIFY_USERS(text, v):
	notify_users = set()
	for word, id in NOTIFIED_USERS.items():
		if id == 0: continue
		if word in text.lower() and id not in notify_users and v.id != id: notify_users.add(id)

	soup = BeautifulSoup(text, features="html.parser")
	for mention in soup.find_all("a", href=re.compile("^\/id\/([0-9]+)")):
		id = int(mention["href"].split("/id/")[1])
		if id != v.id:
			user = g.db.query(User).filter_by(id=id).one_or_none()
			if user and not v.any_block_exists(user): notify_users.add(user.id)

	return notify_users

def NOTIFY_USERS2(text, v):
	notify_users = set()
	for word, id in NOTIFIED_USERS.items():
		if id == 0: continue
		if word in text.lower() and id not in notify_users and v.id != id: notify_users.add(id)

	for i in re.finditer("(^|\s|\n)@((\w|-){1,25})", text, re.A):
		user = get_user(i.group(2), graceful=True)
		if user and not v.any_block_exists(user): notify_users.add(user.id)

	return notify_users