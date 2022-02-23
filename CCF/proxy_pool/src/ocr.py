from PIL import Image
from pytesseract import image_to_string


def ocr(img_path: str):
	try:
		return image_to_string(Image.open(img_path))
	except Exception as e:
		raise e