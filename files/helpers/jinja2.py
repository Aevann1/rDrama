from files.__main__ import app
from .get import *
from files.helpers import const


@app.template_filter("full_link")
def full_link(url):

	return f"https://{app.config['SERVER_NAME']}{url}"

@app.template_filter("app_config")
def app_config(x):
	return app.config.get(x)

@app.template_filter("post_embed")
def post_embed(id, v):

	try: id = int(id)
	except: return None
	
	p = get_post(id, v, graceful=True)
	
	if v and v.oldsite: template = ''
	else: template = 'CHRISTMAS/'
	return render_template(f"{template}submission_listing.html", listing=[p], v=v)

@app.context_processor
def inject_constants():
	constants = [c for c in dir(const) if not c.startswith("_")]
	return {c:getattr(const, c) for c in constants}