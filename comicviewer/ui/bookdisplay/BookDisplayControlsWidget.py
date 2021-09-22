from typing import TYPE_CHECKING, Dict, Iterable, Union

from PySide6 import QtWidgets

from comicviewer.ui import UiUtils
from comicviewer.ui.ZoomEnum import ZoomEnum

if TYPE_CHECKING:
	from comicviewer.ui.bookdisplay.BookDisplayParentWidget import BookDisplayParentWidget


class BookDisplayControlsWidget(QtWidgets.QWidget):
	def __init__(self, parent, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.parent: BookDisplayParentWidget = parent

		self._initializeUi()
		self._zoomTypeToButton: Dict[ZoomEnum, QtWidgets.QPushButton] = {ZoomEnum.ORIGINAL_SIZE: self.zoomOriginalSizeButton, ZoomEnum.FIT_SCREEN: self.zoomFitToScreenButton,
								ZoomEnum.FIT_VERTICAL: self.zoomFitHeightButton, ZoomEnum.FIT_HORIZONTAL: self.zoomFitWidthButton}

	def _initializeUi(self):
		layout = QtWidgets.QVBoxLayout()
		self.setLayout(layout)
		# Since we disabled contents margins before for the image view, we need to set them here so the buttons don't hug the screen edge
		layout.setContentsMargins(0, 5, 5, 5)

		# Page switching controls
		self.currentPageDisplayLabel = QtWidgets.QLabel(' 0 ')
		self.currentPageDisplayLabel.setMinimumWidth(75)  # Make sure the whole control panel doesn't resize when the page counter goes to a new unit (9 to 10, for instance)
		layout.addWidget(self.currentPageDisplayLabel)
		self.maxPageDisplayLabel = QtWidgets.QLabel(' 0 ')
		layout.addWidget(self.maxPageDisplayLabel)
		pageControlsRow = QtWidgets.QHBoxLayout()
		self.previousButton = UiUtils.createButton('<', self.parent.controller.goToPreviousPage, pageControlsRow, "Go to previous page")
		self.nextButton = UiUtils.createButton('>', self.parent.controller.goToNextPage, pageControlsRow, "Go to next page")
		layout.addLayout(pageControlsRow)

		# Zoom controls
		zoomControlsRow1 = QtWidgets.QHBoxLayout()
		self.zoomInButton = UiUtils.createButton('+', self.parent.controller.zoomIn, zoomControlsRow1, "Zoom in")
		self.zoomDisplayLabel = QtWidgets.QLabel('0.00 x')
		zoomControlsRow1.addWidget(self.zoomDisplayLabel)
		self.zoomOutButton = UiUtils.createButton('-', self.parent.controller.zoomOut, zoomControlsRow1, "Zoom out")
		layout.addLayout(zoomControlsRow1)

		zoomControlsRow2 = QtWidgets.QHBoxLayout()
		self.zoomOriginalSizeButton = self._createZoomButton(ZoomEnum.ORIGINAL_SIZE, zoomControlsRow2)
		self.zoomFitToScreenButton = self._createZoomButton(ZoomEnum.FIT_SCREEN, zoomControlsRow2)
		layout.addLayout(zoomControlsRow2)

		zoomControlsRow3 = QtWidgets.QHBoxLayout()
		self.zoomFitHeightButton = self._createZoomButton(ZoomEnum.FIT_VERTICAL, zoomControlsRow3)
		self.zoomFitWidthButton = self._createZoomButton(ZoomEnum.FIT_HORIZONTAL, zoomControlsRow3)
		layout.addLayout(zoomControlsRow3)

		self.closeBookButton = UiUtils.createButton('Close', self.parent.controller.closeBook, layout, "Close the comic book")
		self.showBookInfoButton = UiUtils.createButton('ⓘ', self.parent.controller.showBookInfo, layout, "Show information about this comic book", buttonWidth=20)

		# Push the controls to the top
		layout.addStretch(1)

		self.debugOutput = QtWidgets.QLabel()
		layout.addWidget(self.debugOutput)

	def _createZoomButton(self, zoomType: ZoomEnum, parent):
		return UiUtils.createButton(zoomType.shortDisplayName, lambda: self.parent.controller.setZoomType(zoomType), parent, zoomType.description)

	def updateCurrentPageCountDisplay(self, currentPages: Union[int, Iterable[int]], maxPage: int):
		"""
		Update the current page count display
		:param currentPages: Either a single current page number, or a list of page numbers that are currently displayed
		:param maxPage: The maximum page number of the opened book
		"""
		if isinstance(currentPages, int):
			currentPageText = str(currentPages)
		else:
			currentPageText = ",".join([str(p) for p in currentPages])
		self.currentPageDisplayLabel.setText(f"Cur: {currentPageText}")
		self.maxPageDisplayLabel.setText(f"Max: {maxPage}")

	def updateZoomDisplay(self, newZoomLevel: 0.0, newZoomType: ZoomEnum):
		self.zoomDisplayLabel.setText(f"{newZoomLevel:.2f} x")
		for zoomType, button in self._zoomTypeToButton.items():
			button.setDisabled(zoomType == newZoomType)

	def updateBookInfoButton(self):
		self.showBookInfoButton.setEnabled(self.parent.controller.hasBookInfo())

	def setControlsPanelVisible(self, setVisible: Union[bool, None] = None):
		"""
		Sets whether the page and zoom controls are visible next to the image view
		Either provide a boolean to set the visibility, or pass None or nothing to toggle the visibility
		:param setVisible: The panel will be set visible if True, the panel will be hidden if False, and the visibility will be toggled if this is None or left empty
		"""
		if setVisible is None:
			if self.isHidden():
				self.show()
			else:
				self.hide()
		elif setVisible:
			self.show()
		else:
			self.hide()
