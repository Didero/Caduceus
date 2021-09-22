from typing import Callable, Dict, Union

from PySide6.QtCore import Qt

from comicviewer.keyboard.KeyboardAction import KeyboardAction

_keyActionToFunction: Dict[KeyboardAction, Callable] = {}

# Map the Qt.Key_ key constants to our keyboard actions
_qtKeyToKeyAction = {
	# Navigation
	Qt.Key_PageUp: KeyboardAction.PREVIOUS_PAGE,
	Qt.Key_PageDown: KeyboardAction.NEXT_PAGE,
	Qt.Key_Home: KeyboardAction.FIRST_PAGE,
	Qt.Key_End: KeyboardAction.LAST_PAGE,
	Qt.Key_P: KeyboardAction.PREVIOUS_BOOK,
	Qt.Key_N: KeyboardAction.NEXT_BOOK,
	Qt.Key_X: KeyboardAction.CLOSE_BOOK,
	Qt.Key_S: KeyboardAction.GO_TO_SETTINGS,
	Qt.Key_B: KeyboardAction.GO_TO_BOOK_SELECTION,
	# Zooming
	Qt.Key_Plus: KeyboardAction.ZOOM_IN,
	Qt.Key_Minus: KeyboardAction.ZOOM_OUT,
	# UI display
	Qt.Key_F: KeyboardAction.TOGGLE_FULLSCREEN,
	Qt.Key_C: KeyboardAction.TOGGLE_CONTROLS_PANEL,
	Qt.Key_Escape: KeyboardAction.LEAVE_FULLSCREEN,
	Qt.Key_T: KeyboardAction.TOGGLE_TABBAR,
}

def registerForKeyboardAction(keyboardAction: KeyboardAction, functionToRegister: Callable):
	_keyActionToFunction[keyboardAction] = functionToRegister

def getActionForKey(key) -> Union[KeyboardAction, None]:
	"""
	Get the action linked to the provided key, or None if it can't be found
	:param key: The key to get the action for
	:return: Either the KeyboardAction if it can be found, or None if it can't be found
	"""
	return _qtKeyToKeyAction.get(key, None)

def handleKeyPress(key) -> bool:
	"""
	Handle a Qt keypress
	:param key: The key that was pressed, often from event.key()
	:return: True if the keypress was handled, False if not
	"""
	if key not in _qtKeyToKeyAction:
		return False
	keyAction = _qtKeyToKeyAction[key]
	if keyAction not in _keyActionToFunction:
		return False
	_keyActionToFunction[keyAction]()
	return True
