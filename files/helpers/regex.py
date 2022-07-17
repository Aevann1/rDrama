import re
from .const import *
from random import choice, choices

if SITE_NAME == 'PCM':
	valid_username_chars = 'a-zA-Z0-9_\-А-я'
	valid_username_regex = re.compile("^[a-zA-Z0-9_\-А-я]{3,25}$", flags=re.A)
	mention_regex = re.compile('(^|\s|>)@(([a-zA-Z0-9_\-А-я]){3,25})(?![^<]*<\/(code|pre|a)>)', flags=re.A)
else:
	valid_username_chars = 'a-zA-Z0-9_\-'
	valid_username_regex = re.compile("^[a-zA-Z0-9_\-]{3,25}$", flags=re.A)
	mention_regex = re.compile('(^|\s|>)@(([a-zA-Z0-9_\-]){1,25})(?![^<]*<\/(code|pre|a)>)', flags=re.A)

valid_password_regex = re.compile("^.{8,100}$", flags=re.A)

marseyaward_body_regex = re.compile(">[^<\s+]|[^>\s+]<", flags=re.A)

marseyaward_title_regex = re.compile("( *<img[^>]+>)+", flags=re.A)

marsey_regex = re.compile("[a-z0-9]{1,30}", flags=re.A)

tags_regex = re.compile("[a-z0-9: ]{1,200}", flags=re.A)

valid_sub_regex = re.compile("^[a-zA-Z0-9_\-]{3,20}$", flags=re.A)

query_regex = re.compile("(\w+):(\S+)", flags=re.A)

poll_regex = re.compile("\s*\$\$([^\$\n]+)\$\$\s*", flags=re.A)
bet_regex = re.compile("\s*\$\$\$([^\$\n]+)\$\$\$\s*", flags=re.A)
choice_regex = re.compile("\s*&&([^\$\n]+)&&\s*", flags=re.A)

title_regex = re.compile("[^\w ]", flags=re.A)

based_regex = re.compile("based and (.{1,20}?)(-| )pilled", flags=re.I|re.A)

controversial_regex = re.compile('["> ](https:\/\/old\.reddit\.com/r/[a-zA-Z0-9_]{3,20}\/comments\/[\w\-.#&/=\?@%+]{5,250})["< ]', flags=re.A)

fishylinks_regex = re.compile("https?://\S+", flags=re.A)

spoiler_regex = re.compile('''\|\|(.+)\|\|''', flags=re.A)
reddit_regex = re.compile('(^|\s|<p>)\/?((r|u)\/(\w|-){3,25})(?![^<]*<\/(code|pre|a)>)', flags=re.A)
sub_regex = re.compile('(^|\s|<p>)\/?(h\/(\w|-){3,25})(?![^<]*<\/(code|pre|a)>)', flags=re.A)

strikethrough_regex = re.compile('(^|\s|>)~{1,2}([^~]+)~{1,2}', flags=re.A)

mute_regex = re.compile("/mute @([a-z0-9_\-]{3,25}) ([0-9])+", flags=re.A)

emoji_regex = re.compile(f"<p>\s*(:[!#@]{{0,3}}[{valid_username_chars}]+:\s*)+<\/p>", flags=re.A)
emoji_regex2 = re.compile(f'(?<!"):([!#@{valid_username_chars}]{{1,36}}?):', flags=re.A)
emoji_regex3 = re.compile(f'(?<!"):([!@{valid_username_chars}]{{1,35}}?):', flags=re.A)

snappy_url_regex = re.compile('<a href="(https?:\/\/.+?)".*?>(.+?)<\/a>', flags=re.A)
snappy_youtube_regex = re.compile('<lite-youtube videoid="(.+?)" params="autoplay=1', flags=re.A)

email_regex = re.compile('[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', flags=re.A|re.I)

utm_regex = re.compile('utm_[a-z]+=[a-z0-9_]+&', flags=re.A)
utm_regex2 = re.compile('[?&]utm_[a-z]+=[a-z0-9_]+', flags=re.A)

slur_regex = re.compile(single_words, flags=re.I|re.A)
slur_regex_upper = re.compile(single_words.upper(), flags=re.A)
torture_regex = re.compile('(^|\s)(i|me) ', flags=re.I|re.A)
torture_regex2 = re.compile("(^|\s)i'm ", flags=re.I|re.A)
torture_regex_exclude = re.compile('^\s*>', flags=re.A)


image_check_regex = re.compile(f'!\[\]\(((?!(https:\/\/([a-z0-9-]+\.)*({hosts})\/|\/)).*?)\)', flags=re.A)

video_sub_regex = re.compile(f'(<p>[^<]*)(https:\/\/([a-z0-9-]+\.)*({hosts})\/[\w:~,()\-.#&\/=?@%;+]*?\.(mp4|webm|mov))', flags=re.A)
audio_sub_regex = re.compile(f'(<p>[^<]*)(https:\/\/([a-z0-9-]+\.)*({hosts})\/[\w:~,()\-.#&\/=?@%;+]*?\.(mp3|wav|ogg|aac|m4a|flac))', flags=re.A)

imgur_regex = re.compile('(https:\/\/i\.imgur\.com\/[a-z0-9]+)\.(jpg|png|jpeg|webp)', flags=re.I|re.A)
giphy_regex = re.compile('(https:\/\/media\.giphy\.com\/media\/[a-z0-9]+\/giphy)\.gif', flags=re.I|re.A)

youtube_regex = re.compile('(<p>[^<]*)(https:\/\/youtube\.com\/watch\?v\=([a-z0-9-_]{5,20})[\w\-.#&/=\?@%+]*)', flags=re.I|re.A)

yt_id_regex = re.compile('[a-z0-9-_]{5,20}', flags=re.I|re.A)

image_regex = re.compile("(^|\s)(https:\/\/[\w\-.#&/=\?@%;+,:]{5,250}(\.png|\.jpg|\.jpeg|\.gif|\.webp)(\?[\w\-.#&/=\?@%;+,:]*)?)($|\s)", flags=re.I|re.A)

link_fix_regex = re.compile("(\[.*?\]\()(?!http|/)(.*?\))", flags=re.A)

css_regex = re.compile('https?:\/\/[\w:~,()\-.#&\/=?@%;+]*', flags=re.I|re.A)

procoins_li = (0,2500,5000,10000,25000,50000,125000,250000)

linefeeds_regex = re.compile("([^\n])\n([^\n])", flags=re.A)

greentext_regex = re.compile("(\n|^)>([^ >][^\n]*)", flags=re.A)

ascii_only_regex = re.compile("[ -~]+", flags=re.A)

twitter_to_nitter_regex = re.compile("https:\/\/twitter.com\/(\w{1,15}(\/status\/\d+[^/]*)?)", flags=re.A)

reddit_domain_regex = re.compile("(^|\s|\()https?:\/\/(reddit\.com|new\.reddit.com|www\.reddit.com|i\.reddit\.com|libredd\.it|teddit\.net)\/(r|u)\/", flags=re.A)

color_regex = re.compile("[a-z0-9]{6}", flags=re.A)

showmore_regex = re.compile("(.{3000,40000}?</p>)(<p>.*)", flags=re.A)

search_token_regex = re.compile('"([^"]*)"|(\S+)', flags=re.A)

git_regex = re.compile("ref: (refs/.+)", flags=re.A)

pronouns_regex = re.compile("([a-z]{2,5}|i)/[a-z]{2,5}", flags=re.A)

def sub_matcher(match, upper=False):
	repl = SLURS[match.group(0).lower()]
	return repl if not upper else repl.upper()

def sub_matcher_upper(match):
	return sub_matcher(match, upper=True)

def censor_slurs(body, logged_user):
	if not logged_user or logged_user == 'chat' or logged_user.slurreplacer:
		body = slur_regex_upper.sub(sub_matcher_upper, body)
		body = slur_regex.sub(sub_matcher, body)
	return body

def torture_ap(body, username):
	lines = body.splitlines(keepends=True)

	for i in range(len(lines)):
		if torture_regex_exclude.match(lines[i]):
			continue
		for k, l in AJ_REPLACEMENTS.items():
			lines[i] = lines[i].replace(k, l)
		lines[i] = torture_regex.sub(rf'\1@{username} ', lines[i])
		lines[i] = torture_regex2.sub(rf'\1@{username} is ', lines[i])

	return ''.join(lines)


commands = {
	"fortune": FORTUNE_REPLIES,
	"factcheck": FACTCHECK_REPLIES,
	"8ball": EIGHTBALL_REPLIES,
	"roll": range(1, 9999)
}

command_regex = re.compile("(\s|\n|^)#(fortune|factcheck|8ball|roll)", flags=re.A|re.I)

def command_regex_matcher(match, upper=False):
	result = str(choice(commands[match.group(2).lower()]))
	if match.group(2) == 'roll':
		color = tuple(choices(range(256), k=3))
		result = f'<b style="color:rgb{color}">Your roll: {result}</b>'
	return match.group(1) + result