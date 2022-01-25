from PIL import Image, ImageSequence, ImageOps
from webptools import gifwebp

def process_image(filename=None, resize=0):
	
	i = Image.open(filename)

	exif = i.getexif()
	for k in exif.keys():
		if k != 0x0112:
			exif[k] = None
			del exif[k]
	i.info["exif"] = exif.tobytes()

	if resize:
		size = resize, resize
		frames = ImageSequence.Iterator(i)

		def thumbnails(frames):
			for frame in frames:
				thumbnail = frame.copy()
				thumbnail.thumbnail(size)
				yield thumbnail

		frames = thumbnails(frames)

		om = next(frames)
		om.info = i.info
		om = ImageOps.exif_transpose(om)
		om.save(filename, format="WEBP", save_all=True, append_images=list(frames), loop=0, method=6, allow_mixed=True)
	elif i.format.lower() != "webp":
		if i.format.lower() == "gif":
			gifwebp(input_image=filename, output_image=filename, option="-mixed -metadata none -f 100 -mt -m 6")
		else:
			i = ImageOps.exif_transpose(i)
			i.save(filename, format="WEBP", method=6)

	return f'/static{filename}'