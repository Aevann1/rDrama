from os import environ, listdir
import re
from copy import deepcopy
from json import loads
from files.__main__ import db_session
from files.classes.sub import Sub

SITE = environ.get("DOMAIN", '').strip()
SITE_NAME = environ.get("SITE_NAME", '').strip()
if SITE == "localhost": SITE_FULL = 'http://' + SITE
else: SITE_FULL = 'https://' + SITE

SITE_FULL2 = 'http://' + SITE

if SITE == 'pcmemes.net': CC = "SPLASH MOUNTAIN"
else: CC = "COUNTRY CLUB"
CC_TITLE = CC.title()

AJ_REPLACEMENTS = {
	' your ': " you're ",
	' to ': " too ", 

	' Your ': " You're ",
	' To ': " Too ",

	' YOUR ': " YOU'RE ",
	' TO ': " TOO ",
}

SLURS = {
	"retarded": "r-slurred",
	"retard": "r-slur",
	"tard": "r-slur",
	"gayfag": "gaystrag",
	"poorfag": "poorstrag",
	"richfag": "richstrag",
	"newfag": "newstrag",
	"oldfag": "oldstrag",
	"faggotry": "cute twinkry",
	"faggot": "cute twink",
	"fag": "cute twink",
	"pedophile": "libertarian",
	"pedo": "libertarian",
	"kill yourself": "keep yourself safe",
	"kys": "keep yourself safe",
	"kyle": "Kylie",
	"n1g": "BIPOC",
	"nlg": "BIPOC",
	"nig": "BIPOC",
	"n1gger": "BIPOC",
	"nlgger": "BIPOC",
	"nigger": "BIPOC",
	"rapist": "male feminist",
	"steve akins": "penny verity oaken",
	"trannie": "🚂🚃🚃",
	"tranny": "🚂🚃🚃",
	"troon": "🚂🚃🚃",
	"nonewnormal": "HorseDewormerAddicts",
	"kikery": "https://sciencedirect.com/science/article/abs/pii/S016028960600033X",
	"kike": "https://sciencedirect.com/science/article/abs/pii/S016028960600033X",
	"janny": "j-slur",
	"jannie": "j-slur",
	"janny": "j-slur",
	"latinos": "latinx",
	"latino": "latinx",
	"latinas": "latinx",
	"latina": "latinx",
	"hispanics": "latinx",
	"hispanic": "latinx",
	"uss liberty incident": "tragic accident aboard the USS Liberty",
	"lavon affair": "Lavon Misunderstanding",
	"shylock": "Israeli friend",
	"yid": "Israeli friend",
	"heeb": "Israeli friend",
	"sheeny": "Israeli friend",
	"sheenies": "Israeli friends",
	"hymie": "Israeli friend",
	"allah": "Allah (SWT)",
	"mohammad": "Prophet Mohammad (PBUH)",
	"muhammad": "Prophet Mohammad (PBUH)",
	"i hate marsey": "i love marsey",
	"dancing israelis": "i love Israel",
	"sodomite": "total dreamboat",
	"pajeet": "sexy Indian dude",
	"female": "birthing person",
	"landlord": "landchad",
	"tenant": "renthog",
	"renter": "rentoid",
	"autistic": "neurodivergent",
	"holohoax": "i tried to claim the Holocaust didn't happen because I am a pencil-dicked imbecile and the word filter caught me lol",
	"groomercord": "discord (actually a pretty cool service)",
	"pedocord": "discord (actually a pretty cool service)",
	"i hate carp": "i love Carp",
	"manlet": "little king",
	"gamer": "g*mer",
	"journalist": "journ*list",
	"journalism": "journ*lism",
	"wuhan flu": "SARS-CoV-2 syndemic",
	"china flu": "SARS-CoV-2 syndemic",
	"china virus": "SARS-CoV-2 syndemic",
	"kung flu": "SARS-CoV-2 syndemic",
	"elon musk": "rocket daddy",
	" elon ": " rocket daddy ",
	"fake and gay": "fake and straight",
}

single_words = "|".join([slur.lower() for slur in SLURS.keys()])

SLUR_REGEX = re.compile(rf"(?i)((?<=\s|>)|^)({single_words})((?=[\s<,.]|s[\s<,.])|$)", re.A)
SLUR_REGEX_UPPER = re.compile(rf"((?<=\s|>)|^)({single_words.upper()})((?=[\s<,.]|s[\s<,.])|$)", re.A)

def sub_matcher(match):
	return SLURS[match.group(0).lower()]

def sub_matcher_upper(match):
	return SLURS[match.group(0).lower()].upper()

def censor_slurs(body, logged_user):
	if not logged_user or logged_user.slurreplacer:
		body = SLUR_REGEX_UPPER.sub(sub_matcher_upper, body)
		body = SLUR_REGEX.sub(sub_matcher, body)
	return body

def torture_ap(body, username):
	body = SLUR_REGEX_UPPER.sub(sub_matcher_upper, body)
	body = SLUR_REGEX.sub(sub_matcher, body)
	for k, l in AJ_REPLACEMENTS.items(): body = body.replace(k, l)
	body = re.sub('(^|\s|\n)(i|me) ', rf'\1@{username} ', body, re.I|re.A)
	body = re.sub("(^|\s|\n)i'm ", rf'\1@{username} is ', body, re.I|re.A)
	return body


LONGPOST_REPLIES = ('Wow, you must be a JP fan.', 'This is one of the worst posts I have EVER seen. Delete it.', "No, don't reply like this, please do another wall of unhinged rant please.", '# 😴😴😴', "Ma'am we've been over this before. You need to stop.", "I've known more coherent downies.", "Your pulitzer's in the mail", "That's great and all, but I asked for my burger without cheese.", 'That degree finally paying off', "That's nice sweaty. Why don't you have a seat in the time out corner with Pizzashill until you calm down, then you can have your Capri Sun.", "All them words won't bring your pa back.", "You had a chance to not be completely worthless, but it looks like you threw it away. At least you're consistent.", 'Some people are able to display their intelligence by going on at length on a subject and never actually saying anything. This ability is most common in trades such as politics, public relations, and law. You have impressed me by being able to best them all, while still coming off as an absolute idiot.', "You can type 10,000 characters and you decided that these were the one's that you wanted.", 'Have you owned the libs yet?', "I don't know what you said, because I've seen another human naked.", 'Impressive. Normally people with such severe developmental disabilities struggle to write much more than a sentence or two. He really has exceded our expectations for the writing portion. Sadly the coherency of his writing, along with his abilities in the social skills and reading portions, are far behind his peers with similar disabilities.', "This is a really long way of saying you don't fuck.", "Sorry ma'am, looks like his delusions have gotten worse. We'll have to admit him.", ':#marseywoah:', 'If only you could put that energy into your relationships', 'Posts like this is why I do Heroine.', 'still unemployed then?', 'K', 'look im gunna have 2 ask u 2 keep ur giant dumps in the toilet not in my replys 😷😷😷', "Mommy is soooo proud of you, sweaty. Let's put this sperg out up on the fridge with all your other failures.", "Good job bobby, here's a star", "That was a mistake. You're about to find out the hard way why.", f'You sat down and wrote all this shit. You could have done so many other things with your life. What happened to your life that made you decide writing novels of bullshit on {SITE} was the best option?', "I don't have enough spoons to read this shit", "All those words won't bring daddy back.", 'OUT!', "Damn, you're really mad over this, but thanks for the effort you put into typing that all out! Sadly I won't read it all.", "Jesse what the fuck are you talking about??")

AGENDAPOSTER_PHRASE = 'black lives matter'

AGENDAPOSTER_MSG = """Hi @{username},\n\nYour {type} has been automatically removed because you forgot
		to include `{AGENDAPOSTER_PHRASE}`.\n\nDon't worry, we're here to help! We 
		won't let you post or comment anything that doesn't express your love and acceptance towards 
		the black community. Feel free to resubmit your {type} with `{AGENDAPOSTER_PHRASE}` 
		included. \n\n*This is an automated message; if you need help,
		you can message us [here](/contact).*"""

if SITE in ('rdrama.net','devrama.xyz','2much4you.net','ruqqus.us'):
	PW_ID = 3750
	BASEDBOT_ID = 0
	KIPPY_ID = 7150
	NOTIFICATIONS_ID = 1046
	AUTOJANNY_ID = 2360
	SNAPPY_ID = 261
	LONGPOSTBOT_ID = 1832
	ZOZBOT_ID = 1833
	AUTOPOLLER_ID = 6176
	AUTOBETTER_ID = 7668
	AUTOCHOICE_ID = 9167
	TAX_NOTIF_ID = 995
	PIZZASHILL_ID = 2424
	HIL_ID = 4245
	CRAT_ID = 747
	IDIO_ID = 30
	CARP_ID = 995
	JOAN_ID = 28
	MOOSE_ID = 1904
	AEVANN_ID = 1
	HOMO_ID = 147
	Q_ID = 1480
	LAWLZ_ID = 3833
	LLM_ID = 253
	DAD_ID = 2513
	SOREN_ID = 2546
	MOM_ID = 4588
	DONGER_ID = 541
	BUG_THREAD = 18459
	WELCOME_MSG = f"Hi there! It's me, your soon-to-be favorite rDrama user @carpathianflorist here to give you a brief rundown on some of the sick features we have here. You'll probably want to start by following me, though. So go ahead and click my name and then smash that Follow button. This is actually really important, so go on. Hurry.\n\nThanks!\n\nNext up: If you're a member of the media, similarly just shoot me a DM and I'll set about verifying you and then we can take care of your sad journalism stuff.\n\n**FOR EVERYONE ELSE**\n\n Begin by navigating to [the settings page]({SITE_FULL}/settings/profile) (we'll be prettying this up so it's less convoluted soon, don't worry) and getting some basic customization done.\n\n### Themes\n\nDefinitely change your theme right away, the default one (Midnight) is pretty enough, but why not use something *exotic* like Win98, or *flashy* like Tron? Even Coffee is super tasteful and way more fun than the default. More themes to come when we get around to it!\n\n### Avatar/pfp\n\nYou'll want to set this pretty soon; without uploading one, I put together a randomly-assigned selection of 180ish pictures of furries, ugly goths, mujahideen, anime girls, and My Little Ponys which are used by everyone who was too lazy to set a pfp. Set the banner too while you're at it. Your profile is important!\n\n### Flairs\n\nSince you're already on the settings page, you may as well set a flair, too. As with your username, you can - obviously - choose the color of this, either with a hex value or just from the preset colors. And also like your username, you can change this at any time. [Paypigs](https://marsey1.gumroad.com/l/tfcvri) can even further relive the glory days of 90s-00s internet and set obnoxious signatures.\n\n### PROFILE ANTHEMS\n\nSpeaking of profiles, hey, remember MySpace? Do you miss autoplaying music assaulting your ears every time you visited a friend's page? Yeah, we brought that back. Enter a YouTube URL, wait a few seconds for it to process, and then BAM! you've got a profile anthem which people cannot mute. Unless they spend 20,000 dramacoin in the shop for a mute button. Which you can then remove from your profile by spending 40,000 dramacoin on an unmuteable anthem. Get fucked poors!\n\n### Dramacoin?\n\nDramacoin is basically our take on the karma system. Except unlike the karma system, it's not gay and boring and stupid and useless. Dramacoin can be spent at [Marsey's Dramacoin Emporium]({SITE_FULL}/shop) on upgrades to your user experience (many more coming than what's already listed there), and best of all on tremendously annoying awards to fuck with your fellow dramautists. We're always adding more, so check back regularly in case you happen to miss one of the announcement posts. Holiday-themed awards are currently unavailable while we resolve an internal dispute, but they **will** return, no matter what some other janitors insist.\n\nLike karma, dramacoin is obtained by getting upvotes on your threads and comments. *Unlike* karma, it's also obtained by getting downvotes on your threads and comments. Downvotes don't really do anything here - they pay the same amount of dramacoin and they increase thread/comment ranking just the same as an upvote. You just use them to express petty disapproval and hopefully start a fight. Because all votes are visible here. To hell with your anonymity.\n\nDramacoin can also be traded amongst users from their profiles. Note that there is a 3% transaction fee.\n\n**Dramacoin and shop items cannot be purchased with real money and this will not change.** Though we are notoriously susceptible to bribes, so definitely shoot your shot. It'll probably go well, honestly.\n\n### Badges\n\nRemember all those neat little metallic icons you saw on my profile when you were following me? If not, scroll back up and go have a look. And doublecheck to make sure you pressed the Follow button. Anyway, those are badges. You earn them by doing a variety of things. Some of them even offer benefits, like discounts at the shop. A [complete list of badges and their requirements can be found here]({SITE_FULL}/badges), though I add more pretty regularly, so keep an eye on the changelog.\n\n### Other stuff\n\nWe're always adding new features, and we take a fun-first approach to development. If you have a suggestion for something that would be fun, funny, annoying - or best of all, some combination of all three - definitely make a thread about it. Or just DM me if you're shy. Weirdo. Anyway there's also the [leaderboards]({SITE_FULL}/leaderboard), boring stuff like two-factor authentication you can toggle on somewhere in the settings page (psycho), the ability to save posts and comments, close to a thousand emojis already (several hundred of which are rDrama originals), and on and on and on and on. This is just the basics, mostly to help you get acquainted with some of the things you can do here to make it more easy on the eyes, customizable, and enjoyable. If you don't enjoy it, just go away! We're not changing things to suit you! Get out of here loser! And no, you can't delete your account :na:\n\nI love you.<BR>*xoxo Carp* 💋"
elif SITE == "pcmemes.net":
	PW_ID = 0
	BASEDBOT_ID = 800
	KIPPY_ID = 1592
	NOTIFICATIONS_ID = 1046
	AUTOJANNY_ID = 1050
	SNAPPY_ID = 261
	LONGPOSTBOT_ID = 1832
	ZOZBOT_ID = 1833
	AUTOPOLLER_ID = 3369
	AUTOBETTER_ID = 1867
	AUTOCHOICE_ID = 2072
	TAX_NOTIF_ID = 1592
	PIZZASHILL_ID = 0
	HIL_ID = 0
	CRAT_ID = 0
	IDIO_ID = 0
	CARP_ID = 0
	JOAN_ID = 0
	MOOSE_ID = 0
	AEVANN_ID = 1
	HOMO_ID = 0
	Q_ID = 0
	LAWLZ_ID = 0
	LLM_ID = 0
	DAD_ID = 0
	SOREN_ID = 0
	MOM_ID = 0
	DONGER_ID = 0
	BUG_THREAD = 4103
	WELCOME_MSG = "Welcome to pcmemes.net! Don't forget to turn off the slur filter [here](/settings/content#slurreplacer)"
else:
	PW_ID = 0
	BASEDBOT_ID = 0
	KIPPY_ID = 0
	NOTIFICATIONS_ID = 1
	AUTOJANNY_ID = 2
	SNAPPY_ID = 3
	LONGPOSTBOT_ID = 4
	ZOZBOT_ID = 5
	AUTOPOLLER_ID = 6
	AUTOBETTER_ID = 7
	AUTOCHOICE_ID = 8
	TAX_NOTIF_ID = 9
	PIZZASHILL_ID = 0
	HIL_ID = 0
	CRAT_ID = 0
	IDIO_ID = 0
	CARP_ID = 0
	JOAN_ID = 0
	MOOSE_ID = 0
	AEVANN_ID = 10
	HOMO_ID = 0
	Q_ID = 0
	LAWLZ_ID = 0
	LLM_ID = 0
	DAD_ID = 0
	SOREN_ID = 0
	MOM_ID = 0
	DONGER_ID = 0
	BUG_THREAD = 0
	WELCOME_MSG = f"Welcome to {SITE}!"

PUSHER_ID = environ.get("PUSHER_ID", "").strip()
PUSHER_KEY = environ.get("PUSHER_KEY", "").strip()
DEFAULT_COLOR = environ.get("DEFAULT_COLOR", "fff").strip()
COLORS = {'ff66ac','805ad5','62ca56','38a169','80ffff','2a96f3','eb4963','ff0000','f39731','30409f','3e98a7','e4432d','7b9ae4','ec72de','7f8fa6', 'f8db58','8cdbe6', DEFAULT_COLOR}

AWARDS = {
	"snow": {
		"kind": "snow",
		"title": "Snow",
		"description": "???",
		"icon": "fas fa-snowflake",
		"color": "text-blue-200",
		"price": 300
	},
	"gingerbread": {
		"kind": "gingerbread",
		"title": "Gingerbread",
		"description": "???",
		"icon": "fas fa-gingerbread-man",
		"color": "",
		"price": 300
	},
	"lights": {
		"kind": "lights",
		"title": "Lights",
		"description": "???",
		"icon": "fad fa-lights-holiday",
		"color": "",
		"price": 300
	},
	"candycane": {
		"kind": "candycane",
		"title": "Candy Cane",
		"description": "???",
		"icon": "fad fa-candy-cane",
		"color": "",
		"price": 400
	},
	"fireplace": {
		"kind": "fireplace",
		"title": "Fireplace",
		"description": "???",
		"icon": "fad fa-fireplace",
		"color": "",
		"price": 600
	},
	"grinch": {
		"kind": "grinch",
		"title": "Grinch",
		"description": "???",
		"icon": "fas fa-angry",
		"color": "text-green-500",
		"price": 1000
	},
	"haunt": {
		"kind": "haunt",
		"title": "Haunt",
		"description": "???",
		"icon": "fas fa-book-dead",
		"color": "text-warning",
		"price": 500
	},
	"upsidedown": {
		"kind": "upsidedown",
		"title": "The Upside Down",
		"description": "???",
		"icon": "fad fa-lights-holiday",
		"color": "",
		"price": 400
	},
	"stab": {
		"kind": "stab",
		"title": "Stab",
		"description": "???",
		"icon": "fas fa-knife-kitchen",
		"color": "text-red",
		"price": 300
	},
	"spiders": {
		"kind": "spiders",
		"title": "Spiders",
		"description": "???",
		"icon": "fas fa-spider",
		"color": "text-black",
		"price": 200
	},
	"fog": {
		"kind": "fog",
		"title": "Fog",
		"description": "???",
		"icon": "fas fa-smoke",
		"color": "text-gray",
		"price": 200
	},
	"lootbox": {
		"kind": "lootbox",
		"title": "Lootstocking",
		"description": "???",
		"icon": "fas fa-stocking",
		"color": "text-red",
		"price": 1000
	},
	"shit": {
		"kind": "shit",
		"title": "Shit",
		"description": "Makes flies swarm the post.",
		"icon": "fas fa-poop",
		"color": "text-black-50",
		"price": 300
	},
	"fireflies": {
		"kind": "fireflies",
		"title": "Fireflies",
		"description": "Makes fireflies swarm the post.",
		"icon": "fas fa-sparkles",
		"color": "text-warning",
		"price": 300
	},
	"train": {
		"kind": "train",
		"title": "Train",
		"description": "Summons a train on the post.",
		"icon": "fas fa-train",
		"color": "text-pink",
		"price": 300
	},
	"scooter": {
		"kind": "scooter",
		"title": "Scooter",
		"description": "Summons a scooter on the post.",
		"icon": "fas fa-flag-usa",
		"color": "text-muted",
		"price": 300
	},
	"wholesome": {
        "kind": "wholesome",
        "title": "Wholesome",
        "description": "Summons a wholesome marsey on the post.",
        "icon": "fas fa-smile-beam",
        "color": "text-yellow",
        "price": 300
    },
	"tilt": {
        "kind": "tilt",
        "title": "Tilt",
        "description": "Tilts the post or comment",
        "icon": "fas fa-car-tilt",
        "color": "text-blue",
        "price": 300
    },
	"ghosts": {
		"kind": "ghosts",
		"title": "Ghosts",
		"description": "Hides the usernames of everyone in the thread",
		"icon": "fas fa-ghost",
		"color": "text-white",
		"price": 500
	},
	"rehab": {
        "kind": "rehab",
        "title": "Rehab",
        "description": "Prevents the user from gambling for 24 hours in a last ditch effort to save them from themself.",
        "icon": "fas fa-dice-six",
        "color": "text-black",
        "price": 777
    }, 
	"progressivestack": {
        "kind": "progressivestack",
        "title": "Progressive Stack",
        "description": "Makes votes on the recipient's posts and comments weigh double in the ranking algorithm for 6 hours.",
        "icon": "fas fa-bullhorn",
        "color": "text-red",
        "price": 1000
    },
	"pin": {
		"kind": "pin",
		"title": "1-Hour Pin",
		"description": "Pins the post/comment.",
		"icon": "fas fa-thumbtack fa-rotate--45",
		"color": "text-warning",
		"price": 1000
	},
	"unpin": {
		"kind": "unpin",
		"title": "1-Hour Unpin",
		"description": "Removes 1 hour from the pin duration of the post/comment.",
		"icon": "fas fa-thumbtack fa-rotate--45",
		"color": "text-black",
		"price": 1000
	},
	"flairlock": {
		"kind": "flairlock",
		"title": "1-Day Flairlock",
		"description": "Sets a flair for the recipient and locks it or 24 hours.",
		"icon": "fas fa-lock",
		"color": "text-black",
		"price": 1250
	},
	"pizzashill": {
		"kind": "pizzashill",
		"title": "Pizzashill",
		"description": "Forces the recipient to make all posts/comments > 280 characters for 24 hours.",
		"icon": "fas fa-pizza-slice",
		"color": "text-orange",
		"price": 1500
	},
	"bird": {
		"kind": "bird",
		"title": "Bird Site",
		"description": "Forces the recipient to make all posts/comments < 140 characters for 24 hours.",
		"icon": "fab fa-twitter",
		"color": "text-blue",
		"price": 1500
	},
	"agendaposter": {
		"kind": "agendaposter",
		"title": "Chud",
		"description": "Forces the chud theme on the recipient for 24 hours.",
		"icon": "fas fa-snooze",
		"color": "text-purple",
		"price": 2500
	},
	"marsey": {
		"kind": "marsey",
		"title": "Marsey",
		"description": "Makes the recipient unable to post/comment anything but marsey emojis for 24 hours.",
		"icon": "fas fa-cat",
		"color": "text-orange",
		"price": 3000
	},
	"ban": {
		"kind": "ban",
		"title": "1-Day Ban",
		"description": "Bans the recipient for a day.",
		"icon": "fas fa-gavel",
		"color": "text-danger",
		"price": 3000
	},
	"unban": {
		"kind": "unban",
		"title": "1-Day Unban",
		"description": "Removes 1 day from the ban duration of the recipient.",
		"icon": "fas fa-gavel",
		"color": "text-success",
		"price": 3500
	},
	"benefactor": {
        "kind": "benefactor",
        "title": "Benefactor",
        "description": "Grants one month of paypig status and 2500 marseybux to the recipient. Cannot be used on yourself.",
        "icon": "fas fa-gift",
        "color": "text-blue",
        "price": 4000
    },
	"grass": {
		"kind": "grass",
		"title": "Grass",
		"description": "Ban the recipient for 30 days (if they provide a timestamped picture of them touching grass/snow/sand/ass to the admins, they will get unbanned immediately)",
		"icon": "fas fa-seedling",
		"color": "text-success",
		"price": 10000
	},
	"eye": {
		"kind": "eye",
		"title": "All-Seeing Eye",
		"description": "Gives the recipient the ability to view private profiles.",
		"icon": "fas fa-eye",
		"color": "text-silver",
		"price": 10000
	},
	"unblockable": {
		"kind": "unblockable",
		"title": "Unblockable",
		"description": "Makes the recipient unblockable and removes all blocks on them.",
		"icon": "far fa-laugh-squint",
		"color": "text-lightgreen",
		"price": 10000
	},
	"nword": {
		"kind": "nword",
		"title": "Nword Pass",
		"description": "Gives the recipient the ability to speak that which must not be spoken",
		"icon": "fas fa-edit",
		"color": "text-success",
		"price": 10000
	},
	"fish": {
		"kind": "fish",
		"title": "Fish",
		"description": "This user cannot be unfollowed",
		"icon": "fas fa-fish",
		"color": "text-lightblue",
		"price": 20000
	},
	"pause": {
		"kind": "pause",
		"title": "Pause",
		"description": "Gives the recipient the ability to pause profile anthems.",
		"icon": "fas fa-volume-mute",
		"color": "text-danger",
		"price": 20000
	},
	"unpausable": {
		"kind": "unpausable",
		"title": "Unpausable",
		"description": "Makes the profile anthem of the recipient unpausable.",
		"icon": "fas fa-volume",
		"color": "text-success",
		"price": 40000
	},
	"alt": {
		"kind": "alt",
		"title": "Alt-Seeing Eye",
		"description": "Gives the recipient the ability to view alts.",
		"icon": "fas fa-eye",
		"color": "text-gold",
		"price": 50000
	},
}

AWARDS2 = deepcopy(AWARDS)
for k, val in AWARDS.items():
	if val['description'] == '???': AWARDS2.pop(k)
	if SITE == 'pcmemes.net' and k in ('ban','pizzashill','marsey','bird','grass','chud'): AWARDS2.pop(k)

TROLLTITLES = [
	"how will @{username} ever recover?",
	"@{username} BTFO",
	"[META] Getting really sick of @{username}’s shit",
	"Pretty sure this is @{username}'s Reddit account",
	"Hey jannies can you please ban @{username}",
]

NOTIFIED_USERS = {
	'aevan': AEVANN_ID,
	'avean': AEVANN_ID,
	'joan': JOAN_ID,
	'pewkie': JOAN_ID,
	'carp': CARP_ID,
	'idio3': IDIO_ID,
	'idio ': IDIO_ID,
	'landlord_messiah': LLM_ID,
	'landlordmessiah': LLM_ID,
	' llm ': LLM_ID,
	'landlet': LLM_ID,
	'dong': DONGER_ID,
	'kippy': KIPPY_ID,
	'the_homocracy': HOMO_ID,
	'soren': SOREN_ID
}

FORTUNE_REPLIES = ('<b style="color:#6023f8">Your fortune: Allah Wills It</b>','<b style="color:#d302a7">Your fortune: Inshallah, Only Good Things Shall Come To Pass</b>','<b style="color:#e7890c">Your fortune: Allah Smiles At You This Day</b>','<b style="color:#7fec11">Your fortune: Your Bussy Is In For A Blasting</b>','<b style="color:#43fd3b">Your fortune: You Will Be Propositioned By A High-Tier Twink</b>','<b style="color:#9d05da">Your fortune: Repent, You Have Displeased Allah And His Vengeance Is Nigh</b>','<b style="color:#f51c6a">Your fortune: Reply Hazy, Try Again</b>','<b style="color:#00cbb0">Your fortune: lmao you just lost 100 dramacoin</b>','<b style="color:#2a56fb">Your fortune: Yikes 😬</b>','<b style="color:#0893e1">Your fortune: You Will Be Blessed With Many Black Bulls</b>','<b style="color:#16f174">Your fortune: NEETmax, The Day Is Lost If You Venture Outside</b>','<b style="color:#fd4d32">Your fortune: A Taste Of Jannah Awaits You Today</b>','<b style="color:#bac200">Your fortune: Watch Your Back</b>','<b style="color:#6023f8">Your fortune: Outlook good</b>','<b style="color:#d302a7">Your fortune: Godly Luck</b>','<b style="color:#e7890c">Your fortune: Good Luck</b>','<b style="color:#7fec11">Your fortune: Bad Luck</b>','<b style="color:#43fd3b">Your fortune: Good news will come to you by mail</b>','<b style="color:#9d05da">Your fortune: Very Bad Luck</b>','<b style="color:#00cbb0">Your fortune: ｷﾀ━━━━━━(ﾟ∀ﾟ)━━━━━━ !!!!</b>','<b style="color:#2a56fb">Your fortune: Better not tell you now</b>','<b style="color:#0893e1">Your fortune: You will meet a dark handsome stranger</b>','<b style="color:#16f174">Your fortune: （　´_ゝ`）ﾌｰﾝ</b>','<b style="color:#fd4d32">Your fortune: Excellent Luck</b>','<b style="color:#bac200">Your fortune: Average Luck</b>')

no_pass_phrase = """<p>Sorry whiteboy, we're gonna need to see some ID before you start throwin that word around like it's nothing.\n\nTake a 10 minute time-out and come back when you've learned your lesson and/or paid reparations (by purchasing a BIPOC Approved™ rDrama NWord Pass© from the <a href="/shop">shop</a>) \n\n<em>This is an automated message; if you need help, you can message us <a href="/contact">here</a>.</em></p>"""

ROLES={
	"owner": "864612849199480914",
	"admin": "879459632656048180" if environ.get("DOMAIN") == "pcmemes.net" else "846509661288267776",
	"linked": "890342909390520382",
	"1": "868129042346414132",
	"2": "875569477671067688",
	"3": "869434199575236649",
	"4": "868140288013664296",
	"5": "886781932430565418",
	}

if SITE_NAME == 'Drama': patron = 'Paypig'
else: patron = 'Patron'

REDDIT_NOTIFS = {
	'idio3': IDIO_ID,
	'aevann': AEVANN_ID,
	'carpflo': CARP_ID,
	'carpathianflorist': CARP_ID,
	'carpathian florist': CARP_ID,
	'the_homocracy': HOMO_ID
}

toomuch_subs = ('2much4you','2balkan4you','2middleeast4you','2asia4you','2caucasian4you','2european4you','2american4you')