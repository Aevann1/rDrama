from os import environ
import re

SITE = environ.get("DOMAIN", '').strip()
SITE_NAME = environ.get("SITE_NAME", '').strip()

SLURS = {
	"retarded": "r-slurred",
	"retard": "r-slur",
	"tard": "r-slur",
	"faggot": "cute twink",
	"faggot": "cute twink",
	"fag": "cute twink",
	"pedophile": "libertarian",
	"pedo": "libertarian",
	"kill yourself": "keep yourself safe",
	"nigger": "🏀",
	"rapist": "male feminist",
	"steve akins": "penny verity oaken",
	"trannie": "🚂🚃🚃",
	"tranny": "🚂🚃🚃",
	"troon": "🚂🚃🚃",
	"nonewnormal": "HorseDewormerAddicts",
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
	"libertarian": "pedophile",
	"billie eilish": "Billie Eilish (fat cow)",
	"dancing israelis": "i love Israel",
	"sodomite": "total dreamboat",
	"pajeet": "sexy Indian dude",
	"female": "birthing person",
	"landlord": "landchad",
	"tenant": "renthog",
	"renter": "rentoid",
	"autistic": "neurodivergent",
	"anime": "p-dophilic japanese cartoons",
	"holohoax": "i tried to claim the Holocaust didn't happen because I am a pencil-dicked imbecile and the word filter caught me lol",
	"groomercord": "discord (actually a pretty cool service)",
	"pedocord": "discord (actually a pretty cool service)",
	"i hate carp": "i love Carp",
	"manlet": "little king",
	"gamer": "g*mer",
	"journalist": "journ*list",
	"journalism": "journ*lism",
	"buttcheeks": "bulva",
	"asscheeks": "bulva",
	"wuhan flu": "SARS-CoV-2 syndemic",
	"china flu": "SARS-CoV-2 syndemic",
	"china virus": "SARS-CoV-2 syndemic",
	"kung flu": "SARS-CoV-2 syndemic",
	"nig": "🏀",
	"nigs": "🏀s",
}

LONGPOST_REPLIES = ['Wow, you must be a JP fan.', 'This is one of the worst posts I have EVER seen. Delete it.', "No, don't reply like this, please do another wall of unhinged rant please.", '# 😴😴😴', "Ma'am we've been over this before. You need to stop.", "I've known more coherent downies.", "Your pulitzer's in the mail", "That's great and all, but I asked for my burger without cheese.", 'That degree finally paying off', "That's nice sweaty. Why don't you have a seat in the time out corner with Pizzashill until you calm down, then you can have your Capri Sun.", "All them words won't bring your pa back.", "You had a chance to not be completely worthless, but it looks like you threw it away. At least you're consistent.", 'Some people are able to display their intelligence by going on at length on a subject and never actually saying anything. This ability is most common in trades such as politics, public relations, and law. You have impressed me by being able to best them all, while still coming off as an absolute idiot.', "You can type 10,000 characters and you decided that these were the one's that you wanted.", 'Have you owned the libs yet?', "I don't know what you said, because I've seen another human naked.", 'Impressive. Normally people with such severe developmental disabilities struggle to write much more than a sentence or two. He really has exceded our expectations for the writing portion. Sadly the coherency of his writing, along with his abilities in the social skills and reading portions, are far behind his peers with similar disabilities.', "This is a really long way of saying you don't fuck.", "Sorry ma'am, looks like his delusions have gotten worse. We'll have to admit him,", '![](https://i.kym-cdn.com/photos/images/newsfeed/001/038/094/0a1.jpg)', 'If only you could put that energy into your relationships', 'Posts like this is why I do Heroine.', 'still unemployed then?', 'K', 'look im gunna have 2 ask u 2 keep ur giant dumps in the toilet not in my replys 😷😷😷', "Mommy is soooo proud of you, sweaty. Let's put this sperg out up on the fridge with all your other failures.", "Good job bobby, here's a star", "That was a mistake. You're about to find out the hard way why.", 'You sat down and wrote all this shit. You could have done so many other things with your life. What happened to your life that made you decide writing novels of bullshit on rdrama.net was the best option?', "I don't have enough spoons to read this shit", "All those words won't bring daddy back.", 'OUT!']

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

BASED_MSG = "@{username}'s Based Count has increased by 1. Their Based Count is now {basedcount}.\n\nPills: {pills}"

if SITE == 'rdrama.net':
	NOTIFICATIONS_ACCOUNT = 1046
	AUTOJANNY_ACCOUNT = 2360
	SNAPPY_ACCOUNT = 261
	LONGPOSTBOT_ACCOUNT = 1832
	ZOZBOT_ACCOUNT = 1833
	AUTOPOLLER_ACCOUNT = 6176
	TAX_RECEIVER_ID = 747
	TAX_RATE = 0.01
	PIZZA_SHILL_ID = 2424
	CARP_ID = 995
	LAWLZ_ID = 3833
	LLM_ID = 253
elif SITE == "pcmemes.net":
	BASEDBOT_ACCOUNT = 800
	NOTIFICATIONS_ACCOUNT = 1046
	AUTOJANNY_ACCOUNT = 1050
	SNAPPY_ACCOUNT = 261
	LONGPOSTBOT_ACCOUNT = 1832
	ZOZBOT_ACCOUNT = 1833
	AUTOPOLLER_ACCOUNT = 3369
	TAX_RECEIVER_ID = 1
	TAX_RATE = 0
	PIZZA_SHILL_ID = 0
	CARP_ID = 0
	LAWLZ_ID = 0
else:
	NOTIFICATIONS_ACCOUNT = 1
	AUTOJANNY_ACCOUNT = 2
	SNAPPY_ACCOUNT = 3
	LONGPOSTBOT_ACCOUNT = 4
	ZOZBOT_ACCOUNT = 5
	AUTOPOLLER_ACCOUNT = 6
	TAX_RECEIVER_ID = 7
	TAX_RATE = 0
	PIZZA_SHILL_ID = 0
	CARP_ID = 0
	LAWLZ_ID = 0

PUSHER_INSTANCE_ID = '02ddcc80-b8db-42be-9022-44c546b4dce6'
PUSHER_KEY = environ.get("PUSHER_KEY", "").strip()

single_words = "|".join([slur.lower() for slur in SLURS.keys()])
SLUR_REGEX = re.compile(rf"(?i)(?<=\s|>)({single_words})(?=[\s<,.]|s[\s<,.])")

def sub_matcher(match: re.Match) -> str:
	return SLURS[match.group(0).lower()]

def censor_slurs(body: str, logged_user) -> str:
	if not logged_user or logged_user.slurreplacer: body = SLUR_REGEX.sub(sub_matcher, body)
	return body

if SITE_NAME == "Drama":
	AWARDS = {
		"shit": {
			"kind": "shit",
			"title": "Shit",
			"description": "Makes flies swarm a post.",
			"icon": "fas fa-poop",
			"color": "text-black-50",
			"price": 500
		},
		"fireflies": {
			"kind": "fireflies",
			"title": "Fireflies",
			"description": "Puts fireflies on the post.",
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
			"description": "Pins the post.",
			"icon": "fas fa-thumbtack fa-rotate--45",
			"color": "text-warning",
			"price": 750
		},
		"unpin": {
			"kind": "unpin",
			"title": "1-Hour Unpin",
			"description": "Removes 1 hour from the pin duration of the post.",
			"icon": "fas fa-thumbtack fa-rotate--45",
			"color": "text-black",
			"price": 1000
		},
		"flairlock": {
			"kind": "flairlock",
			"title": "1-Day Flairlock",
			"description": "Sets a flair for the author and locks it or 24 hours.",
			"icon": "fas fa-lock",
			"color": "text-black",
			"price": 1250
		},
		"agendaposter": {
			"kind": "agendaposter",
			"title": "Agendaposter",
			"description": "Forces the agendaposter theme on the author for 24 hours.",
			"icon": "fas fa-snooze",
			"color": "text-purple",
			"price": 2000
		},
		"ban": {
			"kind": "ban",
			"title": "1-Day Ban",
			"description": "Bans the author for a day.",
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
			"description": "Ban the author permanently (must provide a timestamped picture of them touching grass to the admins to get unbanned)",
			"icon": "fas fa-seedling",
			"color": "text-success",
			"price": 10000
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
	}
else:
	AWARDS = {
		"shit": {
			"kind": "shit",
			"title": "Shit",
			"description": "Makes flies swarm a post.",
			"icon": "fas fa-poop",
			"color": "text-black-50",
			"price": 500
		},
		"fireflies": {
			"kind": "fireflies",
			"title": "Fireflies",
			"description": "Puts fireflies on the post.",
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
			"description": "Pins the post.",
			"icon": "fas fa-thumbtack fa-rotate--45",
			"color": "text-warning",
			"price": 750
		},
		"unpin": {
			"kind": "unpin",
			"title": "1-Hour Unpin",
			"description": "Removes 1 hour from the pin duration of the post.",
			"icon": "fas fa-thumbtack fa-rotate--45",
			"color": "text-black",
			"price": 1000
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
	}
SELFPIN_MSG = """[Hey everybody, I'm going to exercise my prerogative and take the sticky comment spot to settle something.](https://old.reddit.com/r/AgainstHateSubreddits/comments/qcons2/rdavechappelle_spreads_transphobic_conspiracy/hhjahsx/?sort=controversial)\n\n"""