import logging, os
from typing import Optional, Tuple

from PySide6 import QtCore, QtGui, QtWidgets

from comicviewer.MainController import MainController
from comicviewer.ui.bookdisplay.BookDisplayParentWidget import BookDisplayParentWidget
from comicviewer.ui.LibraryPanel import LibraryPanel
from comicviewer.ui.HistoryPanel import HistoryPanel
from comicviewer.files import FileOpenerFactory
from comicviewer.ui.settingspanel.SettingsParentWidget import SettingsParentWidget


class MainWindow(QtWidgets.QMainWindow):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.controller = MainController(self)

		self._initializeUI()
		self.resize(1920, 1080)
		self._centerWindowOnScreen()
		# Enable dropping files onto this application, to load comic books without having to navigate to them (see the 'dragEnterEvent' and 'dropEvent' methods)
		self.setAcceptDrops(True)
		# Listen for key presses
		self.installEventFilter(self)
		self.controller.afterInit()

	def _initializeUI(self):
		# Create the central widget that will hold all our layouts and controls
		centerWidget = QtWidgets.QWidget(self)
		self.setCentralWidget(centerWidget)
		# Set the central widget's layout where we're going to add our widgets
		centerLayout = QtWidgets.QHBoxLayout()
		# Make image view hug the screen edges
		centerLayout.setContentsMargins(0, 0, 0, 0)
		centerWidget.setLayout(centerLayout)

		self.tabView = QtWidgets.QTabWidget()
		self.tabView.setTabBar(self._HorizontalTextTabBar())
		# self.tabView.tabBar().hide()
		self.tabView.setTabPosition(QtWidgets.QTabWidget.TabPosition.East)
		# Remove any border from each tab pane, so the image view can take up as much window space as possible
		self.tabView.setContentsMargins(0, 0, 0, 0)
		self.tabView.setDocumentMode(True)
		centerLayout.addWidget(self.tabView, 10)

		# Create a settings tab
		self.settingsTabIndex = self.tabView.addTab(SettingsParentWidget(self.controller), '⚙')

		# Create the widget that shows the comic book selection widgets
		self.comicBookSelectionParentWidget = QtWidgets.QWidget()
		comicBookSelectionLayout = QtWidgets.QHBoxLayout()
		self.comicBookSelectionParentWidget.setLayout(comicBookSelectionLayout)
		self.bookSelectionTabIndex = self.tabView.addTab(self.comicBookSelectionParentWidget, '📚')
		self.tabView.setCurrentIndex(self.bookSelectionTabIndex)
		self.tabView.currentChanged.connect(self._onTabChanged)

		# Create the library panel
		self.libraryPanel = LibraryPanel(self.controller)
		comicBookSelectionLayout.addWidget(self.libraryPanel)

		# Create the history view panel
		self.historyPanel = HistoryPanel(self.controller)
		comicBookSelectionLayout.addWidget(self.historyPanel)

		self.show()

	def _onTabChanged(self, newTabIndex):
		self.controller.onTabChanged(newTabIndex)

	def _centerWindowOnScreen(self):
		frameGm = self.frameGeometry()
		screen = QtGui.QGuiApplication.primaryScreen()
		centerPoint = screen.availableGeometry().center()
		frameGm.moveCenter(centerPoint)
		self.move(frameGm.topLeft())

	def eventFilter(self, source: QtCore.QObject, event: QtCore.QEvent):
		# Send any keypresses to the controller
		if event.type() == QtCore.QEvent.KeyPress:
			return self.controller.handleKeyPress(event.key())
		return False

	def getActiveBookDisplay(self) -> Optional[BookDisplayParentWidget]:
		""":return: The currently active book display widget"""
		activeWidget = self.tabView.currentWidget()
		if isinstance(activeWidget, BookDisplayParentWidget):
			return activeWidget
		return None

	def addBookDisplayTab(self, tabTooltipText: str = None, shouldSwitchToTab: bool = True) -> Tuple[int, BookDisplayParentWidget]:
		widget = BookDisplayParentWidget(self.controller)
		tabIndex = self.tabView.addTab(widget, '📖')
		if tabTooltipText:
			self.tabView.setTabToolTip(tabIndex, tabTooltipText)
		if shouldSwitchToTab:
			self.tabView.setCurrentIndex(tabIndex)
		return tabIndex, widget

	def removeBookDisplayTab(self, indexToRemove):
		if self.tabView.count() >= indexToRemove:
			logging.warning(f"Trying to remove tab index {indexToRemove}, but there are only {self.tabView.count()} tabs")
			return
		self.tabView.removeTab(indexToRemove)

	def closeBook(self):
		# Switch back to the book selection tab
		self.tabView.setCurrentWidget(self.comicBookSelectionParentWidget)

	def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
		"""
		Handles when a file is dragged onto the window
		Only accept a folder to set as the base library folder, or a comic book to open directly
		:param event: The event detailing the drag event, should either be ignored or accepted
		"""
		if not event.mimeData().hasUrls():
			return event.ignore()
		urls = event.mimeData().urls()
		# Only accept a single dropped file, to avoid confusion
		if len(urls) > 1:
			return event.ignore()
		# Accept a folder (as a new base path) or a file (as a comic to load), but not a website URL
		url: QtCore.QUrl = urls[0]
		if not url.isLocalFile():
			return event.ignore()
		dragFilePath = url.toLocalFile()
		if not os.path.isdir(dragFilePath) and not FileOpenerFactory.isFileSupported(dragFilePath):
			return event.ignore()
		event.accept()

	def dropEvent(self, event: QtGui.QDropEvent):
		"""
		Handles when a file that was dragged over the window is dropped
		All the checking whether it's a valid drag item is done in 'dragEventEnter', so we don't have to do that here
		If the dragged item refers to a folder, it opens that folder as the new library folder. If it's a file, it'll open it as a comic book
		:param event: The event detailing the drop event
		"""
		dropPath = event.mimeData().urls()[0].toLocalFile()
		# If a directory was dropped on the viewer, set that as the library path
		if os.path.isdir(dropPath):
			self._setBookSelectionPath(dropPath)
		# Otherwise it's a file we can open, since we already checked in the 'dragEnter' event
		else:
			self.controller.loadComicBook(dropPath)

	def closeEvent(self, event: QtGui.QCloseEvent):
		"""Called when the window is being closed"""
		self.controller.handleWindowClose()
		# Allow the window to be closed
		event.accept()

	# Tab bar that shows its text horizontally when the tab bar is vertical
	# From https://stackoverflow.com/questions/46607298/pyqt-qtabwidget-horizontal-tab-and-horizontal-text-in-qtdesigner
	class _HorizontalTextTabBar(QtWidgets.QTabBar):
		def paintEvent(self, event):
			painter = QtWidgets.QStylePainter(self)
			option = QtWidgets.QStyleOptionTab()
			for index in range(self.count()):
				self.initStyleOption(option, index)
				painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, option)
				painter.drawText(self.tabRect(index), QtCore.Qt.AlignCenter | QtCore.Qt.TextDontClip, self.tabText(index))

		def tabSizeHint(self, index):
			size = QtWidgets.QTabBar.tabSizeHint(self, index)
			if size.width() < size.height():
				size.transpose()
			return size
