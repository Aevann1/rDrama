from files.__main__ import app
from .get import *
from os import listdir, environ
from .const import * 

@app.template_filter("post_embed")
def post_embed(id, v):

	try: id = int(id)
	except: return None
	
	p = get_post(id, v, graceful=True)
	
	if p: return render_template("submission_listing.html", listing=[p], v=v)
	return ''

@app.context_processor
def inject_constants():
	return {"environ":environ, "SITE":SITE, "SITE_NAME":SITE_NAME, "SITE_FULL":SITE_FULL, "AUTOJANNY_ID":AUTOJANNY_ID, "NOTIFICATIONS_ID":NOTIFICATIONS_ID, "PUSHER_ID":PUSHER_ID, "CC":CC, "CC_TITLE":CC_TITLE, "listdir":listdir, "MOOSE_ID":MOOSE_ID, "AEVANN_ID":AEVANN_ID, "config":app.config.get, "DEFAULT_COLOR":DEFAULT_COLOR, "COLORS":COLORS, "toomuch_subs":toomuch_subs}