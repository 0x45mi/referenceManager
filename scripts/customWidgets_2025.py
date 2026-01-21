from PySide6.QtWidgets import QComboBox, QLineEdit
from PySide6 import QtCore, QtGui, QtWidgets
import math


class EComboBox(QComboBox):
    def focusOutEvent(self, event):   
        # Ensure there's a QLineEdit and the validator is set
        if self.lineEdit() and self.lineEdit().hasAcceptableInput():
            self.lineEdit().returnPressed.emit() 
        elif self.lineEdit():
            self.lineEdit().setAlignment(QtGui.Qt.AlignRight)
            self.lineEdit().setText("🔴")
            #self.lineEdit().setStyleSheet(self.styleSheet() + "background-color: rgba(174, 149, 255, 255)")
        super().focusOutEvent(event)

    def focusInEvent(self, e):
        if self.lineEdit():
            self.lineEdit().clear()
            self.lineEdit().setAlignment(QtGui.Qt.AlignLeft)
            self.lineEdit().setStyleSheet(self.styleSheet())
        return super().focusInEvent(e)

class AutoLineEdit(QLineEdit):
    def focusOutEvent(self, event):
        self.editingFinished.emit()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self.returnPressed.emit()
        super().keyPressEvent(event)
        
class VideoRangeSlider(QtWidgets.QAbstractSlider):

    in_out_valueChanged = QtCore.Signal(int)
    slider_active = QtCore.Signal(bool)
    sliderStateChanged = QtCore.Signal(object, object, object) #in_point, playhead_frame, out_point -to send to the cache machine

    def __init__(self, orientation=QtCore.Qt.Horizontal, parent=None):
        super().__init__(parent)
        self.setOrientation(orientation)
        self.setMouseTracking(True)
        self.setAttribute(QtCore.Qt.WA_Hover, True)

        self.variables = {
            "_frStart": 0,
            "_inPoint": 0,
            "_frame": 0,
            "_outPoint": 100,
            "_frEnd": 100
            }

        self.setMinimum(self.variables.get("_frStart"))
        self.setMaximum(self.variables.get("_frEnd"))
        self.setMinimumSize(300, 38)  # Ensure it's large enough to be visible
        self.setFixedHeight(38)

        # track
        self.hover = None #the phantom
        self.hovered = None #the handle
        self.active_handle = None
        self.last_position = 0 #to avoid tablet cursor updating too much

        # debounce timer
        self.debounce_timer = QtCore.QTimer(self)
        self.debounce_timer.setSingleShot(True)  # Only fire once after inactivity
        self.debounce_timer.timeout.connect(self.emit_values)
        self.debounce_timer.timeout.connect(self.emit_sliderStateChanged)
    


# Paint        

    def paintEvent(self, event):
        
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0))

        # draw groove 
        groove = QtCore.QRect(13, self.height() // 2 + 3, self.width() - 26, 6)
        painter.setBrush(QtGui.QColor(67, 67, 67)) 
        painter.setPen(QtGui.Qt.NoPen)
        painter.drawRect(groove)


        # draw range highlight
        left = self.value_to_pixel(self.variables.get("_inPoint"))
        width = self.value_to_pixel(self.variables.get("_outPoint")) - left
        range_highlight = QtCore.QRect(left, self.height() // 2 + 2, width , 8)
        painter.setBrush(QtGui.QColor(128, 128, 128)) 
        painter.drawRect(range_highlight)

        # draw cache
        self.draw_cache(painter)

        # draw slider handles
        self.draw_handle(painter, self.variables.get("_inPoint"), 1, 0)
        self.draw_handle(painter, self.variables.get("_frame"), 1.5, 0)
        self.draw_handle(painter, self.variables.get("_outPoint"), 1, 0)

        # draw phantom
        if self.hover:
            self.draw_handle(painter, self.pixel_to_value(int(self.hover)), 1.4, 1)
            self.draw_frame_number(painter, self.pixel_to_value(int(self.hover)), .5)
        
        # draw frame number
        self.draw_frame_number(painter, self.variables.get("_frame"), 1)

        #draw timeline marker
        self.draw_timelineMarker(painter)

        painter.end()

    def draw_frame_number(self, painter, value, brt):
                
        x_pos = self.value_to_pixel(value)
        r= QtCore.QRectF(x_pos - 30 , self.height() // 2 - 19, 60, 22)
        text = str(value)
        text_option = QtGui.QTextOption(QtCore.Qt.AlignHCenter)
        font = QtGui.QFont("Helvetica", 12)

        # Draw background rectangle
        metrics = QtGui.QFontMetrics(font)
        text_rect = metrics.boundingRect(text)
        text_rect.moveCenter(QtCore.QPoint(x_pos, (self.height() // 2 - 12)))
        painter.setBrush(QtGui.QColor(0, 0, 0))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(text_rect)

        if value in self.parent().parent().parent().timeline_markers:
            base_color = QtGui.QColor(169, 169, 255)
            brt = 1
        else:
            base_color = QtGui.QColor(169, 169, 169)
        colour = QtGui.QColor(
            int(base_color.red() * brt),
            int(base_color.green() * brt),
            int(base_color.blue() * brt)
        )
        pen = QtGui.QPen(colour, 1, QtGui.Qt.SolidLine, QtGui.Qt.RoundCap, QtGui.Qt.RoundJoin)
        painter.setFont(font)
        painter.setPen(pen)
        painter.drawText(r, text, text_option)

    def draw_handle(self, painter, value, brt, one):
        x_pos = self.value_to_pixel(value)
        handleR = QtCore.QRect(x_pos - 1 , self.height() // 2 + 1, 2 - one, 10)
        painter.setPen(QtGui.Qt.NoPen)
        if value in self.parent().parent().parent().timeline_markers:
           base_color = QtGui.QColor(140, 140, 255)
           brt = 1
        else:
           base_color = QtGui.QColor(140, 140, 140)
        colour = QtGui.QColor(
            int(base_color.red() * brt),
            int(base_color.green() * brt),
            int(base_color.blue() * brt)
        )
        painter.setBrush(QtGui.QColor(colour))
        painter.drawRect(handleR)

        if self.hovered == "_inPoint":
            if self.variables.get(self.hovered) == value:
                handle_highlight = QtCore.QRect(x_pos -  3, self.height() // 2 + 0, 5 , 12)
                painter.setBrush(QtGui.QColor(169, 169, 169, 255))
                painter.drawRect(handle_highlight)
                triangle = [
                    QtCore.QPoint(x_pos -  3, self.height() // 2 + 11),
                    QtCore.QPoint(x_pos -  3, self.height() // 2 + 1),
                    QtCore.QPoint(x_pos -  13, self.height() // 2 + 6)
                    ]
                painter.drawConvexPolygon(triangle)

        elif self.hovered == "_outPoint":
            if self.variables.get(self.hovered) == value:
                handle_highlight = QtCore.QRect(x_pos -  2, self.height() // 2 + 0, 5 , 12)
                painter.setBrush(QtGui.QColor(169, 169, 169, 255))
                painter.drawRect(handle_highlight)
                triangle = [
                    QtCore.QPoint(x_pos +  3, self.height() // 2 + 11),
                    QtCore.QPoint(x_pos +  3, self.height() // 2 + 1),
                    QtCore.QPoint(x_pos +  13, self.height() // 2 + 6)
                    ]
                painter.drawConvexPolygon(triangle)

    def draw_timelineMarker(self, painter):
        for marker in self.parent().parent().parent().timeline_markers:
            x_pos = self.value_to_pixel(marker)
            markerTick = QtCore.QRect(x_pos, self.height() // 2 + 2, 1, 8)
            dot = QtCore.QRect(x_pos - 1 , self.height() // 2 + 9, 3, 3)
            painter.setPen(QtGui.QPen((QtGui.QColor(200, 200, 255, 255)), .5, QtGui.Qt.SolidLine, QtGui.Qt.SquareCap, QtGui.Qt.MiterJoin))
            painter.setBrush(QtGui.QBrush((QtGui.QColor(255, 255, 255, 255))))

            painter.drawRect(markerTick)
            painter.drawEllipse(dot)


    def draw_cache(self, painter):
        for key in self.parent().parent().parent().frame_cache:
            if key != self.maximum():
                painter.setBrush(QtGui.QColor(50, 200, 50))
                x_pos = self.value_to_pixel(key)
                next = self.value_to_pixel(key + 1)
                rect = QtCore.QRect(x_pos, self.height() // 2 + 3, next- x_pos, 6)
                painter.drawRect(rect)


# Events

    def process_pointer_event(self, event):
        mouse_x = event.pos().x()
        mouse_y = event.pos().y()

        if (12 < mouse_x < self.width() - 12) and (4 < mouse_y < self.height() - 4):
            self.hover = str(mouse_x)
        else:
            self.hover = None

        closest_handle = self.get_closest_handle(mouse_x)
        if abs(self.value_to_pixel(self.variables.get(closest_handle)) - mouse_x) < 10 and abs((self.height() // 2 + 3) - mouse_y) < 12:
            self.hovered = closest_handle
        else:
            self.hovered = None

        if self.active_handle:
            self.hovered = self.active_handle
            self.update_handle(self.pixel_to_value(mouse_x))

        self.update()

    def process_pointer_press(self, event):
        mouse_x = event.pos().x()
        if self.hovered:
            self.active_handle = self.hovered
        else:
            self.active_handle = "_frame"

        self.update_handle(self.pixel_to_value(mouse_x))
        self.slider_active.emit(True)

    def process_pointer_release(self, event):
        self.active_handle = None
        self.slider_active.emit(False)
        
    def mousePressEvent(self, event):
        self.process_pointer_press(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        self.process_pointer_release(event)
        event.accept()

    def mouseMoveEvent (self, event):
        self.process_pointer_event(event)
        event.accept()

    def tabletEvent(self, event: QtGui.QTabletEvent):
        event_type = event.type()

        if event_type == QtCore.QEvent.TabletMove:
            self.process_pointer_event(event)
            event.accept()

        elif event_type == QtCore.QEvent.TabletPress:
            self.process_pointer_press(event)
            event.accept()

        elif event_type == QtCore.QEvent.TabletRelease:
            self.process_pointer_release(event)
            event.accept()

        else:
            super().tabletEvent(event)


# Functions

    def get_closest_handle(self, mouse_x):
        return min(
            ["_inPoint", "_outPoint", "_frame"],
            key=lambda key: abs(self.value_to_pixel(self.variables[key]) - mouse_x)
        )

    def update_handle(self, value):
        self.variables[self.active_handle] = self.clamp_values(value)
        self.variables["_frame"] = self.variables.get(self.active_handle)

        delta_x = abs(value - self.last_position)

        if delta_x >= 1:
            self.last_position = value
            self.debounce_timer.start(.1)
        self.repaint()

    def emit_values(self):
        self.in_out_valueChanged.emit(self.variables.get("_outPoint") - self.variables.get("_inPoint"))
        self.valueChanged.emit(self.variables["_frame"])
 
    def emit_sliderStateChanged(self):
        self.sliderStateChanged.emit(
            self.variables.get("_inPoint"),
            self.variables.get("_frame"),
            self.variables.get("_outPoint")
        )
        
    def setValue(self, value):
        self.variables["_frame"] = value
        self.valueChanged.emit(self.variables["_frame"])
        self.emit_sliderStateChanged()
        self.update()
            
    def clamp_values(self, value):
        if self.active_handle == "_inPoint":
            return max(self.minimum(), min(value, (self.variables.get("_outPoint")) - 1))
        elif self.active_handle == "_frame":
            return max(self.minimum(), min(value, self.maximum()))
        elif self.active_handle == "_outPoint":
            return max(self.variables.get("_inPoint") + 1, min(value, self.maximum()))    

    def value_to_pixel(self, value):
        return int((self.width() -26) * (value - self.minimum())  / (self.maximum() - self.minimum()) + 13)

    def pixel_to_value(self, pixel):
        return int(round(self.minimum() + (pixel - 13) * (self.maximum() - self.minimum()) / (self.width() - 26), 0))

    #def relative_value_to_pixel(self, value):

class FilledWidget(QtWidgets.QWidget):
    def __init__(self, height, col, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)  # Ensure the background is painted
        self.setMaximumHeight(height)
        self.colour = col

        # Create a layout inside this widget
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)  # Apply the layout

    def paintEvent(self, event):
        """Custom painting method to fill background color."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        bg_rect = self.rect()  # Get full widget area
        painter.setBrush(QtGui.QBrush(QtGui.QColor(self.colour)))  # Set red background
        painter.setPen(QtCore.Qt.NoPen)  # Remove border
        painter.drawRect(bg_rect)  # Draw background

        painter.end()

class FilledVWidget(QtWidgets.QWidget):
    def __init__(self, col, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)  # Ensure the background is painted
        self.colour = col

        # Create a layout inside this widget
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)  # Apply the layout

    def paintEvent(self, event):
        """Custom painting method to fill background color."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        bg_rect = self.rect()  # Get full widget area
        painter.setBrush(QtGui.QBrush(QtGui.QColor(self.colour)))  # Set red background
        painter.setPen(QtCore.Qt.NoPen)  # Remove border
        painter.drawRect(bg_rect)  # Draw background

        painter.end()

class FilledWidgetGradient(QtWidgets.QWidget):
    def __init__(self, height, parent=None):
        super().__init__(parent)
        #self.setAutoFillBackground(True)  # Ensure the background is painted
        self.setMaximumHeight(height)

        # Create a layout inside this widget
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)  # Apply the layout

    def paintEvent(self, event):
        super().paintEvent(event)
        """Custom painting method to fill background color."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        bg_rect = self.rect()  # Get full widget area
        linearGrad = QtGui.QLinearGradient(QtCore.QPointF(0, 0), QtCore.QPointF(0, 38))
        linearGrad.setColorAt(0, QtGui.QColor(58, 58, 58))
        linearGrad.setColorAt(.25, QtGui.QColor(55, 55, 55))
        linearGrad.setColorAt(.45, QtGui.QColor(50, 50, 50))
        linearGrad.setColorAt(.75, QtGui.QColor(30, 30, 30))
        linearGrad.setColorAt(1, QtCore.Qt.black)
        brush = QtGui.QBrush(linearGrad)
        #brush.setStyle(QtGui.Qt.LinearGradientPattern)
        painter.setBrush(brush)
        pen = QtGui.QPen(QtCore.Qt.SolidLine)
        pen.setColor(QtGui.QColor(58, 58, 58))
        pen.setJoinStyle(QtGui.Qt.RoundJoin)
        painter.setPen(pen)  
        #painter.drawRect(bg_rect)
        painter.drawRoundedRect(bg_rect, 4, 4)  # Draw background

        painter.end()

class IconButton(QtWidgets.QPushButton):
    def __init__(self, icon_type="Play_forwards", parent=None):
        super().__init__(parent)  # Correct superclass initialization
        self.icon_type = icon_type  # Store the icon type

    def draw_cog(self, painter, center, teeth, radius):
        path = QtGui.QPainterPath()

        outer = radius
        notch = radius * 0.22  # depth of tooth cut
        inner = outer - notch

        tooth_angle = 2 * math.pi / teeth
        gap = tooth_angle * .3

        for i in range(teeth):
            a0 = i * tooth_angle
            a1 = a0 + gap
            a2 = a0 + tooth_angle

            p1 = QtCore.QPointF(
                center.x() + outer * math.cos(a1),
                center.y() + outer * math.sin(a1)
            )
            p2 = QtCore.QPointF(
                center.x() + inner * math.cos(a1),
                center.y() + inner * math.sin(a1)
            )
            p3 = QtCore.QPointF(
                center.x() + inner * math.cos(a2),
                center.y() + inner * math.sin(a2)
            )
            p4 = QtCore.QPointF(
                center.x() + outer * math.cos(a2),
                center.y() + outer * math.sin(a2)
            )

            if i == 0:
                path.moveTo(p1)
            else:
                path.lineTo(p1)

            path.lineTo(p2)
            path.lineTo(p3)
            path.lineTo(p4)

        path.closeSubpath()
        painter.drawPath(path)



    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(150, 150, 150, 255))

        if self.icon_type == "Play_forwards":
            if self.parent().parent() and not self.parent().parent().is_playing:
                points = [
                    QtCore.QPoint(self.width() // 2 - 4, self.height() // 2 + 6),  
                    QtCore.QPoint(self.width() // 2 - 4, self.height() // 2 - 6),  
                    QtCore.QPoint(self.width() // 2 + 7, self.height() // 2)
                ]
                triangle = QtGui.QPolygon(points)
                painter.drawConvexPolygon(triangle)
            
            elif self.parent().parent() and self.parent().parent().is_playing:
                rect_01 = QtCore.QRect(self.width() // 2 - 5, self.height() // 2 - 6, 4, 12)
                rect_02 = QtCore.QRect(self.width() // 2 + 1, self.height() // 2 - 6, 4, 12)
                painter.drawRoundedRect(rect_01, 1, 1)
                painter.drawRoundedRect(rect_02, 1, 1)

        if self.icon_type == "Step_one_frame_backwards":
            points = [
                QtCore.QPoint(self.width() // 2 + 3, self.height() // 2 + 6),  
                QtCore.QPoint(self.width() // 2 + 3, self.height() // 2 - 6),  
                QtCore.QPoint(self.width() // 2 - 5, self.height() // 2)
            ]

            triangle = QtGui.QPolygon(points)
            rectangle = QtCore.QRect(self.width() // 2 + 5, self.height() // 2 - 5, 1.5, 10)
            painter.drawConvexPolygon(triangle)
            painter.drawRect(rectangle)

        if self.icon_type == "Step_one_frame_forwards":
            points = [
                QtCore.QPoint(self.width() // 2 - 4, self.height() // 2 + 6),  
                QtCore.QPoint(self.width() // 2 - 4, self.height() // 2 - 6),  
                QtCore.QPoint(self.width() // 2 + 4, self.height() // 2)
            ]

            triangle = QtGui.QPolygon(points)
            rectangle = QtCore.QRect(self.width() // 2 - 7, self.height() // 2 - 5, 1.5, 10)
            painter.drawConvexPolygon(triangle)
            painter.drawRect(rectangle)

        if self.icon_type == "Set_range_start":
            points = [
                QtCore.QPoint(self.width() // 2 + 6, self.height() // 2 + 6),  
                QtCore.QPoint(self.width() // 2 + 6, self.height() // 2 - 6),  
                QtCore.QPoint(self.width() // 2 - 2, self.height() // 2)
            ]

            triangle = QtGui.QPolygon(points)
            rectangle = QtCore.QRect(self.width() // 2 - 5, self.height() // 2 - 5, 1.5, 10)
            painter.drawConvexPolygon(triangle)
            painter.drawRect(rectangle)

        if self.icon_type == "Set_range_end":
            points = [
                QtCore.QPoint(self.width() // 2 - 6, self.height() // 2 + 6),  
                QtCore.QPoint(self.width() // 2 - 6, self.height() // 2 - 6),  
                QtCore.QPoint(self.width() // 2 + 2, self.height() // 2)
            ]

            triangle = QtGui.QPolygon(points)
            rectangle = QtCore.QRect(self.width() // 2 + 4, self.height() // 2 - 5, 1.5, 10)
            painter.drawConvexPolygon(triangle)
            painter.drawRect(rectangle)

        if self.icon_type == "Flip":
            points_01 = [
                QtCore.QPoint(self.width() // 2 + 6, self.height() // 2 - 2),  
                QtCore.QPoint(self.width() // 2 - 6, self.height() // 2 - 2),  
                QtCore.QPoint(self.width() // 2 , self.height() // 2 - 6)
            ]
            points_02 = [
                QtCore.QPoint(self.width() // 2 + 6, self.height() // 2 + 3),  
                QtCore.QPoint(self.width() // 2 - 6, self.height() // 2 + 3),  
                QtCore.QPoint(self.width() // 2, self.height() // 2 + 7)
            ]
            triangle_01 = QtGui.QPolygon(points_01)
            triangle_02 = QtGui.QPolygon(points_02)
            painter.setBrush(QtGui.QColor(140, 140, 140, 255))
            painter.drawConvexPolygon(triangle_01)
            painter.drawConvexPolygon(triangle_02)
            rectangle = QtCore.QRect(self.width() // 2 - 7, self.height() // 2 , 14, 1)
            painter.drawRoundedRect(rectangle, 1, 1)

        if self.icon_type == "Flop":
            points_01 = [
                QtCore.QPoint(self.width() // 2 + 3, self.height() // 2 + 7),
                QtCore.QPoint(self.width() // 2 + 3, self.height() // 2 - 6),  
                QtCore.QPoint(self.width() // 2 + 7, self.height() // 2)
            ]
            points_02 = [
                QtCore.QPoint(self.width() // 2 - 2, self.height() // 2 + 7),  
                QtCore.QPoint(self.width() // 2 - 2, self.height() // 2 - 6),  
                QtCore.QPoint(self.width() // 2 - 6, self.height() // 2)
            ]
            triangle_01 = QtGui.QPolygon(points_01)
            triangle_02 = QtGui.QPolygon(points_02)
            painter.drawConvexPolygon(triangle_01)
            painter.drawConvexPolygon(triangle_02)
            rectangle = QtCore.QRect(self.width() // 2 , self.height() // 2 - 7, 1, 15)
            painter.drawRoundedRect(rectangle,1 ,1)

        if self.icon_type == "Crop":
            dashdot_pen = QtGui.QPen((QtGui.QColor(140, 140, 140, 255)), 2, QtGui.Qt.DashDotLine, QtGui.Qt.SquareCap, QtGui.Qt.MiterJoin)
            painter.setPen(dashdot_pen)
            painter.setBrush(QtGui.QColor(150, 150, 150, 0))
            frame = QtCore.QRect(self.width() // 2 - (12 * 0.5), self.height() // 2 - (12 * 0.5), 12, 12)
            painter.drawRect(frame)

        if self.icon_type == "Timer":
            pen = QtGui.QPen((QtGui.QColor(140, 140, 140, 255)), 2, QtGui.Qt.SolidLine, QtGui.Qt.RoundCap, QtGui.Qt.RoundJoin)
            painter.setPen(pen)
            rectangle = QtCore.QRect(self.width() // 2 - 4, self.height() // 2 - 6, 12, 14)
            startAngle = -100 * 16
            spanAngle = 240 * 16
            painter.drawArc(rectangle, startAngle, spanAngle)

            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QColor(140, 140, 140, 255))
            rect_01 = QtCore.QRect(self.width() // 2 - 10, self.height() // 2 - 1, 8, 2)
            rect_02 = QtCore.QRect(self.width() // 2 - 8, self.height() // 2 + 3, 6, 2)
            rect_03 = QtCore.QRect(self.width() // 2 - 4, self.height() // 2 + 7, 6, 2)
            painter.drawRoundedRect(rect_01, 1, 1)
            painter.drawRoundedRect(rect_02, 1, 1)
            painter.drawRoundedRect(rect_03, 1, 1)
            rect_04 = QtCore.QRect(self.width() // 2 + 2, self.height() // 2 - 3, 1, 4)
            painter.drawRect(rect_04)
            rect_05 = QtCore.QRect(self.width() // 2, self.height() // 2 - 9, 4, 2)
            painter.drawRoundedRect(rect_05, 1, 1)

        if self.icon_type == "Reset":
            pen = QtGui.QPen((QtGui.QColor(140, 140, 140, 255)), 2, QtGui.Qt.SolidLine, QtGui.Qt.RoundCap, QtGui.Qt.RoundJoin)
            brush = QtGui.QBrush((QtGui.QColor(140, 140, 140, 255)))
            painter.setPen(pen)
            painter.setBrush(brush)
            rectangle = QtCore.QRect(self.width() // 2 - 6, self.height() // 2 - 7, 13, 13)
            startAngle = -100 * 16
            spanAngle = 260 * 16
            painter.drawArc(rectangle, startAngle, spanAngle)

            points = [
                    QtCore.QPoint(self.width() // 2 - 8, self.height() // 2 - 1),  
                    QtCore.QPoint(self.width() // 2 - 2, self.height() // 2 - 1),  
                    QtCore.QPoint(self.width() // 2 - 5, self.height() // 2 + 2)
                ]
            triangle = QtGui.QPolygon(points)
            painter.drawConvexPolygon(triangle)

        if self.icon_type == "Info":
            pen = QtGui.QPen((QtGui.QColor(140, 140, 140, 255)), 1.5, QtGui.Qt.SolidLine, QtGui.Qt.SquareCap, QtGui.Qt.RoundJoin)
            brush = QtGui.QBrush((QtGui.QColor(140, 140, 140, 255)))
            painter.setPen(pen)
            painter.setBrush(brush)

            self.draw_cog(painter, center=(QtCore.QPoint(self.width()//2, self.height()//2 )), teeth=7, radius=8)

            painter.setBrush(QtGui.QBrush((QtGui.QColor(35, 35, 35, 255))))
            painter.setPen(QtGui.QPen((QtGui.QColor(140, 140, 140, 255)), 1.5, QtGui.Qt.SolidLine, QtGui.Qt.SquareCap, QtGui.Qt.RoundJoin))
            painter.drawEllipse(QtCore.QPointF(QtCore.QPoint(self.width()//2, self.height()//2 )), 6, 6)

        if self.icon_type == "Copy":
            rectangle2 = QtCore.QRect(self.width() // 2 - 2, self.height() // 2 - 7, 8, 10)
            painter.setPen(QtGui.QPen((QtGui.QColor(150, 150, 150, 255)), 2, QtGui.Qt.SolidLine, QtGui.Qt.RoundCap, QtGui.Qt.RoundJoin))
            painter.setBrush(QtGui.QBrush((QtGui.QColor(150, 150, 150, 0))))
            painter.drawRect(rectangle2)

            rectangle = QtCore.QRect(self.width() // 2 - 6, self.height() // 2 - 3, 8, 10)
            painter.setPen(QtGui.QPen((QtGui.QColor(150, 150, 150, 255)), 2, QtGui.Qt.SolidLine, QtGui.Qt.RoundCap, QtGui.Qt.RoundJoin))
            painter.setBrush(QtGui.QBrush((QtGui.QColor(150, 150, 150, 255))))
            painter.drawRect(rectangle)

        if self.icon_type == "Edit":
            pen = QtGui.QPen((QtGui.QColor(150, 150, 150, 255)), 2, QtGui.Qt.SolidLine, QtGui.Qt.RoundCap, QtGui.Qt.RoundJoin)
            brush = QtGui.QBrush((QtGui.QColor(150, 150, 150, 255)))
            painter.setPen(pen)
            painter.setBrush(brush)

            body = QtCore.QRectF(9, 11, 8, 4) 
            eraser = QtCore.QRectF(20, 11, 1, 4) 
            eraser_tip = QtCore.QRectF(21, 11, 1, 4) 
            tip = QtGui.QPolygonF([
                QtCore.QPointF(4, 13),  
                QtCore.QPointF(8, 11),  
                QtCore.QPointF(8, 15)  
            ])
            tip_tip = QtGui.QPolygonF([
                QtCore.QPointF(4, 13),  
                QtCore.QPointF(6, 12),  
                QtCore.QPointF(6, 14)  
            ])

            painter.save()
            painter.rotate(-45)
            painter.translate(-12, 6.5)
            painter.drawRect(body)
            painter.drawRect(eraser)
            painter.drawRoundedRect(eraser_tip, 1, 1)
            painter.drawPolygon(tip)
            painter.setPen(QtGui.QPen((QtGui.QColor(130, 130, 130, 255)), 2, QtGui.Qt.SolidLine, QtGui.Qt.RoundCap, QtGui.Qt.MiterJoin))
            painter.drawPolygon(tip_tip)
            painter.restore()

        if self.icon_type == "mini_reset":
            points = [
                QtCore.QPoint(self.width() // 2 - 1, self.height() // 2 + 4),  
                QtCore.QPoint(self.width() // 2 - 1, self.height() // 2 - 4),  
                QtCore.QPoint(self.width() // 2 - 8, self.height() // 2)
            ]

            triangle = QtGui.QPolygon(points)
            rectangle = QtCore.QRect(self.width() // 2 - 1, self.height() // 2 - 1 , 8, 2)
            painter.setPen(QtGui.QPen((QtGui.QColor(160, 160, 160, 255)), 1, QtGui.Qt.SolidLine, QtGui.Qt.RoundCap, QtGui.Qt.RoundJoin))
            painter.drawConvexPolygon(triangle)
            painter.drawRect(rectangle)

        if self.icon_type == "mini_reset2":
            
            arcRectangle = QtCore.QRect(self.width() // 2 - 1 , self.height() // 2 - 2 , 7, 7)
            painter.setPen(QtGui.QPen((QtGui.QColor(160, 160, 160, 255)), 2, QtGui.Qt.SolidLine, QtGui.Qt.RoundCap, QtGui.Qt.RoundJoin))
            painter.drawArc(arcRectangle, 270*16, 180*16)

            painter.drawLine(7, 6, 14, 6)
            painter.drawLine(10, 9, 7, 6)
            painter.drawLine(10, 3, 7, 6)

        if self.icon_type == "Volume":

            #Low Volume
            if not self.isChecked():
                if 0 < self.parent().parent().volume_slider.value() <= 33 or 66 < self.parent().parent().volume_slider.value():

                    painter.setPen(QtGui.QPen((QtGui.QColor(49, 49, 49, 255)), 5, QtGui.Qt.SolidLine, QtGui.Qt.FlatCap, QtGui.Qt.BevelJoin))
                    arcRectangle = QtCore.QRect(self.width() // 2 + 4 , self.height() // 2 - 1 , 1, 2)
                    painter.drawArc(arcRectangle, -90*16, 180*16)

                    painter.setPen(QtGui.QPen((QtGui.QColor(130, 130, 130, 255)), 1.5, QtGui.Qt.SolidLine, QtGui.Qt.SquareCap, QtGui.Qt.RoundJoin))
                    painter.drawArc(arcRectangle, -90*16, 180*16)
            

            #Cone
            painter.setPen(QtGui.QPen((QtGui.QColor(150, 150, 150, 255)), 1.5, QtGui.Qt.SolidLine, QtGui.Qt.SquareCap, QtGui.Qt.RoundJoin))

            painter.drawLine(18, self.height() // 2 + 7, 18, self.height() // 2 - 7)
            painter.drawLine(18, self.height() // 2 + 7, 10, self.height() // 2 + 3)
            painter.drawLine(18, self.height() // 2 - 7, 10, self.height() // 2 - 3)

            painter.setPen(QtGui.QPen((QtGui.QColor(150, 150, 150, 255)), 1.5, QtGui.Qt.SolidLine, QtGui.Qt.SquareCap, QtGui.Qt.RoundJoin))
            arcRectangle = QtCore.QRect(self.width() // 2 - 8, self.height() // 2 - 3 , 8, 6)
            painter.drawArc(arcRectangle, 130*16, 100*16)

            #Mute
            
            if self.isChecked() or self.parent().parent().volume_slider.value() == 0:          
                painter.setPen(QtGui.QPen((QtGui.QColor(49, 49, 49, 255)), 5, QtGui.Qt.SolidLine, QtGui.Qt.FlatCap, QtGui.Qt.BevelJoin))
                painter.drawLine(22, self.height() // 2 + 4, 16, self.height()//2 - 4)
                painter.drawLine(22, self.height() // 2 - 4, 16, self.height()//2 + 4)

                painter.setPen(QtGui.QPen((QtGui.QColor(150, 150, 150, 255)), 1.5, QtGui.Qt.SolidLine, QtGui.Qt.SquareCap, QtGui.Qt.RoundJoin))
                painter.drawLine(22, self.height() // 2 + 3, 17, self.height()//2 - 3)
                painter.drawLine(22, self.height() // 2 - 3, 17, self.height()//2 + 3)
            

            #Medium Volume
            if not self.isChecked():
                if 33< self.parent().parent().volume_slider.value() <= 66:
                    painter.setPen(QtGui.QPen((QtGui.QColor(130, 130, 130, 255)), 1.5, QtGui.Qt.SolidLine, QtGui.Qt.RoundCap, QtGui.Qt.RoundJoin))
                    arcRectangle = QtCore.QRect(self.width() // 2 + 4 , self.height() // 2 - 3 , 3, 6)
                    painter.drawArc(arcRectangle, -90*16, 180*16)
            

            #High Volume
            if not self.isChecked():
                if 66 < self.parent().parent().volume_slider.value():
                    painter.setPen(QtGui.QPen((QtGui.QColor(150, 150, 150, 255)), 1.5, QtGui.Qt.SolidLine, QtGui.Qt.RoundCap, QtGui.Qt.RoundJoin))
                    arcRectangle = QtCore.QRect(self.width() // 2  , self.height() // 2 - 5 , 8, 10)
                    painter.drawArc(arcRectangle, -75*16, 150*16)



            

            

        painter.end()

class CropLabel(QtWidgets.QLabel):
    #signals
    sig_forwards = QtCore.Signal(int) 
    sig_backwards = QtCore.Signal(int) 
    slider_active = QtCore.Signal(bool)  

    def __init__(self, parent=None):
        super().__init__(parent) 
        self.setMinimumSize(450, 300)
        self.setMouseTracking(False)
        

        self.image_x = 800
        self.image_y = 500

        self.crop_points = {
            "topLeft": QtCore.QPoint(100, 100),
            "bottomRight": QtCore.QPoint(700, 400),
            "topRight": QtCore.QPoint(700, 100),
            "bottomLeft": QtCore.QPoint(100, 400),            
        }

        #track
        self.hover = None
        self.active = None
        self.last_mousex_position = 0

        #debounce timer
        self.debounce_timer = QtCore.QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(.01)  # 100ms
        self.debounce_ready = True  # Flag to track timer state
        self.debounce_timer.timeout.connect(self._reset_debounce)

        
        

    def set_crop_to_image(self, imageX, imageY):
        self.image_x = imageX
        self.image_y = imageY
        pt1 = QtCore.QPoint(0 + 0.1*imageX, 0 + 0.1*imageY)
        pt2 = QtCore.QPoint(imageX - 0.1*imageX, imageY - 0.1*imageY)
        self.make_point_dict(pt1, pt2)

 
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        if self.parent().crop:
            self.setMouseTracking(True)

            painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
            painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 30, 155)))

            frame = QtCore.QRectF(0, 0, self.width(), self.height())
            crop = QtCore.QRect(self.value_to_pixel(self.crop_points.get("topLeft")), self.value_to_pixel(self.crop_points.get("bottomRight")))
            
            painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 155)))
            path = QtGui.QPainterPath()
            path.addRect(frame)
            path.addRect(crop)
            painter.drawPath(path)


            solid_pen = QtGui.QPen((QtGui.QColor(255, 255, 255, 255)), 2, QtGui.Qt.SolidLine, QtGui.Qt.SquareCap, QtGui.Qt.MiterJoin)
            dashdot_pen = QtGui.QPen((QtGui.QColor(255, 255, 255, 255)), 2, QtGui.Qt.DashDotLine, QtGui.Qt.SquareCap, QtGui.Qt.MiterJoin)
            corner_hover_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 255), 3, QtGui.Qt.SolidLine)
            dashdot_hover_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 150), 3, QtGui.Qt.SolidLine)

            painter.setBrush(QtGui.QBrush(QtGui.QColor(250, 255, 234, 0)))

            corner_length = 15 
            clearance = 20

            topLeft = crop.topLeft()
            topRight = crop.topRight()
            bottomLeft = crop.bottomLeft()
            bottomRight = crop.bottomRight()

            painter.setPen(dashdot_hover_pen)
            if self.hover == "top":
                painter.drawLine(topLeft + QtCore.QPoint(clearance, 0), topRight - QtCore.QPoint(clearance, 0))
            if self.hover == "bottom":
                painter.drawLine(bottomLeft + QtCore.QPoint(clearance, 0), bottomRight - QtCore.QPoint(clearance, 0))
            if self.hover == "left":
                painter.drawLine(topLeft + QtCore.QPoint(0, clearance), bottomLeft - QtCore.QPoint(0, clearance))
            if self.hover == "right":
                painter.drawLine(topRight + QtCore.QPoint(0, clearance), bottomRight - QtCore.QPoint(0, clearance))

            painter.setPen(dashdot_pen)
            painter.drawLine(topLeft, topRight)     # Top side
            painter.drawLine(bottomLeft, bottomRight)  # Bottom side
            painter.drawLine(topLeft, bottomLeft)   # Left side
            painter.drawLine(topRight, bottomRight)  # Right side

            def draw_corner(corner_name):
                
                if self.hover == corner_name:
                    painter.setPen(corner_hover_pen)
                else:
                    painter.setPen(solid_pen)
                
                if corner_name == "topLeft":
                    # Top-left corner
                    painter.drawLine(topLeft, topLeft + QtCore.QPoint(corner_length, 0))  # Horizontal
                    painter.drawLine(topLeft, topLeft + QtCore.QPoint(0, corner_length))  # Vertical
                elif corner_name == "topRight":
                    # Top-right corner
                    painter.drawLine(topRight, topRight - QtCore.QPoint(corner_length, 0))  # Horizontal
                    painter.drawLine(topRight, topRight + QtCore.QPoint(0, corner_length))  # Vertical
                elif corner_name == "bottomLeft":
                    # Bottom-left corner
                    painter.drawLine(bottomLeft, bottomLeft + QtCore.QPoint(corner_length, 0))  # Horizontal
                    painter.drawLine(bottomLeft, bottomLeft - QtCore.QPoint(0, corner_length))  # Vertical
                elif corner_name == "bottomRight":
                    # Bottom-right corner
                    painter.drawLine(bottomRight, bottomRight - QtCore.QPoint(corner_length, 0))  # Horizontal
                    painter.drawLine(bottomRight, bottomRight - QtCore.QPoint(0, corner_length))  # Vertical

            draw_corner("topLeft")
            draw_corner("topRight")
            draw_corner("bottomLeft")
            draw_corner("bottomRight")

        painter.end()
            
    def crop_flip(self):
        p1 = QtCore.QPoint(self.crop_points["bottomLeft"].x(), self.image_y - self.crop_points["bottomLeft"].y())
        p2 = QtCore.QPoint(self.crop_points["topRight"].x(), self.image_y - self.crop_points["topRight"].y())
        self.make_point_dict(p1, p2)

    def crop_flop(self):
        p1 = QtCore.QPoint(self.image_x - self.crop_points["topRight"].x(),  self.crop_points["topRight"].y())
        p2 = QtCore.QPoint(self.image_x - self.crop_points["bottomLeft"].x(),  self.crop_points["bottomLeft"].y())
        self.make_point_dict(p1, p2)

    def offset(self):
        frame = QtCore.QRect(self.width() // 2 - (self.load_scale().x() * 0.5), self.height() // 2 - (self.load_scale().y() * 0.5), self.load_scale().x(), self.load_scale().y())
        return QtCore.QPoint(frame.topLeft())

    def load_scale(self):
        scale_factor = min(self.width() / self.image_x, self.height() / self.image_y)
        w = self.image_x * scale_factor
        h = self.image_y * scale_factor
        return QtCore.QPointF(w, h)  #This is not a point, this is the scaled rectangle width x height, qpoint provides a nice way to access the values
    
    def value_to_pixel(self, point):
        pix_x = int(point.x() * (self.load_scale().x() / self.image_x)) + self.offset().x()
        pix_y = int(point.y()* (self.load_scale().y() / self.image_y)) + self.offset().y()
        return QtCore.QPoint(pix_x, pix_y)
    
    def pixel_to_value(self, pixel):
        val_x = int((pixel.x() - self.offset().x()) * self.image_x / self.load_scale().x())
        val_y = int((pixel.y() - self.offset().y()) * self.image_y / self.load_scale().y())
        return QtCore.QPoint(val_x, val_y)

    def make_point_dict(self, p1, p2):
        # Determine top-left and bottom-right based on min/max x and y
        topLeft = QtCore.QPoint(min(p1.x(), p2.x()), min(p1.y(), p2.y()))
        bottomRight = QtCore.QPoint(max(p1.x(), p2.x()), max(p1.y(), p2.y()))

        # Compute remaining points
        self.crop_points = {
            "topLeft": topLeft,
            "topRight": QtCore.QPoint(bottomRight.x(), topLeft.y()),
            "bottomLeft": QtCore.QPoint(topLeft.x(), bottomRight.y()),
            "bottomRight": bottomRight
        }
        self.update()         

    def opposite(self, point):
        if point == "topLeft": return "bottomRight"
        elif point == "topRight": return "bottomLeft"
        elif point == "bottomLeft": return "topRight"
        elif point == "bottomRight": return "topLeft"

    def translate(self, str):
        if str == "top" or str == "topLeft":
            return "topLeft"
        elif str == "right" or str == "topRight":
            return "topRight"
        elif str == "bottom" or str == "bottomRight":
            return "bottomRight"
        elif str == "left" or str == "bottomLeft":
            return "bottomLeft"
        
    def clamp_values(self, mouse):
        minimum_size = 0.1 * max(self.image_x, self.image_y)

        # Ensure values remain within image boundaries
        clamped_mouse_x = min(self.image_x - 1, max(2, self.pixel_to_value(mouse).x()))
        clamped_mouse_y = min(self.image_y - 1, max(2, self.pixel_to_value(mouse).y()))

        # Get the opposite corner's position
        opposite_x = self.crop_points[self.opposite(self.translate(self.active))].x()
        opposite_y = self.crop_points[self.opposite(self.translate(self.active))].y()

        # Enforce minimum crop size
        if self.active in ["topLeft", "bottomLeft", "left"]:
            clamped_mouse_x = min(clamped_mouse_x, opposite_x - minimum_size)
        if self.active in ["topRight", "bottomRight", "right"]:
            clamped_mouse_x = max(clamped_mouse_x, opposite_x + minimum_size)
        if self.active in ["topLeft", "topRight", "top"]:
            clamped_mouse_y = min(clamped_mouse_y, opposite_y - minimum_size)
        if self.active in ["bottomLeft", "bottomRight", "bottom"]:
            clamped_mouse_y = max(clamped_mouse_y, opposite_y + minimum_size)

        # Handle dragging logic for edges separately
        if self.active == "top":
            return QtCore.QPoint(self.crop_points["topLeft"].x(), clamped_mouse_y)
        elif self.active == "right":
            return QtCore.QPoint(clamped_mouse_x, self.crop_points["topRight"].y())
        elif self.active == "bottom":
            return QtCore.QPoint(self.crop_points["bottomRight"].x(), clamped_mouse_y)
        elif self.active == "left":
            return QtCore.QPoint(clamped_mouse_x, self.crop_points["bottomLeft"].y())
        else: 
            return QtCore.QPoint(clamped_mouse_x, clamped_mouse_y)
            
    def update_corners(self, mouse):
        self.crop_points[self.translate(self.active)] = self.clamp_values(mouse)
        self.make_point_dict(self.crop_points[self.translate(self.active)], self.crop_points[self.opposite(self.translate(self.active))])

    def ffmpeg_crop(self):
        width = abs(self.crop_points["topRight"].x() - self.crop_points["topLeft"].x())
        height = abs(self.crop_points["bottomLeft"].y() - self.crop_points["topLeft"].y())
        return f"crop={width}:{height}:{self.crop_points['topLeft'].x()}:{self.crop_points['topLeft'].y()}"
        
    def mousePressEvent(self, ev):
        self.process_pointer_press(ev)
        return super().mousePressEvent(ev)
    
    def mouseMoveEvent(self, ev):
        self.process_pointer_event(ev)
        return super().mouseMoveEvent(ev)
    
    def mouseReleaseEvent(self, ev):
        self.process_pointer_release(ev)
        return super().mouseReleaseEvent(ev)
    
    def process_pointer_event(self, ev):
        mouse = QtCore.QPoint(ev.pos().x(), ev.pos().y())
        self.hover = None
        threshold = 15

        if self.parent().crop :
            if (self.value_to_pixel(self.crop_points["topLeft"]).x() - threshold < mouse.x() < self.value_to_pixel(self.crop_points["bottomRight"]).x() + threshold):  # Horizontal check
                if abs(mouse.y() - (self.value_to_pixel(self.crop_points["topLeft"]).y())) < threshold:
                    self.hover = "top"
                elif abs(mouse.y() - (self.value_to_pixel(self.crop_points["bottomRight"]).y())) < threshold:
                    self.hover = "bottom" 

            if (self.value_to_pixel(self.crop_points["topLeft"]).y() - threshold < mouse.y() < self.value_to_pixel(self.crop_points["bottomRight"]).y() + threshold):  # Vertical check
                if abs(mouse.x() - self.value_to_pixel(self.crop_points["topLeft"]).x()) < threshold:
                    self.hover = "left" 
                elif abs(mouse.x() - self.value_to_pixel(self.crop_points["bottomRight"]).x()) < threshold:
                    self.hover = "right"

            for key in self.crop_points:
                if abs(((mouse) - self.value_to_pixel(self.crop_points[key])).x()) < threshold and abs(((mouse) - self.value_to_pixel(self.crop_points[key])).y()) < threshold:
                    self.hover = key
                    break

            if self.active and ev.buttons() & QtCore.Qt.LeftButton:
                self.hover = self.active
                self.update_corners(mouse)

        if not self.active and ev.buttons() & QtCore.Qt.LeftButton:
            delta = mouse.x() - self.last_mousex_position
            if abs(delta) > 2 and self.debounce_ready:
                if abs(delta) <= 5:
                    frames = 1
                elif 6 <= abs(delta) <=10:
                    frames = 2
                elif 11 <= abs(delta) <=15:
                    frames = 4
                elif 16 <= abs(delta) <=22:
                    frames = 8
                elif 23 <= abs(delta) <=28:
                    frames = 16
                else:
                    frames = 32

                if delta > 0:
                    self.sig_forwards.emit(frames)
                else:
                    self.sig_backwards.emit(frames)

                self.last_mousex_position = mouse.x()
                self.debounce_ready = False
                self.debounce_timer.start()

        self.repaint()

    def _reset_debounce(self):
        self.debounce_ready = True

    def process_pointer_press(self, ev):
        self.slider_active.emit(True)
        self.active = self.hover
        self.last_mousex_position = ev.pos().x()
    
    def process_pointer_release(self, ev):
        self.active = self.hover
        self.slider_active.emit(False)
        

        
    
    def tabletEvent(self, event: QtGui.QTabletEvent):
        event_type = event.type()

        if event_type == QtCore.QEvent.TabletMove:
            self.process_pointer_event(event)
            event.accept()

        elif event_type == QtCore.QEvent.TabletPress:
            self.process_pointer_press(event)
            event.accept()

        elif event_type == QtCore.QEvent.TabletRelease:
            self.process_pointer_release(event)
            event.accept()

        else:
            super().tabletEvent(event)
    


    def resizeEvent(self, event):
        self.update()
        return super().resizeEvent(event)

class CacheDict(QtCore.QObject):
    cache_changed = QtCore.Signal(int)

    def __init__(self, cache_size=800, look_ahead=750, look_behind=50, mini_margin=35, *args, **kwargs):
        super().__init__()
        self._data = dict(*args, **kwargs)
        self.cache_size = cache_size
        self.look_ahead = look_ahead
        self.look_behind = look_behind

        # Out of range
        self.mini_margin = mini_margin

    def __setitem__(self, key, value):
        if key not in self:
            self._data[key] = value
            self.emit_signal(key)

    def __getitem__(self, key):
        return self._data[key]

    def __delitem__(self, key):
        del self._data[key]
        self.emit_signal(key)

    def __contains__(self, key):
        return key in self._data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def evict(self, key):
        del self._data[key]

    def emit_signal(self, key):
        self.cache_changed.emit(key)

    def configure(self, size, look_ahead, look_behind, mini_margin=35):
        self.cache_size = size
        self.look_ahead = look_ahead
        self.look_behind = look_behind
        self.mini_margin = mini_margin

