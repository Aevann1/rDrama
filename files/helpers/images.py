from PIL import Image as IImage, ImageSequence
from webptools import gifwebp

def process_image(filename=None, resize=False):
	
	i = IImage.open(filename)

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
		om.save(filename, format="WEBP", save_all=True, append_images=list(frames), loop=0)
	elif i.format.lower() != "webp":
		if i.format.lower() == "gif": gifwebp(input_image=filename, output_image=filename, option="-q 80")
		else: i.save(filename, format="WEBP")

	return filename