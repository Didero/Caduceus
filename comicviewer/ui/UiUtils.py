from PySide6.QtWidgets import QMessageBox, QPushButton

def createButton(buttonText, clickFunction, parent=None, tooltipText=None, buttonWidth=None, isDisabled=False):
	button = QPushButton(buttonText)
	button.clicked.connect(clickFunction)
	button.setMaximumWidth(5 + 10 * len(buttonText) if buttonWidth is None else buttonWidth)
	if tooltipText:
		button.setToolTip(tooltipText)
	if isDisabled:
		button.setDisabled(True)
	if parent is not None:
		parent.addWidget(button)
	return button

def _showMessagePopup(title, message, parent=None, messageType=QMessageBox.Information):
	messageBox = QMessageBox()
	messageBox.setWindowTitle(title)
	messageBox.setText(message)
	messageBox.setIcon(messageType)
	if parent:
		messageBox.setParent(parent)
	messageBox.exec_()

def showInformationMessagePopup(title, message, parent=None):
	_showMessagePopup(title, message, parent, QMessageBox.Information)

def showWarningMessagePopup(title, message, parent=None):
	_showMessagePopup(title, message, parent, QMessageBox.Warning)

def showErrorMessagePopup(title, message, parent=None):
	_showMessagePopup(title, message, parent, QMessageBox.Critical)


def askUserQuestion(title, message, parent=None) -> bool:
	return QMessageBox.question(parent, title, message) == QMessageBox.StandardButton.Yes
