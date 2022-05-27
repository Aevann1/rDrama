import bleach
from bs4 import BeautifulSoup
from bleach.css_sanitizer import CSSSanitizer
from bleach.linkifier import LinkifyFilter, build_url_re
from functools import partial
from .get import *
from os import path, environ
import re
from mistletoe import markdown
from json import loads, dump
from random import random, choice
import signal
import time
import requests

TLDS = ( # Original gTLDs and ccTLDs
	'ac','ad','ae','aero','af','ag','ai','al','am','an','ao','aq','ar','arpa','as','asia','at',
	'au','aw','ax','az','ba','bb','bd','be','bf','bg','bh','bi','biz','bj','bm','bn','bo','br',
	'bs','bt','bv','bw','by','bz','ca','cafe','cat','cc','cd','cf','cg','ch','ci','ck','cl',
	'cm','cn','co','com','coop','cr','cu','cv','cx','cy','cz','de','dj','dk','dm','do','dz','ec',
	'edu','ee','eg','er','es','et','eu','fi','fj','fk','fm','fo','fr','ga','gb','gd','ge','gf',
	'gg','gh','gi','gl','gm','gn','gov','gp','gq','gr','gs','gt','gu','gw','gy','hk','hm','hn',
	'hr','ht','hu','id','ie','il','im','in','info','int','io','iq','ir','is','it','je','jm','jo',
	'jobs','jp','ke','kg','kh','ki','km','kn','kp','kr','kw','ky','kz','la','lb','lc','li','lk',
	'lr','ls','lt','lu','lv','ly','ma','mc','md','me','mg','mh','mil','mk','ml','mm','mn','mo',
	'mobi','mp','mq','mr','ms','mt','mu','museum','mv','mw','mx','my','mz','na','name',
	'nc','ne','net','nf','ng','ni','nl','no','np','nr','nu','nz','om','org','pa','pe','pf','pg',
	'ph','pk','pl','pm','pn','post','pr','pro','ps','pt','pw','py','qa','re','ro','rs','ru','rw',
	'sa','sb','sc','sd','se','sg','sh','si','sj','sk','sl','sm','sn','so','social','sr','ss','st',
	'su','sv','sx','sy','sz','tc','td','tel','tf','tg','th','tj','tk','tl','tm','tn','to','tp',
	'tr','travel','tt','tv','tw','tz','ua','ug','uk','us','uy','uz','va','vc','ve','vg','vi','vn',
	'vu','wf','ws','xn','xxx','ye','yt','yu','za','zm','zw',
	# New gTLDs
	'club','florist','fun','gay','lgbt','lol','moe','monster','win','wtf','xyz',
	)

allowed_tags = ('b','blockquote','br','code','del','em','h1','h2','h3','h4','h5','h6','hr','i',
	'li','ol','p','pre','strong','sub','sup','table','tbody','th','thead','td','tr','ul',
	'marquee','a','span','ruby','rp','rt','spoiler','img','lite-youtube','video','source','audio')

allowed_styles = ['color', 'background-color', 'font-weight', 'text-align',]

def allowed_attributes(tag, name, value):

	if name == 'style': return True

	if tag == 'marquee':
		if name in ['direction', 'behavior', 'scrollamount']: return True
		if name in {'height', 'width'}:
			try: value = int(value.replace('px', ''))
			except: return False
			if 0 < value <= 250: return True
		return False
	
	if tag == 'a':
		if name == 'href' and '\\' not in value: return True
		if name == 'rel' and value == 'nofollow noopener noreferrer': return True
		if name == 'target' and value == '_blank': return True
		return False

	if tag == 'img':
		if name in ['src','data-src']: return is_safe_url(value)
		if name == 'loading' and value == 'lazy': return True
		if name == 'data-bs-toggle' and value == 'tooltip': return True
		if name in ['g','b'] and not value: return True
		if name in ['alt','title']: return True
		if name == 'referrpolicy' and value == 'no-referrer': return True
		return False

	if tag == 'lite-youtube':
		if name == 'params' and value.startswith('autoplay=1&modestbranding=1'): return True
		if name == 'videoid': return True
		return False

	if tag == 'video':
		if name == 'controls' and value == '': return True
		if name == 'preload' and value == 'none': return True
		return False

	if tag == 'source':
		if name == 'src': return is_safe_url(value)

	if tag == 'audio':
		if name == 'src': return is_safe_url(value)
		if name == 'controls' and value == '': return True
		if name == 'preload' and value == 'none': return True
		return False

	if tag == 'p':
		if name == 'class' and value == 'mb-0': return True
		return False

	if tag == 'span':
		if name == 'data-bs-toggle' and value == 'tooltip': return True
		if name == 'title': return True
		if name == 'alt': return True
		return False


url_re = build_url_re(tlds=TLDS, protocols=['http', 'https'])

def callback(attrs, new=False):
	if (None, "href") not in attrs:
		return # Incorrect <a> tag

	href = attrs[(None, "href")]

	# \ in href right after / makes most browsers ditch site hostname and allows for a host injection bypassing the check, see <a href="/\google.com">cool</a>
	if "\\" in href:
		attrs["_text"] = href # Laugh at this user
		del attrs[(None, "href")] # Make unclickable and reset harmful payload
		return attrs

	if not href.startswith('/') and not href.startswith(f'{SITE_FULL}/'):
		attrs[(None, "target")] = "_blank"
		attrs[(None, "rel")] = "nofollow noopener noreferrer"	

	return attrs


def handler(signum, frame):
	print("Timeout!", flush=True)
	raise Exception("Timeout")

def render_emoji(html, regexp, edit, marseys_used=set(), b=False):
	emojis = list(regexp.finditer(html))
	captured = set()

	for i in emojis:
		if i.group(0) in captured: continue
		captured.add(i.group(0))

		emoji = i.group(1).lower()
		attrs = ''
		if b: attrs += ' b'
		if not edit and len(emojis) <= 20 and random() < 0.0025 and ('marsey' in emoji or emoji in marseys_const2): attrs += ' g'

		old = emoji
		emoji = emoji.replace('!','').replace('#','')
		if emoji == 'marseyrandom': emoji = choice(marseys_const2)

		emoji_partial_pat = '<img loading="lazy" alt=":{0}:" src="{1}"{2}>'
		emoji_partial = '<img loading="lazy" data-bs-toggle="tooltip" alt=":{0}:" title=":{0}:" src="{1}"{2}>'
		emoji_html = None

		if emoji.endswith('pat'):
			if path.isfile(f"files/assets/images/emojis/{emoji.replace('pat','')}.webp"):
				emoji_html = f'<span data-bs-toggle="tooltip" alt=":{old}:" title=":{old}:"><img src="/assets/images/hand.webp">{emoji_partial_pat.format(old, f"/e/{emoji[:-3]}.webp", attrs)}</span>'
			elif emoji.startswith('@'):
				if u := get_user(emoji[1:-3], graceful=True):
					emoji_html = f'<span data-bs-toggle="tooltip" alt=":{old}:" title=":{old}:"><img src="/assets/images/hand.webp">{emoji_partial_pat.format(old, f"/pp/{u.id}", attrs)}</span>'
		elif path.isfile(f'files/assets/images/emojis/{emoji}.webp'):
			emoji_html = emoji_partial.format(old, f'/e/{emoji}.webp', attrs)


		if emoji_html:
			marseys_used.add(emoji)
			html = re.sub(f'(?<!"){i.group(0)}', emoji_html, html)
	return html


def sanitize(sanitized, alert=False, comment=False, edit=False):

	signal.signal(signal.SIGALRM, handler)
	signal.alarm(1)

	if '```' not in sanitized and '<pre>' not in sanitized:
		sanitized = linefeeds_regex.sub(r'\1\n\n\2', sanitized)

	sanitized = image_regex.sub(r'\1![](\2)\4', sanitized)

	sanitized = image_check_regex.sub(r'\1', sanitized)

	sanitized = link_fix_regex.sub(r'\2https://\3', sanitized)

	sanitized = markdown(sanitized)

	sanitized = strikethrough_regex.sub(r'<del>\1</del>', sanitized)

	sanitized = sanitized.replace('‎','').replace('​','').replace("\ufeff", "").replace("𒐪","")

	if alert:
		captured = []
		for i in mention_regex2.finditer(sanitized):
			if i.group(0) in captured: continue
			captured.append(i.group(0))

			u = get_user(i.group(1), graceful=True)
			if u:
				sanitized = sanitized.replace(i.group(0), f'''<p><a href="/id/{u.id}"><img loading="lazy" src="/pp/{u.id}">@{u.username}</a>''')
	else:
		sanitized = reddit_regex.sub(r'\1<a href="https://old.reddit.com/\2" rel="nofollow noopener noreferrer">/\2</a>', sanitized)

		sanitized = sub_regex.sub(r'\1<a href="/\2">/\2</a>', sanitized)

		for i in mention_regex.finditer(sanitized):
			u = get_user(i.group(2), graceful=True)

			if u and (not (g.v and g.v.any_block_exists(u)) or g.v.admin_level > 1):
				sanitized = sanitized.replace(i.group(0), f'''{i.group(1)}<a href="/id/{u.id}"><img loading="lazy" src="/pp/{u.id}">@{u.username}</a>''', 1)


	sanitized = imgur_regex.sub(r'\1_d.webp?maxwidth=9999&fidelity=high', sanitized)

	soup = BeautifulSoup(sanitized, 'lxml')

	for tag in soup.find_all("img"):
		if tag.get("src") and not tag["src"].startswith('/pp/'):
			tag["loading"] = "lazy"
			tag["data-src"] = tag["src"]
			tag["src"] = "/assets/images/loading.webp"
			tag['alt'] = f'![]({tag["data-src"]})'
			tag['referrerpolicy'] = "no-referrer"

	for tag in soup.find_all("a"):
		if tag.get("href") and fishylinks_regex.fullmatch(str(tag.string)):
			tag.string = tag["href"]


	sanitized = str(soup)
	
	sanitized = spoiler_regex.sub(r'<spoiler>\1</spoiler>', sanitized)
	
	marseys_used = set()

	emojis = list(emoji_regex.finditer(sanitized))
	if len(emojis) > 20: edit = True

	captured = []
	for i in emojis:
		if i.group(0) in captured: continue
		captured.append(i.group(0))

		old = i.group(0)
		if 'marseylong1' in old or 'marseylong2' in old or 'marseyllama1' in old or 'marseyllama2' in old: new = old.lower().replace(">", " class='mb-0'>")
		else: new = old.lower()

		new = render_emoji(new, emoji_regex2, edit, marseys_used, True)

		sanitized = sanitized.replace(old, new)

	emojis = list(emoji_regex2.finditer(sanitized))
	if len(emojis) > 20: edit = True

	sanitized = render_emoji(sanitized, emoji_regex2, edit, marseys_used)

	for rd in ["://reddit.com", "://new.reddit.com", "://www.reddit.com", "://redd.it", "://libredd.it", "://teddit.net"]:
		sanitized = sanitized.replace(rd, "://old.reddit.com")

	sanitized = normalize_url(sanitized)

	sanitized = sanitized.replace('&amp;','&')

	if "https://youtube.com/watch?v=" in sanitized: sanitized = sanitized.replace("?t=", "&t=")

	captured = []
	for i in youtube_regex.finditer(sanitized):
		if i.group(0) in captured: continue
		captured.append(i.group(0))

		params = parse_qs(urlparse(i.group(2)).query)
		t = params.get('t', params.get('start', [0]))[0]
		if isinstance(t, str): t = t.replace('s','')

		htmlsource = f'{i.group(1)}<lite-youtube videoid="{i.group(3)}" params="autoplay=1&modestbranding=1'
		if t: htmlsource += f'&start={t}'
		htmlsource += '"></lite-youtube>'

		sanitized = sanitized.replace(i.group(0), htmlsource)

	sanitized = video_sub_regex.sub(r'\1<video controls preload="none"><source src="\2"></video>', sanitized)
	sanitized = audio_sub_regex.sub(r'\1<audio controls preload="none" src="\2"></audio>', sanitized)

	if comment:
		for marsey in g.db.query(Marsey).filter(Marsey.name.in_(marseys_used)).all():
			marsey.count += 1
			g.db.add(marsey)

	if '#fortune' in sanitized:
		sanitized = sanitized.replace('#fortune', '')
		sanitized += '\n\n<p>' + choice(FORTUNE_REPLIES) + '</p>'

	if '#8ball' in sanitized:
		(b8txt, b8knd) = choice(EIGHTBALL_REPLIES)
		b8color = EIGHTBALL_COLORS[b8knd]
		sanitized = sanitized.replace('#8ball', '')
		sanitized += '\n\n<p><span style="font-weight: bold; color: %s;">The 8-Ball Says: %s</span></p>' % (b8color, b8txt)

	if '#factcheck' in sanitized:
		sanitized = sanitized.replace('#factcheck', '')
		sanitized += '\n\n<p>' + choice(FACTCHECK_REPLIES) + '</p>'

	sanitized = sanitized.replace('<p></p>', '')
	sanitized = utm_regex.sub('', sanitized)
	sanitized = utm_regex2.sub('', sanitized)


	sanitized = sanitized.replace('<html><body>','').replace('</body></html>','')

	css_sanitizer = CSSSanitizer(allowed_css_properties=allowed_styles)
	sanitized = bleach.Cleaner(tags=allowed_tags,
								attributes=allowed_attributes,
								protocols=['http', 'https'],
								css_sanitizer=css_sanitizer,
								filters=[partial(LinkifyFilter, skip_tags=["pre"], 
									parse_email=False, callbacks=[callback], url_re=url_re)]
								).clean(sanitized)

	soup = BeautifulSoup(sanitized, 'lxml')

	links = soup.find_all("a")

	domain_list = set()

	for link in links:

		href = link.get("href")
		if not href: continue
		
		url = urlparse(href)
		domain = url.netloc
		url_path = url.path
		domain_list.add(domain+url_path)

		parts = domain.split(".")
		for i in range(len(parts)):
			new_domain = parts[i]
			for j in range(i + 1, len(parts)):
				new_domain += "." + parts[j]
				domain_list.add(new_domain)

	bans = g.db.query(BannedDomain.domain).filter(BannedDomain.domain.in_(list(domain_list))).all()

	if bans: abort(403, description=f"Remove the banned domains {bans} and try again!")


	signal.alarm(0)

	return sanitized





def allowed_attributes_emojis(tag, name, value):

	if tag == 'img':
		if name == 'src' and value.startswith('/') and '\\' not in value: return True
		if name == 'loading' and value == 'lazy': return True
		if name == 'data-bs-toggle' and value == 'tooltip': return True
		if name == 'g' and not value: return True
		if name in ['alt','title']: return True

	if tag == 'span':
		if name == 'data-bs-toggle' and value == 'tooltip': return True
		if name == 'title': return True
		if name == 'alt': return True
		return False
	return False


def filter_emojis_only(title, edit=False, graceful=False):

	signal.signal(signal.SIGALRM, handler)
	signal.alarm(1)
	
	title = title.replace('‎','').replace('​','').replace("\ufeff", "").replace("𒐪","").replace("\n", "").replace("\r", "").replace("\t", "").replace("&", "&amp;").replace('<','&lt;').replace('>','&gt;').replace('"', '&quot;').replace("'", "&#039;").strip()

	title = render_emoji(title, emoji_regex3, edit)

	title = strikethrough_regex.sub(r'<del>\1</del>', title)

	title = bleach.clean(title, tags=['img','del','span'], attributes=allowed_attributes_emojis, protocols=['http','https'])

	signal.alarm(0)

	if len(title) > 1500 and not graceful: abort(400)
	else: return title

def normalize_url(url):
	url = url.replace("nitter.net", "twitter.com") \
			 .replace("old.reddit.com/gallery", "reddit.com/gallery") \
			 .replace("https://youtu.be/", "https://youtube.com/watch?v=") \
			 .replace("https://music.youtube.com/watch?v=", "https://youtube.com/watch?v=") \
			 .replace("https://youtube.com/shorts/", "https://youtube.com/watch?v=") \
			 .replace("https://mobile.twitter", "https://twitter") \
			 .replace("https://m.facebook", "https://facebook") \
			 .replace("m.wikipedia.org", "wikipedia.org") \
			 .replace("https://m.youtube", "https://youtube") \
			 .replace("https://www.youtube", "https://youtube") \
			 .replace("https://www.twitter", "https://twitter") \
			 .replace("https://www.instagram", "https://instagram") \
			 .replace("https://www.tiktok", "https://tiktok")

	if "/i.imgur.com/" in url:
		url = url.replace(".png", ".webp").replace(".jpg", ".webp").replace(".jpeg", ".webp")
	elif "/media.giphy.com/" in url or "/c.tenor.com/" in url:
		url = url.replace(".gif", ".webp")
	elif "/i.ibb.co/" in url:
		url = url.replace(".png", ".webp").replace(".jpg", ".webp")\
				 .replace(".jpeg", ".webp").replace(".gif", ".webp")

	return url
