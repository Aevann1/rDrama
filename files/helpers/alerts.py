import mistletoe

from files.classes import *
from flask import g
from .markdown import *
from .sanitize import *
from .const import *


def send_notification(vid, user, text):

	text = text.replace('r/', 'r\/').replace('u/', 'u\/')
	text = text.replace("\n", "\n\n").replace("\n\n\n\n\n\n", "\n\n").replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
	with CustomRenderer() as renderer:
		text_html = renderer.render(mistletoe.Document(text))

	text_html = sanitize(text_html)
	
	new_comment = Comment(author_id=vid,
						  parent_submission=None,
						  distinguish_level=6,
						  )
	g.db.add(new_comment)

	g.db.flush()

	new_aux = CommentAux(id=new_comment.id,
						 body=text,
						 body_html=text_html,
						 )
	g.db.add(new_aux)

	notif = Notification(comment_id=new_comment.id,
						 user_id=user.id)
	g.db.add(notif)


def send_pm(vid, user, text):

	with CustomRenderer() as renderer: text_html = renderer.render(mistletoe.Document(text))

	text_html = sanitize(text_html)

	new_comment = Comment(author_id=vid,
						  parent_submission=None,
						  level=1,
						  sentto=user.id
						  )
	g.db.add(new_comment)

	g.db.flush()

	new_aux = CommentAux(id=new_comment.id, body=text, body_html=text_html)
	g.db.add(new_aux)

	notif = Notification(comment_id=new_comment.id, user_id=user.id)
	g.db.add(notif)


def send_follow_notif(vid, user, text):

	text = text.replace("\n", "\n\n").replace("\n\n\n\n\n\n", "\n\n").replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")

	with CustomRenderer() as renderer: text_html = renderer.render(mistletoe.Document(text))
	text_html = sanitize(text_html)
	
	new_comment = Comment(author_id=NOTIFICATIONS_ACCOUNT,
						  parent_submission=None,
						  distinguish_level=6,
						  )
	g.db.add(new_comment)
	g.db.flush()

	new_aux = CommentAux(id=new_comment.id,
						 body=text,
						 body_html=text_html,
						 )
	g.db.add(new_aux)

	notif = Notification(comment_id=new_comment.id,
						 user_id=user,
						 followsender=vid)
	g.db.add(notif)
	
def send_unfollow_notif(vid, user, text):

	text = text.replace("\n", "\n\n").replace("\n\n\n\n\n\n", "\n\n").replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")

	with CustomRenderer() as renderer:
		text_html = renderer.render(mistletoe.Document(text))
	text_html = sanitize(text_html)
	
	new_comment = Comment(author_id=NOTIFICATIONS_ACCOUNT,
						  parent_submission=None,
						  distinguish_level=6,
						  )
	g.db.add(new_comment)
	g.db.flush()

	new_aux = CommentAux(id=new_comment.id,
						 body=text,
						 body_html=text_html,
						 )
	g.db.add(new_aux)

	notif = Notification(comment_id=new_comment.id,
						 user_id=user,
						 unfollowsender=vid)
	g.db.add(notif)

def send_block_notif(vid, user, text):

	text = text.replace("\n", "\n\n").replace("\n\n\n\n\n\n", "\n\n").replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")

	with CustomRenderer() as renderer:
		text_html = renderer.render(mistletoe.Document(text))
	text_html = sanitize(text_html)
	
	new_comment = Comment(author_id=NOTIFICATIONS_ACCOUNT,
						  parent_submission=None,
						  distinguish_level=6,
						  )
	g.db.add(new_comment)
	g.db.flush()

	new_aux = CommentAux(id=new_comment.id,
						 body=text,
						 body_html=text_html,
						 )
	g.db.add(new_aux)

	notif = Notification(comment_id=new_comment.id,
						 user_id=user,
						 blocksender=vid)
	g.db.add(notif)
	
def send_unblock_notif(vid, user, text):

	text = text.replace("\n", "\n\n").replace("\n\n\n\n\n\n", "\n\n").replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")

	with CustomRenderer() as renderer:
		text_html = renderer.render(mistletoe.Document(text))
	text_html = sanitize(text_html)
	
	new_comment = Comment(author_id=NOTIFICATIONS_ACCOUNT,
						  parent_submission=None,
						  distinguish_level=6,
						  )
	g.db.add(new_comment)
	g.db.flush()

	new_aux = CommentAux(id=new_comment.id,
						 body=text,
						 body_html=text_html,
						 )
	g.db.add(new_aux)

	notif = Notification(comment_id=new_comment.id,
						 user_id=user,
						 unblocksender=vid)
	g.db.add(notif)

def send_admin(vid, text):

	text = text.replace("\n", "\n\n").replace("\n\n\n\n\n\n", "\n\n").replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")

	with CustomRenderer() as renderer: text_html = renderer.render(mistletoe.Document(text))

	text_html = sanitize(text_html)

	new_comment = Comment(author_id=vid,
						  parent_submission=None,
						  level=1,
						  sentto=0
						  )
	g.db.add(new_comment)
	g.db.flush()
	new_aux = CommentAux(id=new_comment.id, body=text, body_html=text_html)
	g.db.add(new_aux)

	admins = g.db.query(User).filter(User.admin_level > 0).all()
	for admin in admins:
		notif = Notification(comment_id=new_comment.id, user_id=admin.id)
		g.db.add(notif)
