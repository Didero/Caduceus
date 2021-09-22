import logging, os, sys

from PySide6.QtWidgets import QApplication

# Set up some data we need for proper data retrieval
# We need to do this before importing our own classes, because those classes need these values set to work properly
QApplication.setApplicationName("Caduceus")  # Named 'Caduceus' because it's the snake-entwined staff of Hermes/Mercury, messenger of the gods and god of commerce and communication, among other things
from comicviewer.files import FileUtils
libPath = os.path.join(FileUtils.getProgramPath(), "lib")
os.environ['PATH'] += os.pathsep + FileUtils.getProgramPath() + os.pathsep + libPath

# Now we can set up the logging configuration
from comicviewer.settings.SettingsEnum import SettingsEnum
from comicviewer.settings import SettingsStore
logLevel = SettingsStore.getSettingValue(SettingsEnum.LOGGING_LEVEL).logLevel
logging.basicConfig(level=logLevel, format="[%(asctime)s] <%(levelname)s> %(message)s [%(module)s:%(lineno)d %(funcName)s()  threadID %(thread)d]")

# Finally we've set up everything enough that we can open the actual window
from comicviewer.ui.MainWindow import MainWindow
app = QApplication()
window = MainWindow()
exitStatusCode = app.exec()
sys.exit(exitStatusCode)
