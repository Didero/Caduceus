import logging, time
from abc import ABC, abstractmethod
from typing import List, Optional

from comicviewer.images import ImageUtils


class BaseFileOpener(ABC):
	SUPPORTED_EXTENSIONS = ()

	def __init__(self, filepath):
		startTime = time.perf_counter()
		self.filepath = filepath
		self.file = None
		self.open()
		self.comicInfoFilepath = None
		self.imageNames = []
		for fn in self._getFileList():
			if fn.endswith('ComicInfo.xml'):
				self.comicInfoFilepath = fn
			elif ImageUtils.isImageSupported(fn):
				self.imageNames.append(fn)
		# Load order might not be logical page order, so sort the pages
		self.imageNames.sort()
		logging.debug(f"Loading '{self.filepath}' took {time.perf_counter() - startTime:.4f} seconds")

	@abstractmethod
	def open(self):
		"""This method should open the supported file from the filepath passed in the constructor, and store it in self.file"""
		pass

	def close(self):
		"""Closes the opened file. Should be called when done with this archive"""
		if self.file:
			self.file.close()

	def getMaximumImageIndex(self) -> int:
		"""Get the highest index that's requestable from getImageBytesByIndex"""
		return len(self.imageNames) - 1

	def getImageBytesByIndex(self, index) -> bytes:
		"""This method returns the image specified by the provided index, or throw an error if that index isn't available"""
		return self._readFile(self.imageNames[index])

	def hasComicInfo(self) -> bool:
		""":return: This method returns whether the opened file contains comic book info"""
		return self.comicInfoFilepath is not None

	def getComicInfo(self) -> Optional[bytes]:
		""":return: This method returns either the comic info file (ComicInfo.xml etc) if it's available, or None if it's not available"""
		return self._readFile(self.comicInfoFilepath) if self.hasComicInfo() else None

	@abstractmethod
	def _getFileList(self) -> List[str]:
		""":return: This internal method should return the list of all files inside the archive. This is used to create the supported file list"""
		pass

	@abstractmethod
	def _readFile(self, filename: str) -> bytes:
		"""
		Return the bytes for the file specified by the provided filename
		:param filename: The filename to load from the archive
		:return: The bytes of the file specified by the filename
		"""
		pass
