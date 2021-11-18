from files.helpers.wrappers import *
from files.helpers.get import *
from flask import g
from files.__main__ import app, limiter
from os import path

@app.post("/flag/post/<pid>")
@limiter.limit("1/second")
@auth_desired
def api_flag_post(pid, v):

	post = get_post(pid)

	if v and not v.shadowbanned:
		existing = g.db.query(Flag.id).filter_by(user_id=v.id, post_id=post.id).first()

		if existing: return "", 409

		reason = request.values.get("reason", "").strip()[:100]
		if "<" in reason: return {"error": f"Reasons can't contain <"}

		for i in re.finditer(':(.{1,30}?):', reason):
			if path.isfile(f'./files/assets/images/emojis/{i.group(1)}.webp'):
				reason = reason.replace(f':{i.group(1)}:', f'<img loading="lazy" data-bs-toggle="tooltip" title="{i.group(1)}" delay="0" height=20 src="http://{site}/assets/images/emojis/{i.group(1)}.webp">')

		flag = Flag(post_id=post.id,
					user_id=v.id,
					reason=reason,
					)
					

		g.db.add(flag)

		g.db.commit()

	return {"message": "Post reported!"}


@app.post("/flag/comment/<cid>")
@limiter.limit("1/second")
@auth_desired
def api_flag_comment(cid, v):

	comment = get_comment(cid)
	
	if v and not v.shadowbanned:
		existing = g.db.query(CommentFlag.id).filter_by(
			user_id=v.id, comment_id=comment.id).first()

		if existing: return "", 409
		reason = request.values.get("reason", "").strip()[:100]
		if "<" in reason: return {"error": f"Reasons can't contain <"}

		for i in re.finditer(':(.{1,30}?):', reason):
			if path.isfile(f'./files/assets/images/emojis/{i.group(1)}.webp'):
				reason = reason.replace(f':{i.group(1)}:', f'<img loading="lazy" data-bs-toggle="tooltip" title="{i.group(1)}" delay="0" height=20 src="http://{site}/assets/images/emojis/{i.group(1)}.webp">')

		flag = CommentFlag(comment_id=comment.id,
					user_id=v.id,
					reason=reason,
					)

		g.db.add(flag)

		g.db.commit()

	return {"message": "Comment reported!"}


@app.post('/del_report/<report_fn>')
@limiter.limit("1/second")
@admin_level_required(2)
@validate_formkey
def remove_report(report_fn, v):

	if report_fn.startswith('c'):
		report = g.db.query(CommentFlag).filter_by(id=int(report_fn.lstrip('c'))).first()
	elif report_fn.startswith('p'):
		report = g.db.query(Flag).filter_by(id=int(report_fn.lstrip('p'))).first()
	else:
		return {"error": "Invalid report ID"}, 400

	g.db.delete(report)

	g.db.commit()

	return {"message": "Removed report"}