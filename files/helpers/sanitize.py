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
						'sub',
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
						'sub',
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
						]

def sanitize_marquee(tag, name, value):
	if name in allowed_attributes['*'] or name in ['direction', 'behavior', 'scrollamount']: return True

	if name in ['height', 'width']:
		try: value = int(value.replace('px', ''))
		except: return False
		if 0 < value <= 250: return True

	return False

allowed_attributes = {
		'*': ['href', 'style', 'src', 'class', 'title', 'rel', 'data-bs-original-name'],
		'marquee': sanitize_marquee}

allowed_protocols = ['http', 'https']

allowed_styles = ['color', 'background-color', 'font-weight', 'transform', '-webkit-transform']

def sanitize(sanitized, noimages=False):

	sanitized = sanitized.replace("\ufeff", "").replace("m.youtube.com", "youtube.com").replace("𒐪","")

	for i in re.finditer('https://i.imgur.com/(([^_]*?)\.(jpg|png|jpeg))', sanitized):
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
			link["target"] = "_blank"
			link["onclick"] = f"expandDesktopImage('{tag['data-src']}');"
			link["data-bs-toggle"] = "modal"
			link["data-bs-target"] = "#expandImageModal"

			tag.wrap(link)

	for tag in soup.find_all("a"):
		if tag.get("href"):
			tag["target"] = "_blank"
			if site not in tag["href"] and not tag["href"].startswith('/'): tag["rel"] = "nofollow noopener noreferrer"

			if re.match("https?://\S+", str(tag.string)):
				try: tag.string = tag["href"]
				except: tag.string = ""


	sanitized = str(soup)
	
	start = '&lt;s&gt;'
	end = '&lt;/s&gt;' 

	try:
		if not session.get("favorite_emojis"): session["favorite_emojis"] = {}
	except:
		pass

	if start in sanitized and end in sanitized and start in sanitized.split(end)[0] and end in sanitized.split(start)[1]: sanitized = sanitized.replace(start, '<span class="spoiler">').replace(end, '</span>')
	
	for i in re.finditer("[^a]>\s*(:!?\w+:\s*)+<\/", sanitized):
		old = i.group(0)
		if 'marseylong1' in old or 'marseylong2' in old or 'marseyllama1' in old or 'marseyllama2' in old: new = old.lower().replace(">", " class='mb-0'>")
		else: new = old.lower()
		for i in re.finditer('(?<!"):([^ ]{1,30}?):', new):
			emoji = i.group(1).lower()
			if emoji.startswith("!"):
				emoji = emoji[1:]
				if path.isfile(f'./files/assets/images/emojis/{emoji}.webp'):
					new = re.sub(f'(?<!"):!{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":!{emoji}:" title=":!{emoji}:" delay="0" class="bigemoji mirrored" src="http://{site}/assets/images/emojis/{emoji}.webp" >', new)
			
					if emoji in session["favorite_emojis"]: session["favorite_emojis"][emoji] += 1
					else: session["favorite_emojis"][emoji] = 1

			elif path.isfile(f'./files/assets/images/emojis/{emoji}.webp'):
				new = re.sub(f'(?<!"):{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":{emoji}:" title=":{emoji}:" delay="0" class="bigemoji" src="http://{site}/assets/images/emojis/{emoji}.webp" >', new)
					
				if emoji in session["favorite_emojis"]: session["favorite_emojis"][emoji] += 1
				else: session["favorite_emojis"][emoji] = 1

		sanitized = sanitized.replace(old, new)


	for i in re.finditer('(?<!"):([^ ]{1,30}?):', sanitized):
		emoji = i.group(1).lower()
		if emoji.startswith("!"):
			emoji = emoji[1:]
			if path.isfile(f'./files/assets/images/emojis/{emoji}.webp'):
				sanitized = re.sub(f'(?<!"):!{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":!{emoji}:" title=":!{emoji}:" delay="0" class="emoji mirrored" src="http://{site}/assets/images/emojis/{emoji}.webp">', sanitized)
		
				if emoji in session["favorite_emojis"]: session["favorite_emojis"][emoji] += 1
				else: session["favorite_emojis"][emoji] = 1

		elif path.isfile(f'./files/assets/images/emojis/{emoji}.webp'):
			sanitized = re.sub(f'(?<!"):{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":{emoji}:" title=":{emoji}:" delay="0" class="emoji" src="http://{site}/assets/images/emojis/{emoji}.webp">', sanitized)
				
			if emoji in session["favorite_emojis"]: session["favorite_emojis"][emoji] += 1
			else: session["favorite_emojis"][emoji] = 1


	sanitized = sanitized.replace("https://www.", "https://").replace("https://youtu.be/", "https://youtube.com/watch?v=").replace("https://music.youtube.com/watch?v=", "https://youtube.com/watch?v=").replace("https://open.spotify.com/", "https://open.spotify.com/embed/").replace("https://streamable.com/", "https://streamable.com/e/").replace("https://youtube.com/shorts/", "https://youtube.com/watch?v=").replace("https://mobile.twitter", "https://twitter").replace("https://m.facebook", "https://facebook").replace("https://m.wikipedia", "https://wikipedia").replace("https://m.youtube", "https://youtube")


	for i in re.finditer('" target="_blank">(https://youtube.com/watch\?v\=.*?)</a>', sanitized):
		url = i.group(1)
		replacing = f'<a href="{url}" rel="nofollow noopener noreferrer" target="_blank">{url}</a>'
		url = url.replace("watch?v=", "embed/").replace("&amp;t", "?start").replace("?t", "?start")
		url = re.sub('(\?start=([0-9]*?))s', r'\1', url)
		htmlsource = f'<iframe class="embedvid" loading="lazy" src="{url}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
		sanitized = sanitized.replace(replacing, htmlsource)
		
	for i in re.finditer('<a href="(https://streamable.com/e/.*?)"', sanitized):
		url = i.group(1)
		replacing = f'<a href="{url}" rel="nofollow noopener noreferrer" target="_blank">{url}</a>'
		htmlsource = f'<iframe class="embedvid" loading="lazy" src="{url}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
		sanitized = sanitized.replace(replacing, htmlsource)

	for i in re.finditer('<p>(https:.*?\.mp4)</p>', sanitized):
		sanitized = sanitized.replace(i.group(0), f'<p><video controls loop preload="metadata" class="embedvid"><source src="{i.group(1)}" type="video/mp4"></video>')

	for i in re.finditer('<a href="(https://open.spotify.com/embed/.*?)"', sanitized):
		url = i.group(1)
		replacing = f'<a href="{url}" rel="nofollow noopener noreferrer" target="_blank">{url}</a>'
		htmlsource = f'<iframe src="{url}" class="spotify" frameBorder="0" allowtransparency="true" allow="encrypted-media"></iframe>'
		sanitized = sanitized.replace(replacing, htmlsource)

	for rd in ["https://reddit.com/", "https://new.reddit.com/", "https://www.reddit.com/", "https://redd.it/"]:
		sanitized = sanitized.replace(rd, "https://old.reddit.com/")

	sanitized = sanitized.replace("old.reddit.com/gallery", "new.reddit.com/gallery")
	sanitized = re.sub(' (https:\/\/[^ <>]*)', r' <a target="_blank" rel="nofollow noopener noreferrer" href="\1">\1</a>', sanitized)
	sanitized = re.sub('<p>(https:\/\/[^ <>]*)', r'<p><a target="_blank" rel="nofollow noopener noreferrer" href="\1">\1</a></p>', sanitized)

	return sanitized

def filter_title(title):
	title = title.strip()
	title = title.replace("\n", "")
	title = title.replace("\r", "")
	title = title.replace("\t", "")

	title = bleach.clean(title, tags=[])

	for i in re.finditer('(?<!"):([^ ]{1,30}?):', title):
		emoji = i.group(1)

		if emoji.startswith("!"):
			emoji = emoji[1:]
			if path.isfile(f'./files/assets/images/emojis/{emoji}.webp'):
				title = re.sub(f'(?<!"):!{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":!{emoji}:" title=":!{emoji}:" delay="0" height=30 src="http://{site}/assets/images/emojis/{emoji}.webp" class="mirrored">', title)
				
		elif path.isfile(f'./files/assets/images/emojis/{emoji}.webp'):
			title = re.sub(f'(?<!"):{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":{emoji}:" title=":{emoji}:" delay="0" height=30 src="http://{site}/assets/images/emojis/{emoji}.webp">', title)
	
	if len(title) > 1500: abort(400)
	else: return title