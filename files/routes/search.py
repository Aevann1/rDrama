from files.helpers.wrappers import *
import re
from sqlalchemy import *
from flask import *
from files.__main__ import app, cache
import random

query_regex=re.compile("(\w+):(\S+)")
valid_params=[
	'author',
	'domain',
	'over18'
]

def searchparse(text):

	#takes test in filter:term format and returns data

	criteria = {x[0]:x[1] for x in query_regex.findall(text)}

	for x in criteria:
		if x in valid_params:
			text = text.replace(f"{x}:{criteria[x]}", "")

	text=text.strip()

	if text:
		criteria['q']=text

	return criteria


def searchlisting(criteria, v=None, page=1, t="None", sort="top", b=None):

	posts = g.db.query(Submission).options(
				lazyload('*')
			).join(
				Submission.submission_aux,
			).join(
				Submission.author
			)
	
	if 'q' in criteria:
		words=criteria['q'].split()
		words=[SubmissionAux.title.ilike('%'+x+'%') for x in words]
		words=tuple(words)
		posts=posts.filter(*words)
		
	if 'over18' in criteria:
		posts = posts.filter(Submission.over_18==True)

	if 'author' in criteria:
		posts=posts.filter(
				Submission.author_id==get_user(criteria['author']).id,
				User.is_private==False,
			)

	if 'domain' in criteria:
		domain=criteria['domain']
		posts=posts.filter(
			or_(
				SubmissionAux.url.ilike("https://"+domain+'/%'),
				SubmissionAux.url.ilike("https://"+domain+'/%'),
				SubmissionAux.url.ilike("https://"+domain),
				SubmissionAux.url.ilike("https://"+domain),
				SubmissionAux.url.ilike("https://www."+domain+'/%'),
				SubmissionAux.url.ilike("https://www."+domain+'/%'),
				SubmissionAux.url.ilike("https://www."+domain),
				SubmissionAux.url.ilike("https://www."+domain),
				SubmissionAux.url.ilike("https://old." + domain + '/%'),
				SubmissionAux.url.ilike("https://old." + domain + '/%'),
				SubmissionAux.url.ilike("https://old." + domain),
				SubmissionAux.url.ilike("https://old." + domain)
				)
			)

	if not(v and v.admin_level >= 3):
		posts = posts.filter(
			Submission.deleted_utc == 0,
			Submission.is_banned == False,
			)

	if v and v.admin_level >= 4:
		pass
	elif v:
		blocking = g.db.query(
			UserBlock.target_id).filter_by(
			user_id=v.id).subquery()
		blocked = g.db.query(
			UserBlock.user_id).filter_by(
			target_id=v.id).subquery()

		posts = posts.filter(
			Submission.author_id.notin_(blocking),
			Submission.author_id.notin_(blocked),
		)

	if t:
		now = int(time.time())
		if t == 'hour':
			cutoff = now - 3600
		elif t == 'day':
			cutoff = now - 86400
		elif t == 'week':
			cutoff = now - 604800
		elif t == 'month':
			cutoff = now - 2592000
		elif t == 'year':
			cutoff = now - 31536000
		else:
			cutoff = 0
		posts = posts.filter(Submission.created_utc >= cutoff)

	posts=posts.options(
		contains_eager(Submission.submission_aux),
		contains_eager(Submission.author),
		)

	if sort == "new":
		posts = posts.order_by(Submission.created_utc.desc()).all()
	elif sort == "old":
		posts = posts.order_by(Submission.created_utc.asc()).all()
	elif sort == "controversial":
		posts = sorted(posts.all(), key=lambda x: x.score_disputed, reverse=True)
	elif sort == "top":
		posts = sorted(posts.all(), key=lambda x: x.score, reverse=True)
	elif sort == "bottom":
		posts = sorted(posts.all(), key=lambda x: x.score)
	elif sort == "comments":
		posts = posts.order_by(Submission.comment_count.desc()).all()
	elif sort == "random":
		posts = posts.all()
		posts = random.sample(posts, k=len(posts))
	else:
		abort(400)

	total = len(posts)

	firstrange = 25 * (page - 1)
	secondrange = firstrange+26
	posts = posts[firstrange:secondrange]

	return total, [x.id for x in posts]


def searchcommentlisting(criteria, v=None, page=1, t="None", sort="top"):

	comments = g.db.query(Comment).options(lazyload('*')).filter(Comment.parent_submission != None).join(Comment.comment_aux)

	if 'q' in criteria:
		words=criteria['q'].split()
		words=[CommentAux.body.ilike('%'+x+'%') for x in words]
		words=tuple(words)
		comments=comments.filter(*words)

	if not(v and v.admin_level >= 3):
		comments = comments.filter(
			Comment.deleted_utc == 0,
			Comment.is_banned == False)

	if t:
		now = int(time.time())
		if t == 'hour':
			cutoff = now - 3600
		elif t == 'day':
			cutoff = now - 86400
		elif t == 'week':
			cutoff = now - 604800
		elif t == 'month':
			cutoff = now - 2592000
		elif t == 'year':
			cutoff = now - 31536000
		else:
			cutoff = 0
		comments = comments.filter(Comment.created_utc >= cutoff)

	comments=comments.options(contains_eager(Comment.comment_aux))

	if sort == "new":
		comments = comments.order_by(Comment.created_utc.desc()).all()
	elif sort == "old":
		comments = comments.order_by(Comment.created_utc.asc()).all()
	elif sort == "controversial":
		comments = sorted(comments.all(), key=lambda x: x.score_disputed, reverse=True)
	elif sort == "top":
		comments = sorted(comments.all(), key=lambda x: x.score, reverse=True)
	elif sort == "bottom":
		comments = sorted(comments.all(), key=lambda x: x.score)

	total = len(list(comments))
	firstrange = 25 * (page - 1)
	secondrange = firstrange+26
	comments = comments[firstrange:secondrange]
	return total, [x.id for x in comments]

@app.get("/search/posts")
@auth_desired
def searchposts(v):


	query = request.args.get("q", '').strip()

	page = max(1, int(request.args.get("page", 1)))

	sort = request.args.get("sort", "top").lower()
	t = request.args.get('t', 'all').lower()

	criteria=searchparse(query)
	total, ids = searchlisting(criteria, v=v, page=page, t=t, sort=sort)

	next_exists = (len(ids) == 26)
	ids = ids[:25]

	posts = get_posts(ids, v=v)

	if v and v.admin_level>3 and "domain" in criteria:
		domain=criteria['domain']
		domain_obj=get_domain(domain)
	else:
		domain=None
		domain_obj=None

	if request.headers.get("Authorization"): return {"data":[x.json for x in posts]}
	else: return render_template("search.html",
						   v=v,
						   query=query,
						   total=total,
						   page=page,
						   listing=posts,
						   sort=sort,
						   t=t,
						   next_exists=next_exists,
						   domain=domain,
						   domain_obj=domain_obj
						   )

@app.get("/search/comments")
@auth_desired
def searchcomments(v):


	query = request.args.get("q", '').strip()

	try: page = max(1, int(request.args.get("page", 1)))
	except: page = 1

	sort = request.args.get("sort", "top").lower()
	t = request.args.get('t', 'all').lower()

	criteria=searchparse(query)
	total, ids = searchcommentlisting(criteria, v=v, page=page, t=t, sort=sort)

	next_exists = (len(ids) == 26)
	ids = ids[:25]

	comments = get_comments(ids, v=v)

	if request.headers.get("Authorization"): return [x.json for x in comments]
	else: return render_template("search_comments.html", v=v, query=query, total=total, page=page, comments=comments, sort=sort, t=t, next_exists=next_exists)


@app.get("/search/users")
@auth_desired
def searchusers(v):


	query = request.args.get("q", '').strip()

	page = max(1, int(request.args.get("page", 1)))
	sort = request.args.get("sort", "top").lower()
	t = request.args.get('t', 'all').lower()
	term=query.lstrip('@')
	term=term.replace('\\','')
	term=term.replace('_','\_')
	
	users=g.db.query(User).filter(User.username.ilike(f'%{term}%'))
	
	users=users.order_by(User.username.ilike(term).desc(), User.stored_subscriber_count.desc())
	
	total=users.count()
	
	users=[x for x in users.offset(25 * (page-1)).limit(26)]
	next_exists=(len(users)==26)
	users=users[:25]
	
	
	if request.headers.get("Authorization"): return [x.json for x in users]
	else: return render_template("search_users.html", v=v, query=query, total=total, page=page, users=users, sort=sort, t=t, next_exists=next_exists)