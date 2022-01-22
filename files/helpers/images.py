from PIL import Image as IImage, ImageSequence
from webptools import gifwebp
import time

def process_image(file=None, filename=None, resize=0):
	
	if not filename: filename = f'/images/{time.time()}'.replace('.','')[:-5] + '.webp'

	if file:
		file.save(filename)
		i = IImage.open(file)
	else: i = IImage.open(filename)

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
		om.save(filename, format="WEBP", save_all=True, append_images=list(frames), loop=0, method=6, allow_mixed=True)
	elif i.format.lower() != "webp":
		if i.format.lower() == "gif":
			gifwebp(input_image=filename, output_image=filename, option="-mixed -metadata none -f 100 -mt -m 6")
		else: i.save(filename, format="WEBP", method=6)

	return f'/static{filename}'