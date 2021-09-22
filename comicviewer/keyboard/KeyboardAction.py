from enum import Enum, auto

class KeyboardAction(Enum):
	# Navigation keys
	PREVIOUS_PAGE = auto()
	NEXT_PAGE = auto()
	FIRST_PAGE = auto()
	LAST_PAGE = auto()
	PREVIOUS_BOOK = auto()
	NEXT_BOOK = auto()
	CLOSE_BOOK = auto()
	GO_TO_SETTINGS = auto()
	GO_TO_BOOK_SELECTION = auto()
	# Zooming keys
	ZOOM_IN = auto()
	ZOOM_OUT = auto()
	ZOOM_ORIGINAL_SIZE = auto()
	ZOOM_FIT_SCREEN = auto()
	# UI display keys
	TOGGLE_FULLSCREEN = auto()
	LEAVE_FULLSCREEN = auto()
	TOGGLE_CONTROLS_PANEL = auto()
	TOGGLE_TABBAR = auto()
