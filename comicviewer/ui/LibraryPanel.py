from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from comicviewer.files import FileOpenerFactory
from comicviewer.ui import UiUtils
from comicviewer.settings.SettingsEnum import SettingsEnum
from comicviewer.settings import SettingsStore
if TYPE_CHECKING:
	from comicviewer.MainController import MainController

class LibraryPanel(QtWidgets.QWidget):
	"""This panel shows the library view, including buttons to change it or load a non-library book"""
	def __init__(self, windowController, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.windowController: MainController = windowController

		layout = QtWidgets.QVBoxLayout()
		self.setLayout(layout)
		layout.addWidget(QtWidgets.QLabel("Choose a comic book:"))
		# Create a book selection widget
		self.selectionModel = QtWidgets.QFileSystemModel()
		# Only show supported comic books
		self.selectionModel.setNameFilterDisables(False)
		self.selectionModel.setNameFilters(['*' + ext for ext in FileOpenerFactory.supportedExtensions])

		self.selectionView = QtWidgets.QTreeView()
		self.selectionView.setModel(self.selectionModel)
		self._setBookSelectionPath(SettingsStore.getSettingValue(SettingsEnum.LIBRARY_PATH))
		# Hide all columns except the name
		for i in range(1, self.selectionView.header().count()):
			self.selectionView.header().hideSection(i)
		self.selectionView.header().hide()
		# Make sure a horizontal scrollbar appears as needed
		self.selectionView.header().setStretchLastSection(False)
		self.selectionView.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		# Handle selection changes
		self.selectionView.activated.connect(self._onSelectionChange)
		layout.addWidget(self.selectionView, 10)
		# Button to change the base folder of the file selector
		UiUtils.createButton('Change comic book library folder', self._onLibraryBrowseButtonPress, layout)
		# Button to load a single book
		UiUtils.createButton('Browse for single book', self._onBookBrowseButtonPress, layout)

	def _setBookSelectionPath(self, path):
		SettingsStore.setSettingValue(SettingsEnum.LIBRARY_PATH, path)
		# Set the root folder of the view
		self.selectionModel.setRootPath(path)
		# Update the selection
		self.selectionView.setRootIndex(self.selectionModel.index(path))

	def _onSelectionChange(self, selectedIndex: QtCore.QModelIndex):
		selectedPath = self.selectionModel.filePath(selectedIndex)
		# Actually change the comic book
		self.windowController.loadComicBook(selectedPath)

	def _onLibraryBrowseButtonPress(self):
		path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Comics Folder", SettingsStore.getSettingValue(SettingsEnum.LIBRARY_PATH))
		# 'path' is None if the file dialog is dismissed
		if path:
			self._setBookSelectionPath(path)

	def _onBookBrowseButtonPress(self):
		fileFilter = "Comic Books (*" + " *".join(FileOpenerFactory.supportedExtensions) + ")"
		path = QtWidgets.QFileDialog.getOpenFileName(self, "Load Comic Book", SettingsStore.getSettingValue(SettingsEnum.LIBRARY_PATH), fileFilter)[0]  # 'getOpenFileName' returns a tuple, first entry is filepath, second entry is filter used
		if path:
			self.windowController.loadComicBook(path)
