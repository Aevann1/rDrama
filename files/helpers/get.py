from files.classes import *
from flask import g

def get_user(username, v=None, graceful=False):

	username = username.replace('\\', '')
	username = username.replace('_', '\_')
	username = username.replace('%', '')

	user = g.db.query(
		User
		).filter(
		or_(
			User.username.ilike(username),
			User.original_username.ilike(username)
			)
		).first()

	if not user:
		if not graceful:
			abort(404)
		else:
			return None

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

def get_account(id, v=None):

	user = g.db.query(User).filter_by(id = id).first()
				
	if not user:
		try: id = int(str(id), 36)
		except: abort(404)
		user = g.db.query(User).filter_by(id = id).first()
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


def get_post(i, v=None, graceful=False):

	if v:
		vt = g.db.query(Vote).filter_by(
			user_id=v.id, submission_id=i).subquery()
		blocking = v.blocking.subquery()

		items = g.db.query(
			Submission,
			vt.c.vote_type,
			blocking.c.id,
		)

		items=items.filter(Submission.id == i
		).join(
			vt, 
			vt.c.submission_id == Submission.id, 
			isouter=True
		).join(
			blocking, 
			blocking.c.target_id == Submission.author_id, 
			isouter=True
		)

		items=items.first()

		if not items and not graceful:
			abort(404)
		x = items[0]
		x.voted = items[1] or 0
		x.is_blocking = items[2] or 0
	else:
		items = g.db.query(
			Submission
		).filter(Submission.id == i).first()
		if not items and not graceful:
			abort(404)
		x=items

	return x


def get_posts(pids, v=None):

	if not pids:
		return []

	pids=tuple(pids)

	if v:
		vt = g.db.query(Vote).filter(
			Vote.submission_id.in_(pids), 
			Vote.user_id==v.id
			).subquery()

		blocking = v.blocking.subquery()
		blocked = v.blocked.subquery()

		query = g.db.query(
			Submission,
			vt.c.vote_type,
			blocking.c.id,
			blocked.c.id,
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

	if v:

		comment=g.db.query(Comment).filter(Comment.id == i).first()

		if not comment and not graceful: abort(404)

		block = g.db.query(UserBlock).filter(
			or_(
				and_(
					UserBlock.user_id == v.id,
					UserBlock.target_id == comment.author_id
				),
				and_(UserBlock.user_id == comment.author_id,
					 UserBlock.target_id == v.id
					 )
			)
		).first()

		vts = g.db.query(CommentVote).filter_by(user_id=v.id, comment_id=comment.id)
		vt = g.db.query(CommentVote).filter_by(user_id=v.id, comment_id=comment.id).first()
		comment.is_blocking = block and block.user_id == v.id
		comment.is_blocked = block and block.target_id == v.id
		comment.voted = vt.vote_type if vt else 0

	else:
		comment = g.db.query(Comment).filter(Comment.id == i).first()
		if not comment and not graceful:abort(404)

	return comment


def get_comments(cids, v=None, load_parent=False):

	if not cids: return []

	cids=tuple(cids)

	if v:
		votes = g.db.query(CommentVote).filter_by(user_id=v.id).subquery()

		blocking = v.blocking.subquery()

		blocked = v.blocked.subquery()

		comments = g.db.query(
			Comment,
			votes.c.vote_type,
			blocking.c.id,
			blocked.c.id,
		).filter(Comment.id.in_(cids))
 
		if not (v and v.shadowbanned) and not (v and v.admin_level > 1):
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
		parents = {x.id: x for x in parents}
		for c in output: c.sex = parents.get(c.parent_comment_id)

	return sorted(output, key=lambda x: cids.index(x.id))


def get_domain(s):

	parts = s.split(".")
	domain_list = set([])
	for i in range(len(parts)):
		new_domain = parts[i]
		for j in range(i + 1, len(parts)):
			new_domain += "." + parts[j]

		domain_list.add(new_domain)

	domain_list = tuple(list(domain_list))

	doms = [x for x in g.db.query(BannedDomain).filter(BannedDomain.domain.in_(domain_list)).all()]

	if not doms:
		return None

	doms = sorted(doms, key=lambda x: len(x.domain), reverse=True)

	return doms[0]