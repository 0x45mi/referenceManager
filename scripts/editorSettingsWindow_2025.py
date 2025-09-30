import sys

from PySide6.QtWidgets import QDialog, QApplication, QRadioButton, QCheckBox, QVBoxLayout, QLabel, QSpacerItem, QSizePolicy, QFrame, QLineEdit
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QGuiApplication, QDoubleValidator
import styleSheet
import customWidgets_2025 as cw

class SettingsWindow(QDialog):

    def __init__(self, parent=None):

        self.copyClicked = Signal(bool)

        super().__init__(parent)

        ## Widgets ##
        col = "#212121"
        colLight = "#313131"
        tcol = "#bbbbbb"
        self.setFixedSize(500, 300)

        def heading1(title):
            titleLabel = QLabel(title)
            titleLabel.setSizePolicy(QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum))
            titleLabel.setMargin(0)
            titleLabel.setStyleSheet(f"font-size: 11.5px; color: {tcol};")
            return titleLabel
        
        self.path_lineEdit = QLineEdit()
        self.path_lineEdit.setSizePolicy(QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum))
        self.path_lineEdit.setReadOnly(True)
        self.path_lineEdit.setStyleSheet(styleSheet.Dark_style())
        self.path_lineEdit.setText("")

        self.separator = QFrame(self)
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        def heading2(title): #output path, cache size, look ahead, look behind
            titleLabel2 = QLabel(title)
            titleLabel2.setAlignment(Qt.AlignLeft)
            titleLabel2.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))
            titleLabel2.setStyleSheet(f"font-size: 11px; color: {tcol};")
            return titleLabel2
        
        def my_lineEdit(numStr):
            my_lineEdit = (cw.AutoLineEdit(numStr))
            my_lineEdit.setValidator(QDoubleValidator(0, 2147483647, 0))
            my_lineEdit.setAlignment(Qt.AlignRight)
            my_lineEdit.setMaximumSize(50, 16)
            my_lineEdit.setStyleSheet(styleSheet.Dark_style())
            return my_lineEdit

        def cache_field(title, numStr):
            cacheField_widget = cw.FilledWidget(38, col, self)
            cacheField_widget.layout.setSpacing(6)
            cacheField_widget.layout.setAlignment(Qt.AlignLeft)
            cacheField_widget.layout.addItem(QSpacerItem(120, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
            cacheField_widget.layout.addWidget(heading2(title))
            cacheField_widget.layout.addItem(QSpacerItem(1, 1, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum))
            cacheField_widget.line_edit = my_lineEdit(numStr)
            cacheField_widget.layout.addWidget(cacheField_widget.line_edit)
            cacheField_widget.layout.addItem(QSpacerItem(240, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
            return cacheField_widget
        
        def myRadioButton(title):
            my_radioButton = QRadioButton(title)
            my_radioButton.setStyleSheet(f"font-size: 11px; color: {tcol};")
            return my_radioButton
        
        def radioButton_lay():
            radioButton_layout = cw.FilledVWidget(col, self)
            radioButton_layout.imagePlane_rb = myRadioButton("Image plane")
            radioButton_layout.floatingImagePlane_rb = myRadioButton("Floating image plane")
            radioButton_layout.layout.addWidget(radioButton_layout.imagePlane_rb)
            radioButton_layout.layout.addWidget(radioButton_layout.floatingImagePlane_rb)
            return radioButton_layout
        
        def my_iconButton(id):
            icon_pushbutton = cw.IconButton(id)
            icon_pushbutton.setAutoDefault(False)
            icon_pushbutton.setDefault(False)
            icon_pushbutton.setFixedSize(29, 26)
            icon_pushbutton.setStyleSheet(styleSheet.maya_button_style())
            return icon_pushbutton
        
        def heading_widget(title):
            heading_widget = cw.FilledWidget(22, colLight, self)
            heading_widget.layout.setContentsMargins(22, 0, 20, 0)
            heading_widget.layout.addWidget(heading1(title))
            return heading_widget

        
        ### Layout ###

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout_frame = cw.FilledVWidget(col, self)

        referenceFolder_widget = cw.FilledVWidget(col, self)
        layout_frame.layout.setSpacing(0)
        layout_frame.layout.setContentsMargins(8, 4, 8, 10)
        referenceFolder_widget.layout.addWidget(heading_widget("Reference folder"))

        path_widget = cw.FilledWidget(38, col, self)
        path_widget.setContentsMargins(22, 0, 22, 0)
        path_widget.layout.setSpacing(4)
        path_widget.layout.addItem(QSpacerItem(25, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        path_widget.layout.addWidget(heading2("Output path:"))
        path_widget.layout.addWidget(self.path_lineEdit)
        twoButton_layout = cw.FilledWidget(38, col, self)
        twoButton_layout.layout.setSpacing(1)
        self.copyButton = my_iconButton("Copy")
        twoButton_layout.layout.addWidget(self.copyButton)
        self.editButton = my_iconButton("Edit")
        twoButton_layout.layout.addWidget(self.editButton)
        path_widget.layout.addWidget(twoButton_layout)
        referenceFolder_widget.layout.addWidget(path_widget)
        layout_frame.layout.addWidget(referenceFolder_widget)

        self.caching_widget = cw.FilledVWidget(col, self)
        cachingCheckboxWidget = cw.FilledWidget(22, colLight, self)
        cachingCheckboxWidget.layout.setContentsMargins(22, 0, 23, 0)
        cachingCheckboxWidget.layout.setSpacing(9)
        cachingCheckboxWidget.layout.addWidget(heading1("Caching"))
        self.cachingCheckbox = QCheckBox()
        cachingCheckboxWidget.layout.addWidget(self.cachingCheckbox)
        self.cacheReset = cw.IconButton("mini_reset2")
        self.cacheReset.setAutoDefault(False)
        self.cacheReset.setDefault(False)
        self.cacheReset.setFixedSize(27, 16)
        self.cacheReset.setStyleSheet(styleSheet.Light_button_style())
        cachingCheckboxWidget.layout.addWidget(self.cacheReset)
        
        self.caching_widget.layout.addWidget(cachingCheckboxWidget)
        self.caching_widget.layout.addItem(QSpacerItem(1, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

        self.caching_options = cw.FilledVWidget(col, self)
        self.cacheSize = cache_field("Cache size", "123")
        self.lookAhead = cache_field("Look ahead", "456")
        self.lookBehind = cache_field("Look behind", "789")
        self.caching_options.layout.addWidget(self.cacheSize)
        self.caching_options.layout.addWidget(self.lookAhead)
        self.caching_options.layout.addWidget(self.lookBehind)

        self.caching_widget.layout.addWidget(self.caching_options)
        layout_frame.layout.addWidget(self.caching_widget)

        plateSetup_widget = cw.FilledVWidget(col, self)
        plateSetup_widget.layout.addWidget(heading_widget("Plate setup in Maya"))
        radioButton_widget = cw.FilledWidget(42, col, self)
        radioButton_widget.layout.addItem(QSpacerItem(120, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        self.radioButton_layout = radioButton_lay()
        radioButton_widget.layout.addWidget(self.radioButton_layout)
        plateSetup_widget.layout.addWidget(radioButton_widget)
        layout_frame.layout.addWidget(plateSetup_widget)

        layout.addWidget(layout_frame)
        self.setLayout(layout)  


        ### Event handlers ###

        self.cacheReset.clicked.connect(self.resetCacheSettings)
        self.copyButton.clicked.connect(self.copyToClipboard)
        self.cachingCheckbox.clicked.connect(self.cacheSwitch)

    def populateSettings(self, outputPath, cachingBool, cachesize, lookAhead, lookBehind, IPBool):
        self.path_lineEdit.setText(outputPath)
        self.cachingCheckbox.setChecked(cachingBool)
        self.cacheSize.line_edit.setText(cachesize)
        self.lookAhead.line_edit.setText(lookAhead)
        self.lookBehind.line_edit.setText(lookBehind)
        self.cacheSwitch(cachingBool)
        
        if IPBool == 0:
            self.radioButton_layout.imagePlane_rb.setChecked(True)
            self.radioButton_layout.floatingImagePlane_rb.setChecked(False)
        else:
            self.radioButton_layout.imagePlane_rb.setChecked(False)
            self.radioButton_layout.floatingImagePlane_rb.setChecked(True)

    def cacheSwitch(self, checked: bool):
        self.cachingCheckbox.setChecked(checked)

        # Update QLineEdits
        for lineEdit in self.caching_widget.findChildren(QLineEdit):
            lineEdit.setEnabled(checked)
            if checked:
                lineEdit.setStyleSheet(styleSheet.Dark_style())
            else:
                lineEdit.setStyleSheet(styleSheet.Dark_style() + "color: #414141;")

        # Update QLabel styles
        for label in self.caching_options.findChildren(QLabel):
            if checked:
                label.setStyleSheet("font-size: 11px; color: #bbbbbb;")
            else:
                label.setStyleSheet("font-size: 11px; color: #414141;")
        
    def resetCacheSettings(self):
        self.cacheSwitch(True)
        self.cacheSize.line_edit.setText("800")
        self.lookAhead.line_edit.setText("750")
        self.lookBehind.line_edit.setText("50")

    def copyToClipboard(self):
        # Copy text
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.path_lineEdit.text())

        # Show floating message
        toast = QLabel("Copied to clipboard", self)
        toast.setStyleSheet("""
            border-style: outset;
            border-width: 1px;
            border-radius: 3px;
            border-color: #414141;
            color: #bbbbbb;
            background-color: #111111;
            padding: 6px 12px;
            font-size: 11px;
        """)
        toast.setWindowFlags(Qt.ToolTip)
        toast.adjustSize()

        # Center it over parent
        if self:
            geo = self.geometry()
            x = geo.x() + (geo.width() - toast.width()) // 2 
            y = geo.y() + 25  # a little below the top
            toast.move(x, y)

        toast.show()

        # Hide automatically after 1.5 seconds
        QTimer.singleShot(1200, toast.close)

    def mousePressEvent(self, event):
        if QApplication.focusWidget():  # Check if any widget has focus
            QApplication.focusWidget().clearFocus()  # Explicitly remove focus
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if QApplication.focusWidget():
                QApplication.focusWidget().clearFocus()
            return  # prevent further handling (optional)
        super().keyPressEvent(event)
    
'''
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = SettingsWindow()
    window.populateSettings("Me llamo Carlos", True, "800", "750", "50", 0)
    window.show()


    sys.exit(app.exec())'''