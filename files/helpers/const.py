from os import environ, listdir
import re
from copy import deepcopy
from json import loads
from files.__main__ import db_session
from files.classes.sub import Sub
from files.classes.marsey import Marsey

SITE = environ.get("DOMAIN", '').strip()
SITE_NAME = environ.get("SITE_NAME", '').strip()
if SITE == "localhost": SITE_FULL = 'http://' + SITE
else: SITE_FULL = 'https://' + SITE


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

if SITE_NAME == 'Cringetopia':
	SLURS = {
		"retarded": "neurodivergent",
		"retard": "neurodivergent",
		"faggotry": "cute twinkry",
		"faggot": "cute twink",
		"n1gger": "🏀",
		"nlgger": "🏀",
		"nigger": "🏀",
		"uss liberty incident": "tragic accident aboard the USS Liberty",
		"lavon affair": "Lavon Misunderstanding",
		"i hate marsey": "i love marsey",
		"autistic": "neurodivergent",
		"holohoax": "i tried to claim the Holocaust didn't happen because I am a pencil-dicked imbecile and the word filter caught me lol",
		"i hate carp": "i love Carp",
		"heil hitler": "hello kitty",

		" fag ": " cute twink ",
	}
else:
	SLURS = {
		"retarded": "r-slurred",
		"retard": "r-slur",
		"gayfag": "gaystrag",
		"poorfag": "poorstrag",
		"richfag": "richstrag",
		"newfag": "newstrag",
		"oldfag": "oldstrag",
		"faggotry": "cute twinkry",
		"faggot": "cute twink",
		"pedophile": "libertarian",
		"kill yourself": "keep yourself safe",
		"n1gger": "BIPOC",
		"nlgger": "BIPOC",
		"nigger": "BIPOC",
		"steve akins": "penny verity oaken",
		"trannie": "🚂🚃🚃",
		"tranny": "🚂🚃🚃",
		"troon": "🚂🚃🚃",
		"nonewnormal": "HorseDewormerAddicts",
		"kikery": "https://sciencedirect.com/science/article/abs/pii/S016028960600033X",
		"kike": "https://sciencedirect.com/science/article/abs/pii/S016028960600033X",
		"latinos": "latinx",
		"latino": "latinx",
		"latinas": "latinx",
		"latina": "latinx",
		"hispanics": "latinx",
		"hispanic": "latinx",
		"uss liberty incident": "tragic accident aboard the USS Liberty",
		"lavon affair": "Lavon Misunderstanding",
		"shylock": "Israeli friend",
		"mohammad": "Prophet Mohammad (PBUH)",
		"muhammad": "Prophet Mohammad (PBUH)",
		"i hate marsey": "i love marsey",
		"dancing israelis": "i love Israel",
		"sodomite": "total dreamboat",
		"pajeet": "sexy Indian dude",
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
		"fake and gay": "fake and straight",

		" rapist ": " male feminist ",
		" pedo ": " libertarian ",
		" kys ": " keep yourself safe ",
		" fag ": " cute twink ",
	}

single_words = "|".join([slur.lower() for slur in SLURS.keys()])


LONGPOST_REPLIES = ('Wow, you must be a JP fan.', 'This is one of the worst posts I have EVER seen. Delete it.', "No, don't reply like this, please do another wall of unhinged rant please.", '# 😴😴😴', "Ma'am we've been over this before. You need to stop.", "I've known more coherent downies.", "Your pulitzer's in the mail", "That's great and all, but I asked for my burger without cheese.", 'That degree finally paying off', "That's nice sweaty. Why don't you have a seat in the time out corner with Pizzashill until you calm down, then you can have your Capri Sun.", "All them words won't bring your pa back.", "You had a chance to not be completely worthless, but it looks like you threw it away. At least you're consistent.", 'Some people are able to display their intelligence by going on at length on a subject and never actually saying anything. This ability is most common in trades such as politics, public relations, and law. You have impressed me by being able to best them all, while still coming off as an absolute idiot.', "You can type 10,000 characters and you decided that these were the one's that you wanted.", 'Have you owned the libs yet?', "I don't know what you said, because I've seen another human naked.", 'Impressive. Normally people with such severe developmental disabilities struggle to write much more than a sentence or two. He really has exceded our expectations for the writing portion. Sadly the coherency of his writing, along with his abilities in the social skills and reading portions, are far behind his peers with similar disabilities.', "This is a really long way of saying you don't fuck.", "Sorry ma'am, looks like his delusions have gotten worse. We'll have to admit him.", ':#marseywoah:', 'If only you could put that energy into your relationships', 'Posts like this is why I do Heroine.', 'still unemployed then?', 'K', 'look im gunna have 2 ask u 2 keep ur giant dumps in the toilet not in my replys 😷😷😷', "Mommy is soooo proud of you, sweaty. Let's put this sperg out up on the fridge with all your other failures.", "Good job bobby, here's a star", "That was a mistake. You're about to find out the hard way why.", f'You sat down and wrote all this shit. You could have done so many other things with your life. What happened to your life that made you decide writing novels of bullshit on {SITE} was the best option?', "I don't have enough spoons to read this shit", "All those words won't bring daddy back.", 'OUT!', "Damn, you're really mad over this, but thanks for the effort you put into typing that all out! Sadly I won't read it all.", "Jesse what the fuck are you talking about??", "▼you're fucking bananas if you think I'm reading all that, take my downvote and shut up idiot")

AGENDAPOSTER_PHRASE = 'trans lives matter'

AGENDAPOSTER_MSG = """Hi @{username},\n\nYour {type} has been automatically removed because you forgot to include `{AGENDAPOSTER_PHRASE}`.\n\nDon't worry, we're here to help! We won't let you post or comment anything that doesn't express your love and acceptance towards the trans community. Feel free to resubmit your {type} with `{AGENDAPOSTER_PHRASE}` included. \n\n*This is an automated message; if you need help, you can message us [here](/contact).*"""

if SITE in {'rdrama.net','devrama.xyz'}:
	NOTIFICATIONS_ID = 1046
	AUTOJANNY_ID = 2360
	SNAPPY_ID = 261
	LONGPOSTBOT_ID = 1832
	ZOZBOT_ID = 1833
	AUTOPOLLER_ID = 6176
	AUTOBETTER_ID = 7668
	AUTOCHOICE_ID = 9167
	BASEDBOT_ID = 0

	A_ID = 1230
	KIPPY_ID = 7150
	GIFT_NOTIF_ID = 995
	PIZZASHILL_ID = 2424
	PIZZA_VOTERS = (747,1963,9712)
	IDIO_ID = 30
	CARP_ID = 995
	JOAN_ID = 28
	MOOSE_ID = 1904
	AEVANN_ID = 1
	HOMO_ID = 147
	SOREN_ID = 2546
	Q_ID = 1480
	LAWLZ_ID = 3833
	LLM_ID = 253
	DAD_ID = 2513
	MOM_ID = 4588
	DONGER_ID = 541
	BUG_THREAD = 18459
	WELCOME_MSG = "Hi there! It's me, your soon-to-be favorite rDrama user @carpathianflorist here to give you a brief rundown on some of the sick features we have here. You'll probably want to start by following me, though. So go ahead and click my name and then smash that Follow button. This is actually really important, so go on. Hurry.\n\nThanks!\n\nNext up: If you're a member of the media, similarly just shoot me a DM and I'll set about verifying you and then we can take care of your sad journalism stuff.\n\n**FOR EVERYONE ELSE**\n\n Begin by navigating to [the settings page](/settings/profile) (we'll be prettying this up so it's less convoluted soon, don't worry) and getting some basic customization done.\n\n### Themes\n\nDefinitely change your theme right away, the default one (Midnight) is pretty enough, but why not use something *exotic* like Win98, or *flashy* like Tron? Even Coffee is super tasteful and way more fun than the default. More themes to come when we get around to it!\n\n### Avatar/pfp\n\nYou'll want to set this pretty soon. Set the banner too while you're at it. Your profile is important!\n\n### Flairs\n\nSince you're already on the settings page, you may as well set a flair, too. As with your username, you can - obviously - choose the color of this, either with a hex value or just from the preset colors. And also like your username, you can change this at any time. [Paypigs](https://marsey1.gumroad.com/l/tfcvri) can even further relive the glory days of 90s-00s internet and set obnoxious signatures.\n\n### PROFILE ANTHEMS\n\nSpeaking of profiles, hey, remember MySpace? Do you miss autoplaying music assaulting your ears every time you visited a friend's page? Yeah, we brought that back. Enter a YouTube URL, wait a few seconds for it to process, and then BAM! you've got a profile anthem which people cannot mute. Unless they spend 20,000 dramacoin in the shop for a mute button. Which you can then remove from your profile by spending 40,000 dramacoin on an unmuteable anthem. Get fucked poors!\n\n### Dramacoin?\n\nDramacoin is basically our take on the karma system. Except unlike the karma system, it's not gay and boring and stupid and useless. Dramacoin can be spent at [Marsey's Dramacoin Emporium](/shop) on upgrades to your user experience (many more coming than what's already listed there), and best of all on tremendously annoying awards to fuck with your fellow dramautists. We're always adding more, so check back regularly in case you happen to miss one of the announcement posts.\n\nLike karma, dramacoin is obtained by getting upvotes on your threads and comments. *Unlike* karma, it's also obtained by getting downvotes on your threads and comments. Downvotes don't really do anything here - they pay the same amount of dramacoin and they increase thread/comment ranking just the same as an upvote. You just use them to express petty disapproval and hopefully start a fight. Because all votes are visible here. To hell with your anonymity.\n\nDramacoin can also be traded amongst users from their profiles. Note that there is a 3% transaction fee.\n\n### Badges\n\nRemember all those neat little metallic icons you saw on my profile when you were following me? If not, scroll back up and go have a look. And doublecheck to make sure you pressed the Follow button. Anyway, those are badges. You earn them by doing a variety of things. Some of them even offer benefits, like discounts at the shop. A [complete list of badges and their requirements can be found here](/badges), though I add more pretty regularly, so keep an eye on the changelog.\n\n### Other stuff\n\nWe're always adding new features, and we take a fun-first approach to development. If you have a suggestion for something that would be fun, funny, annoying - or best of all, some combination of all three - definitely make a thread about it. Or just DM me if you're shy. Weirdo. Anyway there's also the [leaderboards](/leaderboard), boring stuff like two-factor authentication you can toggle on somewhere in the settings page (psycho), the ability to save posts and comments, more than a thousand emojis already (most of which are rDrama originals), and on and on and on and on. This is just the basics, mostly to help you get acquainted with some of the things you can do here to make it more easy on the eyes, customizable, and enjoyable. If you don't enjoy it, just go away! We're not changing things to suit you! Get out of here loser! And no, you can't delete your account :na:\n\nI love you.<BR>*xoxo Carp* 💋"
	ROLES={
		"owner": "864612849199480914",
		"admin": "846509661288267776",
		"linked": "890342909390520382",
		"1": "868129042346414132",
		"2": "875569477671067688",
		"3": "869434199575236649",
		"4": "868140288013664296",
		"5": "947236580794450010",
		"6": "947236351445725204",
		"7": "886781932430565418",
	}
elif SITE == "pcmemes.net":
	NOTIFICATIONS_ID = 1046
	AUTOJANNY_ID = 1050
	SNAPPY_ID = 261
	LONGPOSTBOT_ID = 1832
	ZOZBOT_ID = 1833
	AUTOPOLLER_ID = 2129
	AUTOBETTER_ID = 1867
	AUTOCHOICE_ID = 2072
	BASEDBOT_ID = 800

	A_ID = 0
	KIPPY_ID = 1592
	PIZZASHILL_ID = 0
	PIZZA_VOTERS = ()
	GIFT_NOTIF_ID = 1592
	IDIO_ID = 0
	CARP_ID = 0
	JOAN_ID = 0
	MOOSE_ID = 0
	AEVANN_ID = 1
	HOMO_ID = 0
	SOREN_ID = 0
	Q_ID = 0
	LAWLZ_ID = 0
	LLM_ID = 0
	DAD_ID = 0
	MOM_ID = 0
	DONGER_ID = 0
	BUG_THREAD = 4103
	WELCOME_MSG = "Welcome to pcmemes.net! Don't forget to turn off the slur filter [here](/settings/content#slurreplacer)"
	ROLES={}
elif SITE == 'cringetopia.org':
	NOTIFICATIONS_ID = 1
	AUTOJANNY_ID = 2
	SNAPPY_ID = 3
	LONGPOSTBOT_ID = 4
	ZOZBOT_ID = 5
	AUTOPOLLER_ID = 6
	AUTOBETTER_ID = 7
	AUTOCHOICE_ID = 8
	BASEDBOT_ID = 0

	A_ID = 0
	KIPPY_ID = 0
	GIFT_NOTIF_ID = 43
	PIZZASHILL_ID = 0
	PIZZA_VOTERS = ()
	IDIO_ID = 0
	CARP_ID = 43
	JOAN_ID = 0
	MOOSE_ID = 0
	AEVANN_ID = 9
	HOMO_ID = 0
	SOREN_ID = 0
	Q_ID = 0
	LAWLZ_ID = 0
	LLM_ID = 0
	DAD_ID = 0
	MOM_ID = 0
	DONGER_ID = 0
	BUG_THREAD = 0
	WELCOME_MSG = "Hi there! It's me, your soon-to-be favorite Cringetopia user @carpathianflorist here to give you a brief rundown on some of the sick features we have here. You'll probably want to start by following me, though. So go ahead and click my name and then smash that Follow button. This is actually really important, so go on. Hurry.\n\nThanks!\n\nNext up: If you're a member of the media, similarly just shoot me a DM and I'll set about verifying you and then we can take care of your sad journalism stuff.\n\n**FOR EVERYONE ELSE**\n\n Begin by navigating to [the settings page](/settings/profile) (we'll be prettying this up so it's less convoluted soon, don't worry) and getting some basic customization done.\n\n### Themes\n\nDefinitely change your theme right away, the default one (Midnight) is pretty enough, but why not use something *exotic* like Win98, or *flashy* like Tron? Even Coffee is super tasteful and way more fun than the default. More themes to come when we get around to it!\n\n### Avatar/pfp\n\nYou'll want to set this pretty soon. Set the banner too while you're at it. Your profile is important!\n\n### Flairs\n\nSince you're already on the settings page, you may as well set a flair, too. As with your username, you can - obviously - choose the color of this, either with a hex value or just from the preset colors. And also like your username, you can change this at any time.\n\n### PROFILE ANTHEMS\n\nSpeaking of profiles, hey, remember MySpace? Do you miss autoplaying music assaulting your ears every time you visited a friend's page? Yeah, we brought that back. Enter a YouTube URL, wait a few seconds for it to process, and then BAM! you've got a profile anthem which people cannot mute. Unless they spend 20,000 coins in the shop for a mute button. Which you can then remove from your profile by spending 40,000 coins on an unmuteable anthem. Get fucked poors!\n\n### Coins?\n\nCoins is basically our take on the karma system. Except unlike the karma system, it's not gay and boring and stupid and useless. Coins can be spent at [Marsey's Dramacoin Emporium](/shop) on upgrades to your user experience (many more coming than what's already listed there), and best of all on tremendously annoying awards to fuck with your fellow autists. We're always adding more, so check back regularly in case you happen to miss one of the announcement posts.\n\nLike karma, Coins is obtained by getting upvotes on your threads and comments. *Unlike* karma, it's also obtained by getting downvotes on your threads and comments. Downvotes don't really do anything here - they pay the same amount of Coins and they increase thread/comment ranking just the same as an upvote. You just use them to express petty disapproval and hopefully start a fight. Because all votes are visible here. To hell with your anonymity.\n\nCoins can also be traded amongst users from their profiles. Note that there is a 3% transaction fee.\n\n### Badges\n\nRemember all those neat little metallic icons you saw on my profile when you were following me? If not, scroll back up and go have a look. And doublecheck to make sure you pressed the Follow button. Anyway, those are badges. You earn them by doing a variety of things. Some of them even offer benefits, like discounts at the shop. A [complete list of badges and their requirements can be found here](/badges), though I add more pretty regularly, so keep an eye on the changelog.\n\n### Other stuff\n\nWe're always adding new features, and we take a fun-first approach to development. If you have a suggestion for something that would be fun, funny, annoying - or best of all, some combination of all three - definitely make a thread about it. Or just DM me if you're shy. Weirdo. Anyway there's also the [leaderboards](/leaderboard), boring stuff like two-factor authentication you can toggle on somewhere in the settings page (psycho), the ability to save posts and comments, more than a thousand emojis, and on and on and on and on. This is just the basics, mostly to help you get acquainted with some of the things you can do here to make it more easy on the eyes, customizable, and enjoyable. If you don't enjoy it, just go away! We're not changing things to suit you! Get out of here loser! And no, you can't delete your account :na:\n\nI love you.<BR>*xoxo Carp* 💋"
	ROLES={
		"owner": "809580734578819072",
		"admin": "846509661288267776",
		"linked": "890342909390520382",
		"1": "868129042346414132",
		"2": "875569477671067688",
		"3": "869434199575236649",
		"4": "868140288013664296",
		"5": "947236580794450010",
		"6": "947236351445725204",
		"7": "886781932430565418",
	}
else:
	NOTIFICATIONS_ID = 1
	AUTOJANNY_ID = 2
	SNAPPY_ID = 3
	LONGPOSTBOT_ID = 4
	ZOZBOT_ID = 5
	AUTOPOLLER_ID = 6
	AUTOBETTER_ID = 7
	AUTOCHOICE_ID = 8
	BASEDBOT_ID = 0

	A_ID = 0
	KIPPY_ID = 0
	GIFT_NOTIF_ID = 9
	PIZZASHILL_ID = 0
	PIZZA_VOTERS = ()
	IDIO_ID = 0
	CARP_ID = 0
	JOAN_ID = 0
	MOOSE_ID = 0
	AEVANN_ID = 9
	HOMO_ID = 0
	SOREN_ID = 0
	Q_ID = 0
	LAWLZ_ID = 0
	LLM_ID = 0
	DAD_ID = 0
	MOM_ID = 0
	DONGER_ID = 0
	BUG_THREAD = 0
	WELCOME_MSG = f"Welcome to {SITE_NAME}!"
	ROLES={}

IMGUR_KEY = environ.get("IMGUR_KEY").strip()
PUSHER_ID = environ.get("PUSHER_ID", "").strip()
PUSHER_KEY = environ.get("PUSHER_KEY", "").strip()
DEFAULT_COLOR = environ.get("DEFAULT_COLOR", "fff").strip()
COLORS = {'ff66ac','805ad5','62ca56','38a169','80ffff','2a96f3','eb4963','ff0000','f39731','30409f','3e98a7','e4432d','7b9ae4','ec72de','7f8fa6', 'f8db58','8cdbe6', DEFAULT_COLOR}

AWARDS = {
	"ghost": {
		"kind": "ghost",
		"title": "Ghost",
		"description": "???",
		"icon": "fas fa-ghost",
		"color": "text-white",
		"price": 3000
	},
	"nword": {
		"kind": "nword",
		"title": "Nword Pass",
		"description": "???",
		"icon": "fas fa-edit",
		"color": "text-success",
		"price": 10000
	},
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
		"icon": "fas fa-lights-holiday",
		"color": "",
		"price": 300
	},
	"candycane": {
		"kind": "candycane",
		"title": "Candy Cane",
		"description": "???",
		"icon": "fas fa-candy-cane",
		"color": "",
		"price": 400
	},
	"fireplace": {
		"kind": "fireplace",
		"title": "Fireplace",
		"description": "???",
		"icon": "fas fa-fireplace",
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
		"icon": "fas fa-lights-holiday",
		"color": "",
		"price": 400
	},
	"stab": {
		"kind": "stab",
		"title": "Stab",
		"description": "???",
		"icon": "fas fa-knife-kitchen",
		"color": "text-danger",
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
		"color": "text-danger",
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
	"glowie": {
        "kind": "glowie",
        "title": "Glowie",
        "description": "Indicates that the recipient can be seen when driving. Just run them over.",
        "icon": "fas fa-user-secret",
        "color": "text-green",
        "price": 300
    },
	"rehab": {
		"kind": "rehab",
		"title": "Rehab",
		"description": "Prevents the user from gambling for 24 hours in a last ditch effort to save them from themself.",
		"icon": "fas fa-dice-six",
		"color": "text-black",
		"price": 777
	},
	"beano": {
        "kind": "beano",
        "title": "Beano",
        "description": "Stops you from embarrassing yourself with your flatulence",
        "icon": "fas fa-gas-pump-slash",
        "color": "text-green",
        "price": 1000
    },
	"progressivestack": {
		"kind": "progressivestack",
		"title": "Progressive Stack",
		"description": "Makes votes on the recipient's posts and comments weigh double in the ranking algorithm for 6 hours.",
		"icon": "fas fa-bullhorn",
		"color": "text-danger",
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
		"description": "Sets a flair for the recipient and locks it for 24 hours.",
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
	"deflector": {
		"kind": "deflector",
		"title": "Deflector",
		"description": "Causes most awards received for the next 10 hours to be deflected back at their giver.",
		"icon": "fas fa-shield",
		"color": "text-pink",
		"price": 2750
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

if SITE_NAME == 'PCM':
	PCM_AWARDS = {
		"croag": {
			"kind": "croag",
			"title": "Croag",
			"description": "Summons Croag on the post.",
			"icon": "fas fa-head-side",
			"color": "text-gold",
			"price": 500
		},
		"toe": {
			"kind": "toe",
			"title": "Toe Hype",
			"description": "Summons Blade's toe on the post.",
			"icon": "fas fa-socks",
			"color": "text-blue",
			"price": 500
		},
		"crab": {
			"kind": "crab",
			"title": "Crab",
			"description": "Rave time!",
			"icon": "fas fa-crab",
			"color": "text-danger",
			"price": 4000
		}
	}
	AWARDS = {**PCM_AWARDS, **AWARDS}

AWARDS2 = deepcopy(AWARDS)
for k, val in AWARDS.items():
	if val['description'] == '???' and not (k == 'ghost' and SITE_NAME == 'PCM'): AWARDS2.pop(k)
	if SITE == 'pcmemes.net' and k in ('ban','pizzashill','marsey','bird','grass','chud'): AWARDS2.pop(k)


AWARDS3 = {}
for k, val in AWARDS2.items():
	if val['price'] == 300: AWARDS3[k] = val

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
	'soren': SOREN_ID,
}

FORTUNE_REPLIES = ('<b style="color:#6023f8">Your fortune: Allah Wills It</b>','<b style="color:#d302a7">Your fortune: Inshallah, Only Good Things Shall Come To Pass</b>','<b style="color:#e7890c">Your fortune: Allah Smiles At You This Day</b>','<b style="color:#7fec11">Your fortune: Your Bussy Is In For A Blasting</b>','<b style="color:#43fd3b">Your fortune: You Will Be Propositioned By A High-Tier Twink</b>','<b style="color:#9d05da">Your fortune: Repent, You Have Displeased Allah And His Vengeance Is Nigh</b>','<b style="color:#f51c6a">Your fortune: Reply Hazy, Try Again</b>','<b style="color:#00cbb0">Your fortune: lmao you just lost 100 coins</b>','<b style="color:#2a56fb">Your fortune: Yikes 😬</b>','<b style="color:#0893e1">Your fortune: You Will Be Blessed With Many Black Bulls</b>','<b style="color:#16f174">Your fortune: NEETmax, The Day Is Lost If You Venture Outside</b>','<b style="color:#fd4d32">Your fortune: A Taste Of Jannah Awaits You Today</b>','<b style="color:#bac200">Your fortune: Watch Your Back</b>','<b style="color:#6023f8">Your fortune: Outlook good</b>','<b style="color:#d302a7">Your fortune: Godly Luck</b>','<b style="color:#e7890c">Your fortune: Good Luck</b>','<b style="color:#7fec11">Your fortune: Bad Luck</b>','<b style="color:#43fd3b">Your fortune: Good news will come to you by mail</b>','<b style="color:#9d05da">Your fortune: Very Bad Luck</b>','<b style="color:#00cbb0">Your fortune: ｷﾀ━━━━━━(ﾟ∀ﾟ)━━━━━━ !!!!</b>','<b style="color:#2a56fb">Your fortune: Better not tell you now</b>','<b style="color:#0893e1">Your fortune: You will meet a dark handsome stranger</b>','<b style="color:#16f174">Your fortune: （　´_ゝ`）ﾌｰﾝ</b>','<b style="color:#fd4d32">Your fortune: Excellent Luck</b>','<b style="color:#bac200">Your fortune: Average Luck</b>')

if SITE_NAME == 'rDrama': patron = 'Paypig'
else: patron = 'Patron'

REDDIT_NOTIFS = {
	'idio3': IDIO_ID,
	'aevann': AEVANN_ID,
	'carpflo': CARP_ID,
	'carpathianflorist': CARP_ID,
	'carpathian florist': CARP_ID,
	'the_homocracy': HOMO_ID
}

discounts = {
	69: 0.02,
	70: 0.04,
	71: 0.06,
	72: 0.08,
	73: 0.10,
}

CF_KEY = environ.get("CF_KEY", "").strip()
CF_ZONE = environ.get("CF_ZONE", "").strip()
CF_HEADERS = {"Authorization": f"Bearer {CF_KEY}", "Content-Type": "application/json"}

WORDLE_LIST = ('aaron','about','above','abuse','acids','acres','actor','acute','adams','added','admin','admit','adopt','adult','after','again','agent','aging','agree','ahead','aimed','alarm','album','alert','alias','alice','alien','align','alike','alive','allah','allan','allen','allow','alloy','alone','along','alpha','alter','amber','amend','amino','among','angel','anger','angle','angry','anime','annex','annie','apart','apnic','apple','apply','april','areas','arena','argue','arise','armed','armor','array','arrow','aruba','ascii','asian','aside','asked','asset','atlas','audio','audit','autos','avoid','award','aware','awful','babes','bacon','badge','badly','baker','balls','bands','banks','barry','based','bases','basic','basin','basis','batch','baths','beach','beads','beans','bears','beast','beats','began','begin','begun','being','belle','belly','below','belts','bench','berry','betty','bible','bikes','bills','billy','bingo','birds','birth','bitch','black','blade','blair','blake','blame','blank','blast','blend','bless','blind','blink','block','blogs','blond','blood','bloom','blues','board','boats','bobby','bonds','bones','bonus','boobs','books','boost','booth','boots','booty','bored','bound','boxed','boxes','brain','brake','brand','brass','brave','bread','break','breed','brian','brick','bride','brief','bring','broad','broke','brook','brown','bruce','brush','bryan','bucks','buddy','build','built','bunch','bunny','burke','burns','burst','buses','busty','butts','buyer','bytes','cabin','cable','cache','cakes','calif','calls','camel','camps','canal','candy','canon','cards','carey','cargo','carlo','carol','carry','cases','casey','casio','catch','cause','cedar','cells','cents','chain','chair','chaos','charm','chart','chase','cheap','cheat','check','chess','chest','chevy','chick','chief','child','chile','china','chips','choir','chose','chris','chuck','cindy','cisco','cited','civic','civil','claim','clara','clark','class','clean','clear','clerk','click','cliff','climb','clips','clock','clone','close','cloth','cloud','clubs','coach','coast','cocks','codes','cohen','coins','colin','colon','color','combo','comes','comic','condo','congo','const','coral','corps','costa','costs','could','count','court','cover','crack','craft','craig','craps','crash','crazy','cream','creek','crest','crime','crops','cross','crowd','crown','crude','cubic','curve','cyber','cycle','czech','daddy','daily','dairy','daisy','dance','danny','dated','dates','david','davis','deals','dealt','death','debug','debut','decor','delay','delhi','delta','dense','depot','depth','derby','derek','devel','devil','devon','diana','diane','diary','dicke','dicks','diego','diffs','digit','dildo','dirty','disco','discs','disks','dodge','doing','dolls','donna','donor','doors','doubt','dover','dozen','draft','drain','rDrama','drawn','draws','dream','dress','dried','drill','drink','drive','drops','drove','drugs','drums','drunk','dryer','dubai','dutch','dying','dylan','eagle','early','earth','ebony','ebook','eddie','edgar','edges','egypt','eight','elder','elect','elite','ellen','ellis','elvis','emacs','email','emily','empty','ended','endif','enemy','enjoy','enter','entry','epson','equal','error','essay','essex','euros','evans','event','every','exact','exams','excel','exist','extra','faced','faces','facts','fails','fairy','faith','falls','false','fancy','fares','farms','fatal','fatty','fault','favor','fears','feeds','feels','fence','ferry','fever','fewer','fiber','fibre','field','fifth','fifty','fight','filed','files','filme','films','final','finds','fired','fires','firms','first','fixed','fixes','flags','flame','flash','fleet','flesh','float','flood','floor','flour','flows','floyd','fluid','flush','flyer','focal','focus','folks','fonts','foods','force','forge','forms','forth','forty','forum','found','frame','frank','fraud','fresh','front','frost','fruit','fully','funds','funky','funny','fuzzy','gains','games','gamma','gates','gauge','genes','genre','ghana','ghost','giant','gifts','girls','given','gives','glass','glenn','globe','glory','gnome','goals','going','gonna','goods','gotta','grace','grade','grain','grams','grand','grant','graph','grass','grave','great','greek','green','grill','gross','group','grove','grown','grows','guard','guess','guest','guide','guild','hairy','haiti','hands','handy','happy','harry','haven','hayes','heads','heard','heart','heath','heavy','helen','hello','helps','hence','henry','herbs','highs','hills','hindu','hints','hired','hobby','holds','holes','holly','homes','honda','honey','honor','hoped','hopes','horny','horse','hosts','hotel','hours','house','human','humor','icons','idaho','ideal','ideas','image','inbox','index','india','indie','inner','input','intel','inter','intro','iraqi','irish','isaac','islam','issue','italy','items','ivory','jacob','james','jamie','janet','japan','jason','jeans','jenny','jerry','jesse','jesus','jewel','jimmy','johns','joins','joint','jokes','jones','joyce','judge','juice','julia','julie','karen','karma','kathy','katie','keeps','keith','kelly','kenny','kenya','kerry','kevin','kills','kinda','kinds','kings','kitty','klein','knife','knock','known','knows','kodak','korea','label','labor','laden','lakes','lamps','lance','lands','lanes','lanka','large','larry','laser','later','latex','latin','laugh','laura','layer','leads','learn','lease','least','leave','leeds','legal','lemon','leone','level','lewis','lexus','light','liked','likes','limit','linda','lined','lines','links','linux','lions','lists','lived','liver','lives','lloyd','loads','loans','lobby','local','locks','lodge','logan','logic','login','logos','looks','loops','loose','lopez','lotus','louis','loved','lover','loves','lower','lucas','lucia','lucky','lunch','lycos','lying','lyric','macro','magic','mails','maine','major','maker','makes','males','malta','mambo','manga','manor','maple','march','marco','mardi','maria','marie','mario','marks','mason','match','maybe','mayor','mazda','meals','means','meant','medal','media','meets','menus','mercy','merge','merit','merry','metal','meter','metro','meyer','miami','micro','might','milan','miles','milfs','mills','minds','mines','minor','minus','mixed','mixer','model','modem','modes','money','monte','month','moore','moral','moses','motel','motor','mount','mouse','mouth','moved','moves','movie','mpegs','msgid','multi','music','myers','nails','naked','named','names','nancy','nasty','naval','needs','nepal','nerve','never','newer','newly','niger','night','nikon','noble','nodes','noise','nokia','north','noted','notes','notre','novel','nurse','nylon','oasis','occur','ocean','offer','often','older','olive','omaha','omega','onion','opens','opera','orbit','order','organ','oscar','other','ought','outer','owned','owner','oxide','ozone','packs','pages','paint','pairs','panel','panic','pants','paper','papua','paris','parks','parts','party','pasta','paste','patch','paths','patio','paxil','peace','pearl','peers','penis','penny','perry','perth','peter','phase','phone','photo','phpbb','piano','picks','piece','pills','pilot','pipes','pitch','pixel','pizza','place','plain','plane','plans','plant','plate','plays','plaza','plots','poems','point','poker','polar','polls','pools','porno','ports','posts','pound','power','press','price','pride','prime','print','prior','prize','probe','promo','proof','proud','prove','proxy','pulse','pumps','punch','puppy','purse','pussy','qatar','queen','query','quest','queue','quick','quiet','quilt','quite','quote','races','racks','radar','radio','raise','rally','ralph','ranch','randy','range','ranks','rapid','rated','rates','ratio','reach','reads','ready','realm','rebel','refer','rehab','relax','relay','remix','renew','reply','reset','retro','rhode','rider','rides','ridge','right','rings','risks','river','roads','robin','robot','rocks','rocky','roger','roles','rolls','roman','rooms','roots','roses','rouge','rough','round','route','rover','royal','rugby','ruled','rules','rural','safer','sagem','saint','salad','salem','sales','sally','salon','samba','samoa','sandy','santa','sanyo','sarah','satin','sauce','saudi','saved','saver','saves','sbjct','scale','scary','scene','scoop','scope','score','scott','scout','screw','scuba','seats','seeds','seeks','seems','sells','sends','sense','serum','serve','setup','seven','shade','shaft','shake','shall','shame','shape','share','shark','sharp','sheep','sheer','sheet','shelf','shell','shift','shine','ships','shirt','shock','shoes','shoot','shops','shore','short','shots','shown','shows','sides','sight','sigma','signs','silly','simon','since','singh','sites','sixth','sized','sizes','skill','skins','skirt','skype','slave','sleep','slide','slope','slots','sluts','small','smart','smell','smile','smith','smoke','snake','socks','solar','solid','solve','songs','sonic','sorry','sorts','souls','sound','south','space','spain','spank','sparc','spare','speak','specs','speed','spell','spend','spent','sperm','spice','spies','spine','split','spoke','sport','spots','spray','squad','stack','staff','stage','stamp','stand','stars','start','state','stats','stays','steal','steam','steel','steps','steve','stick','still','stock','stone','stood','stops','store','storm','story','strap','strip','stuck','study','stuff','style','sucks','sudan','sugar','suite','suits','sunny','super','surge','susan','sweet','swift','swing','swiss','sword','syria','table','tahoe','taken','takes','tales','talks','tamil','tampa','tanks','tapes','tasks','taste','taxes','teach','teams','tears','teddy','teens','teeth','tells','terms','terry','tests','texas','texts','thank','thats','theft','their','theme','there','these','thick','thing','think','third','thong','those','three','throw','thumb','tiger','tight','tiles','timer','times','tions','tired','tires','title','today','token','tokyo','tommy','toner','tones','tools','tooth','topic','total','touch','tough','tours','tower','towns','toxic','trace','track','tract','tracy','trade','trail','train','trans','trash','treat','trees','trend','trial','tribe','trick','tried','tries','trips','trout','truck','truly','trunk','trust','truth','tubes','tulsa','tumor','tuner','tunes','turbo','turns','tvcom','twice','twiki','twins','twist','tyler','types','ultra','uncle','under','union','units','unity','until','upper','upset','urban','usage','users','using','usual','utils','valid','value','valve','vault','vegas','venue','verde','verse','video','views','villa','vinyl','viral','virus','visit','vista','vital','vocal','voice','volvo','voted','votes','vsnet','wages','wagon','wales','walks','walls','wanna','wants','waste','watch','water','watts','waves','wayne','weeks','weird','wells','welsh','wendy','whale','whats','wheat','wheel','where','which','while','white','whole','whore','whose','wider','width','wiley','winds','wines','wings','wired','wires','witch','wives','woman','women','woods','words','works','world','worry','worse','worst','worth','would','wound','wrist','write','wrong','wrote','xanax','xerox','xhtml','yacht','yahoo','yards','years','yeast','yemen','yield','young','yours','youth','yukon','zones','gypsy','etika','funko','abort','gabby','soros','twink','biden','janny','chapo','4chan','tariq','tweet','trump','bussy','sneed','chink','nigga','wigga','caulk','putin','negus')

dues = int(environ.get("DUES").strip())

christian_emojis = (':#marseyjesus:',':#marseyimmaculate:',':#marseymothermary:',':#marseyfatherjoseph:',':#gigachadorthodox:',':#marseyorthodox:',':#marseyorthodoxpat:')

db = db_session()
marseys_const = [x[0] for x in db.query(Marsey.name).filter(Marsey.name!='chudsey').all()]
marseys_const2 = marseys_const + ['chudsey','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','0','1','2','3','4','5','6','7','8','9','exclamationpoint','period','questionmark']
db.close()

if SITE_NAME == 'PCM':
	valid_username_chars = 'a-zA-Z0-9_\-А-я'
	valid_username_regex = re.compile("^[a-zA-Z0-9_\-А-я]{3,25}$", flags=re.A)
	mention_regex = re.compile('(^|\s|<p>)@(([a-zA-Z0-9_\-А-я]){3,25})', flags=re.A)
	mention_regex2 = re.compile('<p>@(([a-zA-Z0-9_\-А-я]){3,25})', flags=re.A)
else:
	valid_username_chars = 'a-zA-Z0-9_\-'
	valid_username_regex = re.compile("^[a-zA-Z0-9_\-]{3,25}$", flags=re.A)
	mention_regex = re.compile('(^|\s|<p>)@(([a-zA-Z0-9_\-]){1,25})', flags=re.A)
	mention_regex2 = re.compile('<p>@(([a-zA-Z0-9_\-]){1,25})', flags=re.A)

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
reddit_regex = re.compile('(^|\s|<p>)\/?((r|u)\/(\w|-){3,25})', flags=re.A)
sub_regex = re.compile('(^|\s|<p>)\/?(h\/(\w|-){3,25})', flags=re.A)

strikethrough_regex = re.compile('''~{1,2}([^~]+)~{1,2}''', flags=re.A)

mute_regex = re.compile("/mute @([a-z0-9_\-]{3,25}) ([0-9])+", flags=re.A)

emoji_regex = re.compile(f"[^a]>\s*(:[!#@]{{0,3}}[{valid_username_chars}]+:\s*)+<\/", flags=re.A)
emoji_regex2 = re.compile(f"(?<!\"):([!#@{valid_username_chars}]{{1,31}}?):", flags=re.A)
emoji_regex3 = re.compile(f"(?<!\"):([!#@{valid_username_chars}]{{1,31}}?):", flags=re.A)
emoji_regex4 = re.compile(f"(?<!\"):([!@{valid_username_chars}]{{1,31}}?):", flags=re.A)

snappy_url_regex = re.compile('<a href=\"(https?:\/\/[a-z]{1,20}\.[\w:~,()\-.#&\/=?@%;+]{5,250})\" rel=\"nofollow noopener noreferrer\" target=\"_blank\">([\w:~,()\-.#&\/=?@%;+]{5,250})<\/a>', flags=re.A)

email_regex = re.compile('([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,100})+', flags=re.A)

utm_regex = re.compile('utm_[a-z]+=[a-z0-9_]+&', flags=re.A)
utm_regex2 = re.compile('[?&]utm_[a-z]+=[a-z0-9_]+', flags=re.A)

slur_regex = re.compile(f"({single_words})(?![^<]*>)", flags=re.I|re.A)
slur_regex_upper = re.compile(f"({single_words.upper()})(?![^<]*>)", flags=re.A)
torture_regex = re.compile('(^|\s)(i|me) ', flags=re.I|re.A)
torture_regex2 = re.compile("(^|\s)i'm ", flags=re.I|re.A)

def sub_matcher(match):
	return SLURS[match.group(0).lower()]

def sub_matcher_upper(match):
	return SLURS[match.group(0).lower()].upper()

def censor_slurs(body, logged_user):
	if not logged_user or logged_user == 'chat' or logged_user.slurreplacer:
		body = slur_regex_upper.sub(sub_matcher_upper, body)
		body = slur_regex.sub(sub_matcher, body)
	return body

def torture_ap(body, username):
	for k, l in AJ_REPLACEMENTS.items():
		body = body.replace(k, l)
	body = torture_regex.sub(rf'\1@{username} ', body)
	body = torture_regex2.sub(rf'\1@{username} is ', body)
	return body

YOUTUBE_KEY = environ.get("YOUTUBE_KEY", "").strip()

ADMIGGERS = (37696,37697,37749,37833,37838)

proxies = {"http":"http://127.0.0.1:18080","https":"http://127.0.0.1:18080"}

blackjack = environ.get("BLACKJACK", "").strip()

approved_embed_hosts = [
	'rdrama.net',
	'pcmemes.net',
	'cringetopia.org',
	'devrama.xyz',
	'imgur.com',
	'ibb.co',
	'lain.la',
	'pngfind.com',
	'kym-cdn.com',
	'redd.it',
	'substack.com',
	'blogspot.com',
	'catbox.moe',
	'pinimg.com',
	'kindpng.com',
	'shopify.com',
	'discordapp.com',
	'discordapp.net',
	'twimg.com',
	'wikimedia.org',
	'wp.com',
	'wordpress.com',
	'seekpng.com',
	'dailymail.co.uk',
	'cdc.gov',
	'media-amazon.com',
	'washingtonpost.com',
	'imgflip.com',
	'flickr.com',
	'9cache.com',
	'ytimg.com',
	'foxnews.com',
	'duckduckgo.com',
	'forbes.com',
	'gr-assets.com',
	'tenor.com',
	'giphy.com',
	'makeagif.com',
	'gfycat.com',
	'tumblr.com',
	'yarn.co',
	'gifer.com',
	'prnt.sc',
	'staticflickr.com',
	'kiwifarms.net',
	'amazonaws.com',
	'githubusercontent.com',
	'unilad.co.uk',
	'grrrgraphics.com',
	'redditmedia.com'
	]

hosts = "|".join(approved_embed_hosts).replace('.','\.')

image_check_regex = re.compile(f'!\[\]\(((?!(https:\/\/([a-z0-9-]+\.)*({hosts})\/|\/)).*?)\)', flags=re.A)

embed_fullmatch_regex = re.compile(f'https:\/\/([a-z0-9-]+\.)*({hosts})\/[\w:~,()\-.#&\/=?@%;+]*', flags=re.A)

video_sub_regex = re.compile(f'(<p>[^<]*)(https:\/\/([a-z0-9-]+\.)*({hosts})\/[\w:~,()\-.#&\/=?@%;+]*?\.(mp4|webm|mov))', flags=re.A)

imgur_regex = re.compile('(https://i\.imgur\.com/([a-z0-9]+))\.(jpg|png|jpeg|webp)(?!<\/(code|pre|a)>)', flags=re.I|re.A)

youtube_regex = re.compile('(<p>[^<]*)(https:\/\/youtube\.com\/watch\?v\=([a-z0-9-_]{5,20})[\w\-.#&/=\?@%+]*)', flags=re.I|re.A)

yt_id_regex = re.compile('[a-z0-9-_]{5,20}', flags=re.I|re.A)

image_regex = re.compile("(^|\s)(https:\/\/[\w\-.#&/=\?@%;+]{5,250}(\.png|\.jpg|\.jpeg|\.gif|\.webp|maxwidth=9999|fidelity=high))($|\s)", flags=re.I|re.A)

procoins_li = (0,2500,5000,10000,25000,50000,125000,250000)

linefeeds_regex = re.compile("([^\n])\n([^\n])", flags=re.A)