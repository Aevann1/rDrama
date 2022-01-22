from files.__main__ import app
from .get import *
from os import listdir, environ
from .const import * 

@app.template_filter("full_link")
def full_link(url):

	return f"{SITE_FULL}{url}"

@app.template_filter("app_config")
def app_config(x):
	return app.config.get(x)

@app.template_filter("post_embed")
def post_embed(id, v):

	try: id = int(id)
	except: return None
	
	p = get_post(id, v, graceful=True)
	
	return render_template("submission_listing.html", listing=[p], v=v)

@app.context_processor
def inject_constants():
	return {"environ":environ, "SITE_NAME":SITE_NAME, "AUTOJANNY_ID":AUTOJANNY_ID, "NOTIFICATIONS_ID":NOTIFICATIONS_ID, "PUSHER_ID":PUSHER_ID, "CC":CC, "CC_TITLE":CC_TITLE, "listdir":listdir, "MOOSE_ID":MOOSE_ID}
