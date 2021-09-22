import logging, time
import os.path
from typing import TYPE_CHECKING, Iterable, Union

from PySide6.QtWidgets import QApplication

from comicviewer.keyboard import KeyboardHandler
from comicviewer.keyboard.KeyboardAction import KeyboardAction
from comicviewer.misc import HistoryStore
from comicviewer.ui.bookdisplay.BookDisplayParentWidget import BookDisplayParentWidget
from comicviewer.settings import SettingsStore
from comicviewer.settings.SettingsEnum import SettingsEnum
from comicviewer.ui import UiUtils

if TYPE_CHECKING:
	from comicviewer.ui.MainWindow import MainWindow


class MainController:
	def __init__(self, window):
		self.window: MainWindow = window
		self.updateWindowTitle()
		self._initializeKeyboardHandling()
		self._wasMaximizedBeforeFullscreen: bool = False

	def _initializeKeyboardHandling(self):
		# Navigation keys
		KeyboardHandler.registerForKeyboardAction(KeyboardAction.CLOSE_BOOK, self.onCloseBookKeyPressed)
		KeyboardHandler.registerForKeyboardAction(KeyboardAction.PREVIOUS_BOOK, lambda: self.changeBookTabIndex(-1))
		KeyboardHandler.registerForKeyboardAction(KeyboardAction.NEXT_BOOK, lambda: self.changeBookTabIndex(1))
		KeyboardHandler.registerForKeyboardAction(KeyboardAction.GO_TO_SETTINGS, lambda: self.window.tabView.setCurrentIndex(self.window.settingsTabIndex))
		KeyboardHandler.registerForKeyboardAction(KeyboardAction.GO_TO_BOOK_SELECTION, lambda: self.window.tabView.setCurrentIndex(self.window.bookSelectionTabIndex))
		# UI keys
		KeyboardHandler.registerForKeyboardAction(KeyboardAction.TOGGLE_FULLSCREEN, self.setFullscreen)
		KeyboardHandler.registerForKeyboardAction(KeyboardAction.LEAVE_FULLSCREEN, lambda: self.setFullscreen(False))
		KeyboardHandler.registerForKeyboardAction(KeyboardAction.TOGGLE_TABBAR, self.setTabBarVisible)

	def afterInit(self):
		"""Should be called after the MainWindow is fully initialized"""
		if SettingsStore.getSettingValue(SettingsEnum.RESTORE_PREVIOUS_SESSION):
			startTime = time.perf_counter()
			# Get the selected book before loading the session, because loading overwrites the currently selected book
			selectedBookPath = HistoryStore.getCurrentBook()
			# Open all the books from the previous sessions
			indexToSelect = None
			widgetToSelect: BookDisplayParentWidget or None = None
			missingFiles = []
			for bookPath in HistoryStore.getSession():
				# If the book no longer exists, don't open it
				if not os.path.isfile(bookPath):
					missingFiles.append(bookPath)
					HistoryStore.storeBookClosed(bookPath, False)
					continue
				index, widget = self.window.addBookDisplayTab(bookPath, False)
				widget.controller.initializeWithPath(bookPath)
				if bookPath == selectedBookPath:
					indexToSelect = index
					widgetToSelect = widget
			# Select the tab that was selected when the program was closed
			if indexToSelect is not None and widgetToSelect is not None:
				self.window.tabView.setCurrentIndex(indexToSelect)
			logging.debug(f"Restoring {self.window.tabView.count() - 2} tabs of the previous session took {time.perf_counter() - startTime:.4f} seconds")
			if missingFiles:
				# We changed the history, so save it
				HistoryStore.saveHistory()
				# Show a message listing which file(s) couldn't be opened
				shouldBePlural = len(missingFiles) > 1
				pluralS = 's' if shouldBePlural else ''
				missingFilesString = '-' + '\n-'.join(missingFiles)
				msg = f"The following file{pluralS} {'were' if shouldBePlural else 'was'} opened last session\n" \
					f"but do{'' if shouldBePlural else 'es'}n't exist anymore:\n{missingFilesString}"
				UiUtils.showWarningMessagePopup(f"Missing File{pluralS}", msg)
		# Make sure all the tab-related display things (window title etc) is correct
		self.onTabChanged(self.window.tabView.currentIndex())

	def onTabChanged(self, newTabIndex):
		if newTabIndex == self.window.bookSelectionTabIndex or newTabIndex == self.window.settingsTabIndex:
			HistoryStore.setCurrentBook(None)
			# Make sure the history view is always up-to-date when we switch back to the book selection tab for any reason
			if newTabIndex == self.window.bookSelectionTabIndex:
				self.window.historyPanel.updateHistoryView()
				self.updateWindowTitle("Book Selection")
			else:
				self.updateWindowTitle("Settings")
		else:
			# Book view, update the window title
			self.updateWindowTitle(self.window.tabView.widget(newTabIndex).controller.bookPath)
		# Make sure the tab bar is visible if more than one book can be opened, so users can switch to another open book
		if not self.window.tabView.tabBar().isVisible() and SettingsStore.getSettingValue(SettingsEnum.ALLOW_MULTIPLE_BOOKS) and self.window.tabView.count() > 2:
			self.setTabBarVisible(True)

	def onSettingsChanged(self, changedSettings: Iterable[SettingsEnum]):
		if SettingsEnum.LOGGING_LEVEL in changedSettings:
			newLogLevel = SettingsStore.getSettingValue(SettingsEnum.LOGGING_LEVEL).logLevel
			logger = logging.getLogger()
			logger.setLevel(newLogLevel)
			for logHandler in logger.handlers:
				logHandler.setLevel(newLogLevel)
		if SettingsEnum.BOOK_HISTORY_SIZE in changedSettings:
			HistoryStore.trimHistory()
		if self.window.tabView.count() == 2:
			# No books are open, no need to update book views or close books
			return
		# If there are more books open than allowed, close the extras
		if SettingsEnum.ALLOW_MULTIPLE_BOOKS in changedSettings and not SettingsStore.getSettingValue(SettingsEnum.ALLOW_MULTIPLE_BOOKS) and self.window.tabView.count() > 3:
			booksToClose = self.window.tabView.count() - 3
			for i in range(0, booksToClose):
				widget: BookDisplayParentWidget = self.window.tabView.widget(4)
				widget.controller.closeBook(False)
		# Check to see if we need to update parts of the book display views
		shouldUpdateImageCaches = False
		shouldRedrawViews = False
		for changedSetting in changedSettings:
			if changedSetting in (SettingsEnum.SHOW_TWO_PAGES, SettingsEnum.GAP_BETWEEN_PAGES, SettingsEnum.DEFAULT_ZOOM_TYPE):
				shouldRedrawViews = True
				# Since redrawing the view includes updating the cache, no need to keep checking
				break
			elif changedSetting in (SettingsEnum.CACHE_BEHIND_COUNT, SettingsEnum.CACHE_AHEAD_COUNT, SettingsEnum.UNCACHE_EXTRA_RANGE):
				shouldUpdateImageCaches = True
				# Don't break, because we might run into a setting that requires redrawing the view entirely
		if shouldUpdateImageCaches or shouldRedrawViews:
			for index in range(self.window.bookSelectionTabIndex + 1, self.window.tabView.count()):
				widget: BookDisplayParentWidget = self.window.tabView.widget(index)
				# Updating the view also updates the cache, so don't do both
				if shouldRedrawViews:
					widget.controller.updateView()
				elif shouldUpdateImageCaches:
					widget.controller.updateImageCache()

	def handleKeyPress(self, key) -> bool:
		startTime = time.perf_counter()
		wasHandled = KeyboardHandler.handleKeyPress(key)
		if not wasHandled:
			action = KeyboardHandler.getActionForKey(key)
			if action is not None:
				wasHandled = self.window.getActiveBookDisplay().controller.handleKeyboardAction(action)
		# logging.debug(f"Handling keypress {key} took {time.perf_counter() - startTime:.4f} seconds, {wasHandled=}")
		return wasHandled

	def onCloseBookKeyPressed(self):
		# Check if there is currently a book selected
		currentWidget = self.window.tabView.currentWidget()
		if isinstance(currentWidget, BookDisplayParentWidget):
			currentWidget.controller.closeBook()

	def changeBookTabIndex(self, indexChange):
		# Only change if there's more than one book opened
		if self.window.tabView.count() > 3:
			newIndex = self.window.tabView.currentIndex() + indexChange
			if newIndex == self.window.bookSelectionTabIndex:
				# Stepped back to the book selection index, cycle back to the last book
				newIndex = self.window.tabView.count() - 1
			elif newIndex >= self.window.tabView.count():
				# Stepped past the last book, cycle back to the first book
				newIndex = self.window.bookSelectionTabIndex + 1
			if newIndex != self.window.tabView.currentIndex():
				self.window.tabView.setCurrentIndex(newIndex)

	def onComicBookClosed(self, bookDisplayWidget: BookDisplayParentWidget):
		"""
		Called when the currently displayed comic book is closed
		:param bookDisplayWidget: The widget that sent us the book closed event
		"""
		self.updateWindowTitle()
		# Close the relevant book display tab
		tabCount = self.window.tabView.count()
		for index in range(0, tabCount):
			if index == self.window.bookSelectionTabIndex:
				continue
			# Found the widget
			if self.window.tabView.widget(index) == bookDisplayWidget:
				self.window.tabView.removeTab(index)
				# Closing the book tab makes the tabview stay at the index if there was a higher index, so it selects the next book
				# If there's no higher index, it selects the previous index. So we don't need to manually change tabs
				break

	def loadComicBook(self, comicBookPath):
		# Check if the requested book already exists, if so switch to it
		for index in range(0, self.window.tabView.count()):
			tabWidget = self.window.tabView.widget(index)
			if not isinstance(tabWidget, BookDisplayParentWidget):
				continue
			if comicBookPath == tabWidget.controller.bookPath:
				self.window.tabView.setCurrentIndex(index)
				### HistoryStore.currentlySelectedBookPath = comicBookPath
				return
		# Check if we need to open a new tab or replace a current one
		if self.window.tabView.count() > 2 and not SettingsStore.getSettingValue(SettingsEnum.ALLOW_MULTIPLE_BOOKS):
			# There's already a book open, and we can only have one opened book. Ask if we should close that one
			shouldOpen = UiUtils.askUserQuestion("Close open comic book?", "Single-book mode is enabled.\nShould the selected book replace the opened book?", self.window)
			if not shouldOpen:
				return
			# Close the currently open tab
			bookDisplayWidget: BookDisplayParentWidget = self.window.tabView.widget(self.window.bookSelectionTabIndex + 1)
			bookDisplayWidget.controller.closeBook(False)
		displayIndex, displayWidget = self.window.addBookDisplayTab(comicBookPath, True)
		displayWidget.controller.loadBook(comicBookPath)
		### HistoryStore.currentlySelectedBookPath = comicBookPath
		self.updateWindowTitle(comicBookPath)

	def updateWindowTitle(self, bookTitle: str = None):
		title = QApplication.applicationName() + " Comic Viewer"
		if bookTitle:
			title += " - " + bookTitle
		self.window.setWindowTitle(title)

	def isFullscreen(self) -> bool:
		""":return: True if the window is currently fullscreen, False otherwise"""
		return self.window.isFullScreen()

	def setFullscreen(self, setFullscreen: Union[bool, None] = None):
		"""
		Sets whether the window is shown fullscreen or not. Providing no argument or None toggles the fullscreen state
		:param setFullscreen: Set to fullscreen if True, set to normal if False, toggle fullscreen state if None
		"""
		if setFullscreen is None:
			setFullscreen = not self.isFullscreen()
		if setFullscreen:
			self._wasMaximizedBeforeFullscreen = self.window.isMaximized()
			self.window.showFullScreen()
		elif self._wasMaximizedBeforeFullscreen:
			self.window.showMaximized()
		else:
			self.window.showNormal()

	def isTabBarVisible(self) -> bool:
		""":return: True if the book selection / book view tab bar is visible, False if it's hidden"""
		return not self.window.tabView.tabBar().isHidden()

	def setTabBarVisible(self, setVisible: Union[bool, None] = None):
		"""
		Sets whether the book selection / book view is visible or not. Providing no argument or None toggles the state
		:param setVisible: Set to visible if True, set to hidden if False, toggle state if None
		"""
		if setVisible is None:
			setVisible = not self.isTabBarVisible()
		# Don't allow hiding he tab bar on the book selection tab, because then one of the book selection tabs grabs focus and pressing T again searches in that list
		if setVisible is False and self.window.tabView.currentIndex() == self.window.bookSelectionTabIndex:
			return
		self.window.tabView.tabBar().setVisible(setVisible)

	def handleWindowClose(self):
		HistoryStore.saveHistory()
