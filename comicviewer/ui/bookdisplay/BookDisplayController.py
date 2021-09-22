from typing import TYPE_CHECKING, Callable, Dict, Union
import logging, time

from PySide6.QtCore import QEvent

from comicviewer.files import FileOpenerFactory
from comicviewer.images.ImageCacheHandler import ImageCacheHandler
from comicviewer.ui.ZoomEnum import ZoomEnum
from comicviewer.settings.SettingsEnum import SettingsEnum
from comicviewer.settings import SettingsStore
from comicviewer.misc.DirectionEnum import DirectionEnum
from comicviewer.files.ComicInfoParser import ComicInfoParser
from comicviewer.keyboard.KeyboardAction import KeyboardAction
from comicviewer.ui import UiUtils
from comicviewer.misc import HistoryStore

if TYPE_CHECKING:
	from comicviewer.ui.bookdisplay.BookDisplayParentWidget import BookDisplayParentWidget
	from comicviewer.files.BaseFileOpener import BaseFileOpener


class BookDisplayController:
	def __init__(self, parent):
		self.parent: BookDisplayParentWidget = parent
		# Initialize some variables
		self.isInitialized: bool = False
		self.currentImageIndex: int = -1
		self.maxImageIndex: int = 0
		self.isShowingTwoPages: bool = False
		self._lastEdgeScrollDirection: DirectionEnum or None = None
		self._lastEdgeScrollTime: float = 0
		self.bookPath: str or None = None
		self.bookFileReader: BaseFileOpener or None = None
		self.imageCacheHandler: ImageCacheHandler or None = None
		self.comicInfoParser: ComicInfoParser or None = None
		self._setUpKeyboardActions()

	def _setUpKeyboardActions(self):
		self._keyboardActionToFunction: Dict[KeyboardAction, Callable] = {
			# Page changes
			KeyboardAction.PREVIOUS_PAGE: self.goToPreviousPage,
			KeyboardAction.NEXT_PAGE: self.goToNextPage,
			KeyboardAction.FIRST_PAGE: self.goToFirstPage,
			KeyboardAction.LAST_PAGE: self.goToLastPage,
			# Zooming
			KeyboardAction.ZOOM_IN: self.zoomIn,
			KeyboardAction.ZOOM_OUT: self.zoomOut,
			KeyboardAction.ZOOM_FIT_SCREEN: lambda: self.setZoomType(ZoomEnum.FIT_SCREEN),
			KeyboardAction.ZOOM_ORIGINAL_SIZE: lambda: self.setZoomType(ZoomEnum.ORIGINAL_SIZE),
			# UI controls
			KeyboardAction.TOGGLE_CONTROLS_PANEL: self.setControlsPanelVisible
		}

	def handleKeyboardAction(self, action: KeyboardAction):
		"""
		Execute the function linked to the provided keyboard action, if any
		Use this approach instead of KeyboardHandler's registerForKeyboardAction because there can be multiple BookDisplayViews and this saves un- and re-registering when book tab changes
		The MainController is in charge of calling this method
		:param action: The keyboard action to potentially execute
		:return: True if the keyboard action was handled, False otherwise
		"""
		if action in self._keyboardActionToFunction:
			startTime = time.perf_counter()
			self._keyboardActionToFunction[action]()
			logging.debug(f"Handling action {action} took {time.perf_counter() - startTime:.4f} seconds")
			return True
		return False

	def onMadeVisibible(self):
		"""Should be called when this book display is made visible"""
		if self.bookPath is not None:
			if not self.isInitialized:
				self.loadBookData()
			HistoryStore.setCurrentBook(self.bookPath)

	def closeBook(self, shouldUpdateDisplays=True):
		if self.bookFileReader:
			# Store where we were
			HistoryStore.storeBookClosed(self.bookFileReader.filepath)
			self.parent.windowController.onComicBookClosed(self.parent)
			self.parent.view.clearImages()
			self.comicInfoParser = None
			self.imageCacheHandler = None
			self.bookFileReader.close()
			self.bookFileReader = None
			self.currentImageIndex = -1
			self.maxImageIndex = 0
			if shouldUpdateDisplays:
				self.updatePageCountDisplay()
				self.updateZoomDisplay()

	def initializeWithPath(self, bookPath):
		"""
		Use this method to store which book should be loaded later, but don't load the book yet
		:param bookPath: The bookpath to store and load loater
		:raise AtttributeError: If a bookPath was already set
		"""
		if self.bookPath is not None:
			raise AttributeError(f"Book path was already set, to {self.bookPath}, can't set it to something else")
		self.bookPath = bookPath
		HistoryStore.storeBookOpened(self.bookPath)

	def loadBook(self, bookPath: str):
		# Close the previous book, if there is any
		self.closeBook(False)
		# Load the book
		self.bookPath = bookPath
		self.loadBookData()

	def loadBookData(self):
		"""Load the previously stored book path. Store a bookpath with 'initializeWithPath'. Or call 'loadBook' with a path to load the book immediately"""
		if self.bookPath is None:
			raise AttributeError("Bookpath hasn't been initialized yet")
		if self.isInitialized:
			return
		startTime = time.perf_counter()
		self.bookFileReader: BaseFileOpener = FileOpenerFactory.getFileOpenerForFile(self.bookPath)
		self.maxImageIndex = self.bookFileReader.getMaximumImageIndex()
		self.imageCacheHandler: ImageCacheHandler = ImageCacheHandler(self.bookFileReader)
		self.comicInfoParser = ComicInfoParser(self.bookFileReader)
		self.parent.controlsColumn.updateBookInfoButton()
		startIndex = HistoryStore.getStoredPage(self.bookPath)
		self._goToPageIndex(startIndex)
		HistoryStore.storeBookOpened(self.bookPath)
		logging.debug(f"Loading comic book took {time.perf_counter() - startTime:.4f} seconds")
		self.isInitialized = True

	def goToPreviousPage(self) -> bool:
		if self.bookFileReader is None:
			return False
		if self.currentImageIndex == 0:
			return False
		if not self.isLastPage() and SettingsStore.getSettingValue(SettingsEnum.SHOW_TWO_PAGES) and not self.isTwoPageSpread(self.currentImageIndex - 1):
			newIndex = max(0, self.currentImageIndex - 2)
		else:
			newIndex = self.currentImageIndex - 1
		didPageChange = self._goToPageIndex(newIndex)
		if didPageChange:
			# If you're going up a page, scroll to the bottom
			self.parent.view.scrollToBottom()
		return didPageChange

	def goToNextPage(self) -> bool:
		newIndex = self.currentImageIndex + (2 if self.isShowingTwoPages else 1)
		return self._goToPageIndex(newIndex)

	def goToFirstPage(self) -> bool:
		if self.currentImageIndex == 0:
			self.parent.view.scrollToTop()
			return False
		else:
			return self._goToPageIndex(0)

	def goToLastPage(self) -> bool:
		# If the last page isn't a back cover or a wide image, show it with the second-to-last image
		if self.comicInfoParser.canImageBeDoublePage(self.maxImageIndex) and not self.isTwoPageSpread(self.maxImageIndex):
			newIndex = self.maxImageIndex - 1
		else:
			newIndex = self.maxImageIndex
		return self._goToPageIndex(newIndex)

	def showWithPreviousPage(self) -> bool:
		"""
		Show one index lower. This is used as a correction for when we accidentally show two images that shouldn't be shown together, for instance if you go to the last page but it's not a backcover
		:return: True if the page changed, False otherwise
		"""
		return self._goToPageIndex(self.currentImageIndex - 1)

	def showWithNextPage(self) -> bool:
		"""
		Show one index higher. This is used as a correction for when we accidentally show two images that shouldn't be shown together, for instance if you go to the first page but it's not a frontcover
		:return: True if the page changed, False otherwise
		"""
		return self._goToPageIndex(self.currentImageIndex + 1)

	def _goToPageIndex(self, newIndex: int, forceRedraw=False) -> bool:
		"""
		Go to the provided page index
		:param newIndex: The absolute index to show
		:return: True if the page changed, False otherwise
		"""
		if not self.bookFileReader:
			return False
		if not forceRedraw and newIndex == self.currentImageIndex:
			return False
		if newIndex < 0 or newIndex > self.maxImageIndex:
			return False

		startTime = time.perf_counter()
		# Show a second image if this isn't a cover or a two-page spread, and if the user wants two show to pages at once
		self.isShowingTwoPages = newIndex < self.maxImageIndex and SettingsStore.getSettingValue(SettingsEnum.SHOW_TWO_PAGES)
		if self.isShowingTwoPages:
			self.isShowingTwoPages = self.comicInfoParser.canImageBeDoublePage(newIndex)
			# If the comic info parser doesn't know if it can be double page, check if it's the first image or a wide image
			if self.isShowingTwoPages is None:
				self.isShowingTwoPages = newIndex != 0 and not self.isTwoPageSpread(newIndex)
		logging.debug(f"Determined if we need a second page at {time.perf_counter() - startTime:.4f} seconds in, {self.isShowingTwoPages=}")
		try:
			if self.isShowingTwoPages:
				image1, image2 = self.imageCacheHandler.retrieveImages(newIndex, newIndex + 1)
				logging.debug(f"Loaded two images at {time.perf_counter() - startTime:.4f} seconds in")
				self.parent.view.setImages(image1, image2)
			else:
				image = self.imageCacheHandler.retrieveImages(newIndex)[0]
				self.parent.view.setImages(image)
		except Exception as e:
			logging.exception(f"{type(e)} exception while loading page index {newIndex}: {e}\n")
			UiUtils.showErrorMessagePopup("Error", f"Something went wrong while loading an image.\nPlease make sure your comic book file isn't corrupt\n"
											f"If this error persists, please report this exception:\n{e} [{type(e)}]")
			return False

		# Changing pages succeeded, store that we're now on a new page
		self.currentImageIndex = newIndex
		logging.debug(f"Changing page to index {self.currentImageIndex} took {time.perf_counter() - startTime:.4f} seconds")
		HistoryStore.setStoredPage(self.bookFileReader.filepath, self.currentImageIndex)
		self.updatePageCountDisplay()
		# Changing image may also change the zoom level, so update the display of that as well
		self.updateZoomDisplay()
		return True

	def isFirstPage(self):
		return self.currentImageIndex == 0

	def isLastPage(self):
		return self.currentImageIndex == self.maxImageIndex

	def isTwoPageSpread(self, index=None):
		"""
		Checks if the index is a two page spread. If no index is provided, the current index is used
		:param index: The index to check, or the curren index if left empty
		:return: True if the (current) index is a two page spread, False otherwise
		"""
		return self.imageCacheHandler.isImageTwoPageSpread(index if index is not None else self.currentImageIndex)

	def updateImageCache(self):
		"""Make sure the image cache is up to date"""
		if self.imageCacheHandler is None:
			return
		if self.isShowingTwoPages:
			self.imageCacheHandler.updateCache(self.currentImageIndex, self.currentImageIndex + 1)
		else:
			self.imageCacheHandler.updateCache(self.currentImageIndex)

	def updateView(self):
		"""Redraw the currently displayed page(s)"""
		if self.isInitialized:
			self._goToPageIndex(self.currentImageIndex, True)

	def updatePageCountDisplay(self):
		"""Update the displayed current page number(s) in the controls panel"""
		if self.bookFileReader:
			currentPages = [self.currentImageIndex + 1]
			if self.isShowingTwoPages:
				currentPages.append(self.currentImageIndex + 2)
			self.parent.controlsColumn.updateCurrentPageCountDisplay(currentPages, self.maxImageIndex + 1)
		else:
			self.parent.controlsColumn.updateCurrentPageCountDisplay(0, 0)

	def setZoomType(self, zoomType: ZoomEnum):
		if self.bookFileReader:
			self.parent.view.setZoomType(zoomType)
			self.updateZoomDisplay()

	def getZoomType(self) -> ZoomEnum:
		return self.parent.view.currentZoomType

	def zoomIn(self):
		if self.bookFileReader:
			self.parent.view.zoomIn()
			self.updateZoomDisplay()

	def zoomOut(self):
		if self.bookFileReader:
			self.parent.view.zoomOut()
			self.updateZoomDisplay()

	def updateZoomDisplay(self):
		if self.bookFileReader:
			zoomLevel = self.parent.view.imageScale
		else:
			zoomLevel = 0.0
		self.parent.controlsColumn.updateZoomDisplay(zoomLevel, self.parent.view.currentZoomType)

	def handleScrollwheel(self, event: QEvent) -> bool:
		"""
		Handle mouse scrolling when the book display view is focussed
		This only gets called when scrolling at the edges of the view, otherwise that widget intercepts the wheel event
		:param event: The event as caught by the eventfilter
		:return: True if the event was handled, False otherwise
		"""
		scrollAngle = event.angleDelta()
		if scrollAngle.y() > 0:
			self.handleScroll(DirectionEnum.NORTH, True)
			return True
		elif scrollAngle.x() > 0:
			self.handleScroll(DirectionEnum.WEST, True)
			return True
		elif scrollAngle.y() < 0:
			self.handleScroll(DirectionEnum.SOUTH, True)
			return True
		elif scrollAngle.x() < 0:
			self.handleScroll(DirectionEnum.EAST, True)
			return True
		return False

	def handleScroll(self, scrollDirection: DirectionEnum, isEdgeScroll: bool):
		"""
		Inform the controller about scrolling. Needed to make scrolling past the edge of the image(s) change the page
		:param scrollDirection: The direction the user scrolled in
		:param isEdgeScroll: Whether the scroll action was against the edge of the image
		"""
		# Check if we should change page if scroll past the page limit
		logging.debug(f"HandleScroll in direction {scrollDirection}, {isEdgeScroll=}, last scroll direction is {self._lastEdgeScrollDirection}")
		startTime = time.perf_counter()
		if not SettingsStore.getSettingValue(SettingsEnum.CHANGE_PAGE_WHEN_SCROLL_PAST_EDGE):
			return
		if scrollDirection == DirectionEnum.UNKNOWN:
			return
		if not isEdgeScroll:
			# If this isn't an edge scroll, clear the stored edge scroll direction
			self._lastEdgeScrollDirection = None
			return
		shouldChangePage = True
		# If the 'pause on edge scrolling' setting is on, don't immediately change page, but only if the user persists in edge scrolling in the same direction
		# This shouldn't apply to the zoom types that already maximise in a certain direction
		timeBeforePageChange = SettingsStore.getSettingValue(SettingsEnum.TIME_BEFORE_SCROLL_CHANGES_PAGE)
		if timeBeforePageChange > 0 and\
				self.parent.view.currentZoomType != ZoomEnum.FIT_SCREEN and\
				not (self.parent.view.currentZoomType == ZoomEnum.FIT_HORIZONTAL and scrollDirection in (DirectionEnum.WEST, DirectionEnum.EAST)) and\
				not (self.parent.view.currentZoomType == ZoomEnum.FIT_VERTICAL and scrollDirection in (DirectionEnum.NORTH, DirectionEnum.SOUTH)) and\
				timeBeforePageChange > 0:
			logging.debug(f"Checking if should pause before changing page, time is {time.time()}, last scroll time is {self._lastEdgeScrollTime}")
			shouldChangePage = scrollDirection == self._lastEdgeScrollDirection and time.time() - self._lastEdgeScrollTime > timeBeforePageChange
		if shouldChangePage:
			if scrollDirection == DirectionEnum.NORTH or scrollDirection == DirectionEnum.WEST:
				self.goToPreviousPage()
			elif scrollDirection == DirectionEnum.SOUTH or scrollDirection == DirectionEnum.EAST:
				self.goToNextPage()
			# Clear the last edge scroll direction so we don't accidentally repeat
			self._lastEdgeScrollDirection = None
		else:
			self._lastEdgeScrollDirection = scrollDirection
			self._lastEdgeScrollTime = time.time()
		logging.debug(f"Handling scroll took {time.perf_counter() - startTime:.4f} seconds")

	def isControlsPanelVisible(self) -> bool:
		return not self.parent.controlsColumn.isHidden()

	def setControlsPanelVisible(self, setVisible: Union[bool, None] = None):
		"""
		Sets whether the page and zoom controls are visible next to the image view
		Either provide a boolean to set the visibility, or pass None or nothing to toggle the visibility
		:param setVisible: The panel will be set visible if True, the panel will be hidden if False, and the visibility will be toggled if this is None or left empty
		"""
		if setVisible is None:
			if self.parent.controlsColumn.isHidden():
				self.parent.controlsColumn.show()
			else:
				self.parent.controlsColumn.hide()
		elif setVisible:
			self.parent.controlsColumn.show()
		else:
			self.parent.controlsColumn.hide()

	def hasBookInfo(self) -> bool:
		""":return: True if there is book info (like writer and publication date) to show, False otherwise"""
		return self.comicInfoParser is not None and self.comicInfoParser.hasInfo()

	def showBookInfo(self):
		if self.hasBookInfo():
			UiUtils.showInformationMessagePopup("Comic Book Info", self.comicInfoParser.getInfo())
