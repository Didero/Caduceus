from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtCore import QObject, QEvent

from comicviewer.ui.bookdisplay.BookDisplayView import BookDisplayView
from comicviewer.ui.bookdisplay.BookDisplayControlsWidget import BookDisplayControlsWidget
from comicviewer.ui.bookdisplay.BookDisplayController import BookDisplayController
from comicviewer.keyboard import KeyboardHandler

if TYPE_CHECKING:
	from comicviewer.MainController import MainController


class BookDisplayParentWidget(QWidget):
	def __init__(self, windowController):
		# Create the widget that shows the image and the controls
		super().__init__()
		self.windowController: MainController = windowController
		self.controller = BookDisplayController(self)
		layout = QHBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(layout)
		self.view = BookDisplayView(self)
		layout.addWidget(self.view)
		self.controlsColumn = BookDisplayControlsWidget(self)
		layout.addWidget(self.controlsColumn)
		self.installEventFilter(self)

	def eventFilter(self, source: QObject, event: QEvent):
		# Send any keypresses to the controller
		if event.type() == QEvent.KeyPress:
			return KeyboardHandler.handleKeyPress(event.key())
		# Same for scroll events. Actually moving the image with the scrollwheel is handled by the BookDisplayView
		elif event.type() == QEvent.Wheel:
			return self.controller.handleScrollwheel(event)
		elif event.type() == QEvent.Show:
			self.controller.onMadeVisibible()
		return False
