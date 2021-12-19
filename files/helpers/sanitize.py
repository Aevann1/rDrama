import bleach
from bs4 import BeautifulSoup
from bleach.linkifier import LinkifyFilter
from functools import partial
from .get import *
from os import path, environ
import re

site = environ.get("DOMAIN").strip()

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

	if name in ['height', 'width']:
		try: value = int(value.replace('px', ''))
		except: return False
		if 0 < value <= 250: return True

	return False

allowed_attributes = {
		'*': ['href', 'style', 'src', 'class', 'title'],
		'marquee': sanitize_marquee}

allowed_protocols = ['http', 'https']

allowed_styles = ['color', 'background-color', 'font-weight', 'transform', '-webkit-transform']

def sanitize(sanitized, noimages=False):

	sanitized = sanitized.replace("\ufeff", "").replace("𒐪","").replace("<script","")

	for i in re.finditer('https://i\.imgur\.com/(([^_]*?)\.(jpg|png|jpeg))', sanitized):
		sanitized = sanitized.replace(i.group(1), i.group(2) + "_d." + i.group(3) + "?maxwidth=9999")

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

	soup = BeautifulSoup(sanitized, features="html.parser")

	for tag in soup.find_all("img"):

		if tag.get("src") and "pp20" not in tag.get("class", ""):

			if site not in tag["src"] and not tag["src"].startswith('/'): tag["rel"] = "nofollow noopener noreferrer"
			tag["class"] = "in-comment-image"
			tag["loading"] = "lazy"
			tag["data-src"] = tag["src"]
			tag["src"] = "/assets/images/loading.webp"

			link = soup.new_tag("a")
			link["href"] = tag["data-src"]
			if site not in link["href"] and not link["href"].startswith('/'): link["rel"] = "nofollow noopener noreferrer"
			link["onclick"] = f"expandDesktopImage('{tag['data-src']}');"
			link["data-bs-toggle"] = "modal"
			link["data-bs-target"] = "#expandImageModal"

			tag.wrap(link)

	for tag in soup.find_all("a"):
		if tag.get("href"):
			if site not in tag["href"] and not tag["href"].startswith('/'):
				tag["target"] = "_blank"
				tag["rel"] = "nofollow noopener noreferrer"

			if re.match("https?://\S+", str(tag.string)):
				try: tag.string = tag["href"]
				except: tag.string = ""


	sanitized = str(soup)
	
	sanitized = re.sub('\|\|(.*?)\|\|', r'<span class="spoiler">\1</span>', sanitized)
	
	for i in re.finditer("[^a]>\s*(:[!#]{0,2}\w+:\s*)+<\/", sanitized):
		old = i.group(0)
		if 'marseylong1' in old or 'marseylong2' in old or 'marseyllama1' in old or 'marseyllama2' in old: new = old.lower().replace(">", " class='mb-0'>")
		else: new = old.lower()
		for i in re.finditer('(?<!"):([!#A-Za-z0-9]{1,30}?):', new):
			emoji = i.group(1).lower()
			if emoji.startswith("#!") or emoji.startswith("!#"):
				classes = 'class="emoji-lg mirrored" '
				remoji = emoji[2:]
			elif emoji.startswith("#"):
				classes = 'class="emoji-lg" '
				remoji = emoji[1:]
			elif emoji.startswith("!"):
				classes = 'height=60 class="emoji-md mirrored" '
				remoji = emoji[1:]
			else:
				classes = 'height=60 class="emoji-md" '
				remoji = emoji

			if path.isfile(f'files/assets/images/emojis/{remoji}.webp'):
				new = re.sub(f'(?<!"):{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":{emoji}:" title=":{emoji}:" delay="0" {classes}src="/assets/images/emojis/{remoji}.webp" >', new, flags=re.I)
					
		sanitized = sanitized.replace(old, new)


	for i in re.finditer('(?<!"):([!A-Za-z0-9]{1,30}?):', sanitized):
		emoji = i.group(1).lower()
		if emoji.startswith("!"):
			emoji = emoji[1:]
			if path.isfile(f'files/assets/images/emojis/{emoji}.webp'):
				sanitized = re.sub(f'(?<!"):!{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":!{emoji}:" title=":!{emoji}:" delay="0" height=30 class="emoji mirrored" src="/assets/images/emojis/{emoji}.webp">', sanitized, flags=re.I)

		elif path.isfile(f'files/assets/images/emojis/{emoji}.webp'):
			sanitized = re.sub(f'(?<!"):{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":{emoji}:" title=":{emoji}:" delay="0" height=30 class="emoji" src="/assets/images/emojis/{emoji}.webp">', sanitized, flags=re.I)

	sanitized = sanitized.replace("https://www.", "https://").replace("https://youtu.be/", "https://youtube.com/watch?v=").replace("https://music.youtube.com/watch?v=", "https://youtube.com/watch?v=").replace("https://open.spotify.com/", "https://open.spotify.com/embed/").replace("https://streamable.com/", "https://streamable.com/e/").replace("https://youtube.com/shorts/", "https://youtube.com/watch?v=").replace("https://mobile.twitter", "https://twitter").replace("https://m.facebook", "https://facebook").replace("m.wikipedia.org", "wikipedia.org").replace("https://m.youtube", "https://youtube")

	if "https://youtube.com/watch?v=" in sanitized: sanitized = sanitized.replace("?t=", "&t=")

	for i in re.finditer('" target="_blank">(https://youtube\.com/watch\?v\=(.*?))</a>', sanitized):
		url = i.group(1)
		yt_id = i.group(2).split('&')[0].split('%')[0]
		replacing = f'<a href="{url}" rel="nofollow noopener noreferrer" target="_blank">{url}</a>'

		params = parse_qs(urlparse(url.replace('&amp;','&')).query)
		t = params.get('t', params.get('start', [0]))[0]
		if isinstance(t, str): t = t.replace('s','')

		htmlsource = f'<lite-youtube videoid="{yt_id}" params="controls=0&modestbranding=1'
		if t: htmlsource += f'&start={t}'
		htmlsource += '"></lite-youtube>'

		sanitized = sanitized.replace(replacing, htmlsource)
	for i in re.finditer('>(https://.*?\.(mp4|webm|mov))</a></p>', sanitized):
		sanitized = sanitized.replace(f'<p><a href="{i.group(1)}" rel="nofollow noopener noreferrer" target="_blank">{i.group(1)}</a></p>', f'<p><video controls preload="none" class="embedvid"><source src="{i.group(1)}" type="video/{i.group(2)}"></video>')
	for i in re.finditer('<p>(https:.*?\.(mp4|webm))</p>', sanitized):
		sanitized = sanitized.replace(i.group(0), f'<p><video controls preload="none" class="embedvid"><source src="{i.group(1)}" type="video/{i.group(2)}"></video>')

	for rd in ["https://reddit.com/", "https://new.reddit.com/", "https://www.reddit.com/", "https://redd.it/"]:
		sanitized = sanitized.replace(rd, "https://old.reddit.com/")

	sanitized = sanitized.replace("old.reddit.com/gallery", "new.reddit.com/gallery")
	sanitized = re.sub(' (https:\/\/[^ <>]*)', r' <a target="_blank" rel="nofollow noopener noreferrer" href="\1">\1</a>', sanitized)
	sanitized = re.sub('<p>(https:\/\/[^ <>]*)', r'<p><a target="_blank" rel="nofollow noopener noreferrer" href="\1">\1</a></p>', sanitized)

	return sanitized

def filter_emojis_only(title):

	title = title.replace('<','').replace('>','').replace("\n", "").replace("\r", "").replace("\t", "").strip()

	title = bleach.clean(title, tags=[])

	for i in re.finditer('(?<!"):([!A-Za-z0-9]{1,30}?):', title):
		emoji = i.group(1).lower()

		if emoji.startswith("!"):
			emoji = emoji[1:]
			if path.isfile(f'files/assets/images/emojis/{emoji}.webp'):
				title = re.sub(f'(?<!"):!{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":!{emoji}:" title=":!{emoji}:" delay="0" height=30 src="/assets/images/emojis/{emoji}.webp" class="emoji mirrored">', title, flags=re.I)
				
		elif path.isfile(f'files/assets/images/emojis/{emoji}.webp'):
			title = re.sub(f'(?<!"):{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":{emoji}:" title=":{emoji}:" delay="0" height=30 class="emoji" src="/assets/images/emojis/{emoji}.webp">', title, flags=re.I)
	
	if len(title) > 1500: abort(400)
	else: return title