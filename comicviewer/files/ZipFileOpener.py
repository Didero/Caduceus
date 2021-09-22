import zipfile
from typing import List

from comicviewer.files.BaseFileOpener import BaseFileOpener


class ZipFileOpener(BaseFileOpener):
	SUPPORTED_EXTENSIONS = ('.zip', '.cbz')

	def open(self):
		self.file = zipfile.ZipFile(self.filepath, 'r')

	def _getFileList(self) -> List[str]:
		return self.file.namelist()

	def _readFile(self, filename: str) -> bytes:
		with self.file.open(filename) as f:
			return f.read()
