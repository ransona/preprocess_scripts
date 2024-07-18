import os
import pickle
from PyQt5 import QtWidgets, QtGui, QtCore

class PickleEditorApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QtWidgets.QVBoxLayout(self)

        # File list
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.currentItemChanged.connect(self.loadPickleFile)
        self.layout.addWidget(self.listWidget)

        # Editor area
        self.editor = QtWidgets.QTextEdit()
        self.editor.setReadOnly(False)
        self.layout.addWidget(self.editor)

        # Save button
        self.saveButton = QtWidgets.QPushButton("Save Changes")
        self.saveButton.clicked.connect(self.saveChanges)
        self.layout.addWidget(self.saveButton)

        self.currentFile = None
        self.originalContent = None

        # Load .pickle files from the folder
        self.loadFileList()

        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle('Pickle File Editor')
        self.show()

    def loadFileList(self):
        folder_path = '.'  # Set to the directory you want to list
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.pickle'):
                self.listWidget.addItem(file_name)

    def loadPickleFile(self, current, previous):
        if current is None:
            return
        
        if previous and self.originalContent != self.editor.toPlainText():
            reply = QtWidgets.QMessageBox.question(self, 'Save Changes?',
                "Do you want to save changes to the file?", QtWidgets.QMessageBox.Yes |
                QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                self.saveChanges()

        file_path = os.path.join('.', current.text())
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
            self.editor.clear()
            self.editor.setPlainText(str(data))
            self.currentFile = file_path
            self.originalContent = str(data)

    def saveChanges(self):
        if self.currentFile:
            data = eval(self.editor.toPlainText())
            with open(self.currentFile, 'wb') as f:
                pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
            self.originalContent = self.editor.toPlainText()
            QtWidgets.QMessageBox.information(self, "Success", "Changes saved successfully!")

def main():
    app = QtWidgets.QApplication([])
    ex = PickleEditorApp()
    app.exec_()

if __name__ == '__main__':
    main()
