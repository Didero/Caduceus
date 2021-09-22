from typing import TYPE_CHECKING, Callable, Dict

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction

from comicviewer.ui.ZoomEnum import ZoomEnum

if TYPE_CHECKING:
	from comicviewer.ui.bookdisplay.BookDisplayParentWidget import BookDisplayParentWidget
	from comicviewer.ui.bookdisplay.BookDisplayController import BookDisplayController


class BookDisplayContextMenu(QMenu):
	def __init__(self, parentWidget, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.parentWidget: BookDisplayParentWidget = parentWidget
		self.controller: BookDisplayController = self.parentWidget.controller
		self._zoomTypeToAction: Dict[ZoomEnum, QAction] = {}

		separator = QAction(self)
		separator.setSeparator(True)

		self.viewOptionsMenu = self._createMenu("View")
		self.toggleFullscreenAction = self._createAction("Fullscreen", self.viewOptionsMenu, self.parentWidget.windowController.setFullscreen, isCheckable=True)
		self.toggleControlsPanelAction = self._createAction("Controls Panel", self.viewOptionsMenu, self.controller.setControlsPanelVisible, isCheckable=True)
		self.toggleTabBarAction = self._createAction("Tab Bar", self.viewOptionsMenu, self.parentWidget.windowController.setTabBarVisible, isCheckable=True)
		self.viewOptionsMenu.addAction(separator)
		self.showWithPreviousPageAction = self._createAction("Show with previous page", self.viewOptionsMenu, self.controller.showWithPreviousPage)
		self.showWithNextPageAction = self._createAction("Show with next page", self.viewOptionsMenu, self.controller.showWithNextPage)

		self.zoomOptionsMenu = self._createMenu("Zoom")
		self.setZoomOriginalAction = self._createZoomTypeAction(ZoomEnum.ORIGINAL_SIZE)
		self.setZoomFitScreenAction = self._createZoomTypeAction(ZoomEnum.FIT_SCREEN)
		self.setZoomFitWidthAction = self._createZoomTypeAction(ZoomEnum.FIT_HORIZONTAL)
		self.setZoomFitHeightAction = self._createZoomTypeAction(ZoomEnum.FIT_VERTICAL)
		self.zoomOptionsMenu.addAction(separator)
		self.zoomInAction = self._createAction("Zoom In", self.zoomOptionsMenu, self.controller.zoomIn)
		self.zoomOutAction = self._createAction("Zoom Out", self.zoomOptionsMenu, self.controller.zoomOut)

		self.navigateOptionsMenu = self._createMenu("Navigate")
		self.firstPageAction = self._createAction("First Page", self.navigateOptionsMenu, self.controller.goToFirstPage)
		self.previousPageAction = self._createAction("Previous Page", self.navigateOptionsMenu, self.controller.goToPreviousPage)
		self.nextPageAction = self._createAction("Next Page", self.navigateOptionsMenu, self.controller.goToNextPage)
		self.lastPageAction = self._createAction("Last Page", self.navigateOptionsMenu, self.controller.goToLastPage)
		self.navigateOptionsMenu.addAction(separator)
		self.previousBookAction = self._createAction("Previous Book Tab", self.navigateOptionsMenu, lambda: self.parentWidget.windowController.changeBookTabIndex(-1))
		self.nextBookAction = self._createAction("Next Book Tab", self.navigateOptionsMenu, lambda: self.parentWidget.windowController.changeBookTabIndex(1))

	def updateMenu(self):
		"""Update which actions are disabled and (un)checked based on the current state. Should be called before showing this menu"""
		# Set the checked state of the toggle actions. This is important, because the check state is passed to the toggle method, without this, the actions won't work properly
		self.toggleFullscreenAction.setChecked(self.parentWidget.windowController.isFullscreen())
		self.toggleControlsPanelAction.setChecked(self.controller.isControlsPanelVisible())
		self.toggleTabBarAction.setChecked(self.parentWidget.windowController.isTabBarVisible())
		# Don't allow adjusting the index when we're showing two pages, or when we're at the limits
		self.showWithPreviousPageAction.setDisabled(self.controller.isFirstPage() or self.controller.isTwoPageSpread())
		self.showWithNextPageAction.setDisabled(self.controller.isLastPage() or self.controller.isTwoPageSpread())
		# Disable the current zoom type action
		currentZoomType = self.controller.getZoomType()
		for zoomType, action in self._zoomTypeToAction.items():
			action.setEnabled(currentZoomType != zoomType)
		# Disable book changes if there is only one book opened
		areMultipleBooksOpened = self.parentWidget.windowController.window.tabView.count() > 3
		self.previousBookAction.setEnabled(areMultipleBooksOpened)
		self.nextBookAction.setEnabled(areMultipleBooksOpened)

	def _createMenu(self, text: str, parent = None) -> QMenu:
		if parent is None:
			parent = self
		menu = QMenu(text, parent)
		parent.addMenu(menu)
		return menu

	def _createAction(self, text: str, parentMenu: QMenu, actionFunction: Callable, tooltipText: str = None, isCheckable: bool = False) -> QAction:
		action = QAction(text, parentMenu)
		parentMenu.addAction(action)
		action.triggered.connect(actionFunction)
		if tooltipText:
			action.setToolTip(tooltipText)
		if isCheckable:
			action.setCheckable(True)
		return action

	def _createZoomTypeAction(self, zoomType: ZoomEnum) -> QAction:
		action = self._createAction(zoomType.displayName, self.zoomOptionsMenu, lambda *x: self.controller.setZoomType(zoomType), tooltipText=zoomType.description)
		self._zoomTypeToAction[zoomType] = action
		return action