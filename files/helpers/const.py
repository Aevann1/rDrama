from os import environ
import re

SITE = environ.get("DOMAIN", '').strip()
SITE_NAME = environ.get("SITE_NAME", '').strip()

AJ_REPLACEMENTS = {
	"you're": '$#3$2',
	'your': "you're",
	'$#3$2': 'your',

	"too": '$#3$3',
	'to': "too",
	'$#3$3': 'to',
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
	"nig": "BIPOC",
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
	"mohammad": "Mohammad (PBUH)",
	"muhammad": "Mohammad (PBUH)",
	"i hate marsey": "i love marsey",
	"billie eilish": "Billie Eilish (fat cow)",
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
}

LONGPOST_REPLIES = ['Wow, you must be a JP fan.', 'This is one of the worst posts I have EVER seen. Delete it.', "No, don't reply like this, please do another wall of unhinged rant please.", '# 😴😴😴', "Ma'am we've been over this before. You need to stop.", "I've known more coherent downies.", "Your pulitzer's in the mail", "That's great and all, but I asked for my burger without cheese.", 'That degree finally paying off', "That's nice sweaty. Why don't you have a seat in the time out corner with Pizzashill until you calm down, then you can have your Capri Sun.", "All them words won't bring your pa back.", "You had a chance to not be completely worthless, but it looks like you threw it away. At least you're consistent.", 'Some people are able to display their intelligence by going on at length on a subject and never actually saying anything. This ability is most common in trades such as politics, public relations, and law. You have impressed me by being able to best them all, while still coming off as an absolute idiot.', "You can type 10,000 characters and you decided that these were the one's that you wanted.", 'Have you owned the libs yet?', "I don't know what you said, because I've seen another human naked.", 'Impressive. Normally people with such severe developmental disabilities struggle to write much more than a sentence or two. He really has exceded our expectations for the writing portion. Sadly the coherency of his writing, along with his abilities in the social skills and reading portions, are far behind his peers with similar disabilities.', "This is a really long way of saying you don't fuck.", "Sorry ma'am, looks like his delusions have gotten worse. We'll have to admit him,", ':#marseywoah:', 'If only you could put that energy into your relationships', 'Posts like this is why I do Heroine.', 'still unemployed then?', 'K', 'look im gunna have 2 ask u 2 keep ur giant dumps in the toilet not in my replys 😷😷😷', "Mommy is soooo proud of you, sweaty. Let's put this sperg out up on the fridge with all your other failures.", "Good job bobby, here's a star", "That was a mistake. You're about to find out the hard way why.", 'You sat down and wrote all this shit. You could have done so many other things with your life. What happened to your life that made you decide writing novels of bullshit on rdrama.net was the best option?', "I don't have enough spoons to read this shit", "All those words won't bring daddy back.", 'OUT!']

AGENDAPOSTER_MSG = """Hi @{username},\n\nYour comment has been automatically removed because you forgot
		to include `trans lives matter`.\n\nDon't worry, we're here to help! We 
		won't let you post or comment anything that doesn't express your love and acceptance towards 
		the trans community. Feel free to resubmit your comment with `trans lives matter` 
		included. \n\n*This is an automated message; if you need help,
		you can message us [here](/contact).*"""

VAXX_MSG = """Hi @{username}, it appears that you may be trying to spread dangerous misinformation regarding ineffective COVID-19 treatments based on pseudoscientific hearsay. Your post has been removed because it contained the word ivermectin. We ask that you understand that horse dewormer neither treats, nor prevents, COVID-19. For more information, please read up on what the FDA has to say on the matter:

https://www.fda.gov/consumers/consumer-updates/why-you-should-not-use-ivermectin-treat-or-prevent-covid-19

COVID-19 is not a joke, it is a global pandemic and it has been hard on all of us. It will likely go down as one of the most defining periods of our generation. Many of us have lost loved ones to the virus. It has caused confusion, fear, frustration, and served to further divide us. Tens of millions around the world have died. There is nothing to be gained by spreading bad science based on very understandable fear.

The only proven method of prevention is the COVID-19 vaccine, paired with appropriate social distancing, handwashing, and masks. Vaccines are free in the United States - if you'd like to locate your nearest vaccine provider, please visit https://www.vaccines.gov/ and schedule an appointment today.

Thank you."""

WELCOME_MSG = "Hi there! It's me, your soon-to-be favorite rDrama user @carpathianflorist here to give you a brief rundown on some of the sick features we have here. You'll probably want to start by following me, though. So go ahead and click my name and then smash that Follow button. This is actually really important, so go on. Hurry.\n\nThanks!\n\nNext up: If you're a member of the media, similarly just shoot me a DM and I'll set about verifying you and then we can take care of your sad journalism stuff.\n\n**FOR EVERYONE ELSE**\n\n Begin by navigating to [the settings page](https://rdrama.net/settings/profile) (we'll be prettying this up so it's less convoluted soon, don't worry) and getting some basic customization done.\n\n### Themes\n\nDefinitely change your theme right away, the default one (Midnight) is pretty enough, but why not use something *exotic* like Win98, or *flashy* like Tron? Even Coffee is super tasteful and way more fun than the default. More themes to come when we get around to it!\n\n### Avatar/pfp\n\nYou'll want to set this pretty soon; without uploading one, I put together a randomly-assigned selection of 180ish pictures of furries, ugly goths, mujahideen, anime girls, and My Little Ponys which are used by everyone who was too lazy to set a pfp. Set the banner too while you're at it. Your profile is important!\n\n### Flairs\n\nSince you're already on the settings page, you may as well set a flair, too. As with your username, you can - obviously - choose the color of this, either with a hex value or just from the preset colors. And also like your username, you can change this at any time. [Paypigs](https://marsey1.gumroad.com/l/tfcvri) can even further relive the glory days of 90s-00s internet and set obnoxious signatures.\n\n### PROFILE ANTHEMS\n\nSpeaking of profiles, hey, remember MySpace? Do you miss autoplaying music assaulting your ears every time you visited a friend's page? Yeah, we brought that back. Enter a YouTube URL, wait a few seconds for it to process, and then BAM! you've got a profile anthem which people cannot mute. Unless they spend 20,000 dramacoin in the shop for a mute button. Which you can then remove from your profile by spending 40,000 dramacoin on an unmuteable anthem. Get fucked poors!\n\n### Dramacoin?\n\nDramacoin is basically our take on the karma system. Except unlike the karma system, it's not gay and boring and stupid and useless. Dramacoin can be spent at [Marsey's Dramacoin Emporium](https://rdrama.net/shop) on upgrades to your user experience (many more coming than what's already listed there), and best of all on tremendously annoying awards to fuck with your fellow dramautists. We're always adding more, so check back regularly in case you happen to miss one of the announcement posts. Holiday-themed awards are currently unavailable while we resolve an internal dispute, but they **will** return, no matter what some other janitors insist.\n\nLike karma, dramacoin is obtained by getting upvotes on your threads and comments. *Unlike* karma, it's also obtained by getting downvotes on your threads and comments. Downvotes don't really do anything here - they pay the same amount of dramacoin and they increase thread/comment ranking just the same as an upvote. You just use them to express petty disapproval and hopefully start a fight. Because all votes are visible here. To hell with your anonymity.\n\nDramacoin can also be traded amongst users from their profiles. Note that there is a 3% transaction fee.\n\n**Dramacoin and shop items cannot be purchased with real money and this will not change.** Though we are notoriously susceptible to bribes, so definitely shoot your shot. It'll probably go well, honestly.\n\n### Badges\n\nRemember all those neat little metallic icons you saw on my profile when you were following me? If not, scroll back up and go have a look. And doublecheck to make sure you pressed the Follow button. Anyway, those are badges. You earn them by doing a variety of things. Some of them even offer benefits, like discounts at the shop. A [complete list of badges and their requirements can be found here](https://rdrama.net/badges), though I add more pretty regularly, so keep an eye on the changelog.\n\n### Other stuff\n\nWe're always adding new features, and we take a fun-first approach to development. If you have a suggestion for something that would be fun, funny, annoying - or best of all, some combination of all three - definitely make a thread about it. Or just DM me if you're shy. Weirdo. Anyway there's also the [leaderboards](https://rdrama.net/leaderboard), boring stuff like two-factor authentication you can toggle on somewhere in the settings page (psycho), the ability to save posts and comments, close to a thousand emojis already (several hundred of which are rDrama originals), and on and on and on and on. This is just the basics, mostly to help you get acquainted with some of the things you can do here to make it more easy on the eyes, customizable, and enjoyable. If you don't enjoy it, just go away! We're not changing things to suit you! Get out of here loser! And no, you can't delete your account :na:\n\nI love you.<BR>*xoxo Carp* 💋"

if 'rdrama.net' in SITE:
	BASEDBOT_ID = 0
	KIPPY_ID = 7150
	NOTIFICATIONS_ID = 1046
	AUTOJANNY_ID = 2360
	SNAPPY_ID = 261
	LONGPOSTBOT_ID = 1832
	ZOZBOT_ID = 1833
	AUTOPOLLER_ID = 6176
	AUTOBETTER_ID = 7668
	TAX_RECEIVER_ID = 747
	PIZZA_SHILL_ID = 2424
	IDIO_ID = 30
	CARP_ID = 995
	JOAN_ID = 28
	AEVANN_ID = 1
	KLEN_ID = 2050
	LAWLZ_ID = 3833
	LLM_ID = 253
	DAD_ID = 2513
	MOM_ID = 4588
	DONGER_ID = 541
	FARTBINN_ID = 2256 
	BUG_THREAD = 18459
	EMOJI_THREAD = 16583
elif SITE == "pcmemes.net":
	BASEDBOT_ID = 800
	KIPPY_ID = 1592
	NOTIFICATIONS_ID = 1046
	AUTOJANNY_ID = 1050
	SNAPPY_ID = 261
	LONGPOSTBOT_ID = 1832
	ZOZBOT_ID = 1833
	AUTOPOLLER_ID = 3369
	AUTOBETTER_ID = 0
	TAX_RECEIVER_ID = 1592
	PIZZA_SHILL_ID = 0
	IDIO_ID = 0
	CARP_ID = 0
	JOAN_ID = 0
	AEVANN_ID = 1
	KLEN_ID = 0
	LAWLZ_ID = 0
	LLM_ID = 0
	DAD_ID = 0
	MOM_ID = 0
	DONGER_ID = 0
	FARTBINN_ID = 0
	BUG_THREAD = 4103
	EMOJI_THREAD = 0
else:
	BASEDBOT_ID = 0
	KIPPY_ID = 0
	NOTIFICATIONS_ID = 1
	AUTOJANNY_ID = 2
	SNAPPY_ID = 3
	LONGPOSTBOT_ID = 4
	ZOZBOT_ID = 5
	AUTOPOLLER_ID = 6
	AUTOBETTER_ID = 7
	TAX_RECEIVER_ID = 8
	PIZZA_SHILL_ID = 0
	IDIO_ID = 0
	CARP_ID = 0
	JOAN_ID = 0
	AEVANN_ID = 0
	KLEN_ID = 0
	LAWLZ_ID = 0
	LLM_ID = 0
	DAD_ID = 0
	MOM_ID = 0
	DONGER_ID = 0
	FARTBINN_ID = 0
	BUG_THREAD = 0
	EMOJI_THREAD = 0

PUSHER_INSTANCE_ID = '02ddcc80-b8db-42be-9022-44c546b4dce6'
PUSHER_KEY = environ.get("PUSHER_KEY", "").strip()

single_words = "|".join([slur.lower() for slur in SLURS.keys()])
SLUR_REGEX = re.compile(rf"(?i)((?<=\s|>)|^)({single_words})((?=[\s<,.]|s[\s<,.])|$)")

def sub_matcher(match: re.Match) -> str:
	return SLURS[match.group(0).lower()]

def censor_slurs(body: str, logged_user) -> str:
	if not logged_user or logged_user.slurreplacer: body = SLUR_REGEX.sub(sub_matcher, body)
	return body

def censor_slurs2(body: str) -> str:
	return SLUR_REGEX.sub(sub_matcher, body)

BADGES = {
	1: {
		'name': 'Alpha User',
		'description': 'Joined during open alpha'
	},
	2: {
		'name': 'Verified Email',
		'description': 'Verified Email'
	},
	3: {
		'name': 'Code Contributor',
		'description': 'Contributed to Drama source code'
	},
	4: {
		'name': 'White Hat',
		'description': 'Responsibly reported a security issue'
	},
	6: {
		'name': 'Beta User',
		'description': 'Joined during open beta'
	},
	7: {
		'name': 'Bug Finder',
		'description': 'Found a bug'
	},
	10: {
		'name': 'Bronze Recruiter',
		'description': 'Recruited 1 friend to join Drama'
	},
	11: {
		'name': 'Silver Recruiter',
		'description': 'Recruited 10 friends to join Drama'
	},
	12: {
		'name': 'Gold Recruiter',
		'description': 'Recruited 100 friends to join Drama'
	},
	15: {
		'name': 'Idea Maker',
		'description': 'Had a good idea for Drama which was implemented by the developers'
	},
	16: {
		'name': 'Marsey Master',
		'description': 'Contributed 10 (or more!!!!) Marsey emojis ✨'
	},
	17: {
		'name': 'Marsey Artisan',
		'description': 'Contributed a Marsey emoji ✨'
	},
	18: {
		'name': 'Artisan',
		'description': 'Contributed to Drama artwork'
	},
	21: {
		'name': 'Paypig',
		'description': 'Contributed at least $5'
	},
	22: {
		'name': 'Renthog',
		'description': 'Contributed at least $10'
	},
	23: {
		'name': 'Landchad',
		'description': 'Contributed at least $20'
	},
	24: {
		'name': 'Terminally online turboautist',
		'description': 'Contributed at least $50'
	},
	25: {
		'name': 'Rich Bich',
		'description': 'Contributed at least $100'
	},
	26: {
		'name': 'Agendaposter',
		'description': 'Forced to use the agendaposter theme'
	},
	27: {
		'name': 'Lolcow',
		'description': 'Beautiful and valid milk provider'
	},
	58: {
		'name': 'Diamond Recruiter',
		'description': 'Recruited 1000 friends to join Drama'
	},
	60: {
		'name': 'Unironically Retarded',
		'description': 'Demonstrated a wholesale inability to read the room'
	},
	61: {
		'name': 'Lab Rat',
		'description': 'Helped test features in development'
	},
	62: {
		'name': 'Master Baiter',
		'description': 'For outstanding achievement in the field of catching fish'
	},
	63: {
		'name': 'Balls',
		'description': 'I wrote carp on my balls as a sign of submission'
	},
	64: {
		'name': 'The Other Kind Of Good Journalist',
		'description': 'Contributed positive media attention to rDrama'
	},
	65: {
		'name': '2021 Spooooooky Marsey Artist',
		'description': 'Contributed a VERY SCARY Marsey for Halloween 2021!'
	},
	66: {
		'name': 'Sk8r Boi',
		'description': 'Certifies that this user is NOT a poser'
	},
	67: {
		'name': 'Unpausable',
		'description': 'Spent 40,000 dramacoins on an unpausable profile anthem'
	},
	68: {
		'name': 'Pause Button',
		'description': 'Spent 20,000 dramacoins on a profile anthem pause button'
	},
	69: {
		'name': 'Little Big Spender',
		'description': 'Dropped 10,000 dramacoins at the shop'
	},
	70: {
		'name': 'Big Spender',
		'description': 'Dropped 100,000 dramacoins at the shop'
	},
	71: {
		'name': 'Big Big Spender',
		'description': 'Dropped 250,000 dramacoins at the shop'
	},
	72: {
		'name': 'Big Big Big Spender',
		'description': 'Dropped 500,000 dramacoins at the shop'
	},
	73: {
		'name': 'Le Rich Gentlesir',
		'description': 'Spent a fucking million dramacoins at the shop'
	},
	74: {
		'name': 'Grass Toucher',
		'description': 'Awarded for molesting plant life'
	},
	75: {
		'name': 'Halloween 21',
		'description': 'Awarded for surviving Homoween 2021'
	},
	76: {
		'name': 'Low Roller',
		'description': 'Bought 10 lootboxes'
	},
	77: {
		'name': 'Middle Roller',
		'description': 'Bought 50 lootboxes'
	},
	78: {
		'name': 'High Roller',
		'description': 'Bought 150 lootboxes'
	},
	79: {
		'name': 'Merchant',
		'description': "Contributed a new line of product to Marsey's Coin Emporium"
	},
	80: {
		'name': 'Artist Laureate',
		'description': ''
	},
	81: {
		'name': 'Patron of the Arts',
		'description': 'Sponsored the creation of an approved Marsey'
	},
	82: {
		'name': 'Background',
		'description': 'Bought a profile background from the shop'
	},
	83: {
		'name': 'All-Seeing Eye',
		'description': 'Can view private profiles'
	},
	84: {
		'name': 'Alt-Seeing Eye',
		'description': 'Can see alts'
	},
	85: {
		'name': 'Sigma User',
		'description': ''
	},
	86: {
		'name': 'Holly Jolly Marsey Artist',
		'description': 'Contributed a VERY JOLLY Marsey for Christmas 2021!'
	},
	87: {
		'name': 'Unblockable',
		'description': 'This user is unblockable'
	},
        88: {
		'name': 'Provider',
		'description': 'This user provided a bountiful feast for Thanksgiving'
	},
        89: {
		'name': 'Dinner',
		'description': 'Yes, it is edible'
	},
        90: {
		'name': 'Fish',
		'description': 'This user cannot be unfollowed'
	},
	91: {
		'name': 'Grinch',
		'description': 'This user is a joyless grinch who pays money to avoid having fun'
	},
}

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
	"ghosts": {
		"kind": "ghosts",
		"title": "Ghosts",
		"description": "???",
		"icon": "fas fa-ghost",
		"color": "text-white",
		"price": 200
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
		"title": "Homoween Lootbox",
		"description": "???",
		"icon": "fas fa-treasure-chest",
		"color": "text-orange",
		"price": 1000
	},
	"shit": {
		"kind": "shit",
		"title": "Shit",
		"description": "Makes flies swarm the post.",
		"icon": "fas fa-poop",
		"color": "text-black-50",
		"price": 500
	},
	"fireflies": {
		"kind": "fireflies",
		"title": "Fireflies",
		"description": "Makes fireflies swarm the post.",
		"icon": "fas fa-sparkles",
		"color": "text-warning",
		"price": 500
	},
	"train": {
		"kind": "train",
		"title": "Train",
		"description": "Summons a train on the post.",
		"icon": "fas fa-train",
		"color": "text-pink",
		"price": 500
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
		"title": "Agendaposter",
		"description": "Forces the agendaposter theme on the recipient for 24 hours.",
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
	"grass": {
		"kind": "grass",
		"title": "Grass",
		"description": "Ban the recipient permanently (must provide a timestamped picture of them touching grass to the admins to get unbanned)",
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

AWARDS2 = {
	"shit": {
		"kind": "shit",
		"title": "Shit",
		"description": "Makes flies swarm the post.",
		"icon": "fas fa-poop",
		"color": "text-black-50",
		"price": 500
	},
	"fireflies": {
		"kind": "fireflies",
		"title": "Fireflies",
		"description": "Makes fireflies swarm the post.",
		"icon": "fas fa-sparkles",
		"color": "text-warning",
		"price": 500
	},
	"train": {
		"kind": "train",
		"title": "Train",
		"description": "Summons a train on the post.",
		"icon": "fas fa-train",
		"color": "text-pink",
		"price": 500
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
		"title": "Agendaposter",
		"description": "Forces the agendaposter theme on the recipient for 24 hours.",
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
	"grass": {
		"kind": "grass",
		"title": "Grass",
		"description": "Ban the recipient permanently (must provide a timestamped picture of them touching grass to the admins to get unbanned)",
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
	'dong': FARTBINN_ID
}
