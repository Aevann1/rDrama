from files.classes import *
from flask import g
from .sanitize import *
from .const import *

def create_comment(text_html, autojanny=False):
	if autojanny: author_id = AUTOJANNY_ID
	else: author_id = NOTIFICATIONS_ID

	new_comment = Comment(author_id=author_id,
							parent_submission=None,
							body_html=text_html[:40000],
							distinguish_level=6)
	g.db.add(new_comment)
	g.db.flush()

	new_comment.top_comment_id = new_comment.id

	return new_comment.id

def send_repeatable_notification(uid, text, autojanny=False):

	if uid in bots: return

	if autojanny: author_id = AUTOJANNY_ID
	else: author_id = NOTIFICATIONS_ID
	
	text_html = sanitize(text)

	existing_comment = g.db.query(Comment.id).filter_by(author_id=author_id, parent_submission=None, body_html=text_html).first()

	if existing_comment:
		cid = existing_comment[0]
		existing_notif = g.db.query(Notification.user_id).filter_by(user_id=uid, comment_id=cid).one_or_none()
		if existing_notif: cid = create_comment(text_html, autojanny)
	else: cid = create_comment(text_html, autojanny)

	notif = Notification(comment_id=cid, user_id=uid)
	g.db.add(notif)


def send_notification(uid, text, autojanny=False):

	if uid in bots: return
	cid = notif_comment(text, autojanny)
	add_notif(cid, uid)


def notif_comment(text, autojanny=False):

	if autojanny:
		author_id = AUTOJANNY_ID
		alert = True
	else:
		author_id = NOTIFICATIONS_ID
		alert = False

	text_html = sanitize(text, alert=alert)

	try: existing = g.db.query(Comment.id).filter_by(author_id=author_id, parent_submission=None, body_html=text_html).one_or_none()
	except:
		existing = g.db.query(Comment).filter_by(author_id=author_id, parent_submission=None, body_html=text_html).all()
		

		notifs = g.db.query(Notification).filter(Notification.comment_id.in_([x.id for x in existing])).all()
		for c in notifs: g.db.delete(c)
		g.db.flush()

		
		for c in existing: g.db.delete(c)
		g.db.flush()
		existing = g.db.query(Comment.id).filter_by(author_id=author_id, parent_submission=None, body_html=text_html).one_or_none()
	
	if existing: return existing[0]
	else: return create_comment(text_html, autojanny)


def notif_comment2(p):

	search_html = f'%</a> has mentioned you: <a href="/post/{p.id}">%'

	existing = g.db.query(Comment.id).filter(Comment.author_id == NOTIFICATIONS_ID, Comment.parent_submission == None, Comment.body_html.like(search_html)).first()
	
	if existing: return existing[0]
	else:
		text = f"@{p.author.username} has mentioned you: [{p.title}](/post/{p.id})"
		if p.sub: text += f" in <a href='/h/{p.sub}'>/h/{p.sub}"
		text_html = sanitize(text, alert=True)
		return create_comment(text_html)


def add_notif(cid, uid):
	if uid in bots: return

	existing = g.db.query(Notification.user_id).filter_by(comment_id=cid, user_id=uid).one_or_none()
	if not existing:
		notif = Notification(comment_id=cid, user_id=uid)
		g.db.add(notif)


def NOTIFY_USERS(text, v):
	notify_users = set()
	for word, id in NOTIFIED_USERS.items():
		if id == 0 or v.id == id: continue
		if word in text.lower() and id not in notify_users: notify_users.add(id)

	captured = []
	for i in mention_regex.finditer(text):
		if v.username.lower() == i.group(2).lower(): continue

		if i.group(0) in captured: continue
		captured.append(i.group(0))

		user = get_user(i.group(2), graceful=True)
		if user and v.id != user.id and not v.any_block_exists(user): notify_users.add(user.id)

	return notify_users - bots