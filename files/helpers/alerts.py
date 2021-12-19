import mistletoe

from files.classes import *
from flask import g
from .markdown import *
from .sanitize import *
from .const import *


def send_notification(uid, text, autojanny=False):

	text = text.replace('r/', 'r\/').replace('u/', 'u\/')
	text_html = CustomRenderer().render(mistletoe.Document(text))
	text_html = sanitize(text_html)
	
	if autojanny: author_id = AUTOJANNY_ID
	else:
		author_id = NOTIFICATIONS_ID
		if ' has gifted you ' not in text:
			existing = g.db.query(Comment.id).filter(Comment.author_id == author_id, Comment.body_html == text_html, Comment.notifiedto == uid).first()
			if existing: return

	new_comment = Comment(author_id=author_id,
							parent_submission=None,
							distinguish_level=6,
							body_html=text_html,
							notifiedto=uid
						  )
	g.db.add(new_comment)

	g.db.flush()

	notif = Notification(comment_id=new_comment.id, user_id=uid)
	g.db.add(notif)


def send_follow_notif(vid, user, text):

	text_html = CustomRenderer().render(mistletoe.Document(text))
	text_html = sanitize(text_html)
	
	new_comment = Comment(author_id=NOTIFICATIONS_ID,
							parent_submission=None,
							distinguish_level=6,
							body_html=text_html,
						  )
	g.db.add(new_comment)
	g.db.flush()

	notif = Notification(comment_id=new_comment.id,
						 user_id=user,
						 followsender=vid)
	g.db.add(notif)
	
def send_unfollow_notif(vid, user, text):

	text_html = CustomRenderer().render(mistletoe.Document(text))
	text_html = sanitize(text_html)
	
	new_comment = Comment(author_id=NOTIFICATIONS_ID,
							parent_submission=None,
							distinguish_level=6,
							body_html=text_html,
						  )
	g.db.add(new_comment)
	g.db.flush()

	notif = Notification(comment_id=new_comment.id,
						 user_id=user,
						 unfollowsender=vid)
	g.db.add(notif)

def send_block_notif(vid, user, text):

	text_html = CustomRenderer().render(mistletoe.Document(text))
	text_html = sanitize(text_html)
	
	new_comment = Comment(author_id=NOTIFICATIONS_ID,
							parent_submission=None,
							distinguish_level=6,
							body_html=text_html,
						  )
	g.db.add(new_comment)
	g.db.flush()

	notif = Notification(comment_id=new_comment.id,
						 user_id=user,
						 blocksender=vid)
	g.db.add(notif)
	
def send_unblock_notif(vid, user, text):

	text_html = CustomRenderer().render(mistletoe.Document(text))
	text_html = sanitize(text_html)
	
	new_comment = Comment(author_id=NOTIFICATIONS_ID,
							parent_submission=None,
							distinguish_level=6,
							body_html=text_html,
						  )
	g.db.add(new_comment)
	g.db.flush()

	notif = Notification(comment_id=new_comment.id,
						 user_id=user,
						 unblocksender=vid)
	g.db.add(notif)



def send_admin(vid, text):

	text_html = Renderer().render(mistletoe.Document(text))

	text_html = sanitize(text_html, True)

	new_comment = Comment(author_id=vid,
						  parent_submission=None,
						  level=1,
						  sentto=0,
						  body_html=text_html,
						  )
	g.db.add(new_comment)
	g.db.flush()

	admins = g.db.query(User).filter(User.admin_level > 0).all()
	for admin in admins:
		notif = Notification(comment_id=new_comment.id, user_id=admin.id)
		g.db.add(notif)

def NOTIFY_USERS(text, vid):
	text = text.lower()
	notify_users = set()
	for word, id in NOTIFIED_USERS.items():
		if id == 0: continue
		if word in text and id not in notify_users and vid != id: notify_users.add(id)
	return notify_users