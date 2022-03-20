import time
from files.helpers.wrappers import auth_required
from files.helpers.sanitize import sanitize
from files.helpers.const import *
from datetime import datetime
from flask_socketio import SocketIO, emit
from files.__main__ import app
from flask import render_template
import sys

if SITE_NAME=='PCM':
	@app.get("/chat")
	@auth_required
	def chat( v):
		return render_template("chat.html", v=v)


	sex = SocketIO(app, logger=True, engineio_logger=True, debug=True, async_mode='gevent')

	@sex.on('speak')
	@auth_required
	def speak(data, v):

		data={
			"avatar": v.profile_url,
			"username":v.username,
			"text":sanitize(data[:1000].strip()),
			"time": time.strftime("%d %b %Y at %H:%M:%S", time.gmtime(int(time.time()))),
			"userlink":v.url
		}

		emit('speak', data, broadcast=True)
		return '', 204