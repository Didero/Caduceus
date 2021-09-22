import json, logging, os
from typing import List, Optional

from comicviewer.files import FileUtils
from comicviewer.settings import SettingsStore
from comicviewer.settings.SettingsEnum import SettingsEnum

_historyFilePath = os.path.join(FileUtils.getStoragePath(), 'history.json')
_bookOpenedHistory = []  # The order in which books were loaded, basically the history. Index 0 is the most recently loaded book
_bookToPage = {}  # Which page each book is at
_currentSession = []  # Which books are currently open
_currentlySelectedBookPath = None  # Which book is currently selected

_needsSaving: bool = False


def storeBookOpened(bookPath: str):
	"""
	Store that a book was opened
	:param bookPath: The path of the book that was opened
	"""
	if bookPath in _bookOpenedHistory:
		_bookOpenedHistory.remove(bookPath)
	_bookOpenedHistory.insert(0, bookPath)
	if bookPath not in _currentSession:
		_currentSession.append(bookPath)
	trimHistory()
	saveHistory()

def storeBookClosed(bookPath: str, shouldSave: bool = True):
	"""
	Store that a book was closed
	:param bookPath: The path of the book that was closed
	:param shouldSave: Whether the session change should be saved to file. Should usually be left on True. If set to False, be sure to call 'saveHistory()' manually
	"""
	_currentSession.remove(bookPath)
	if shouldSave:
		saveHistory()
	else:
		_setNeedsSaving()

def setCurrentBook(bookPath: str or None):
	"""
	Set which book is currently opened and displayed. Used to show the same book when the program is closed and reopened
	:param bookPath: The bookpath to store at the currently displayed book. Set to None to clear the stored book khkhkhuhhuhuhuh
	"""
	global _currentlySelectedBookPath
	_currentlySelectedBookPath = bookPath
	_setNeedsSaving()

def getCurrentBook() -> Optional[str]:
	""":return: The current book, or the book that was open if this gets called when the program is started. Can also be None if no book was opened"""
	return _currentlySelectedBookPath

def getStoredPage(bookPath: str):
	return _bookToPage.get(bookPath, 0)

def setStoredPage(bookPath: str, index: int):
	# No need to store that we're at the first page
	if index == 0:
		_bookToPage.pop(bookPath, None)
	else:
		_bookToPage[bookPath] = index
	_setNeedsSaving()

def getHistory() -> List[str]:
	""":return:	Returns a list with the book history. Index 0 is the most recently loaded book.
	This is a copy of the actual list, so modifications to the history list aren't reflected in the returned list"""
	return _bookOpenedHistory[:]

def getSession() -> List[str]:
	"""Get a copy of the current session list. Since it's a copy, modifications to the session list aren't reflected in the returned list"""
	return _currentSession[:]

def removeFromHistory(bookPath: str) -> bool:
	"""
	Remove the provided book path from the book history, if it's not currently opened
	:param bookPath: The book path to remove from history
	:return: True if the book was removed, False if it wasn't removed because it's currently open
	"""
	if bookPath in _bookOpenedHistory and bookPath not in _currentSession:
		_bookOpenedHistory.remove(bookPath)
		_bookToPage.pop(bookPath, None)
		_setNeedsSaving()
		return True
	return False

def clearHistory() -> bool:
	"""
	Clear the entire history, except for books currently opened
	:return: True if the entire history was cleared, False if one or more books were kept because they're curently opened
	"""
	global _bookOpenedHistory
	wasFullyCleared = True
	for bookPath in _bookOpenedHistory[:]:
		# Only remove the books from history that aren't currently open
		if bookPath not in _currentSession:
			_bookOpenedHistory.remove(bookPath)
			_bookToPage.pop(bookPath, None)
		else:
			wasFullyCleared = False
	saveHistory()
	return wasFullyCleared

def trimHistory():
	"""Make sure the history doesn't get larger than allowed"""
	global _bookOpenedHistory
	maxHistorySize = SettingsStore.getSettingValue(SettingsEnum.BOOK_HISTORY_SIZE)
	if maxHistorySize == 0:
		# Keep no history, only update the list if we weren't already storing nothing
		if len(_bookOpenedHistory) > 0:
			_bookOpenedHistory = []
			_setNeedsSaving()
	elif len(_bookOpenedHistory) > maxHistorySize:
		# Remove the oldest book(s) from the history to shrink it back to the required size
		for bookPath in _bookOpenedHistory[maxHistorySize:]:
			if bookPath not in _currentSession:
				_bookToPage.pop(bookPath, None)
		_bookOpenedHistory = _bookOpenedHistory[:maxHistorySize]
		_setNeedsSaving()

def saveHistory():
	if not _needsSaving:
		return
	if not os.path.isdir(FileUtils.getStoragePath()):
		os.makedirs(FileUtils.getStoragePath())
	historyData = {'loadOrder': _bookOpenedHistory, 'bookToPage': _bookToPage}
	if SettingsStore.getSettingValue(SettingsEnum.RESTORE_PREVIOUS_SESSION):
		historyData['session'] = _currentSession
	if _currentlySelectedBookPath:
		historyData['selectedBook'] = _currentlySelectedBookPath
	with open(_historyFilePath, 'w') as historyFile:
		json.dump(historyData, historyFile)
	_setNeedsSaving(False)

def _loadHistory():
	global _bookOpenedHistory, _bookToPage, _currentSession, _currentlySelectedBookPath
	historyData = {}
	if os.path.isfile(_historyFilePath):
		try:
			with open(_historyFilePath, 'r') as historyFile:
				historyData = json.load(historyFile)
		except Exception as e:
			logging.error(f"Loading the history data failed with a '{type(e)}' exception: {e}")
	# Parse the loaded data (or use defaults if it's missing)
	_bookOpenedHistory = historyData.get('loadOrder', [])
	_bookToPage = historyData.get('bookToPage', {})
	if SettingsStore.getSettingValue(SettingsEnum.RESTORE_PREVIOUS_SESSION):
		_currentSession = historyData.get('session', [])
		_currentlySelectedBookPath = historyData.get('selectedBook', None)
	else:
		_currentSession = []
		_currentlySelectedBookPath = None
	_setNeedsSaving(False)

def _setNeedsSaving(needsSaving: bool = True):
	"""
	Set that the in-memory data differs from the on-disk data, so that we need to save
	:param needsSaving: When True (the default), set that we need to save. When False, store that there is no in-memory data we need to save at the moment
	"""
	global _needsSaving
	_needsSaving = needsSaving


_loadHistory()
