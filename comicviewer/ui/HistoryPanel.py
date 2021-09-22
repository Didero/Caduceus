import os
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from comicviewer.misc import HistoryStore
from comicviewer.ui import UiUtils
if TYPE_CHECKING:
	from comicviewer.MainController import MainController

class HistoryPanel(QtWidgets.QWidget):
	def __init__(self, windowController, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.windowController: MainController = windowController

		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(layout)

		layout.addWidget(QtWidgets.QLabel("History"))
		self.historyList = QtWidgets.QListWidget()
		self.historyList.setSelectionMode(QtWidgets.QListWidget.SelectionMode.SingleSelection)
		self.historyList.itemActivated.connect(self._openSelectedBook)
		layout.addWidget(self.historyList)

		self.openButton = UiUtils.createButton("Open selected book", self._openSelectedBook, layout)
		self.removeButton = UiUtils.createButton("Remove selected book from history", self._removeSelectedBook, layout)
		self.clearHistoryButton = UiUtils.createButton("Clear history", self._clearHistory, layout)
		self.historyList.itemSelectionChanged.connect(self._updateButtonState)

		self.updateHistoryView()

	def updateHistoryView(self):
		self.historyList.clear()
		# Fill the view with the history
		for bookPath in HistoryStore.getHistory():
			self.historyList.addItem(QtWidgets.QListWidgetItem(bookPath))
		self._updateButtonState()

	def _updateButtonState(self):
		isItemSelected = self.historyList.currentItem() is not None
		self.openButton.setEnabled(isItemSelected)
		self.removeButton.setEnabled(isItemSelected)
		self.clearHistoryButton.setEnabled(self.historyList.count() > 0)

	def _openSelectedBook(self):
		selectedItem = self.historyList.currentItem()
		if selectedItem is not None:
			bookPath = selectedItem.text()
			if os.path.isfile(bookPath):
				self.windowController.loadComicBook(bookPath)
			else:
				UiUtils.showErrorMessagePopup("File missing", f"The selected comic book\n{bookPath}\ndoesn't exist anymore")

	def _removeSelectedBook(self):
		selectedItem = self.historyList.currentItem()
		if selectedItem is not None:
			wasRemoved = HistoryStore.removeFromHistory(selectedItem.text())
			if not wasRemoved:
				QtWidgets.QMessageBox.critical(self, "Can't remove", "The selected book is opened.\nPlease close it before removing it\nfrom the history")
			else:
				self.updateHistoryView()

	def _clearHistory(self):
		wasFullyCleared = HistoryStore.clearHistory()
		self.updateHistoryView()
		if not wasFullyCleared:
			QtWidgets.QMessageBox.warning(self, "Not fully cleared", "The history could not be\nfully cleared because there are still\nsome books opened.\n\nClose all books to fully clear\nthe history")
