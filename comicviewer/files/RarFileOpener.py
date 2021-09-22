from typing import List

import rarfile

from comicviewer.files.BaseFileOpener import BaseFileOpener


class RarFileOpener(BaseFileOpener):
	SUPPORTED_EXTENSIONS = ('.rar', '.cbr')

	def open(self):
		self.file = rarfile.RarFile(self.filepath)

	def _getFileList(self) -> List[str]:
		return self.file.namelist()

	def _readFile(self, filename: str) -> bytes:
		return self.file.read(filename)
