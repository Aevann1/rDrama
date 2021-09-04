from files.__main__ import app
from files.helpers.wrappers import *
from files.helpers.alerts import *
from files.helpers.get import *
from files.helpers.const import *
from files.classes.award import *
from flask import g, request


def banaward_trigger(post=None, comment=None):

    author = post.author if post else comment.author
    link = f"[this post]({post.permalink})" if post else f"[this comment]({comment.permalink})"

    if not author.is_suspended:
        author.ban(reason="one-day ban award used", days=1)

        send_notification(NOTIFICATIONS_ACCOUNT, author, f"Your account has been suspended for a day for {link}. It sucked and you should feel bad.")
    elif author.unban_utc > 0:
        author.unban_utc += 24*60*60
        g.db.add(author)

        send_notification(NOTIFICATIONS_ACCOUNT, author, f"Your account has been suspended for yet another day for {link}. Seriously man?")


ACTIONS = {
    "ban": banaward_trigger
}

ALLOW_MULTIPLE = (
    "ban",
    "shit",
    "gold"
)


@app.get("/awards")
@auth_required
def get_awards(v):

    return_value = list(AWARDS.values())

    user_awards = v.awards
    for val in return_value:
        val['owned'] = len([x for x in user_awards if x.kind == val['kind'] and not x.given])

    return jsonify(return_value)


@app.put("/post/<pid>/awards")
@auth_required
@validate_formkey
def award_post(pid, v):

    if v.is_suspended and v.unban_utc == 0:
        return {"error": "forbidden"}, 403

    kind = request.form.get("kind", "")

    if kind not in AWARDS:
        return {"error": "That award doesn't exist."}, 404

    post_award = g.db.query(AwardRelationship).filter(
        and_(
            AwardRelationship.kind == kind,
            AwardRelationship.user_id == v.id,
            AwardRelationship.submission_id == None,
            AwardRelationship.comment_id == None
        )
    ).first()

    if not post_award:
        return {"error": "You don't have that award."}, 404

    post = g.db.query(Submission).filter_by(id=pid).first()

    if not post or post.is_banned or post.deleted_utc > 0:
        return {"error": "That post doesn't exist or has been deleted or removed."}, 404

    if post.author_id == v.id:
        return {"error": "You can't award yourself."}, 403

    existing_award = g.db.query(AwardRelationship).filter(
        and_(
            AwardRelationship.submission_id == post.id,
            AwardRelationship.user_id == v.id,
            AwardRelationship.kind == kind
        )
    ).first()

    if existing_award and kind not in ALLOW_MULTIPLE:
        return {"error": "You can't give that award multiple times to the same post."}, 409

    post_award.submission_id = post.id
    #print(f"give award to pid {post_award.submission_id} ({post.id})")
    g.db.add(post_award)

    msg = f"@{v.username} has given your [post]({post.permalink}) the {AWARDS[kind]['title']} Award!"

    note = request.form.get("note", "")
    if note:
        msg += f"\n\n> {note}"

    send_notification(NOTIFICATIONS_ACCOUNT, post.author, msg)

    if kind in ACTIONS:
        ACTIONS[kind](post=post)

    return "", 204


@app.put("/comment/<cid>/awards")
@auth_required
@validate_formkey
def award_comment(cid, v):

    if v.is_suspended and v.unban_utc == 0:
        return {"error": "forbidden"}, 403

    kind = request.form.get("kind", "")

    if kind not in AWARDS:
        return {"error": "That award doesn't exist."}, 404

    comment_award = g.db.query(AwardRelationship).filter(
        and_(
            AwardRelationship.kind == kind,
            AwardRelationship.user_id == v.id,
            AwardRelationship.submission_id == None,
            AwardRelationship.comment_id == None
        )
    ).first()

    if not comment_award:
        return {"error": "You don't have that award."}, 404

    c = g.db.query(Comment).filter_by(id=cid).first()

    if not c or c.is_banned or c.deleted_utc > 0:
        return {"error": "That comment doesn't exist or has been deleted or removed."}, 404

    if c.author_id == v.id:
        return {"error": "You can't award yourself."}, 403

    existing_award = g.db.query(AwardRelationship).filter(
        and_(
            AwardRelationship.comment_id == c.id,
            AwardRelationship.user_id == v.id,
            AwardRelationship.kind == kind
        )
    ).first()

    if existing_award and kind not in ALLOW_MULTIPLE:
        return {"error": "You can't give that award multiple times to the same comment."}, 409

    comment_award.comment_id = c.id
    g.db.add(comment_award)

    msg = f"@{v.username} has given your [comment]({c.permalink}) the {AWARDS[kind]['title']} Award!"

    note = request.form.get("note", "")
    if note:
        msg += f"\n\n> {note}"

    send_notification(NOTIFICATIONS_ACCOUNT, c.author, msg)

    if kind in ACTIONS:
        ACTIONS[kind](comment=c)

    return "", 204

@app.get("/admin/user_award")
@auth_required
def admin_userawards_get(v):

    if v.admin_level < 6:
        abort(403)

    return render_template("admin/user_award.html", awards=list(AWARDS.values()), v=v)

@app.post("/admin/user_award")
@auth_required
@validate_formkey
def admin_userawards_post(v):

    if v.admin_level < 6:
        abort(403)

    u = get_user(request.form.get("username", '1'), graceful=False, v=v)

    awards = []
    notify_awards = {}

    latest = g.db.query(AwardRelationship).order_by(AwardRelationship.id.desc()).first()
    thing = latest.id

    for key, value in request.form.items():
        if key not in AWARDS:
            continue

        if value:

            if int(value) > 0:
                notify_awards[key] = int(value)

            for x in range(int(value)):
                thing += 1

                awards.append(AwardRelationship(
                    id=thing,
                    user_id=u.id,
                    kind=key
                ))

    g.db.bulk_save_objects(awards)
    text = "You were given the following awards:\n\n"

    for key, value in notify_awards.items():
        text += f" - **{value}** {AWARDS[key]['title']} {'Awards' if value != 1 else 'Award'}\n"

    send_notification(NOTIFICATIONS_ACCOUNT, u, text)

    return render_template("admin/user_award.html", awards=list(AWARDS.values()), v=v)
