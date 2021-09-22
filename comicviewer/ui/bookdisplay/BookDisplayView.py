import logging, time
from typing import TYPE_CHECKING, List

from PySide6 import QtCore, QtGui, QtWidgets

from comicviewer.ui.ZoomEnum import ZoomEnum
from comicviewer.settings.SettingsEnum import SettingsEnum
from comicviewer.settings import SettingsStore
from comicviewer.images import ImageUtils
from comicviewer.ui.bookdisplay.BookDisplayContextMenu import BookDisplayContextMenu
from comicviewer.misc.DirectionEnum import DirectionEnum

if TYPE_CHECKING:
	from comicviewer.ui.bookdisplay.BookDisplayParentWidget import BookDisplayParentWidget

_SCROLL_DISTANCE = 100
_ZOOM_STEPS = 0.05

class BookDisplayView(QtWidgets.QGraphicsView):
	def __init__(self, parent, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.parent: BookDisplayParentWidget = parent
		# Initialize some values
		self._baseImages: List[QtGui.QImage] or None = None  # The base images to show. Stored to make repeated scaling easier
		self._imageScene: QtWidgets.QGraphicsScene or None = None  # The scene in which the images get drawn
		self._imageItems: List[QtWidgets.QGraphicsPixmapItem] or None = None  # The images as drawn on the scene
		self._baseImagesWidth = 0
		self._baseImagesHeight = 0
		self._scaledImagesWidth = 0
		self._scaledImagesHeight = 0
		self.currentZoomType = SettingsStore.getSettingValue(SettingsEnum.DEFAULT_ZOOM_TYPE)
		self.imageScale: float = 1  # By which factor we need to shrink the image, depending on zoom type and level
		self.contextMenu: BookDisplayContextMenu or None = None  # Will get filled when needed

		# Create the components
		self._initializeView()

	def _initializeView(self):
		# Remove the small frame around the edges of the view, so we have even more room for the image
		self.setFrameShape(QtWidgets.QFrame.NoFrame)
		self._imageScene = QtWidgets.QGraphicsScene(self)
		self.setScene(self._imageScene)
		self.setBackgroundBrush(QtGui.QBrush(QtCore.Qt.darkGray))
		# Hide the scrollbars
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		# Handle scrolling past the end
		self.verticalScrollBar().actionTriggered.connect(lambda scrollType: self._handleScroll(scrollType, self.verticalScrollBar()))
		self.horizontalScrollBar().actionTriggered.connect(lambda scrollType: self._handleScroll(scrollType, self.horizontalScrollBar()))
		self.installEventFilter(self)

	def _handleScroll(self, scrollType: QtWidgets.QAbstractSlider.SliderAction, scrollbar: QtWidgets.QScrollBar):
		"""
		Check if the user is trying to scroll off the page
		This method fires before the value changes, so we can check the scrollbar value
		We only need to check SliderSingleStepSub and ...Add, which get fired through keyboard arrows
		The scrollwheel fires SliderMove, but when you scroll at the scrollarea edges, the scroll event already gets forwarded to the MainController
		With SliderMove we don't know which direction the scroll move is in, so we can't use it to change page
		"""
		if not self._imageItems:
			return
		if scrollType != QtWidgets.QAbstractSlider.SliderAction.SliderSingleStepSub and scrollType != QtWidgets.QAbstractSlider.SliderAction.SliderSingleStepAdd:
			# Only handle scrollbar changes by keyboard
			self.parent.controller.handleScroll(DirectionEnum.UNKNOWN, False)
			return
		if scrollbar == self.horizontalScrollBar():
			directions = (DirectionEnum.WEST, DirectionEnum.EAST)
		else:
			directions = (DirectionEnum.NORTH, DirectionEnum.SOUTH)
		# Scrolling up
		direction = DirectionEnum.UNKNOWN
		isEdgeScroll = False
		if scrollType == QtWidgets.QAbstractSlider.SliderAction.SliderSingleStepSub:
			direction = directions[0]
			if scrollbar.value() == 0:
				isEdgeScroll = True
		# Scrolling down
		elif scrollType == QtWidgets.QAbstractSlider.SliderAction.SliderSingleStepAdd:
			direction = directions[1]
			if scrollbar.value() == scrollbar.maximum():
				isEdgeScroll = True
		self.parent.controller.handleScroll(direction, isEdgeScroll)

	def clearImages(self):
		self._baseImages = None
		self._clearImageItems()

	def _clearImageItems(self):
		if not self._imageItems:
			return
		for imageItem in self._imageItems:
			self._imageScene.removeItem(imageItem)
		self._imageItems = None
		self._baseImagesWidth = 0
		self._baseImagesHeight = 0
		self._scaledImagesWidth = 0
		self._scaledImagesHeight = 0

	def setImages(self, *images: QtGui.QImage):
		"""
		Display the image(s) to the user
		:param images: One or more images to show
		"""
		self._baseImages = images
		self._baseImagesWidth, self._baseImagesHeight = ImageUtils.calculateWidthAndHeight(self._baseImages, False)
		self._drawImages()

	def _drawImages(self):
		self._clearImageItems()
		if not self._baseImages:
			logging.warning(f"Asked to draw images, but none are loaded")
			return
		startTime = time.perf_counter()
		# Make the images the wanted size
		scaledImages = self._scaleImages(self._baseImages)
		# Store some values we need for dragging and scrolling
		self._scaledImagesWidth, self._scaledImagesHeight = ImageUtils.calculateWidthAndHeight(scaledImages)
		self._setSceneSize()
		# Actually load the images into the scene
		self._imageItems = []
		for image in scaledImages:
			self._imageItems.append(self._imageScene.addPixmap(QtGui.QPixmap(image)))
		# Position the images properly
		self._positionImages()
		# Reset the scroll position
		self._resetScrollPosition()
		# Show a hand icon if the image can be dragged, and no special icon if it can't
		self._setHandIconOnMouseOver()
		# Claim focus, so the image can be moved with the arrow keys
		self.setFocus()
		logging.debug(f"Displaying image took {time.perf_counter() - startTime:.4f} seconds")

	def _scaleImages(self, images: List[QtGui.QImage]) -> List[QtGui.QImage]:
		"""
		Scale the image according to the zoom settings
		While scaling the QGraphicsPixmapItem instead of the QPixmap is faster, scaling the QPixmap leads to better-looking results
		:param image: The pixmap to scale
		:return: The scaled pixmap
		"""
		# FIXME Handle differently-sized images
		startTime = time.perf_counter()
		# Calculate some values for sizing
		totalWidth, highestHeight = ImageUtils.calculateWidthAndHeight(images, False)
		# The image gap won't be scaled, but it does need to be taken into account when calculating the scaling, so calculate how much drawing room we have left
		if len(images) > 1:
			imageGap = SettingsStore.getSettingValue(SettingsEnum.GAP_BETWEEN_PAGES)
			canvasWidthAfterImageGaps = self.width() - imageGap * (len(images) - 1)
		else:
			canvasWidthAfterImageGaps = self.width()
		# Determine image scale based on zoom type
		if self.currentZoomType == ZoomEnum.ORIGINAL_SIZE:
			self.imageScale = 1
		elif self.currentZoomType == ZoomEnum.FIT_VERTICAL:
			self.imageScale = min(1.0, self.height() / highestHeight)
		elif self.currentZoomType == ZoomEnum.FIT_HORIZONTAL:
			self.imageScale = min(1, canvasWidthAfterImageGaps / totalWidth)
		elif self.currentZoomType == ZoomEnum.FIT_SCREEN:
			widthScale = 1
			heightScale = 1
			if totalWidth > canvasWidthAfterImageGaps:
				widthScale = canvasWidthAfterImageGaps / totalWidth
			if highestHeight > self.height():
				heightScale = self.height() / highestHeight
			self.imageScale = min(widthScale, heightScale)
		# No special handling needed for ZoomEnum.CUSTOM, because that already sets the image scale
		if self.imageScale == 1:
			# No need to resize if scale is 1
			scaledImages = images
		else:
			scaledImages = []
			for image in images:
				scaledImages.append(image.scaled(image.width() * self.imageScale, image.height() * self.imageScale, mode=QtCore.Qt.TransformationMode.SmoothTransformation))
		logging.debug(f"Scaling {len(scaledImages)} images by {self.imageScale:.2f}x based on canvas size {self.width()};{self.height()} "
			f"({canvasWidthAfterImageGaps} after subtracting image gap), and images width {totalWidth} and height {highestHeight} "
			f"took {time.perf_counter() - startTime:.4f} seconds")
		return scaledImages

	def _setSceneSize(self):
		"""Set the scene size so it isn't larger than the image or the view. This is needed because by default the scene only grows and doesn't shrink"""
		oldWidth = self._imageScene.width()
		oldHeight = self._imageScene.height()
		width = max(self.width(), self._scaledImagesWidth)
		height = max(self.height(), self._scaledImagesHeight)
		self.setSceneRect(0, 0, width, height)

	def _positionImages(self):
		# Add the images to the top middle of our canvas
		if self._scaledImagesWidth < self.width():
			# If the images are less wide than the canvas, make sure they're placed in the middle
			x = self.width() // 2 - self._scaledImagesWidth // 2
		else:
			# If the image is wider than the canvas, place the top-left corner of the image in the top-left of the canvas
			x = 0
		imageGap = SettingsStore.getSettingValue(SettingsEnum.GAP_BETWEEN_PAGES)
		for imageItem in self._imageItems:
			imageItem.setX(x)
			x += imageItem.boundingRect().width() + imageGap

	def _resetScrollPosition(self):
		self.verticalScrollBar().setValue(0)
		self.horizontalScrollBar().setValue(0)

	def scrollToTop(self):
		self.verticalScrollBar().setValue(0)

	def scrollToBottom(self):
		self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

	def _setHandIconOnMouseOver(self):
		shouldShowHandIcon = True
		if not self._imageItems:
			shouldShowHandIcon = False
		elif self._scaledImagesWidth <= self.width() and self._scaledImagesHeight <= self.height():
			shouldShowHandIcon = False
		self.setDragMode(self.DragMode.ScrollHandDrag if shouldShowHandIcon else self.DragMode.NoDrag)

	def resizeEvent(self, event: QtGui.QResizeEvent):
		if self._imageItems:
			self._setSceneSize()
			self._drawImages()

	def eventFilter(self, source: QtCore.QObject, event: QtCore.QEvent):
		if event.type() == QtCore.QEvent.ContextMenu:
			if self.contextMenu is None:
				self.contextMenu = BookDisplayContextMenu(self.parent, parent=self)
			self.contextMenu.updateMenu()
			self.contextMenu.exec_(event.globalPos())
		return False

	def setZoomType(self, zoomType: ZoomEnum):
		"""
		Set a new zoom type, and adjust the image immediately
		:param zoomType: The new zoom type
		"""
		if zoomType != self.currentZoomType:
			self.currentZoomType = zoomType
			self._drawImages()

	def zoomIn(self):
		self._zoom(_ZOOM_STEPS)

	def zoomOut(self):
		self._zoom(-_ZOOM_STEPS)

	def _zoom(self, zoomStepChange):
		self.currentZoomType = ZoomEnum.CUSTOM
		self.imageScale += zoomStepChange
		self._drawImages()
