from files.helpers.wrappers import *
from files.helpers.get import *
from flask import g
from files.__main__ import app
from files.helpers.sanitize import sanitize
from os import path

@app.post("/flag/post/<pid>")
@auth_desired
def api_flag_post(pid, v):

	post = get_post(pid)

	if v:
		existing = g.db.query(Flag).filter_by(user_id=v.id, post_id=post.id).first()

		if existing: return "", 409

		reason = request.form.get("reason", "").strip()[:100]
		if "<" in reason: return {"error": f"Reasons can't contain <"}

		for i in re.finditer(':(.{1,30}?):', reason):
			if path.isfile(f'./files/assets/images/emojis/{i.group(1)}.gif'):
				reason = reason.replace(f':{i.group(1)}:', f'<img data-toggle="tooltip" title="{i.group(1)}" delay="0" height=20 src="https://{site}/assets/images/emojis/{i.group(1)}.gif"<span>')

		flag = Flag(post_id=post.id,
					user_id=v.id,
					reason=reason,
					)
					

		g.db.add(flag)

	return "", 204


@app.post("/flag/comment/<cid>")
@auth_desired
def api_flag_comment(cid, v):

	comment = get_comment(cid)
	
	if v:
		existing = g.db.query(CommentFlag).filter_by(
			user_id=v.id, comment_id=comment.id).first()

		if existing: return "", 409
		reason = request.form.get("reason", "").strip()[:100]
		if "<" in reason: return {"error": f"Reasons can't contain <"}

		for i in re.finditer(':(.{1,30}?):', reason):
			if path.isfile(f'./files/assets/images/emojis/{i.group(1)}.gif'):
				reason = reason.replace(f':{i.group(1)}:', f'<img data-toggle="tooltip" title="{i.group(1)}" delay="0" height=20 src="https://{site}/assets/images/emojis/{i.group(1)}.gif"<span>')

		flag = CommentFlag(comment_id=comment.id,
					user_id=v.id,
					reason=reason,
					)

		g.db.add(flag)

	return "", 204


@app.post('/del_report/<report_fn>')
@auth_required
@validate_formkey
def remove_report(report_fn, v):

	if v.admin_level < 6:
		return {"error": "go outside"}, 403

	if report_fn.startswith('c'):
		report = g.db.query(CommentFlag).filter_by(id=int(report_fn.lstrip('c'))).first()
	elif report_fn.startswith('p'):
		report = g.db.query(Flag).filter_by(id=int(report_fn.lstrip('p'))).first()
	else:
		return {"error": "Invalid report ID"}, 400

	_response = f"Removed @{report.user.username}'s report"
	g.db.delete(report)

	return {"message": _response}, 200