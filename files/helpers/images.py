import requests
from os import environ
from PIL import Image as IImage, ImageSequence
import base64
from files.classes.images import *
from flask import g

CF_KEY = environ.get("CLOUDFLARE_KEY", "").strip()
CF_ZONE = environ.get("CLOUDFLARE_ZONE", "").strip()
IMGUR_KEY = environ.get("IMGUR_KEY", "").strip()


def upload_file(file=None, resize=False, png=False):
	
	if file: file.save("image.gif")

	if resize:
		i = IImage.open("image.gif")
		size = 100, 100
		frames = ImageSequence.Iterator(i)

		def thumbnails(frames):
			for frame in frames:
				thumbnail = frame.copy()
				thumbnail.thumbnail(size, IImage.ANTIALIAS)
				yield thumbnail

		frames = thumbnails(frames)

		om = next(frames)
		om.info = i.info
		om.save("image.gif", save_all=True, append_images=list(frames), loop=0)

	if png: filedir = "image.png"
	else: filedir = "image.gif"
	try:
		with open(filedir, 'rb') as f:
			data={'image': base64.b64encode(f.read())} 
			req = requests.post('https://api.imgur.com/3/upload.json', headers = {"Authorization": f"Client-ID {IMGUR_KEY}"}, data=data)
		resp = req.json()['data']
		url = resp['link'].replace(".png", "_d.png").replace(".jpg", "_d.jpg").replace(".jpeg", "_d.jpeg")
		if "_d." in url: url += "?maxwidth=9999"
	except: return

	new_image = Image(text=url, deletehash=resp["deletehash"])
	g.db.add(new_image)
	return(url)