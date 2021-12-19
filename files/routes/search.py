from files.helpers.wrappers import *
import re
from sqlalchemy import *
from flask import *
from files.__main__ import app


query_regex=re.compile("(\w+):(\S+)")
valid_params=[
	'author',
	'domain',
	'over18'
]

def searchparse(text):


	criteria = {x[0]:x[1] for x in query_regex.findall(text)}

	for x in criteria:
		if x in valid_params:
			text = text.replace(f"{x}:{criteria[x]}", "")

	text=text.strip()

	if text:
		criteria['q']=text

	return criteria





@app.get("/search/posts")
@auth_desired
def searchposts(v):


	query = request.values.get("q", '').strip()

	page = max(1, int(request.values.get("page", 1)))

	sort = request.values.get("sort", "new").lower()
	t = request.values.get('t', 'all').lower()

	criteria=searchparse(query)












	posts = g.db.query(Submission.id)
	
	if not (v and v.paid_dues): posts = posts.filter(Submission.club == False)
	
	if not (v and v.admin_level > 1): posts = posts.filter(Submission.private == False)
	
	if 'q' in criteria:
		words=criteria['q'].split()
		words=[Submission.title.ilike('%'+x+'%') for x in words]
		words=tuple(words)
		posts=posts.filter(*words)
		
	if 'over18' in criteria: posts = posts.filter(Submission.over_18==True)

	if 'author' in criteria:
		author = get_user(criteria['author'])
		if not author.is_private: posts = posts.filter(Submission.author_id == author.id)

	if 'domain' in criteria:
		domain=criteria['domain']
		posts=posts.filter(
			or_(
				Submission.url.ilike("https://"+domain+'/%'),
				Submission.url.ilike("https://"+domain+'/%'),
				Submission.url.ilike("https://"+domain),
				Submission.url.ilike("https://"+domain),
				Submission.url.ilike("https://www."+domain+'/%'),
				Submission.url.ilike("https://www."+domain+'/%'),
				Submission.url.ilike("https://www."+domain),
				Submission.url.ilike("https://www."+domain),
				Submission.url.ilike("https://old." + domain + '/%'),
				Submission.url.ilike("https://old." + domain + '/%'),
				Submission.url.ilike("https://old." + domain),
				Submission.url.ilike("https://old." + domain)
				)
			)

	if not (v and v.admin_level > 1): posts = posts.filter(Submission.deleted_utc == 0, Submission.is_banned == False)

	if v and v.admin_level > 1: pass
	elif v:
		blocking = [x[0] for x in g.db.query(
			UserBlock.target_id).filter_by(
			user_id=v.id).all()]
		blocked = [x[0] for x in g.db.query(
			UserBlock.user_id).filter_by(
			target_id=v.id).all()]

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

	if sort == "new":
		posts = posts.order_by(Submission.created_utc.desc())
	elif sort == "old":
		posts = posts.order_by(Submission.created_utc.asc())
	elif sort == "controversial":
		posts = posts.order_by(-1 * Submission.upvotes * Submission.downvotes * Submission.downvotes)
	elif sort == "top":
		posts = posts.order_by(Submission.downvotes - Submission.upvotes)
	elif sort == "bottom":
		posts = posts.order_by(Submission.upvotes - Submission.downvotes)
	elif sort == "comments":
		posts = posts.order_by(Submission.comment_count.desc())

	total = posts.count()

	posts = posts.offset(25 * (page - 1)).limit(26).all()

	ids = [x[0] for x in posts]




	next_exists = (len(ids) > 25)
	ids = ids[:25]

	posts = get_posts(ids, v=v)

	if v and v.admin_level>3 and "domain" in criteria:
		domain=criteria['domain']
		domain_obj=get_domain(domain)
	else:
		domain=None
		domain_obj=None

	if request.headers.get("Authorization"): return {"total":total, "data":[x.json for x in posts]}
	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}search.html",
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


	query = request.values.get("q", '').strip()

	try: page = max(1, int(request.values.get("page", 1)))
	except: page = 1

	sort = request.values.get("sort", "new").lower()
	t = request.values.get('t', 'all').lower()

	criteria=searchparse(query)




	comments = g.db.query(Comment.id).filter(Comment.parent_submission != None)

	if 'q' in criteria:
		words=criteria['q'].split()
		words=[Comment.body_html.ilike('%'+x+'%') for x in words]
		words=tuple(words)
		comments=comments.filter(*words)

	if 'over18' in criteria: comments = comments.filter(Comment.over_18==True)

	if 'author' in criteria:
		author = get_user(criteria['author'])
		if not author.is_private: comments = comments.filter(Comment.author_id == author.id)

	if not(v and v.admin_level > 1): comments = comments.filter(Comment.deleted_utc == 0, Comment.is_banned == False)

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



	if sort == "new":
		comments = comments.order_by(Comment.created_utc.desc())
	elif sort == "old":
		comments = comments.order_by(Comment.created_utc.asc())
	elif sort == "controversial":
		comments = comments.order_by(-1 * Comment.upvotes * Comment.downvotes * Comment.downvotes)
	elif sort == "top":
		comments = comments.order_by(Comment.realupvotes.desc())
	elif sort == "bottom":
		comments = comments.order_by(Comment.upvotes - Comment.downvotes)

	total = comments.count()

	comments = comments.offset(25 * (page - 1)).limit(26).all()
	ids = [x[0] for x in comments]




	next_exists = (len(ids) > 25)
	ids = ids[:25]

	comments = get_comments(ids, v=v)

	if request.headers.get("Authorization"): return {"total":total, "data":[x.json for x in comments]}
	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}search_comments.html", v=v, query=query, total=total, page=page, comments=comments, sort=sort, t=t, next_exists=next_exists)


@app.get("/search/users")
@auth_desired
def searchusers(v):


	query = request.values.get("q", '').strip()

	page = max(1, int(request.values.get("page", 1)))
	sort = request.values.get("sort", "new").lower()
	t = request.values.get('t', 'all').lower()
	term=query.lstrip('@')
	term=term.replace('\\','')
	term=term.replace('_','\_')
	
	users=g.db.query(User).filter(User.username.ilike(f'%{term}%'))
	
	users=users.order_by(User.username.ilike(term).desc(), User.stored_subscriber_count.desc())
	
	total=users.count()
	
	users=[x for x in users.offset(25 * (page-1)).limit(26)]
	next_exists=(len(users)>25)
	users=users[:25]
	
	
	if request.headers.get("Authorization"): return [x.json for x in users]
	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}search_users.html", v=v, query=query, total=total, page=page, users=users, sort=sort, t=t, next_exists=next_exists)