import time
import os
import requests
from sys import stdout

from files.helpers.const import *

from PIL import Image, ImageOps
from PIL.ImageSequence import Iterator
from webptools import gifwebp
import subprocess

from flask import abort

def process_image(patron, filename=None, resize=0):
	
	maxsize = 16*1024*1024 if patron else 8*1024*1024

	size = os.stat(filename).st_size

	if size > max_size:
		os.remove(filename)
		
		raise FileUploadError("The maximum file size is: "+maxsize/1024/1024+" mb", 403)
	
	i = Image.open(filename)

	if resize and i.width > resize:
		try: subprocess.call(["convert", filename, "-coalesce", "-resize", f"{resize}>", filename])
		except: raise FileUploadError("error resizing image file")
	elif i.format.lower() != "webp":

		exif = i.getexif()
		for k in exif.keys():
			if k != 0x0112:
				exif[k] = None
				del exif[k]
		i.info["exif"] = exif.tobytes()

		if i.format.lower() == "gif":
			gifwebp(input_image=filename, output_image=filename, option="-mixed -metadata none -f 100 -mt -m 6")
		else:
			i = ImageOps.exif_transpose(i)
			i.save(filename, format="WEBP", method=6)

	return filename
		

	
def upload_files(v, files):	
	body = ""
	for file in files:
		body += "\n\n"+upload_file(v, file)

	return body
	
def upload_file(v, file):
	content_type = file.content_type
		
	if content_type.startswith('image/'): return '![]('+upload_image(v, file)+')'
		
	elif content_type.startswith('video/'): return upload_video(v, file)
			
	else: raise FileUploadException("Image/Video files only", 400)
	
def upload_image(v, file):
	name = f'/images/{time.time()}'.replace('.','') + '.webp'
	file.save(name)
		
	url = process_image(patron, name)

	return f"{url}"
	
def upload_video(v, file):
	extension = ''
	
	content_type = file.content_type
	
	if content_type.startswith('video/mp4'): extension = 'mp4'	
	elif content_type.startswith('video/Quicktime'): extension = 'mov'
	else: raise FileUploadException("Unsupported video format", 400)
	
	
	filename = save_video(file, extension)
	
	maxsize = 64*1024*1024 if patron else 32*1024*1024

	maxsize = 0

	size = os.stat(filename).st_size
	
	if SITE_NAME == 'rDrama' and size < maxsize:
		return SITE_FULL+filename
	else:
		return upload_video_to_host(filename)
	

def upload_video_to_host(video_file_name, keepcopy=False):
	
	with open(video_file_name, 'rb') as f:
		try: req = requests.request("POST", "https://pomf2.lain.la/upload.php", files={'files[]': f}, timeout=5).json()
		except requests.Timeout: raise FileUploadException("Video upload timed out, please try again!")
		
		try: url = req['files'][0]['url']
		except: raise FileUploadException(req['description'], 400)
		
		remove_file_error = os.remove(video_file_name)
		
		return url
	
	
def save_video(file, extension):
	
	name = f'/videos/{time.time()}'.replace('.','') 
	unsanitized = name + '-unsanitized.' + extension
	file.save(unsanitized)
	sanitized = name + '.' + extension
	
	copy_error = os.system(f'ffmpeg -y -loglevel warning -i {unsanitized} -map_metadata -1 -c:v copy -c:a copy {sanitized}')
	
	os.remove(unsanitized)
	
	return sanitized
	

class FileUploadException(Exception):

	def __init__(self, message, code=0):
		self.code = code
		self.message = message
		
		super().__init__(self.message)
	
	def result():
		msg = {"error", message}
		if(code==0):
			return msg
		else:
			return msg, code
