from enum import Enum, auto

class ZoomEnum(Enum):
	ORIGINAL_SIZE = "Original Size", "1x", "Show the image at its original size, without zooming or scaling"
	FIT_VERTICAL = "Fit Vertical", "↕", "Scale the image so that it's displayed as high as the window is"
	FIT_HORIZONTAL = "Fit Horizontal", "↔", "Scale the image so that it's displayed as wide as the window is"
	FIT_SCREEN = "Fit Screen", "↕↔", "Fit either vertically or horizontally, whatever makes the image fit the screen"
	CUSTOM = "Custom", "C", "Zoomed at a custom level, set by manually zooming in and out"

	def __init__(self, displayName, shortDisplayName, description):
		self.displayName = displayName
		self.shortDisplayName = shortDisplayName
		self.description = description

	def __str__(self):
		return self.displayName
