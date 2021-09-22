import os
from typing import Dict, List, Type

from comicviewer.files.BaseFileOpener import BaseFileOpener
from comicviewer.files.ZipFileOpener import ZipFileOpener
from comicviewer.files.RarFileOpener import RarFileOpener

_extensionToFileOpener: Dict[str, Type[BaseFileOpener]] = {}
supportedExtensions: List[str] = []

# Get all the supported file openers
for openerClass in (ZipFileOpener,RarFileOpener):
	for ext in openerClass.SUPPORTED_EXTENSIONS:
		_extensionToFileOpener[ext] = openerClass
		supportedExtensions.append(ext)


def isFileSupported(filepath: str):
	return os.path.splitext(filepath)[1] in supportedExtensions

def getFileOpenerForFile(filepath: str) -> BaseFileOpener:
	"""
	Get the correct file opener for the provided path. Throws a ValueError if the file is not supported
	:param filepath: The full path to the file to get an opener for
	:return: The BaseFileOpener that can handle the provided file
	:raise: ValueError if the provided file can't be opened
	"""
	fileExt = os.path.splitext(filepath)[1]
	if fileExt not in _extensionToFileOpener:
		raise ValueError(f"Unsupported comic book file type '{filepath}', supported formats re ")
	return _extensionToFileOpener[fileExt](filepath)
