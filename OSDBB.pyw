import logging
import sys
import json

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QFileDialog,
    QMainWindow,
    QMessageBox,
)


class GUI(QMainWindow):
    def __init__(self):
        super(GUI, self).__init__()

        self.version = "23.7.1"  # year, month, release number of the month
        self.labels = []
        self.label_dicts = []
        self.is_programmed_change = False  # used to stop input events happening during changes set from code instead of user input
        self.last_used_file_path = ""

        # create osd and editor
        self.osd_window = self.create_osd()
        uic.loadUi("base/osdbb_editor.ui", self)

        # add functionality to editor
        self.action_new.triggered.connect(self.load)
        self.action_open_file.triggered.connect(self.open_file)
        self.action_save.triggered.connect(self.quick_save)
        self.action_save_as.triggered.connect(self.save_as)
        self.action_set_default.triggered.connect(self.set_default)
        self.action_hide.triggered.connect(self.hide)
        self.action_formatting.triggered.connect(self.show_formatting_message)
        self.action_about.triggered.connect(self.show_about_message)
        self.combo_box.addItems(self.get_names_from_labels())
        self.combo_box.currentIndexChanged.connect(self.update_gui_from_label)
        self.line_edit.textChanged.connect(self.update_from_input)
        self.x_spin_box.valueChanged.connect(self.update_from_input)
        self.y_spin_box.valueChanged.connect(self.update_from_input)
        self.plain_text_edit.textChanged.connect(self.update_from_input)
        self.add_button.clicked.connect(self.add_item)
        self.delete_button.clicked.connect(self.delete_item)

        self.show()

    def create_osd(self):
        osd_window = QWidget()
        osd_window.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowTransparentForInput
            | QtCore.Qt.SplashScreen
        )
        osd_window.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        osd_window.setWindowTitle("OSDBB")
        osd_window.showMaximized()

        return osd_window

    def get_initial_label_dicts(self):
        return [
            dict(
                text="New Label",
                x=0,
                y=0,
                style="color: white;\nfont-family: Verdana;\nfont-size: 32pt;\nfont-weight: bold;",
            )
        ]

    def save(self, file_path):
        self.last_used_file_path = file_path

        with open(file_path, "w") as out_file:
            self.dump_labels_to_dicts()
            json.dump(self.label_dicts, out_file, indent=4)
            self.label_dicts.clear()

    def load(self, file_path=None):
        self.label_dicts = self.get_initial_label_dicts()

        if file_path:
            try:
                with open(file_path, "r") as in_file:
                    self.label_dicts = json.load(in_file)
                    self.last_used_file_path = file_path
            except (IOError, json.decoder.JSONDecodeError):
                logging.exception("Load error")

        for label in self.labels:
            label.clear()  # clear QLabels before clearing the labels list

        self.labels.clear()
        self.dump_dicts_to_labels()
        self.label_dicts.clear()
        self.select_latest_entry()

    def open_file(self):
        open_dialog = QFileDialog()
        file_path = open_dialog.getOpenFileName(
            None, "Open File", "layouts", "JSON (*.json)"
        )[0]  # returns tuple with file and type filter

        if file_path:  # file dialog will return empty string if canceled or closed
            self.load(file_path)

    def quick_save(self):
        self.save(self.last_used_file_path)

    def save_as(self):
        save_dialog = QFileDialog()
        file_path = save_dialog.getSaveFileName(
            None, "Save As", "layouts", "JSON (*.json)"
        )[0]

        if file_path:
            self.save(file_path)

    def set_default(self):
        self.save("layouts/default.json")

    def hide(self):
        if self.action_hide.isChecked():
            self.osd_window.hide()
            return

        self.osd_window.showMaximized()
        self.activateWindow()

    def show_formatting_message(self):
        version_message = QMessageBox()
        version_message.setWindowTitle("Formatting")
        version_message.setTextFormat(QtCore.Qt.RichText)
        version_message.setText(
            """OSDBB Editor supports the same subset of HTML tags and CSS properties as QT<br><br>
            <center>Example</center>
            Text: &lt;center&gt;Title&lt;/center&gt;content&lt;br&gt;&lt;img src=&quot;images/picture.jpg&quot;&gt;<br>Style: text-decoration: line-through; border: 8px solid red;<br><br>
            <center>Refer to the full documentation <a href='https://doc.qt.io/qt-5/richtext-html-subset.html'>here</a></center>"""
        )
        version_message.setStandardButtons(QMessageBox.Ok)
        version_message.exec()

    def show_about_message(self):
        version_message = QMessageBox()
        version_message.setWindowTitle("About")
        version_message.setText("Version: " + self.version)
        version_message.setStandardButtons(QMessageBox.Ok)
        version_message.exec()

    def update_dict_from_label(self, index):
        self.label_dicts[index]["text"] = self.labels[index].text()
        self.label_dicts[index]["x"] = self.labels[index].x()
        self.label_dicts[index]["y"] = self.labels[index].y()
        self.label_dicts[index]["style"] = self.labels[index].styleSheet()

    def update_gui_from_label(self):
        index = self.combo_box.currentIndex()
        self.is_programmed_change = True
        self.line_edit.setText(self.labels[index].text())
        self.x_spin_box.setValue(self.labels[index].x())
        self.y_spin_box.setValue(self.labels[index].y())
        self.plain_text_edit.setPlainText(self.labels[index].styleSheet())
        self.is_programmed_change = False

    def update_label_from_gui(self, index):
        self.labels[index].setText(self.line_edit.text())
        self.labels[index].move(self.x_spin_box.value(), self.y_spin_box.value())
        self.labels[index].setStyleSheet(self.plain_text_edit.toPlainText())
        self.labels[index].adjustSize()

    def make_label(self, text, x, y, style):
        label = QLabel(text, self.osd_window)
        label.setStyleSheet(style)
        label.move(x, y)
        label.show()
        self.labels.append(label)

    def dump_dicts_to_labels(self):
        for label_dict in self.label_dicts:
            self.make_label(
                label_dict["text"],
                label_dict["x"],
                label_dict["y"],
                label_dict["style"],
            )

    def dump_labels_to_dicts(self):
        for index in range(len(self.labels)):
            self.label_dicts.append(dict())
            self.update_dict_from_label(index)

    def get_names_from_labels(self):
        names = []

        for label in self.labels:
            names.append(label.text())

        return names

    def select_latest_entry(self):
        self.combo_box.clear()
        self.combo_box.addItems(self.get_names_from_labels())
        self.combo_box.setCurrentIndex(self.combo_box.count() - 1)

    def update_from_input(self):
        if self.is_programmed_change:
            return

        index = self.combo_box.currentIndex()
        self.update_label_from_gui(index)
        self.combo_box.setItemText(index, self.line_edit.text())

    def add_item(self):
        self.make_label(
            "New Label", 0, 0, self.labels[self.combo_box.currentIndex()].styleSheet()
        )
        self.select_latest_entry()

    def delete_item(self):
        if len(self.labels) > 1:
            self.labels[self.combo_box.currentIndex()].clear()
            del self.labels[self.combo_box.currentIndex()]

        self.select_latest_entry()

    def closeEvent(self, event):
        self.osd_window.close()


def main():
    app = QApplication(sys.argv)
    osdbb_editor = GUI()
    osdbb_editor.load("layouts/default.json")
    app.exec_()


if __name__ == "__main__":
    main()
