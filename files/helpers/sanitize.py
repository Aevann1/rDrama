import bleach
from bs4 import BeautifulSoup
from bleach.linkifier import LinkifyFilter
from functools import partial
from .get import *
from os import path, environ
import re

site = environ.get("DOMAIN").strip()

_allowed_tags = tags = ['b',
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

_allowed_attributes = {
	'*': ['href', 'style', 'src', 'class', 'title', 'rel', 'data-bs-original-name', 'direction']
	}

_allowed_protocols = [
	'http', 
	'https'
	]

_allowed_styles =[
	'color',
	'font-weight',
	'transform',
	'-webkit-transform',
]

def sanitize(sanitized, noimages=False):

	sanitized = sanitized.replace("\ufeff", "").replace("m.youtube.com", "youtube.com")

	for i in re.finditer('https://i.imgur.com/(([^_]*?)\.(jpg|png|jpeg))', sanitized):
		sanitized = sanitized.replace(i.group(1), i.group(2) + "_d." + i.group(3) + "?maxwidth=9999")

	if noimages:
		sanitized = bleach.Cleaner(tags=no_images,
									attributes=_allowed_attributes,
									protocols=_allowed_protocols,
									styles=_allowed_styles,
									filters=[partial(LinkifyFilter,
													skip_tags=["pre"],
													parse_email=False,
													)
											]
									).clean(sanitized)
	else:
		sanitized = bleach.Cleaner(tags=_allowed_tags,
							attributes=_allowed_attributes,
							protocols=_allowed_protocols,
							styles=_allowed_styles,
							filters=[partial(LinkifyFilter,
											skip_tags=["pre"],
											parse_email=False,
											)
									]
							).clean(sanitized)

	soup = BeautifulSoup(sanitized, features="html.parser")

	for tag in soup.find_all("img"):

		if tag.get("src", "") and "profile-pic-20" not in tag.get("class", ""):

			tag["rel"] = "nofollow noopener noreferrer"
			tag["class"] = "in-comment-image"
			tag["loading"] = "lazy"
			tag["data-src"] = tag["src"]
			tag["src"] = ""

			link = soup.new_tag("a")
			link["href"] = tag["src"]
			link["rel"] = "nofollow noopener noreferrer"
			link["target"] = "_blank"

			link["onclick"] = f"expandDesktopImage('{tag['data-src']}');"
			link["data-bs-toggle"] = "modal"
			link["data-bs-target"] = "#expandImageModal"

			tag.wrap(link)

	for tag in soup.find_all("a"):

		tag["target"] = "_blank"
		if site not in tag["href"]: tag["rel"] = "nofollow noopener noreferrer"

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
		if 'marseylong' in old: new = old.lower().replace(">", " style='margin-bottom:0 !important'>")
		else: new = old.lower()
		for i in re.finditer('(?<!"):([^ ]{1,30}?):', new):
			emoji = i.group(1).lower()
			if emoji.startswith("!"):
				emoji = emoji[1:]
				if path.isfile(f'./files/assets/images/emojis/{emoji}.webp'):
					new = re.sub(f'(?<!"):!{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":!{emoji}:" title=":!{emoji}:" delay="0" class="bigemoji mirrored" src="https://{site}/assets/images/emojis/{emoji}.webp" >', new)
			
					if emoji in session["favorite_emojis"]: session["favorite_emojis"][emoji] += 1
					else: session["favorite_emojis"][emoji] = 1

			elif path.isfile(f'./files/assets/images/emojis/{emoji}.webp'):
				new = re.sub(f'(?<!"):{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":{emoji}:" title=":{emoji}:" delay="0" class="bigemoji" src="https://{site}/assets/images/emojis/{emoji}.webp" >', new)
					
				if emoji in session["favorite_emojis"]: session["favorite_emojis"][emoji] += 1
				else: session["favorite_emojis"][emoji] = 1

		sanitized = sanitized.replace(old, new)


	for i in re.finditer('(?<!"):([^ ]{1,30}?):', sanitized):
		emoji = i.group(1).lower()
		if emoji.startswith("!"):
			emoji = emoji[1:]
			if path.isfile(f'./files/assets/images/emojis/{emoji}.webp'):
				sanitized = re.sub(f'(?<!"):!{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":!{emoji}:" title=":!{emoji}:" delay="0" class="emoji mirrored" src="https://{site}/assets/images/emojis/{emoji}.webp">', sanitized)
		
				if emoji in session["favorite_emojis"]: session["favorite_emojis"][emoji] += 1
				else: session["favorite_emojis"][emoji] = 1

		elif path.isfile(f'./files/assets/images/emojis/{emoji}.webp'):
			sanitized = re.sub(f'(?<!"):{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":{emoji}:" title=":{emoji}:" delay="0" class="emoji" src="https://{site}/assets/images/emojis/{emoji}.webp">', sanitized)
				
			if emoji in session["favorite_emojis"]: session["favorite_emojis"][emoji] += 1
			else: session["favorite_emojis"][emoji] = 1


	sanitized = sanitized.replace("https://www.", "https://").replace("https://youtu.be/", "https://youtube.com/watch?v=").replace("https://music.youtube.com/watch?v=", "https://youtube.com/watch?v=").replace("https://open.spotify.com/", "https://open.spotify.com/embed/").replace("https://streamable.com/", "https://streamable.com/e/").replace("https://youtube.com/shorts/", "https://youtube.com/watch?v=").replace("https://mobile.twitter", "https://twitter").replace("https://m.facebook", "https://facebook").replace("https://m.wikipedia", "https://wikipedia").replace("https://m.youtube", "https://youtube")


	for i in re.finditer('" target="_blank">(https://youtube.com/watch\?v\=.*?)</a>', sanitized):
		url = i.group(1)
		replacing = f'<a href="{url}" rel="nofollow noopener noreferrer" target="_blank">{url}</a>'
		htmlsource = f'<iframe loading="lazy" data-src="{url}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
		sanitized = sanitized.replace(replacing, htmlsource.replace("watch?v=", "embed/"))

	for i in re.finditer('<a href="(https://streamable.com/e/.*?)"', sanitized):
		url = i.group(1)
		replacing = f'<a href="{url}" rel="nofollow noopener noreferrer" target="_blank">{url}</a>'
		htmlsource = f'<iframe loading="lazy" data-src="{url}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
		sanitized = sanitized.replace(replacing, htmlsource)

	for i in re.finditer('<p>(https:.*?\.mp4)</p>', sanitized):
		sanitized = sanitized.replace(i.group(0), f'<p><video controls loop preload="metadata" class="embedvid"><source data-src="{i.group(1)}" type="video/mp4"></video>')

	for i in re.finditer('<a href="(https://open.spotify.com/embed/.*?)"', sanitized):
		url = i.group(1)
		replacing = f'<a href="{url}" rel="nofollow noopener noreferrer" target="_blank">{url}</a>'
		htmlsource = f'<iframe data-src="{url}" class="spotify" frameBorder="0" allowtransparency="true" allow="encrypted-media"></iframe>'
		sanitized = sanitized.replace(replacing, htmlsource)

	for rd in ["https://reddit.com/", "https://new.reddit.com/", "https://www.reddit.com/", "https://redd.it/"]:
		sanitized = sanitized.replace(rd, "https://old.reddit.com/")
	
	sanitized = re.sub(' (https:\/\/[^ <>]*)', r' <a target="_blank"  rel="nofollow noopener noreferrer" href="\1">\1</a>', sanitized)
	sanitized = re.sub('<p>(https:\/\/[^ <>]*)', r'<p><a target="_blank"  rel="nofollow noopener noreferrer" href="\1">\1</a></p>', sanitized)

	return sanitized
