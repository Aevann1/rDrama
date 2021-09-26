import requests
from os import environ, path, remove
from PIL import Image as IImage, ImageSequence
import base64
from files.classes.images import *
from flask import g
from werkzeug.utils import secure_filename
from webptools import gifwebp

IMGUR_KEY = environ.get("IMGUR_KEY", "").strip()
IBB_KEY = environ.get("IBB_KEY", "").strip()

def upload_ibb(file=None, resize=False):
	
	if file: file.save("image.webp")

	i = IImage.open("image.webp")

	if resize:
		size = 100, 100
		frames = ImageSequence.Iterator(i)

		def thumbnails(frames):
			for frame in frames:
				thumbnail = frame.copy()
				thumbnail.thumbnail(size)
				yield thumbnail

		frames = thumbnails(frames)

		om = next(frames)
		om.info = i.info
		om.save("image.webp", save_all=True, append_images=list(frames), loop=0)
	elif i.format.lower() != "webp":
		if i.format.lower() == "gif": gifwebp(input_image="image.webp", output_image="image.webp", option="-q 80")
		else: i.save("image.webp")


	with open("image.webp", 'rb') as f:
		data={'image': base64.b64encode(f.read())} 
		req = requests.post(f'https://api.imgbb.com/1/upload?key={IBB_KEY}', data=data)
	resp = req.json()['data']
	url = resp['url']

	return url


class UploadException(Exception):
	"""Custom exception to raise if upload goes wrong"""
	pass


def upload_video(file):

	file_path = path.join("temp", secure_filename(file.filename))
	file.save(file_path)

	headers = {"Authorization": f"Client-ID {IMGUR_KEY}"}
	with open(file_path, 'rb') as f:
		try:
			r = requests.post('https://api.imgur.com/3/upload', headers=headers, files={"video": f})

			r.raise_for_status()

			resp = r.json()['data']
		except requests.HTTPError as e:
			raise UploadException("Invalid video. Make sure it's 1 minute long or shorter.")
		except:
			raise UploadException("Error, please try again later.")
		finally:
			remove(file_path)

	link = resp['link']
	img = Image(text=link, deletehash=resp['deletehash'])
	g.db.add(img)

	return link