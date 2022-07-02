from files.classes import *
from flask import g
from sqlalchemy.orm import joinedload

def get_id(username, v=None, graceful=False):
	
	username = username.replace('\\', '').replace('_', '\_').replace('%', '').strip()

	user = g.db.query(
		User.id
		).filter(
		or_(
			User.username.ilike(username),
			User.original_username.ilike(username)
			)
		).one_or_none()

	if not user:
		if not graceful:
			abort(404)
		else:
			return None

	return user[0]


def get_user(username, v=None, graceful=False):

	if not username:
		if not graceful: abort(404)
		else: return None

	username = username.replace('\\', '').replace('_', '\_').replace('%', '').strip()

	user = g.db.query(
		User
		).filter(
		or_(
			User.username.ilike(username),
			User.original_username.ilike(username)
			)
		).one_or_none()

	if not user:
		if not graceful: abort(404)
		else: return None

	if v:
		block = g.db.query(UserBlock).filter(
			or_(
				and_(
					UserBlock.user_id == v.id,
					UserBlock.target_id == user.id
				),
				and_(UserBlock.user_id == user.id,
					 UserBlock.target_id == v.id
					 )
			)
		).first()

		user.is_blocking = block and block.user_id == v.id
		user.is_blocked = block and block.target_id == v.id

	return user

def get_users(usernames, v=None, graceful=False):
	if not usernames:
		if not graceful: abort(404)
		else: return []

	def clean(n):
		return n.replace('\\', '').replace('_', '\_').replace('%', '').strip()

	usernames = [ clean(n) for n in usernames ]

	users = g.db.query(User).filter(
		or_(
			User.username.ilike(any_(usernames)),
			User.original_username.ilike(any_(usernames))
			)
		).all()

	if not users:
		if not graceful: abort(404)
		else: return []

	return users

def get_account(id, v=None):

	try: id = int(id)
	except: abort(404)

	user = g.db.get(User, id)
	if not user: abort(404)

	if v:
		block = g.db.query(UserBlock).filter(
			or_(
				and_(
					UserBlock.user_id == v.id,
					UserBlock.target_id == user.id
				),
				and_(UserBlock.user_id == user.id,
					 UserBlock.target_id == v.id
					 )
			)
		).first()

		user.is_blocking = block and block.user_id == v.id
		user.is_blocked = block and block.target_id == v.id

	return user


def get_post(i, v=None, graceful=False, rendered=False):

	try: i = int(i)
	except: abort(404)

	if not i:
		if graceful: return None
		else: abort(404)

	if v:
		vt = g.db.query(Vote).filter_by(user_id=v.id, submission_id=i).subquery()
		blocking = v.blocking.subquery()

		post = g.db.query(
			Submission,
			vt.c.vote_type,
			blocking.c.target_id,
		)

		post=post.filter(Submission.id == i
		).join(
			vt, 
			vt.c.submission_id == Submission.id, 
			isouter=True
		).join(
			blocking, 
			blocking.c.target_id == Submission.author_id, 
			isouter=True
		)

		if rendered:
			posts = post.options(
				joinedload(Submission.flags),
				joinedload(Submission.awards),
				joinedload(Submission.author),
				joinedload(Submission.options),
				joinedload(Submission.options, SubmissionOption.votes)
			)

		post=post.one_or_none()
		
		if not post:
			if graceful: return None
			else: abort(404)

		x = post[0]
		x.voted = post[1] or 0
		x.is_blocking = post[2] or 0
	else:
		post = g.db.get(Submission, i)
		if not post:
			if graceful: return None
			else: abort(404)
		x=post

	return x


def get_posts(pids, v=None):

	if not pids:
		return []

	if v:
		vt = g.db.query(Vote.vote_type, Vote.submission_id).filter(
			Vote.submission_id.in_(pids), 
			Vote.user_id==v.id
			).subquery()

		blocking = v.blocking.subquery()
		blocked = v.blocked.subquery()

		query = g.db.query(
			Submission,
			vt.c.vote_type,
			blocking.c.target_id,
			blocked.c.target_id,
		).filter(
			Submission.id.in_(pids)
		).join(
			vt, vt.c.submission_id==Submission.id, isouter=True
		).join(
			blocking, 
			blocking.c.target_id == Submission.author_id, 
			isouter=True
		).join(
			blocked, 
			blocked.c.user_id == Submission.author_id, 
			isouter=True
		).options(joinedload(Submission.flags),
			joinedload(Submission.awards),
			joinedload(Submission.author),
			joinedload(Submission.options),
			joinedload(Submission.options, SubmissionOption.votes)
		).all()

		output = [p[0] for p in query]
		for i in range(len(output)):
			output[i].voted = query[i][1] or 0
			output[i].is_blocking = query[i][2] or 0
			output[i].is_blocked = query[i][3] or 0
	else:
		output = g.db.query(Submission,).filter(Submission.id.in_(pids)).all()

	return sorted(output, key=lambda x: pids.index(x.id))

def get_comment(i, v=None, graceful=False):

	try: i = int(i)
	except: abort(404)

	if not i:
		if graceful: return None
		else: abort(404)

	comment=g.db.get(Comment, i)
	if not comment:
		if graceful: return None
		else: abort(404)

	if v:
		block = g.db.query(UserBlock).filter(
			or_(
				and_(
					UserBlock.user_id == v.id,
					UserBlock.target_id == comment.author_id
				),
				and_(
					UserBlock.user_id == comment.author_id,
					UserBlock.target_id == v.id
				)
			)
		).first()

		vt = g.db.query(CommentVote.vote_type).filter_by(user_id=v.id, comment_id=comment.id).one_or_none()
		comment.is_blocking = block and block.user_id == v.id
		comment.is_blocked = block and block.target_id == v.id
		comment.voted = vt.vote_type if vt else 0

	return comment


def get_comments(cids, v=None, load_parent=False):

	if not cids: return []

	if v:
		votes = g.db.query(CommentVote.vote_type, CommentVote.comment_id).filter_by(user_id=v.id).subquery()

		blocking = v.blocking.subquery()

		blocked = v.blocked.subquery()

		comments = g.db.query(
			Comment,
			votes.c.vote_type,
			blocking.c.target_id,
			blocked.c.target_id,
		).filter(Comment.id.in_(cids))
 
		if not (v and (v.shadowbanned or v.admin_level >= 2)):
			comments = comments.join(User, User.id == Comment.author_id).filter(User.shadowbanned == None)

		comments = comments.join(
			votes,
			votes.c.comment_id == Comment.id,
			isouter=True
		).join(
			blocking,
			blocking.c.target_id == Comment.author_id,
			isouter=True
		).join(
			blocked,
			blocked.c.user_id == Comment.author_id,
			isouter=True
		).all()

		output = []
		for c in comments:
			comment = c[0]
			comment.voted = c[1] or 0
			comment.is_blocking = c[2] or 0
			comment.is_blocked = c[3] or 0
			output.append(comment)

	else:
		output = g.db.query(Comment).join(User, User.id == Comment.author_id).filter(User.shadowbanned == None, Comment.id.in_(cids)).all()

	if load_parent:
		parents = [x.parent_comment_id for x in output if x.parent_comment_id]
		parents = get_comments(parents, v=v)

	return sorted(output, key=lambda x: cids.index(x.id))


def get_domain(s):

	parts = s.split(".")
	domain_list = set()
	for i in range(len(parts)):
		new_domain = parts[i]
		for j in range(i + 1, len(parts)):
			new_domain += "." + parts[j]

		domain_list.add(new_domain)

	doms = g.db.query(BannedDomain).filter(BannedDomain.domain.in_(domain_list)).all()

	if not doms:
		return None

	doms = sorted(doms, key=lambda x: len(x.domain), reverse=True)

	return doms[0]
