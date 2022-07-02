from files.helpers.wrappers import *
from files.helpers.get import *
from files.helpers.const import *
from files.classes import *
from flask import *
from files.__main__ import app, limiter, cache
from os import environ

@app.get("/votes/<linK>")
@auth_required
def vote_info_get(v, link):
	try:
		if "t2_" in link: thing = get_post(int(link.split("t2_")[1]), v=v)
		elif "t3_" in link: thing = get_comment(int(link.split("t3_")[1]), v=v)
		else: abort(400)
	except: abort(400)

	if thing.ghost and v.id != AEVANN_ID: abort(403)

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

		if v.admin_level:
			up_ids = [x[0] for x in g.db.query(CommentVote.user_id).filter_by(comment_id=thing_id, vote_type=1).order_by(CommentVote.created_utc).all()]
			total_ups = g.db.query(func.sum(User.truecoins)).filter(User.id.in_(up_ids)).scalar()
			total_ups = format(total_ups, ",")
			patrons_ups = g.db.query(User).filter(User.id.in_(up_ids), User.patron > 0).count()

			return render_template("votes.html",
								v=v,
								thing=thing,
								ups=ups,
								downs=downs,
								total_ups=total_ups,
								patrons_ups=patrons_ups)

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

	coin_mult = 1
	if DOUBLE_XP_ENABLED > 0:
		if not existing and int(time.time()) > DOUBLE_XP_ENABLED:
			coin_mult = 2
		elif existing and existing.created_utc > DOUBLE_XP_ENABLED:
			coin_mult = 2

	if existing and existing.vote_type == new: return "", 204

	if existing:
		if existing.vote_type == 0 and new != 0:
			post.author.coins += coin_delta * coin_mult
			post.author.truecoins += coin_delta
			g.db.add(post.author)
			existing.vote_type = new
			g.db.add(existing)
		elif existing.vote_type != 0 and new == 0:
			post.author.coins -= coin_delta * coin_mult
			post.author.truecoins -= coin_delta
			g.db.add(post.author)
			g.db.delete(existing)
		else:
			existing.vote_type = new
			g.db.add(existing)
	elif new != 0:
		post.author.coins += coin_delta * coin_mult
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
	
	existing = g.db.query(CommentVote).filter_by(user_id=v.id, comment_id=comment.id).one_or_none()

	coin_delta = 1
	if v.id == comment.author_id:
		coin_delta = 0

	coin_mult = 1
	if DOUBLE_XP_ENABLED > 0:
		if not existing and int(time.time()) > DOUBLE_XP_ENABLED:
			coin_mult = 2
		elif existing and existing.created_utc > DOUBLE_XP_ENABLED:
			coin_mult = 2

	if existing and existing.vote_type == new: return "", 204

	if existing:
		if existing.vote_type == 0 and new != 0:
			comment.author.coins += coin_delta * coin_mult
			comment.author.truecoins += coin_delta
			g.db.add(comment.author)
			existing.vote_type = new
			g.db.add(existing)
		elif existing.vote_type != 0 and new == 0:
			comment.author.coins -= coin_delta * coin_mult
			comment.author.truecoins -= coin_delta
			g.db.add(comment.author)
			g.db.delete(existing)
		else:
			existing.vote_type = new
			g.db.add(existing)
	elif new != 0:
		comment.author.coins += coin_delta * coin_mult
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
	return "", 204