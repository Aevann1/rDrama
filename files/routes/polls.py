from files.helpers.wrappers import *
from files.helpers.get import *
from files.helpers.const import *
from files.classes import *
from flask import *
from files.__main__ import app


@app.post("/vote/post/option/<option_id>")
@is_not_permabanned
def api_vote_option(option_id, v):

	option_id = int(option_id)

	option = g.db.get(SubmissionOption, option_id)

	if not option: abort(404)

	if option.exclusive:
		vote = g.db.query(SubmissionOptionVote).join(SubmissionOption).filter(
			SubmissionOptionVote.user_id==v.id,
			SubmissionOptionVote.submission_id==option.submission_id,
			SubmissionOption.exclusive==True).one_or_none()
		if vote:
			g.db.delete(vote)

	existing = g.db.query(SubmissionOptionVote).filter_by(option_id=option_id, user_id=v.id).one_or_none()
	if not existing:
		vote = SubmissionOptionVote(
			option_id=option_id,
			user_id=v.id,
			submission_id=option.submission_id,
		)
		g.db.add(vote)
	elif existing:
		g.db.delete(existing)

	return "", 204

@app.get("/votes/post/option/<option_id>")
@auth_required
def option_votes(option_id, v):

	option_id = int(option_id)

	option = g.db.get(SubmissionOption, option_id)

	if not option: abort(404)

	ups = g.db.query(SubmissionOptionVote).filter_by(option_id=option_id).options(
		joinedload(SubmissionOptionVote.user)
	).all()

	return render_template("poll_votes.html",
						   v=v,
						   thing=option,
						   ups=ups)



@app.post("/vote/comment/option/<option_id>")
@is_not_permabanned
def api_vote_option_comment(option_id, v):

	option_id = int(option_id)

	option = g.db.get(CommentOption, option_id)

	if not option: abort(404)

	if option.exclusive:
		vote = g.db.query(CommentOptionVote).join(CommentOption).filter(
			CommentOptionVote.user_id==v.id,
			CommentOptionVote.comment_id==option.comment_id,
			CommentOption.exclusive==True).one_or_none()
		if vote:
			g.db.delete(vote)

	existing = g.db.query(CommentOptionVote).filter_by(option_id=option_id, user_id=v.id).one_or_none()
	if not existing:
		vote = CommentOptionVote(
			option_id=option_id,
			user_id=v.id,
			comment_id=option.comment_id,
		)
		g.db.add(vote)
	elif existing:
		g.db.delete(existing)

	return "", 204

@app.get("/votes/comment/option/<option_id>")
@auth_required
def option_votes_comment(option_id, v):

	option_id = int(option_id)

	option = g.db.get(CommentOption, option_id)

	if not option: abort(404)

	ups = g.db.query(CommentOptionVote).filter_by(option_id=option_id).options(
		joinedload(CommentOptionVote.user)
	).all()

	return render_template("poll_votes.html",
						   v=v,
						   thing=option,
						   ups=ups)