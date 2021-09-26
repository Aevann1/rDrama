import bleach
from bs4 import BeautifulSoup
from bleach.linkifier import LinkifyFilter
from urllib.parse import ParseResult, urlunparse, urlparse
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
	'*': ['href', 'style', 'src', 'class', 'title', 'rel', 'data-bs-original-name']
	}

_allowed_protocols = [
	'http', 
	'https'
	]

_allowed_styles =[
	'color',
	'font-weight'
]

# filter to make all links show domain on hover

def a_modify(attrs, whatever):

	raw_url=attrs.get((None, "href"), None)
	if raw_url:
		parsed_url = urlparse(raw_url)

		domain = parsed_url.netloc
		attrs[(None, "target")] = "_blank"
		if domain and not domain.endswith(domain):
			attrs[(None, "rel")] = "nofollow noopener noreferrer"

			# Force https for all external links in comments
			# (Website already forces its own https)
			new_url = ParseResult(scheme="https",
								  netloc=parsed_url.netloc,
								  path=parsed_url.path,
								  params=parsed_url.params,
								  query=parsed_url.query,
								  fragment=parsed_url.fragment)

			attrs[(None, "href")] = urlunparse(new_url)

	return attrs


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
													callbacks=[a_modify]
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
											callbacks=[a_modify]
											)
									]
							).clean(sanitized)

	#soupify
	soup = BeautifulSoup(sanitized, features="html.parser")

	#img elements - embed
	for tag in soup.find_all("img"):

		url = tag.get("src", "")
		if not url: continue

		if "profile-pic-20" not in tag.get("class", ""):
			#print(tag.get('class'))
			# set classes and wrap in link

			tag["rel"] = "nofollow noopener noreferrer"
			tag["style"] = "max-height: 100px; max-width: 100%;"
			tag["class"] = "in-comment-image rounded-sm my-2"
			tag["loading"] = "lazy"

			link = soup.new_tag("a")
			link["href"] = tag["src"]
			link["rel"] = "nofollow noopener noreferrer"
			link["target"] = "_blank"

			link["onclick"] = f"expandDesktopImage('{tag['src']}');"
			link["data-bs-toggle"] = "modal"
			link["data-bs-target"] = "#expandImageModal"

			tag.wrap(link)

	#disguised link preventer
	for tag in soup.find_all("a"):

		if re.match("https?://\S+", str(tag.string)):
			try:
				tag.string = tag["href"]
			except:
				tag.string = ""

	#clean up tags in code
	for tag in soup.find_all("code"):
		tag.contents=[x.string for x in tag.contents if x.string]

	#whatever else happens with images, there are only two sets of classes allowed
	for tag in soup.find_all("img"):
		if 'profile-pic-20' not in tag.attrs.get("class",""):
			tag.attrs['class']="in-comment-image rounded-sm my-2"

	#table format
	for tag in soup.find_all("table"):
		tag.attrs['class']="table table-striped"

	for tag in soup.find_all("thead"):
		tag.attrs['class']="bg-primary text-white"


	sanitized = str(soup)

	
	start = '&lt;s&gt;'
	end = '&lt;/s&gt;' 

	try:
		if not session.get("favorite_emojis"): session["favorite_emojis"] = {}
	except:
		pass

	if start in sanitized and end in sanitized and start in sanitized.split(end)[0] and end in sanitized.split(start)[1]: 			sanitized = sanitized.replace(start, '<span class="spoiler">').replace(end, '</span>')
	
	for i in re.finditer('<p>:([^ ]{1,30}?):</p>', sanitized):
		emoji = i.group(1).lower()
		if path.isfile(f'./files/assets/images/emojis/{emoji}.webp'):
			sanitized = sanitized.replace(f'<p>:{emoji}:</p>', f'<p style="margin-bottom:0;"><img loading="lazy" data-bs-toggle="tooltip" alt=":{emoji}:" title=":{emoji}:" delay="0" height=60 src="https://{site}/assets/images/emojis/{emoji}.webp"></p>')

			try:
				if emoji in session["favorite_emojis"]: session["favorite_emojis"][emoji] += 1
				else: session["favorite_emojis"][emoji] = 1
			except:
				pass

	for i in re.finditer('\w*(?<!"):([^ ]{1,30}?):', sanitized):
		emoji = i.group(1).lower()
		if path.isfile(f'./files/assets/images/emojis/{emoji}.webp'):
			sanitized = re.sub(f'\w*(?<!"):{emoji}:', f'<img loading="lazy" data-bs-toggle="tooltip" alt=":{emoji}:" title=":{emoji}:" delay="0" height=30 src="https://{site}/assets/images/emojis/{emoji}.webp">', sanitized)

			try:
				if emoji in session["favorite_emojis"]: session["favorite_emojis"][emoji] += 1
				else: session["favorite_emojis"][emoji] = 1
			except:
				pass


	sanitized = sanitized.replace("https://www.", "https://").replace("https://youtu.be/", "https://youtube.com/watch?v=").replace("https://music.youtube.com/watch?v=", "https://youtube.com/watch?v=").replace("https://open.spotify.com/", "https://open.spotify.com/embed/").replace("https://streamable.com/", "https://streamable.com/e/").replace("https://youtube.com/shorts/", "https://youtube.com/watch?v=").replace("https://mobile.twitter", "https://twitter").replace("https://m.facebook", "https://facebook").replace("https://m.wikipedia", "https://wikipedia").replace("https://m.youtube", "https://youtube")


	for i in re.finditer('" target="_blank">(https://youtube.com/watch\?v\=.*?)</a>', sanitized):
		url = i.group(1)
		replacing = f'<a href="{url}" target="_blank">{url}</a>'
		htmlsource = f'<div style="padding-top:5px; padding-bottom: 10px;"><iframe style="max-width:100%" frameborder="0" src="{url}?controls=0"></iframe></div>'
		sanitized = sanitized.replace(replacing, htmlsource.replace("watch?v=", "embed/"))

	for i in re.finditer('<a href="(https://streamable.com/e/.*?)"', sanitized):
		url = i.group(1)
		replacing = f'<a href="{url}" target="_blank">{url}</a>'
		htmlsource = f'<div style="padding-top:5px; padding-bottom: 10px;"><iframe style="max-width:100%" frameborder="0" src="{url}?controls=0"></iframe></div>'
		sanitized = sanitized.replace(replacing, htmlsource)

	for i in re.finditer('<a href="(https://open.spotify.com/embed/.*?)"', sanitized):
		url = i.group(1)
		replacing = f'<a href="{url}" target="_blank">{url}</a>'
		htmlsource = f'<iframe src="{url}" width="100%" height="80" frameBorder="0" allowtransparency="true" allow="encrypted-media"></iframe>'
		sanitized = sanitized.replace(replacing, htmlsource)

	for rd in ["https://reddit.com/", "https://new.reddit.com/", "https://www.reddit.com/", "https://redd.it/"]:
		sanitized = sanitized.replace(rd, "https://old.reddit.com/")
	
	sanitized = re.sub(' (https:\/\/[^ <>]*)', r' <a target="_blank"  rel="nofollow noopener noreferrer" href="\1">\1</a>', sanitized)
	sanitized = re.sub('<p>(https:\/\/[^ <>]*)', r'<p><a target="_blank"  rel="nofollow noopener noreferrer" href="\1">\1</a></p>', sanitized)

	return sanitized
