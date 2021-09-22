from enum import Enum

from comicviewer.ui.ZoomEnum import ZoomEnum
from comicviewer.misc.LoggingLevelEnum import LoggingLevelEnum


class SettingsEnum(Enum):
	# Cache related settings
	CACHE_AHEAD_COUNT = 2, "How many pages ahead of the current one will be loaded in advance to speed up changing page"
	CACHE_BEHIND_COUNT = 2, "How many pages behind the current one will be loaded in advance to speed up changing page"
	UNCACHE_EXTRA_RANGE = 2, "How far a page has to be beyond the Cache Behind and Cache Ahead ranges to be removed from the cache. Makes it a bit quicker to go back a page to quickly check something and then going to the next page again"
	# Book display settings
	LIBRARY_PATH = "", "The folder of the comic book library", True
	ALLOW_MULTIPLE_BOOKS = True, "If this is true, multiple books can be opened. If this is false, only one book can be opened at a time"
	SHOW_TWO_PAGES = True, "If true, two pages will be shown side-by-side, to emulate a physical comic book. The front and back cover and two-page spreads will still be shown on their own"
	GAP_BETWEEN_PAGES = 5, "If 'Show Two Pages' is on, this setting determines the size in pixels of the gap between the two pages"
	DEFAULT_ZOOM_TYPE = ZoomEnum.FIT_SCREEN, "The default image zoom level"
	# Scrolling settings
	CHANGE_PAGE_WHEN_SCROLL_PAST_EDGE = True, "If this is true, scrolling past the edge of a page changes to the next page. If false, changing pages can only be done with the dedicated page change buttons"
	TIME_BEFORE_SCROLL_CHANGES_PAGE = 0.2, "To prevent changing pages by scrolling too quickly, this setting sets the minimum time between reaching the image edge and actually changing page on persistent scrolling"
	# History settings
	BOOK_HISTORY_SIZE = 5, "How many opened books are saved in the History list"
	RESTORE_PREVIOUS_SESSION = True, "When reopening the application, whether to open the comic book(s) that were open when the application was closed"
	# Misc
	LOGGING_LEVEL = LoggingLevelEnum.INFO, "The lowest message level to log. Keep at 'INFO' unless you have a good reason to change it"

	def __init__(self, defaultValue, fullDescription, isHidden=False):
		self.defaultValue = defaultValue
		self.fullDescription = fullDescription
		self.shortDescription = self.name.replace('_', ' ').title()
		self.isHidden = isHidden
