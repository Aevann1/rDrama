import requests
from os import environ
from PIL import Image as IImage
import os
import base64
import io
from drama.classes.images import *

CF_KEY = environ.get("CLOUDFLARE_KEY").strip()
CF_ZONE = environ.get("CLOUDFLARE_ZONE").strip()
imgurkey = environ.get("imgurkey").strip()

def crop_and_resize(img, resize):

	i = img

	org_ratio = i.width / i.height
	new_ratio = resize[0] / resize[1]

	if new_ratio > org_ratio:
		crop_height = int(i.width / new_ratio)
		box = (0, (i.height // 2) - (crop_height // 2),
			i.width, (i.height // 2) + (crop_height // 2))
	else:
		crop_width = int(new_ratio * i.height)
		box = ((i.width // 2) - (crop_width // 2), 0,
			(i.width // 2) + (crop_width // 2), i.height)

	return i.resize(resize, box=box)


def upload_file(file, resize=None):
	
	if resize:
		file.save("image.gif")
		i = IImage.open("image.gif")
		i = crop_and_resize(i, resize)
		img = io.BytesIO()
		i.save(img, format='GIF')
		req = requests.post('https://api.imgur.com/3/upload.json', headers = {"Authorization": f"Client-ID {imgurkey}"}, data = {'image': base64.b64encode(img.getvalue())})
		try: resp = req.json()['data']
		except Exception as e:
			print(req.text)
			return

	else:
		req = requests.post('https://api.imgur.com/3/upload.json', headers = {"Authorization": f"Client-ID {imgurkey}"}, data = {'image': base64.b64encode(file.read())})
		try: resp = req.json()['data']
		except:
			print(req.text)
			return
	
	try: url = resp['link'].replace(".png", "_d.png").replace(".jpg", "_d.jpg").replace(".jpeg", "_d.jpeg") + "?maxwidth=9999"
	except Exception as e:
		print(req.text)
		return

	new_image = Image(
		text=url,
		deletehash=resp["deletehash"],
		)
		
	g.db.add(new_image)
	return(url)

	
def upload_from_file(filename, resize=None):
	i = IImage.open(filename)
	if resize: i = crop_and_resize(i, resize)
	img = io.BytesIO()
	i.save(img, format='GIF')
	req = requests.post('https://api.imgur.com/3/upload.json', headers = {"Authorization": f"Client-ID {imgurkey}"}, data = {'image': base64.b64encode(img.getvalue())})

	try: 
		resp = req.json()['data']
		url = resp['link'].replace(".png", "_d.png").replace(".jpg", "_d.jpg").replace(".jpeg", "_d.jpeg") + "?maxwidth=9999"
	except Exception as e:
		print(e)
		print(req)
		print(req.text)
		return

	new_image = Image(
		text=url,
		deletehash=resp["deletehash"],
		)
		
	g.db.add(new_image)
	return(url)