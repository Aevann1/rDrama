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
	
	return render_template("submission_listing.html", listing=[p], v=v)

@app.template_filter("favorite_emojis")
def favorite_emojis(x):
	str = ""
	emojis = sorted(x.items(), key=lambda x: x[1], reverse=True)[:25]
	for k, v in emojis:
		str += f'<button class="btn m-1 px-0 emoji2" onclick="getEmoji(\'{k}\')" style="background: None!important; width:60px; overflow: hidden; border: none;" data-bs-toggle="tooltip" title=":{k}:" delay:="0"><img loading="lazy" width=50 src="/assets/images/emojis/{k}.webp" alt="{k}-emoji"></button>'
	return str

@app.context_processor
def inject_constants():
	constants = [c for c in dir(const) if not c.startswith("_")]
	return {c:getattr(const, c) for c in constants}