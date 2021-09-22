import logging, time, os
from typing import Iterable, Tuple

from PySide6.QtCore import QByteArray
from PySide6.QtGui import QImage
from PySide6.QtGui import QImageReader

from comicviewer.settings.SettingsEnum import SettingsEnum
from comicviewer.settings import SettingsStore

supportedImageFormats = ['.' + ext for ext in QImageReader.supportedImageFormats()]

def isImageSupported(imagePath: str) -> bool:
	"""
	Checks if the provided image path is for an image that we can load, by checking its file extension
	:param imagePath: The path to the image to check
	:return: True if the image can be loaded, False otherwise
	"""
	return os.path.splitext(imagePath)[1] in supportedImageFormats

def convertBytesToImage(imageBytes: bytes) -> QImage:
	"""
	Converts the provided bytes from reading a file to an Image (not a Pixmap because those can only be made on the main thread)
	:param imageBytes: The bytes from the image file
	:return: The QImage
	:raise ValueError: Raised when the provided bytes can't be loaded as an image
	"""
	startTime = time.perf_counter()
	img = QImage()
	imgLoadSuccessful = img.loadFromData(QByteArray(imageBytes))
	if not imgLoadSuccessful:
		raise ValueError("Unable to load provided image bytes as QImage")
	logging.debug(f"Converting bytes to image took {time.perf_counter() - startTime:.4f} seconds")
	return img

def calculateWidthAndHeight(images: Iterable[QImage], includeImageGap: bool = True) -> Tuple[int, int]:
	"""
	Calculate the total width and the maximum height of the provided images
	This takes the optional image gap from the settings into account
	:param images: The images to calculate the total width and highest height for
	:param includeImageGap: Whether to include the image gap from the settings in the width calculation
	:return: A tuple where the first entry is the total width and the second entry is the highest height of the provided images
	"""
	startTime = time.perf_counter()
	imageGap = SettingsStore.getSettingValue(SettingsEnum.GAP_BETWEEN_PAGES) if includeImageGap else 0
	totalWidth = -imageGap  # Start negative because there's one fewer image gap than there are images
	highestHeight = 0
	for image in images:
		totalWidth += image.width() + imageGap
		if image.height() > highestHeight:
			highestHeight = image.height()
	logging.debug(f"Calculating width {totalWidth} and height {highestHeight} took {time.perf_counter() - startTime:.4f} seconds")
	return totalWidth, highestHeight
