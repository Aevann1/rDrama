import requests
from os import environ
from PIL import Image as IImage, ImageSequence
import base64
import io
from drama.classes.images import *

CF_KEY = environ.get("CLOUDFLARE_KEY").strip()
CF_ZONE = environ.get("CLOUDFLARE_ZONE").strip()
imgurkey = environ.get("imgurkey").strip()


def upload_file(file=None, resize=False):
	
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
		om.save("image.gif", save_all=True, append_images=list(frames))

	req = requests.post('https://api.imgur.com/3/upload.json', headers = {"Authorization": f"Client-ID {imgurkey}"}, data = {"type": "file", "image": "image.gif"})
	try:
		resp = req.json()['data']
		url = resp['link'].replace(".png", "_d.png").replace(".jpg", "_d.jpg").replace(".jpeg", "_d.jpeg") + "?maxwidth=9999"
	except:
		print(req.text)
		return

	new_image = Image(text=url, deletehash=resp["deletehash"])
	g.db.add(new_image)
	return(url)