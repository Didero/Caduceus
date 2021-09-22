import io, logging, time
from typing import Union

from lxml import etree

from comicviewer.files.BaseFileOpener import BaseFileOpener

_fieldsToShow = ('Title', 'Series', 'Number', 'Year', 'Month', 'Volume', 'Summary', 'StoryArc', 'AgeRating',
				 'Writer', 'Penciller', 'Inker', 'Colorist', 'Letterer', 'CoverArtist', 'Editor', 'Publisher')


class ComicInfoParser:
	def __init__(self, fileOpener: BaseFileOpener):
		self._fileOpener = fileOpener
		startTime = time.perf_counter()
		if not self._fileOpener.hasComicInfo():
			logging.debug(f"Book '{self._fileOpener.filepath}' does not contain a comic info file")
			self._xmlRoot = None
		else:
			with io.BytesIO(self._fileOpener.getComicInfo()) as comicInfoInput:
				self._xmlRoot = etree.parse(comicInfoInput)
		logging.debug(f"Loading comic info from '{self._fileOpener.filepath}' took {time.perf_counter() - startTime:.4f} seconds")

	def hasInfo(self) -> bool:
		""":return: True if this parser can show comic book information, False otherwise"""
		return self._fileOpener.hasComicInfo()

	def getInfo(self) -> Union[str, None]:
		"""
		:return: The comic information, or None if no information could be found
		"""
		if self._xmlRoot is None:
			return None
		startTime = time.perf_counter()
		comicInfoLines = []
		for fieldName in _fieldsToShow:
			fieldText = self._xmlRoot.findtext(fieldName)
			if fieldText:
				comicInfoLines.append(f"{fieldName}:  {fieldText}")
		logging.debug(f"Loading comic info took {time.perf_counter() - startTime:.6f} seconds")
		return "\n".join(comicInfoLines)

	def canImageBeDoublePage(self, index) -> Union[bool, None]:
		"""
		Checks the comic info to see if the provided imae should be shown on its own, or if it can be shown next to another page
		:param index:
		:return: True if the image can be shown next to another, False if it should be shown on its own, and None if we can't determine either way
		"""
		if self._xmlRoot is None:
			return None
		# Try to find information on the provided index
		pageTag = self._xmlRoot.find(f'//Page[@Image="{index}"]')
		if pageTag is not None:
			# A cover should be shown on its own
			if 'Type' in pageTag.attrib and pageTag.attrib['Type'] in ('FrontCover', 'BackCover'):
				return False
			# If the image is wider than it is high, it's most likely a two-page spread, so show it on its own
			elif 'ImageWidth' in pageTag.attrib and 'ImageHeight' in pageTag.attrib:
				return int(pageTag.attrib['ImageWidth'], 10) < int(pageTag.attrib['ImageHeight'], 10)
		# We can't find any way to know if this is a single or double page, so return that we don't know
		return None
