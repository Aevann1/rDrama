import time
from files.helpers.wrappers import auth_required
from files.helpers.sanitize import sanitize
from files.helpers.const import *
from datetime import datetime
from flask_socketio import SocketIO, emit
from files.__main__ import app, limiter, cache
from flask import render_template, make_response, send_from_directory
import sys
import atexit

if SITE == 'localhost':
	socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins=[SITE_FULL], logger=True, engineio_logger=True, debug=True)
else:
	socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins=[SITE_FULL])

typing = []
online = []
messages = cache.get('chat') or []
total = cache.get('total') or 0

@app.get("/chat")
@auth_required
def chat( v):
	return render_template("chat.html", v=v, messages=messages)


@app.get('/chat.js')
@limiter.exempt
def chatjs():
	resp = make_response(send_from_directory('assets', 'js/chat.js'))
	return resp


@socketio.on('speak')
@limiter.limit("3/second;10/minute")
@auth_required
def speak(data, v):
	if v.is_banned: return '', 403
	global messages, total
	text = data[:1000].strip()
	if not text: return '', 403
	text_html = sanitize(text)

	data={
		"avatar": v.profile_url,
		"username":v.username,
		"namecolor":v.namecolor,
		"text":text,
		"text_html":text_html,
		"text_censored":censor_slurs(text_html, 'chat')
	}

	messages.append(data)
	messages = messages[-20:]
	total += 1
	emit('speak', data, broadcast=True)
	return '', 204

@socketio.on('connect')
@auth_required
def connect(v):
	if v.username not in online:
		online.append(v.username)
		emit("online", online, broadcast=True)

	emit('typing', typing)
	return '', 204

@socketio.on('disconnect')
@auth_required
def disconnect(v):
	if v.username in online:
		online.remove(v.username)
		emit("online", online, broadcast=True)

	if v.username in typing: typing.remove(v.username)
	emit('typing', typing, broadcast=True)
	return '', 204

@socketio.on('typing')
@auth_required
def typing_indicator(data, v):

	if data and v.username not in typing: typing.append(v.username)
	elif not data and v.username in typing: typing.remove(v.username)

	emit('typing', typing, broadcast=True)
	return '', 204


def close_running_threads():
	cache.set('chat', messages)
	cache.set('total', total)
atexit.register(close_running_threads)