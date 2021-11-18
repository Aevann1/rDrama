from flask import *
import time
from .security import *

def make_logged_out_formkey(t):

	s = f"{t}+{session['session_id']}"

	return generate_hash(s)


def validate_logged_out_formkey(t, k):

	now = int(time.time())
	if now - t > 3600:
		return False

	s = f"{t}+{session['session_id']}"

	return validate_hash(s, k)
