from files.helpers.wrappers import *
from files.helpers.security import *
from files.helpers.discord import add_role
from files.__main__ import app
import requests

SERVER_ID = environ.get("DISCORD_SERVER_ID",'').strip()
CLIENT_ID = environ.get("DISCORD_CLIENT_ID",'').strip()
CLIENT_SECRET = environ.get("DISCORD_CLIENT_SECRET",'').strip()
BOT_TOKEN = environ.get("DISCORD_BOT_TOKEN").strip()
COINS_NAME = environ.get("COINS_NAME").strip()
DISCORD_ENDPOINT = "https://discordapp.com/api/v6"
WELCOME_CHANNEL="846509313941700618"
SITE_NAME = environ.get("SITE_NAME", "").strip()

@app.get("/discord")
@auth_required
def join_discord(v):
	
	if v.is_suspended != 0 and v.admin_level == 0: return "Banned users cannot join the discord server!"
	
	if SITE_NAME == 'Drama' and v.admin_level == 0 and v.patron == 0 and v.truecoins < 150: return f"You must earn 150 {COINS_NAME} before entering the Discord server. You earn {COINS_NAME} by making posts/comments and getting upvoted."
	
	if v.shadowbanned or v.agendaposter: return ""

	now=int(time.time())

	state=generate_hash(f"{now}+{v.id}+discord")

	state=f"{now}.{state}"

	return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri=https%3A%2F%2F{app.config['SERVER_NAME']}%2Fdiscord_redirect&response_type=code&scope=identify%20guilds.join&state={state}")


@app.get("/discord_redirect")
@auth_required
def discord_redirect(v):


	now=int(time.time())
	state=request.values.get('state','').split('.')

	timestamp=state[0]

	state=state[1]

	if int(timestamp) < now-600:
		abort(400)

	if not validate_hash(f"{timestamp}+{v.id}+discord", state):
		abort(400)

	code = request.values.get("code","")
	if not code:
		abort(400)

	data={
		"client_id":CLIENT_ID,
		'client_secret': CLIENT_SECRET,
		'grant_type': 'authorization_code',
		'code': code,
		'redirect_uri': f"https://{app.config['SERVER_NAME']}/discord_redirect",
		'scope': 'identify guilds.join'
	}
	headers={
		'Content-Type': 'application/x-www-form-urlencoded'
	}
	url="https://discord.com/api/oauth2/token"

	x=requests.post(url, headers=headers, data=data, timeout=5)

	x=x.json()


	try:
		token=x["access_token"]
	except KeyError:
		abort(403)


	url="https://discord.com/api/users/@me"
	headers={
		'Authorization': f"Bearer {token}"
	}
	x=requests.get(url, headers=headers, timeout=5)

	x=x.json()



	headers={
		'Authorization': f"Bot {BOT_TOKEN}",
		'Content-Type': "application/json"
	}

	if v.discord_id and v.discord_id != x['id']:
		url=f"https://discord.com/api/guilds/{SERVER_ID}/members/{v.discord_id}"
		requests.delete(url, headers=headers, timeout=5)

	if g.db.query(User).filter(User.id!=v.id, User.discord_id==x["id"]).first():
		return render_template("message.html", title="Discord account already linked.", error="That Discord account is already in use by another user.", v=v)

	v.discord_id=x["id"]
	g.db.add(v)

	url=f"https://discord.com/api/guilds/{SERVER_ID}/members/{x['id']}"

	name=v.username

	data={
		"access_token":token,
		"nick":name,
	}

	x=requests.put(url, headers=headers, json=data, timeout=5)

	if x.status_code in [201, 204]:

		if v.admin_level > 2:
			add_role(v, "owner")
			time.sleep(0.1)
		
		if v.admin_level > 0: add_role(v, "admin")

		time.sleep(0.1)
		add_role(v, "linked")
		
		if v.patron:
			time.sleep(0.1)
			add_role(v, str(v.patron))
		
	else:
		return x.json()


	if x.status_code==204:

		url=f"https://discord.com/api/guilds/{SERVER_ID}/members/{v.discord_id}"
		data={
			"nick": name
		}

		requests.patch(url, headers=headers, json=data, timeout=5)

	g.db.commit()

	return redirect(f"https://discord.com/channels/{SERVER_ID}/{WELCOME_CHANNEL}")