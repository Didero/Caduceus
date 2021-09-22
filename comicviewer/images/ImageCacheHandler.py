import concurrent.futures, logging, time
from typing import Dict, List

from PySide6.QtGui import QImage

from comicviewer.files.BaseFileOpener import BaseFileOpener
from comicviewer.images import ImageUtils
from comicviewer.settings.SettingsEnum import SettingsEnum
from comicviewer.settings import SettingsStore


class ImageCacheHandler:

	_executor = concurrent.futures.ThreadPoolExecutor()  # Initialize as class variable so all cache handles share it

	def __init__(self, fileOpener: BaseFileOpener):
		"""
		Create a handler for loading and caching images. Caching values are taken from the settings
		:param fileOpener: The opener to get the image bytes from
		"""
		self._fileOpener: BaseFileOpener = fileOpener
		self._imageCache: Dict[int, QImage] = {}
		self._indexesBeingLoaded: Dict[int, concurrent.futures.Future] = {}

	def retrieveImages(self, *indexes: int) -> List[QImage]:
		"""
		Get the images for the provided indexes. Also caches ahead 'cacheRange' number of pages in the background
		:param indexes: The indexes to load, either from the cache if they're there or loaded from disk and stored in the cache
		:return: The images for the provided indexes
		"""
		images = []
		for index in indexes:
			images.append(self._getImage(index))
		# Update cache in a thread so we can return the images ASAP
		self._executor.submit(self.updateCache, *indexes)
		return images

	def updateCache(self, *indexes: int):
		startTime = time.perf_counter()
		self._unchacheDistantImages(*indexes)
		self._cacheNearbyImages(*indexes)
		logging.debug(f"Updating cache based on indexes {indexes} took {time.perf_counter() - startTime:.4f} seconds")

	def isImageTwoPageSpread(self, index: int) -> bool:
		"""
		Checks whether the image at the provided index is a two-page spread
		:param index: The image index to check
		:return: True if the image is a two-page spread, False otherwise
		"""
		image = self._getImage(index)
		return image.width() > image.height()

	def _getImage(self, index):
		if index not in self._imageCache:
			# Check if the image is already being loaded. If it is, wait until it's done, otherwise load it ourselves
			# Use .get() instead of 'if index in indexesBeingLoaded: future = indexesBeingLoaded[index]' because 'get' is atomic, prevents race condition
			future = self._indexesBeingLoaded.get(index, None)
			if future is not None:
				# Image is being loaded, try to cancel it and do it in the main thread
				startTime = time.perf_counter()
				wasCancelled = future.cancel()
				if wasCancelled:
					# Future was cancelled, load the image now
					logging.debug(f"Cancelled loading index {index}, loading in main thread")
					self._loadAndStoreImage(index)
				else:
					# Image loading couldn't be cancelled, probably because it's already running. Wait for it to complete
					future.result()
					logging.debug(f"Index {index} not in cache, but it's already being loaded, waited {time.perf_counter() - startTime:.6f} seconds")
			else:
				logging.debug(f"Index {index} not in cache, loading")
				self._loadAndStoreImage(index)
		return self._imageCache[index]

	def _unchacheDistantImages(self, *indexes: int):
		uncacheExtraRange = SettingsStore.getSettingValue(SettingsEnum.UNCACHE_EXTRA_RANGE)
		lowestIndexToKeep = min(indexes) - SettingsStore.getSettingValue(SettingsEnum.CACHE_BEHIND_COUNT) - uncacheExtraRange
		highestIndexToKeep = max(indexes) + SettingsStore.getSettingValue(SettingsEnum.CACHE_AHEAD_COUNT) + uncacheExtraRange
		logging.debug(f"Uncaching below index {lowestIndexToKeep} and above index {highestIndexToKeep}")
		# Find the indexes to remove
		for index in list(self._imageCache.keys()):
			if index < lowestIndexToKeep or index > highestIndexToKeep:
				# Use 'pop' instead of 'del' in case another thread does something to the key
				self._imageCache.pop(index, None)

	def _cacheNearbyImages(self, *indexes: int):
		minIndex = max(min(indexes) - SettingsStore.getSettingValue(SettingsEnum.CACHE_BEHIND_COUNT), 0)
		maxIndex = min(max(indexes) + SettingsStore.getSettingValue(SettingsEnum.CACHE_AHEAD_COUNT), self._fileOpener.getMaximumImageIndex())
		logging.debug(f"Caching from {minIndex} to {maxIndex}")
		cacheStartTime = time.perf_counter()
		for cacheIndex in range(minIndex, maxIndex + 1):  # 'maxIndex + 1' because range's endpoint is not inclusive
			# Only load the image if we don't already have it loaded and if we're not already loading it
			if cacheIndex not in self._imageCache and cacheIndex not in self._indexesBeingLoaded:
				self._indexesBeingLoaded[cacheIndex] = self._executor.submit(self._loadAndStoreImage, cacheIndex, cacheStartTime)
		logging.debug(f"Setting up image cache ahead took {time.perf_counter() - cacheStartTime:.4f} seconds")

	def _loadAndStoreImage(self, index, cacheStartTime=None):
		# startTime = time.perf_counter()
		self._imageCache[index] = ImageUtils.convertBytesToImage(self._fileOpener.getImageBytesByIndex(index))
		# Clear this from the 'being updated' list. Use 'pop' instead of 'del' because the index might not be in the list if this wasn't called from a thread
		self._indexesBeingLoaded.pop(index, None)
		# logging.debug(f"Loading and storing image index {index} took {time.perf_counter() - startTime:.4f} seconds, {(time.perf_counter() - cacheStartTime) if cacheStartTime else 0:.4f} seconds after cache start")
