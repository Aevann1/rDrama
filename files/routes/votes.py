from files.helpers.wrappers import *
from files.helpers.get import *
from files.helpers.const import *
from files.classes import *
from flask import *
from files.__main__ import app, limiter, cache
from os import environ

@app.get("/votes")
@auth_required
def admin_vote_info_get(v):
	link = request.values.get("link")
	if not link: return render_template("votes.html", v=v)

	try:
		if "t2_" in link: thing = get_post(int(link.split("t2_")[1]), v=v)
		elif "t3_" in link: thing = get_comment(int(link.split("t3_")[1]), v=v)
		else: abort(400)
	except: abort(400)

	if thing.ghost and v.id != AEVANN_ID: abort(403)

	if not thing.author:
		print(thing.id, flush=True)
	if isinstance(thing, Submission):
		if thing.author.shadowbanned and not (v and v.admin_level):
			thing_id = g.db.query(Submission.id).filter_by(upvotes=thing.upvotes, downvotes=thing.downvotes).order_by(Submission.id).first()[0]
		else: thing_id = thing.id

		ups = g.db.query(Vote).filter_by(submission_id=thing_id, vote_type=1).order_by(Vote.created_utc).all()

		downs = g.db.query(Vote).filter_by(submission_id=thing_id, vote_type=-1).order_by(Vote.created_utc).all()

	elif isinstance(thing, Comment):
		if thing.author.shadowbanned and not (v and v.admin_level):
			thing_id = g.db.query(Comment.id).filter_by(upvotes=thing.upvotes, downvotes=thing.downvotes).order_by(Comment.id).first()[0]
		else: thing_id = thing.id

		ups = g.db.query(CommentVote).filter_by(comment_id=thing_id, vote_type=1).order_by(CommentVote.created_utc).all()

		downs = g.db.query(CommentVote).filter_by(comment_id=thing_id, vote_type=-1 ).order_by(CommentVote.created_utc).all()

	else: abort(400)

	return render_template("votes.html",
						   v=v,
						   thing=thing,
						   ups=ups,
						   downs=downs)


@app.post("/vote/post/<post_id>/<new>")
@limiter.limit("5/second;60/minute;1000/hour;2000/day")
@limiter.limit("5/second;60/minute;1000/hour;2000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@is_not_permabanned
def api_vote_post(post_id, new, v):

	if new == "-1" and environ.get('DISABLE_DOWNVOTES') == '1': return {"error": "forbidden."}, 403

	if new not in ["-1", "0", "1"]: abort(400)

	if request.headers.get("Authorization"): abort(403)

	new = int(new)

	post = get_post(post_id)

	existing = g.db.query(Vote).filter_by(user_id=v.id, submission_id=post.id).one_or_none()

	coin_delta = 1
	if v.id == post.author.id:
		coin_delta = 0

	if existing and existing.vote_type == new: return "", 204

	if existing:
		if existing.vote_type == 0 and new != 0:
			post.author.coins += coin_delta
			post.author.truecoins += coin_delta
			g.db.add(post.author)
			existing.vote_type = new
			g.db.add(existing)
		elif existing.vote_type != 0 and new == 0:
			post.author.coins -= coin_delta
			post.author.truecoins -= coin_delta
			g.db.add(post.author)
			g.db.delete(existing)
		else:
			existing.vote_type = new
			g.db.add(existing)
	elif new != 0:
		post.author.coins += coin_delta
		post.author.truecoins += coin_delta
		g.db.add(post.author)

		if new == 1 and (v.agendaposter or v.shadowbanned or (v.is_banned and not v.unban_utc) or (v.profile_url.startswith('/e/') and not v.customtitle and v.namecolor == DEFAULT_COLOR)): real = False
		else: real = True

		vote = Vote(user_id=v.id,
					vote_type=new,
					submission_id=post_id,
					app_id=v.client.application.id if v.client else None,
					real = real
					)
		g.db.add(vote)

	g.db.flush()
	post.upvotes = g.db.query(Vote).filter_by(submission_id=post.id, vote_type=1).count()
	post.downvotes = g.db.query(Vote).filter_by(submission_id=post.id, vote_type=-1).count()
	post.realupvotes = g.db.query(Vote).filter_by(submission_id=post.id, real=True).count()
	if post.author.progressivestack: post.realupvotes *= 2
	g.db.add(post)
	g.db.commit()
	return "", 204

@app.post("/vote/comment/<comment_id>/<new>")
@limiter.limit("5/second;60/minute;1000/hour;2000/day")
@limiter.limit("5/second;60/minute;1000/hour;2000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@is_not_permabanned
def api_vote_comment(comment_id, new, v):

	if new == "-1" and environ.get('DISABLE_DOWNVOTES') == '1': return {"error": "forbidden."}, 403

	if new not in ["-1", "0", "1"]: abort(400)

	if request.headers.get("Authorization"): abort(403)

	new = int(new)

	try: comment_id = int(comment_id)
	except: abort(404)

	comment = get_comment(comment_id)

	if comment.author_id in {AUTOPOLLER_ID,AUTOBETTER_ID,AUTOCHOICE_ID}: return {"error": "forbidden."}, 403
	
	existing = g.db.query(CommentVote).filter_by(user_id=v.id, comment_id=comment.id).one_or_none()

	coin_delta = 1
	if v.id == comment.author_id:
		coin_delta = 0

	if existing and existing.vote_type == new: return "", 204

	if existing:
		if existing.vote_type == 0 and new != 0:
			comment.author.coins += coin_delta
			comment.author.truecoins += coin_delta
			g.db.add(comment.author)
			existing.vote_type = new
			g.db.add(existing)
		elif existing.vote_type != 0 and new == 0:
			comment.author.coins -= coin_delta
			comment.author.truecoins -= coin_delta
			g.db.add(comment.author)
			g.db.delete(existing)
		else:
			existing.vote_type = new
			g.db.add(existing)
	elif new != 0:
		comment.author.coins += coin_delta
		comment.author.truecoins += coin_delta
		g.db.add(comment.author)

		if new == 1 and (v.agendaposter or v.shadowbanned or (v.is_banned and not v.unban_utc) or (v.profile_url.startswith('/e/') and not v.customtitle and v.namecolor == DEFAULT_COLOR)): real = False
		else: real = True

		vote = CommentVote(user_id=v.id,
						vote_type=new,
						comment_id=comment_id,
						app_id=v.client.application.id if v.client else None,
						real=real
						)

		g.db.add(vote)

	g.db.flush()
	comment.upvotes = g.db.query(CommentVote).filter_by(comment_id=comment.id, vote_type=1).count()
	comment.downvotes = g.db.query(CommentVote).filter_by(comment_id=comment.id, vote_type=-1).count()
	comment.realupvotes = g.db.query(CommentVote).filter_by(comment_id=comment.id, real=True).count()
	if comment.author.progressivestack: comment.realupvotes *= 2
	g.db.add(comment)
	g.db.commit()
	return "", 204


@app.post("/vote/poll/<comment_id>")
@is_not_permabanned
def api_vote_poll(comment_id, v):
	
	vote = request.values.get("vote")
	if vote == "true": new = 1
	elif vote == "false": new = 0
	else: abort(400)

	comment_id = int(comment_id)
	comment = get_comment(comment_id)

	existing = g.db.query(CommentVote).filter_by(user_id=v.id, comment_id=comment.id).one_or_none()

	if existing and existing.vote_type == new: return "", 204

	if existing:
		if new == 1:
			existing.vote_type = new
			g.db.add(existing)
		else: g.db.delete(existing)
	elif new == 1:
		vote = CommentVote(user_id=v.id, vote_type=new, comment_id=comment.id)
		g.db.add(vote)

	g.db.flush()
	comment.upvotes = g.db.query(CommentVote).filter_by(comment_id=comment.id, vote_type=1).count()
	g.db.add(comment)
	g.db.commit()
	return "", 204


@app.post("/bet/<comment_id>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@limiter.limit("1/second;30/minute;200/hour;1000/day", key_func=lambda:f'{request.host}-{session.get("lo_user")}')
@is_not_permabanned
def bet(comment_id, v):
	
	if v.coins < 200: return {"error": "You don't have 200 coins!"}

	vote = request.values.get("vote")
	comment_id = int(comment_id)
	comment = get_comment(comment_id)
	
	existing = g.db.query(CommentVote).filter_by(user_id=v.id, comment_id=comment.id).one_or_none()
	if existing: return "", 204

	vote = CommentVote(user_id=v.id, vote_type=1, comment_id=comment.id)
	g.db.add(vote)

	comment.upvotes += 1
	g.db.add(comment)

	v.coins -= 200
	g.db.add(v)
	autobetter = g.db.query(User).filter_by(id=AUTOBETTER_ID).one_or_none()
	autobetter.coins += 200
	g.db.add(autobetter)

	g.db.commit()
	return "", 204

@app.post("/vote/choice/<comment_id>")
@is_not_permabanned
def api_vote_choice(comment_id, v):

	comment_id = int(comment_id)
	comment = get_comment(comment_id)

	existing = g.db.query(CommentVote).filter_by(user_id=v.id, comment_id=comment.id).one_or_none()

	if existing and existing.vote_type == 1: return "", 204

	if existing:
		existing.vote_type = 1
		g.db.add(existing)
	else:
		vote = CommentVote(user_id=v.id, vote_type=1, comment_id=comment.id)
		g.db.add(vote)

	if comment.parent_comment: parent = comment.parent_comment
	else: parent = comment.post

	for vote in parent.total_choice_voted(v):
		vote.comment.upvotes = g.db.query(CommentVote).filter_by(comment_id=vote.comment.id, vote_type=1).count() - 1
		g.db.add(vote.comment)
		g.db.delete(vote)

	g.db.flush()
	comment.upvotes = g.db.query(CommentVote).filter_by(comment_id=comment.id, vote_type=1).count()
	g.db.add(comment)
	g.db.commit()
	return "", 204