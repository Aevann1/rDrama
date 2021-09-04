from files.helpers.wrappers import *
from files.helpers.get import *
from files.classes import *
from flask import *
from files.__main__ import app


@app.get("/votes")
@auth_desired
def admin_vote_info_get(v):


	link = request.args.get("link")
	if not link: return render_template("votes.html", v=v)

	try:
		if "t2_" in link: thing = get_post(int(link.split("t2_")[1]), v=v)
		elif "t3_" in link: thing = get_comment(int(link.split("t3_")[1]), v=v)
		else: abort(400)
	except: abort(400)

	if isinstance(thing, Submission):

		ups = g.db.query(Vote
						 ).options(joinedload(Vote.user)
								   ).filter_by(submission_id=thing.id, vote_type=1
											   ).all()

		downs = g.db.query(Vote
						   ).options(joinedload(Vote.user)
									 ).filter_by(submission_id=thing.id, vote_type=-1
												 ).all()

	elif isinstance(thing, Comment):

		ups = g.db.query(CommentVote
						 ).options(joinedload(CommentVote.user)
								   ).filter_by(comment_id=thing.id, vote_type=1
											   ).all()

		downs = g.db.query(CommentVote
						   ).options(joinedload(CommentVote.user)
									 ).filter_by(comment_id=thing.id, vote_type=-1
												 ).all()

	else:
		abort(400)

	return render_template("votes.html",
						   v=v,
						   thing=thing,
						   ups=ups,
						   downs=downs,)



@app.post("/vote/post/<post_id>/<new>")
@auth_required
@validate_formkey
def api_vote_post(post_id, new, v):

	if new not in ["-1", "0", "1"]: abort(400)

	# disallow bots
	if request.headers.get("X-User-Type","") == "Bot": abort(403)

	new = int(new)

	post = get_post(post_id)

	# check for existing vote
	existing = g.db.query(Vote).filter_by(user_id=v.id, submission_id=post.id).first()

	if existing and existing.vote_type == new: return "", 204

	if existing:
		if existing.vote_type == 0 and new != 0:
			post.author.coins += 1
			g.db.add(post.author)
		elif existing.vote_type != 0 and new == 0:
			post.author.coins -= 1
			g.db.add(post.author)
		existing.vote_type = new
		g.db.add(existing)
	else:
		if new != 0:
			post.author.coins += 1
			g.db.add(post.author)
		vote = Vote(user_id=v.id,
					vote_type=new,
					submission_id=post_id,
					app_id=v.client.application.id if v.client else None
					)
		g.db.add(vote)
	
	try: g.db.flush()
	except: g.db.rollback()
	post.upvotes = g.db.query(Vote).filter_by(submission_id=post.id, vote_type=1).count()
	post.downvotes = g.db.query(Vote).filter_by(submission_id=post.id, vote_type=-1).count()
	g.db.add(post)
	return "", 204

@app.post("/vote/comment/<comment_id>/<new>")
@auth_required
@validate_formkey
def api_vote_comment(comment_id, new, v):

	if new not in ["-1", "0", "1"]: abort(400)

	if request.headers.get("X-User-Type","") == "Bot": abort(403)

	new = int(new)

	try: comment_id = int(comment_id)
	except:
		try: comment_id = int(comment_id, 36)
		except: abort(404)

	comment = get_comment(comment_id)

	# check for existing vote
	existing = g.db.query(CommentVote).filter_by(user_id=v.id, comment_id=comment.id).first()

	if existing and existing.vote_type == new: return "", 204

	if existing:
		if existing.vote_type == 0 and new != 0:
			comment.author.coins += 1
			g.db.add(comment.author)
		elif existing.vote_type != 0 and new == 0:
			comment.author.coins -= 1
			g.db.add(comment.author)
		existing.vote_type = new
		g.db.add(existing)
	else:
		if new != 0:
			comment.author.coins += 1
			g.db.add(comment.author)
		vote = CommentVote(user_id=v.id,
						   vote_type=new,
						   comment_id=comment_id,
						app_id=v.client.application.id if v.client else None
						   )

		g.db.add(vote)
		
	try: g.db.flush()
	except: g.db.rollback()
	comment.upvotes = g.db.query(CommentVote).filter_by(comment_id=comment.id, vote_type=1).count()
	comment.downvotes = g.db.query(CommentVote).filter_by(comment_id=comment.id, vote_type=-1).count()
	g.db.add(comment)
	return "", 204