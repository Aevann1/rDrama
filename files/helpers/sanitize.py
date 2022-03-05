import bleach
from bs4 import BeautifulSoup
from bleach.linkifier import LinkifyFilter
from functools import partial
from .get import *
from os import path, environ
import re
from mistletoe import markdown
from json import loads, dump
from random import random, choice
import signal
import time

allowed_tags = tags = ['b',
						'blockquote',
						'br',
						'code',
						'del',
						'em',
						'h1',
						'h2',
						'h3',
						'h4',
						'h5',
						'h6',
						'hr',
						'i',
						'li',
						'ol',
						'p',
						'pre',
						'strong',
						'sup',
						'table',
						'tbody',
						'th',
						'thead',
						'td',
						'tr',
						'ul',
						'marquee',
						'a',
						'img',
						'span',
						'ruby',
						'rp',
						'rt',
						]

no_images = ['b',
						'blockquote',
						'br',
						'code',
						'del',
						'em',
						'h1',
						'h2',
						'h3',
						'h4',
						'h5',
						'h6',
						'hr',
						'i',
						'li',
						'ol',
						'p',
						'pre',
						'strong',
						'sup',
						'table',
						'tbody',
						'th',
						'thead',
						'td',
						'tr',
						'ul',
						'marquee',
						'a',
						'span',
						'ruby',
						'rp',
						'rt',
						]

def sanitize_marquee(tag, name, value):
	if name in allowed_attributes['*'] or name in ['direction', 'behavior', 'scrollamount']: return True

	if name in {'height', 'width'}:
		try: value = int(value.replace('px', ''))
		except: return False
		if 0 < value <= 250: return True

	return False

allowed_attributes = {
		'*': ['href', 'style', 'src', 'class', 'title', 'loading'],
		'marquee': sanitize_marquee}

allowed_protocols = ['http', 'https']

allowed_styles = ['color', 'background-color', 'font-weight', 'text-align']


def handler(signum, frame):
	print("Forever is over!")
	raise Exception("end of time")


def sanitize(sanitized, noimages=False, alert=False, comment=False, edit=False):

	signal.signal(signal.SIGALRM, handler)
	signal.alarm(1)
	
	sanitized = markdown(sanitized)

	sanitized = sanitized.replace("\ufeff", "").replace("𒐪","").replace("<script","").replace("script>","").replace('‎','')

	if alert:
		captured = []
		for i in mention_regex2.finditer(sanitized):
			if i.group(0) in captured: continue
			captured.append(i.group(0))

			u = get_user(i.group(1), graceful=True)
			if u:
				sanitized = sanitized.replace(i.group(0), f'''<p><a href="/id/{u.id}"><img loading="lazy" src="/uid/{u.id}/pic" class="pp20">@{u.username}</a>''', 1)
	else:
		sanitized = reddit_regex.sub(r'\1<a href="https://old.reddit.com/\2" rel="nofollow noopener noreferrer">/\2</a>', sanitized)

		sanitized = sub_regex.sub(r'\1<a href="/\2" rel="nofollow noopener noreferrer">/\2</a>', sanitized)

		captured = []
		for i in mention_regex.finditer(sanitized):
			if i.group(0) in captured: continue
			captured.append(i.group(0))

			u = get_user(i.group(2), graceful=True)

			if u and (not g.v.any_block_exists(u) or g.v.admin_level > 1):
				if noimages:
					sanitized = sanitized.replace(i.group(0), f'{i.group(1)}<a href="/id/{u.id}">@{u.username}</a>', 1)
				else:
					sanitized = sanitized.replace(i.group(0), f'''{i.group(1)}<a href="/id/{u.id}"><img loading="lazy" src="/uid/{u.id}/pic" class="pp20">@{u.username}</a>''', 1)


	sanitized = imgur_regex.sub(r'\1_d.webp?maxwidth=9999&fidelity=high', sanitized)

	if noimages:
		sanitized = bleach.Cleaner(tags=no_images,
									attributes=allowed_attributes,
									protocols=allowed_protocols,
									styles=allowed_styles,
									filters=[partial(LinkifyFilter,
													skip_tags=["pre"],
													parse_email=False,
													)
											]
									).clean(sanitized)
	else:
		sanitized = bleach.Cleaner(tags=allowed_tags,
							attributes=allowed_attributes,
							protocols=['http', 'https'],
							styles=['color','font-weight','transform','-webkit-transform'],
							filters=[partial(LinkifyFilter,
											skip_tags=["pre"],
											parse_email=False,
											)
									]
							).clean(sanitized)

	soup = BeautifulSoup(sanitized, 'lxml')

	for tag in soup.find_all("img"):
		if tag.get("src") and tag.get("class") != ['pp20']:
			tag["class"] = "in-comment-image"
			tag["loading"] = "lazy"
			tag["data-src"] = tag["src"]
			tag["src"] = "/static/assets/images/loading.webp"
			tag['alt'] = f'![]({tag["data-src"]})'
			tag["onclick"] = "expandDesktopImage(this.src);"
			tag["data-bs-toggle"] = "modal"
			tag["data-bs-target"] = "#expandImageModal"
			tag['referrerpolicy'] = "no-referrer"

	for tag in soup.find_all("a"):
		if tag.get("href"):
			if not tag["href"].startswith(SITE_FULL) and not tag["href"].startswith('/') and not tag["href"].startswith(SITE_FULL2):
				tag["target"] = "_blank"
				tag["rel"] = "nofollow noopener noreferrer"

			if fishylinks_regex.fullmatch(str(tag.string)):
				try: tag.string = tag["href"]
				except: tag.string = ""



	sanitized = str(soup)
	
	sanitized = spoiler_regex.sub(r'<span class="spoiler">\1</span>', sanitized)
	
	if comment: marseys_used = set()

	emojis = list(emoji_regex.finditer(sanitized))
	if len(emojis) > 20: edit = True

	captured = []
	for i in emojis:
		if i.group(0) in captured: continue
		captured.append(i.group(0))

		old = i.group(0)
		if 'marseylong1' in old or 'marseylong2' in old or 'marseyllama1' in old or 'marseyllama2' in old: new = old.lower().replace(">", " class='mb-0'>")
		else: new = old.lower()
		
		captured2 = []
		for i in emoji_regex2.finditer(new):
			if i.group(0) in captured2: continue
			captured2.append(i.group(0))

			emoji = i.group(1).lower()
			if emoji.startswith("#!") or emoji.startswith("!#"):
				classes = 'emoji-lg mirrored'
				remoji = emoji[2:]
			elif emoji.startswith("#"):
				classes = 'emoji-lg'
				remoji = emoji[1:]
			elif emoji.startswith("!"):
				classes = 'emoji-md mirrored'
				remoji = emoji[1:]
			else:
				classes = 'emoji-md'
				remoji = emoji

			if not edit and random() < 0.0025 and ('marsey' in emoji or emoji in marseys_const): classes += ' golden'

			if remoji == 'marseyrandom': remoji = choice(marseys_const)

			if path.isfile(f'files/assets/images/emojis/{remoji}.webp'):
				new = re.sub(f'(?<!"):{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":{emoji}:" title=":{emoji}:" class="{classes}" src="/e/{remoji}.webp">', new, flags=re.I|re.A)
				if comment: marseys_used.add(emoji)
					
		sanitized = sanitized.replace(old, new)

	emojis = list(emoji_regex3.finditer(sanitized))
	if len(emojis) > 20: edit = True

	captured = []
	for i in emojis:
		if i.group(0) in captured: continue
		captured.append(i.group(0))

		emoji = i.group(1).lower().replace('#','')
		if emoji.startswith("!"):
			emoji = emoji[1:]
			classes = 'emoji mirrored'
			if not edit and random() < 0.0025 and ('marsey' in emoji or emoji in marseys_const): classes += ' golden'

			old = emoji
			if emoji == 'marseyrandom': emoji = choice(marseys_const)
			else: emoji = old

			if path.isfile(f'files/assets/images/emojis/{emoji}.webp'):
				sanitized = re.sub(f'(?<!"):{i.group(1).lower()}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":!{old}:" title=":!{old}:" class="{classes}" src="/e/{emoji}.webp">', sanitized, flags=re.I|re.A)
				if comment: marseys_used.add(emoji)
		else:
			classes = 'emoji'
			if not edit and random() < 0.0025 and ('marsey' in emoji or emoji in marseys_const): classes += ' golden'
			
			old = emoji
			if emoji == 'marseyrandom': emoji = choice(marseys_const)
			else: emoji = old

			if path.isfile(f'files/assets/images/emojis/{emoji}.webp'):
				sanitized = re.sub(f'(?<!"):{i.group(1).lower()}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":{old}:" title=":{old}:" class="{classes}" src="/e/{emoji}.webp">', sanitized, flags=re.I|re.A)
				if comment: marseys_used.add(emoji)

	sanitized = sanitized.replace("https://youtu.be/", "https://youtube.com/watch?v=").replace("https://music.youtube.com/watch?v=", "https://youtube.com/watch?v=").replace("https://streamable.com/", "https://streamable.com/e/").replace("https://youtube.com/shorts/", "https://youtube.com/watch?v=").replace("https://mobile.twitter", "https://twitter").replace("https://m.facebook", "https://facebook").replace("m.wikipedia.org", "wikipedia.org").replace("https://m.youtube", "https://youtube").replace("https://www.youtube", "https://youtube")

	if "https://youtube.com/watch?v=" in sanitized: sanitized = sanitized.replace("?t=", "&t=")

	captured = []
	for i in youtube_regex.finditer(sanitized):
		if i.group(0) in captured: continue
		captured.append(i.group(0))

		url = i.group(1)
		yt_id = i.group(2).split('&')[0].split('%')[0]
		replacing = f'<a href="{url}" rel="nofollow noopener noreferrer" target="_blank">{url}</a>'

		params = parse_qs(urlparse(url.replace('&amp;','&')).query)
		t = params.get('t', params.get('start', [0]))[0]
		if isinstance(t, str): t = t.replace('s','')

		htmlsource = f'<lite-youtube videoid="{yt_id}" params="autoplay=1&modestbranding=1'
		if t: htmlsource += f'&start={t}'
		htmlsource += '"></lite-youtube>'

		sanitized = sanitized.replace(replacing, htmlsource)

	for rd in ["://reddit.com", "://new.reddit.com", "://www.reddit.com", "://redd.it", "://libredd.it"]:
		sanitized = sanitized.replace(rd, "://old.reddit.com")

	sanitized = sanitized.replace("old.reddit.com/gallery", "reddit.com/gallery")


	sanitized = unlinked_regex.sub(r'\1<a href="\2" rel="nofollow noopener noreferrer" target="_blank">\2</a>', sanitized)

	if not noimages:
		sanitized = video_regex.sub(r'<p><video controls preload="none" class="embedvid"><source src="\1" type="video/mp4"></video>', sanitized)

	if comment:
		for marsey in g.db.query(Marsey).filter(Marsey.name.in_(marseys_used)).all():
			marsey.count += 1
			g.db.add(marsey)

	signal.alarm(0)

	return sanitized

def handler2(signum, frame):
	print("Forever is over!")
	raise Exception("end of time")

def filter_emojis_only(title, edit=False, graceful=False):

	signal.signal(signal.SIGALRM, handler2)
	signal.alarm(1)
	
	title = title.replace("<script","").replace("script>","").replace("&", "&amp;").replace('<','&lt;').replace('>','&gt;').replace('"', '&quot;').replace("'", "&#039;").replace("\ufeff", "").replace("𒐪","").replace('‎','').replace("\n", "").replace("\r", "").replace("\t", "").strip()

	title = bleach.clean(title, tags=[])

	emojis = list(emoji_regex4.finditer(title))
	if len(emojis) > 20: edit = True

	captured = []
	for i in emojis:
		if i.group(0) in captured: continue
		captured.append(i.group(0))

		emoji = i.group(1).lower()

		if emoji.startswith("!"):
			emoji = emoji[1:]
			classes = 'emoji mirrored'
			if not edit and random() < 0.0025 and ('marsey' in emoji or emoji in marseys_const): classes += ' golden'

			old = emoji
			if emoji == 'marseyrandom': emoji = choice(marseys_const)
			else: emoji = old

			if path.isfile(f'files/assets/images/emojis/{emoji}.webp'):
				title = re.sub(f'(?<!"):!{old}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":!{old}:" title=":!{old}:" src="/e/{emoji}.webp" class="{classes}">', title, flags=re.I|re.A)

		else:
			classes = 'emoji'
			if not edit and random() < 0.0025 and ('marsey' in emoji or emoji in marseys_const): classes += ' golden'

			old = emoji
			if emoji == 'marseyrandom': emoji = choice(marseys_const)
			else: emoji = old

			if path.isfile(f'files/assets/images/emojis/{emoji}.webp'):
				title = re.sub(f'(?<!"):{old}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":{old}:" title=":{old}:" class="{classes}" src="/e/{emoji}.webp">', title, flags=re.I|re.A)

	title = strikethrough_regex.sub(r'<del>\1</del>', title)

	signal.alarm(0)

	if len(title) > 1500 and not graceful: abort(400)
	else: return title