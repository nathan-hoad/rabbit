#!/usr/bin/env python
import sys
import sqlite3
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic
from PyQt4.QtGui import QTableWidgetItem, QMenu, QMessageBox

from rabbit import *

app = QtGui.QApplication(sys.argv)

folder = os.path.split(os.path.realpath(__file__))[0] + '/'

Ui_MainWindow, Qt_MainWindow = uic.loadUiType(folder + 'mainwindow.ui');
Ui_AddWindow, Qt_AddWindow = uic.loadUiType(folder + 'add.ui');

class AddDialog(Qt_AddWindow, Ui_AddWindow):
    def __init__(self, rabbit, add_dialog=True, modify_issue=None):
        super(Qt_AddWindow, self).__init__()
        self.setupUi(self)
        self.setModal(True)

        self.rabbit = rabbit

        self.add_dialog = add_dialog

        i = Issue()

        if not self.add_dialog:
            self.issue = modify_issue
            self.setWindowTitle('Modify Issue')
            i = modify_issue

            self.summary.setText(i.summary)
            self.description.setPlainText(i.description)

        self.type.setText(i.type)
        self.priority.setText(i.priority)

        self.connect(self.buttonBox, QtCore.SIGNAL('accepted()'), self.add)

    def add(self):
        rabbit = self.rabbit

        summary = self.summary.text()
        type = self.type.text()
        priority = self.priority.text()
        description = self.description.toPlainText()

        i = Issue()

        if not self.add_dialog:
            i = self.issue

        i.summary = summary
        i.type = type
        i.priority = priority
        i.description = description

        if self.add_dialog:
            rabbit.add(i)
        else:
            rabbit.update(i)

class RabbitUI(Qt_MainWindow, Ui_MainWindow):
    rabbit = None

    def __init__(self):
        super(Qt_MainWindow, self).__init__()

        self.setupUi(self)
        self.setWindowTitle('Rabbit GUI')

        self.issueTable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self.addButton, QtCore.SIGNAL('clicked()'), self.display_add)
        self.connect(self.issueTable, QtCore.SIGNAL('itemSelectionChanged()'), self.load_detailed)
        self.connect(self.actionFilter, QtCore.SIGNAL('triggered()'), self.filter)
        self.connect(self.actionComment, QtCore.SIGNAL('triggered()'), self.comment)
        self.connect(self.actionModify, QtCore.SIGNAL('triggered()'), self.modify)

        self.issueTable.customContextMenuRequested.connect(self.right_click)

        self.filter_text = 'all'

    def display_add(self):
        a = AddDialog(self.rabbit)
        a.exec()

        if a.result() == QtGui.QDialog.Accepted:
            self.load_rabbit()

    def load_detailed(self):
        selected = self.issueTable.selectedItems()
        if len(selected) == 0:
            self.descriptionLabel.setText('')
            return

        id = selected[0].text()
        id = int(id)

        r = self.rabbit.issue(id)

        self.descriptionLabel.setText(repr(r))

    def load_rabbit(self):
        if not self.rabbit:
            try:
                self.rabbit = Rabbit()
            except MissingRepositoryError:
                Rabbit.init()
                self.rabbit = Rabbit()

        issues = self.rabbit.issues(self.filter_text)
        self.issueTable.setRowCount(len(issues))

        set_item = self.issueTable.setItem

        for i, issue in enumerate(issues):
            set_item(i, 0, QTableWidgetItem(str(issue.i_id)))
            set_item(i, 1, QTableWidgetItem(issue.type))
            set_item(i, 2, QTableWidgetItem(issue.date))
            set_item(i, 3, QTableWidgetItem(issue.status))
            set_item(i, 4, QTableWidgetItem(issue.priority))
            set_item(i, 5, QTableWidgetItem(issue.summary))

        self.issueTable.setWordWrap(True)
        self.issueTable.resizeColumnsToContents()

    def right_click(self, position):
        menu = QMenu()
        menu.addAction('Open')
        menu.addAction('Close')
        menu.addAction('Comment')
        menu.addSeparator()
        menu.addAction('Delete')
        menu.addAction('Modify')
        menu.addSeparator()
        menu.addAction('Filter')

        table = self.issueTable

        action = menu.exec_(self.issueTable.mapToGlobal(position))

        if action is None:
            return

        if action.text() == 'Open':
            items = table.selectedItems()
            items[3].setText('open')

            i_id = int(items[0].text())
            self.rabbit.open([i_id])

        elif action.text() == 'Close':
            items = table.selectedItems()
            items[3].setText('closed')

            i_id = int(items[0].text())
            self.rabbit.close([i_id])

        elif action.text() == 'Comment':
            self.comment()

        elif action.text() == 'Delete':
            result = QMessageBox.warning(self, 'Remove this Issue?', 'Are you sure you want delete this issue?', QMessageBox.Yes, QMessageBox.No)

            if result == QMessageBox.Yes:
                items = table.selectedItems()
                i_id = int(items[0].text())
                table.removeRow(table.currentRow())
                self.rabbit.delete(i_id)

        elif action.text() == 'Modify':
            self.modify()
        elif action.text() == 'Filter':
            self.filter()

    def modify(self):
        items = self.issueTable.selectedItems()

        if len(items) == 0:
            return

        i_id = int(items[0].text())

        a = AddDialog(self.rabbit, False, self.rabbit.issue(i_id))
        a.exec()

        if a.result() == QtGui.QDialog.Accepted:
            self.load_rabbit()

    def comment(self):
        dialog = QtGui.QInputDialog()
        dialog.setLabelText('Enter your comment:')
        dialog.exec()

        if dialog.result() == QtGui.QDialog.Accepted and dialog.textValue():
            t = dialog.textValue()
            items = self.issueTable.selectedItems()
            if len(items) == 0:
                return

            i_id = int(items[0].text())
            self.rabbit.comment(i_id, t)

    def filter(self):
        dialog = QtGui.QInputDialog()
        dialog.setLabelText('Status to filter (blank for everything)')
        dialog.exec()

        if dialog.result() == QtGui.QDialog.Accepted:
            self.filter_text = dialog.textValue()
            self.load_rabbit()


w = RabbitUI()

w.load_rabbit()

w.show()

sys.exit(app.exec_())
