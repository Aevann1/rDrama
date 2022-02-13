from os import environ
import requests
import threading
from .const import *

SERVER_ID = environ.get("DISCORD_SERVER_ID",'').strip()
CLIENT_ID = environ.get("DISCORD_CLIENT_ID",'').strip()
CLIENT_SECRET = environ.get("DISCORD_CLIENT_SECRET",'').strip()
BOT_TOKEN = environ.get("DISCORD_BOT_TOKEN",'').strip()
AUTH = environ.get("DISCORD_AUTH",'').strip()

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

def send_discord_message(message):
	headers = {"Authorization": f"Bot {BOT_TOKEN}"}
	data={"content": message}
	requests.post("https://discordapp.com/api/channels/924485611715452940/messages", headers=headers, data=data, timeout=5)
	requests.post("https://discordapp.com/api/channels/924486091795484732/messages", headers=headers, data=data, timeout=5)