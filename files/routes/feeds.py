import html
from .front import frontlist
from datetime import datetime
from files.helpers.get import *
from yattag import Doc
from files.helpers.wrappers import *
from files.helpers.jinja2 import *

from files.__main__ import app

@app.get('/rss/<sort>/<t>')
@auth_required
def feeds_user(v=None, sort='hot', t='all'):

	page = int(request.values.get("page", 1))

	ids, next_exists = frontlist(
		sort=sort,
		page=page,
		t=t,
		v=None,
		)
	
	posts = get_posts(ids)

	domain = environ.get("DOMAIN").strip()

	doc, tag, text = Doc().tagtext()

	with tag("feed", ("xmlns:media","http://search.yahoo.com/mrss/"), xmlns="http://www.w3.org/2005/Atom",):
		with tag("title", type="text"):
			text(f"{sort} posts from {domain}")

		doc.stag("link", href=SITE_FULL + request.full_path)
		doc.stag("link", href=SITE_FULL)

		for post in posts:
			with tag("entry", ("xml:base", SITE_FULL + request.full_path)):
				with tag("title", type="text"):
					text(post.realtitle(None))

				with tag("id"):
					text(post.fullname)

				if (post.edited_utc):
					with tag("updated"):
						text(datetime.utcfromtimestamp(post.edited_utc).isoformat())

				with tag("published"):
					text(datetime.utcfromtimestamp(post.created_utc).isoformat())
				
				with tag("author"):
					with tag("name"):
						text(post.author_name)
					with tag("uri"):
						text(f'{SITE_FULL}/@{post.author_name}')

				doc.stag("link", href=post.permalink)

				image_url = post.thumb_url or post.embed_url or post.url

				doc.stag("media:thumbnail", url=image_url)

				if len(post.body_html):
					with tag("content", type="html"):
						doc.cdata(f'''<img alt="{post.realtitle(None)}" loading="lazy" src={image_url}><br>{post.realbody(None)}''')

	return Response( "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"+ doc.getvalue(), mimetype="application/xml")