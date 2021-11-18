from os import environ
import requests
import threading

SERVER_ID = environ.get("DISCORD_SERVER_ID",'').strip()
CLIENT_ID = environ.get("DISCORD_CLIENT_ID",'').strip()
CLIENT_SECRET = environ.get("DISCORD_CLIENT_SECRET",'').strip()
BOT_TOKEN = environ.get("DISCORD_BOT_TOKEN",'').strip()
AUTH = environ.get("DISCORD_AUTH",'').strip()

ROLES={
	"owner": "864612849199480914",
	"admin": "879459632656048180" if environ.get("DOMAIN") == "pcmemes.net" else "846509661288267776",
	"linked": "890342909390520382",
	"1": "868129042346414132",
	"2": "875569477671067688",
	"3": "869434199575236649",
	"4": "868140288013664296",
	"5": "880445545771044884",
	"8": "886781932430565418",
	}

def discord_wrap(f):

	def wrapper(*args, **kwargs):

		user=args[0]
		if not user.discord_id:
			return


		thread=threading.Thread(target=f, args=args, kwargs=kwargs)
		thread.start()

	wrapper.__name__=f.__name__
	return wrapper



@discord_wrap
def add_role(user, role_name):
	role_id = ROLES[role_name]
	url = f"https://discordapp.com/api/guilds/{SERVER_ID}/members/{user.discord_id}/roles/{role_id}"
	headers = {"Authorization": f"Bot {BOT_TOKEN}"}
	requests.put(url, headers=headers, timeout=5)

@discord_wrap
def remove_user(user):
	url=f"https://discordapp.com/api/guilds/{SERVER_ID}/members/{user.discord_id}"
	headers = {"Authorization": f"Bot {BOT_TOKEN}"}
	requests.delete(url, headers=headers, timeout=5)

@discord_wrap
def set_nick(user, nick):
	url=f"https://discordapp.com/api/guilds/{SERVER_ID}/members/{user.discord_id}"
	headers = {"Authorization": f"Bot {BOT_TOKEN}"}
	data={"nick": nick}
	requests.patch(url, headers=headers, json=data, timeout=5)

def send_message(message):
	url=f"https://discordapp.com/api/channels/851846904283267094/messages"
	headers = {"Authorization": f"Bot {BOT_TOKEN}"}
	data={"content": message}
	requests.post(url, headers=headers, data=data, timeout=5)