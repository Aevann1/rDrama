from files.helpers.wrappers import *
from files.helpers.get import *
from flask import g
from files.__main__ import app, limiter
from os import path
from files.helpers.sanitize import filter_emojis_only

@app.post("/report/post/<pid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def api_flag_post(pid, v):

	post = get_post(pid)

	if not v.shadowbanned:
		reason = request.values.get("reason", "").strip()[:100]

		if not reason.startswith('!'):
			existing = g.db.query(Flag.id).filter_by(user_id=v.id, post_id=post.id).one_or_none()
			if existing: return "", 409

		reason = filter_emojis_only(reason)

		if len(reason) > 350: return {"error": "Too long."}

		if reason.startswith('!') and v.admin_level > 1:
			post.flair = reason[1:]
			g.db.add(post)
		else:
			flag = Flag(post_id=post.id, user_id=v.id, reason=reason)
			g.db.add(flag)

		g.db.commit()

	return {"message": "Post reported!"}


@app.post("/report/comment/<cid>")
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@auth_required
def api_flag_comment(cid, v):

	comment = get_comment(cid)
	
	if not v.shadowbanned:
		existing = g.db.query(CommentFlag.id).filter_by( user_id=v.id, comment_id=comment.id).one_or_none()
		if existing: return "", 409

		reason = request.values.get("reason", "").strip()[:100]
		reason = filter_emojis_only(reason)

		if len(reason) > 350: return {"error": "Too long."}

		flag = CommentFlag(comment_id=comment.id, user_id=v.id, reason=reason)

		g.db.add(flag)
		g.db.commit()

	return {"message": "Comment reported!"}


@app.post('/del_report/<report_fn>')
@limiter.limit("1/second;30/minute;200/hour;1000/day")
@admin_level_required(2)
def remove_report(report_fn, v):

	if report_fn.startswith('c'):
		report = g.db.query(CommentFlag).filter_by(id=int(report_fn.lstrip('c'))).one_or_none()
		ma=ModAction(
			kind="delete_report",
			user_id=v.id,
			target_comment_id=report.comment_id
		)
	elif report_fn.startswith('p'):
		report = g.db.query(Flag).filter_by(id=int(report_fn.lstrip('p'))).one_or_none()
		ma=ModAction(
			kind="delete_report",
			user_id=v.id,
			target_submission_id=report.post_id
		)
	else: return {"error": "Invalid report ID"}, 400

	g.db.delete(report)

	g.db.add(ma)

	g.db.commit()

	return {"message": "Removed report"}