import logging
from enum import Enum

class LoggingLevelEnum(Enum):
	DEBUG = logging.DEBUG, "Debug"
	INFO = logging.INFO, "Info"
	ERROR = logging.ERROR, "Error"

	def __init__(self, logLevel, displayName):
		self.logLevel = logLevel
		self.displayName = displayName

	def __str__(self):
		return self.displayName
