# -*- coding: utf-8 -*-

"""
Class Tree

TableWidget

PaintWidget
    |------RgbWidget
    |------LumWidget
    |------ImageWidget
    |------ColorWidget
                |------CursorWidget
"""
import re
import json
import logging
import os.path
from serial import Serial
from PySide.QtGui import *
from PySide.QtCore import *
from datetime import datetime

from .misc import SerialPortSelector
from .container import ComponentManager
from ..core.datatype import str2number, str2float, DynamicObject, DynamicObjectDecodeError
from ..misc.settings import UiInputSetting, UiLogMessage, UiLayout, UiFontInput, UiColorInput


__all__ = ['ColorWidget', 'CursorWidget', 'RgbWidget', 'LumWidget', 'ImageWidget',
           'TableWidget', 'ListWidget', 'SerialPortSettingWidget', 'LogMessageWidget',
           'BasicJsonSettingWidget', 'JsonSettingWidget', 'MultiJsonSettingsWidget',
           'MultiGroupJsonSettingsWidget', 'MultiTabJsonSettingsWidget']


class PaintWidget(QWidget):
    def __init__(self, parent=None):
        """Base class provide basic draw functions and get widget message """

        super(PaintWidget, self).__init__(parent)

    def getXRatio(self, maxValue):
        if not self.isNumber(maxValue):
            return 0

        if isinstance(maxValue, int):
            maxValue = float(maxValue)

        x = self.cursor().pos().x()
        return int(round(maxValue / self.width() * x))

    def getYRatio(self, maxValue):
        if not self.isNumber(maxValue):
            return 0

        if isinstance(maxValue, int):
            maxValue = float(maxValue)

        y = self.cursor().pos().y()
        return int(round(maxValue / self.height() * y))

    def getCursorPos(self):
        x = self.cursor().pos().x()
        y = self.cursor().pos().y()
        return x, y

    def getCursorLum(self):
        """Get current cursor position luminance

        :return:
        """
        x, y = self.getCursorPos()
        color = QColor(QPixmap().grabWindow(self.winId()).toImage().pixel(x, y))
        return max(color.red(), color.green(), color.blue())

    def getDynamicTextPos(self, fontSize, textSize):
        """Get dynamic text position

        :param fontSize: Font size
        :param textSize: Text length
        :return:QPoint
        :return:QPoint
        """
        if not isinstance(fontSize, int) or not isinstance(textSize, int):
            return QPoint(self.width() / 2, self.height() / 2)

        # Get mouse position
        x, y = self.getCursorPos()

        # Offset
        offset = 3

        if x < self.width() / 2:
            tx = x + fontSize * offset
        else:
            tx = x - (textSize + offset - 1) * fontSize

        if y < self.height() / 2:
            ty = y + fontSize * offset
        else:
            ty = y - fontSize * (offset - 1)

        return QPoint(tx, ty)

    def drawCenterText(self, painter, font, color, text):
        """Draw dynamic text follow mouse movement

        :param painter:
        :param font: Text Font
        :param color: Text color
        :param text: draw text
        :return:
        """
        if not isinstance(painter, QPainter) or not isinstance(font, QFont) or not self.isColor(color):
            print("TypeError")
            return False

        try:
            painter.setFont(font)
            painter.setPen(QPen(QColor(color)))
            painter.drawText(self.rect(), Qt.AlignCenter, text)
        except TypeError:
            print("Text TypeError")

    def drawDynamicText(self, painter, font, color, text):
        """Draw dynamic text follow mouse movement

        :param painter:
        :param font: Text Font
        :param color: Text color
        :param text: draw text
        :return:
        """
        if not isinstance(painter, QPainter) or not isinstance(font, QFont) or not self.isColor(color):
            return False

        if not isinstance(text, str):
            return False

        painter.setFont(font)
        painter.setPen(QPen(QColor(color)))
        painter.drawText(self.getDynamicTextPos(font.pointSize(), len(text)), text)

    def drawSquare(self, painter, color, start, side):
        return self.drawRectangle(painter, color, start, side, side)

    def drawRectangle(self, painter, color, start, width, height):
        """Draw Rectangle at start point

        :param painter:QPainter
        :param color: Rectangle background color
        :param start: Rectangle upper left conner point position
        :param width: Rectangle width
        :param height:Rectangle height
        :return:
        """
        if not isinstance(painter, QPainter) or not self.isColor(color):
            return False

        if not isinstance(start, QPoint) or not self.isValidWidth(width) or not self.isValidHeight(height):
            return False

        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(QColor(color)))
        painter.drawRect(start.x(), start.y(), width, height)
        return True

    def drawCenterRect(self, painter, color, width, height):
        if not self.isValidWidth(width) or not self.isValidHeight(height):
            return False

        x = self.rect().center().x()
        y = self.rect().center().y()
        start = QPoint(x - width / 2, y - height / 2)
        return self.drawRectangle(painter, color, start, width, height)

    def drawCenterSquare(self, painter, color, side):
        return self.drawCenterRect(painter, color, side, side)

    def drawBackground(self, painter, color):
        if not isinstance(painter, QPainter) or not self.isColor(color):
            return False

        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(QColor(color)))
        painter.drawRect(self.rect())
        return True

    def drawHorizontalLine(self, painter, color, y, xs, xe):
        """Draw a horizontal line at y form xs to xe

        :param painter:
        :param color: line color
        :param y: Vertical pos
        :param xs:Horizontal line start
        :param xe:Horizontal line end
        :return:True or false
        """
        if not isinstance(painter, QPainter) or not self.isColor(color):
            return False

        if not self.isValidHeight(y) or not self.isValidHRange(xs, xe):
            return False

        painter.setPen(QPen(color))
        painter.drawLine(QPoint(xs, y), QPoint(xe, y))

    def drawVerticalLine(self, painter, color, x, ys, ye):
        """

        :param painter:
        :param color: line color
        :param x: Horizontal pos
        :param ys: Vertical line start
        :param ye: Vertical line end
        :return:
        """
        if not isinstance(painter, QPainter) or not self.isColor(color):
            return False

        if not self.isValidWidth(x) or not self.isValidVRange(ys, ye):
            return False

        painter.setPen(QPen(color))
        painter.drawLine(QPoint(x, ys), QPoint(x, ye))

    @staticmethod
    def adjustColorBrightness(color, brightness):
        """Adjust color brightness

        :param color: QColor
        :param brightness: brightness value (0 - 255)
        :return:success return after just color, else Qt.back
        """

        if not PaintWidget.isColor(color) or not PaintWidget.isNumber(brightness):
            return QColor(Qt.black)

        if brightness < 0 or brightness > 255:
            return QColor(Qt.black)

        color = QColor(color)
        if color.black():
            color.setRed(255 - brightness)
            color.setGreen(255 - brightness)
            color.setBlue(255 - brightness)
            return color

        if color.red():
            color.setRed(brightness)

        if color.green():
            color.setGreen(brightness)

        if color.blue():
            color.setBlue(brightness)

        return color

    @staticmethod
    def getColorMode(color):
        """Return color mode, blue -> 1, red -> 4 white -> 7

        :param color:
        :return:
        """

        if not PaintWidget.isColor(color):
            return 0

        mode = 0
        color = QColor(color)

        if color.red():
            mode |= 4

        if color.green():
            mode |= 2

        if color.blue():
            mode |= 1

        return mode

    @staticmethod
    def getColorRawValue(color):
        if not PaintWidget.isColor(color):
            return 0

        color = QColor(color)
        return color.rgb() & 0xffffff

    @staticmethod
    def getRgbMode(r, g, b):
        """From rgb to rgb mode (255, 0, 0) -> 4 (True, True, True) -> 7

        :param r: Red color value or is red set boolean value
        :param g: Green color value or is red set boolean value
        :param b: Blue color value or is set boolean value
        :return:
        """
        mode = 0
        if r:
            mode |= 4

        if g:
            mode |= 2

        if b:
            mode |= 1

        return mode

    @staticmethod
    def isColor(color):
        if not isinstance(color, QColor) and not isinstance(color, Qt.GlobalColor):
            return False

        return True

    @staticmethod
    def isNumber(number):
        if not isinstance(number, float) and not isinstance(number, int):
            return False

        return True

    def isValidWidth(self, x):
        if x < 0 or x > self.width():
            return False

        return True

    def isValidHeight(self, y):
        if y < 0 or y > self.height():
            return False

        return True

    def isValidHRange(self, start, end):
        if not self.isValidWidth(start) or not self.isValidWidth(end):
            return False

        return start < end

    def isValidVRange(self, start, end):
        if not self.isValidHeight(start) or not self.isValidHeight(end):
            return False

        return start < end


class ColorWidget(PaintWidget):
    colorMax = 255.0

    # When color changed will send is signal, r, g, b value
    colorChanged = Signal(int, int, int)

    # When mouse release send this signal
    colorStopChange = Signal(int, int, int)

    def __init__(self, font=QFont("Times New Roman", 10), parent=None):
        """Color grab widget double click mouse left button change color, mouse horizontal move change color brightness

        ColorWidget provide two signal 'colorChanged' and 'colorStopChange', when mouse horizontal moved, the color
        will changed, the 'colorChanged' signal will send. 'colorStopChange' signal will send when the mouse is stop .

        Signal: colorChanged(int r, int g, int b)
        Signal: colorStopChange(int r, int g, int b)

        :param font: Color r, g, b value display font
        :param parent:
        :return:None double click mouse right button will exit
        """
        super(ColorWidget, self).__init__(parent)
        # Enter full screen mode
        self.showFullScreen()

        # Default setting
        self.font = QFont("Times New Roman", 10)
        if isinstance(font, QFont):
            self.font = font

        # Color list
        self.colorIndex = -1
        self.color = (Qt.white, Qt.black)
        self.colorTable = [(Qt.blue, Qt.white), (Qt.green, Qt.black), (Qt.cyan, Qt.black), (Qt.red, Qt.white),
                           (Qt.magenta, Qt.white), (Qt.yellow, Qt.black), (Qt.white, Qt.black), (Qt.black, Qt.white)]

    def getColor(self):
        self.colorIndex += 1
        if self.colorIndex >= len(self.colorTable):
            self.colorIndex = 0

        return self.colorTable[self.colorIndex]

    def addColor(self, color):
        """Add color to color group

        :param color:(QColor, QColor)
        :return:
        """
        if not isinstance(color, (tuple, list)) or len(color) != 2:
            return False

        if not isinstance(color[0], QColor) or not isinstance(color[1], QColor):
            return False

        self.colorTable.append(color)

    def getBackgroundColor(self):
        return QColor(self.color[0])

    def getForegroundColor(self):
        return QColor(self.color[1])

    def mouseDoubleClickEvent(self, ev):
        # Left button change background color
        if ev.button() == Qt.LeftButton:
            self.color = self.getColor()
            self.update()
        # Right button exit
        elif ev.button() == Qt.RightButton:
            self.close()

    def mouseReleaseEvent(self, ev):
        # Send color changed signal
        if ev.button() == Qt.LeftButton:
            value = self.getXRatio(self.colorMax)
            color = ColorWidget.adjustColorBrightness(self.getBackgroundColor(), value)
            self.colorChanged.emit(color.red(), color.green(), color.blue())
            self.colorStopChange.emit(color.red(), color.green(), color.blue())

    def mouseMoveEvent(self, ev):
        # Update re paint
        self.update()

    def paintEvent(self, ev):
        painter = QPainter(self)
        value = self.getXRatio(self.colorMax)
        color = ColorWidget.adjustColorBrightness(self.getBackgroundColor(), value)
        textColor = Qt.white if self.getCursorLum() < 64 else self.getForegroundColor()
        text = "R:{0:d}, G:{1:d}, B{2:d}".format(color.red(), color.green(), color.blue())

        # Send color changed signal
        self.colorChanged.emit(color.red(), color.green(), color.blue())

        # Draw cross line and cursor pos
        self.drawBackground(painter, color)
        self.drawDynamicText(painter, self.font, textColor, text)


class CursorWidget(ColorWidget):
    # When cursor changed will send this signal
    cursorChanged = Signal(int, int, int)

    # When cursor stop changed will send this signal
    cursorStopChange = Signal(int, int, int)

    def __init__(self, font=QFont("Times New Roman", 10), parent=None):
        """Cursor grab widget, double click mouse left button change color, mouse moved change cursor position

        CursorWidget provide two signal 'cursorChanged' and 'cursorStopChange', when mouse moved, the cursor position
        will changed, the 'cursorChanged' signal will send. 'cursorStopChange' signal will send when the mouse is stop .

        Signal: cursorChanged(int x, int y, int backgroundColor)
        Signal: cursorStopChange(int x, int y, int backgroundColor)

        1 signal inherited from ColorWidget: colorChanged

        :param font:Cursor position display font
        :param parent:
        :return:
        """
        super(CursorWidget, self).__init__(font, parent)
        self.color = (Qt.white, Qt.black)
        self.oldColor = self.getForegroundColor()
        self.remap_width, self.remap_height = self.width(), self.height()

    def __remapCursor(self, x, y):
        px = 1 if x == 0 else self.remap_width * 1.0 / self.width() * (x + 1)
        py = 1 if y == 0 else self.remap_height * 1.0 / self.height() * (y + 1)
        return int(round(px)) - 1, int(round(py)) - 1

    def setRemap(self, width, height):
        """Set cursor remap width and height

        :param width: remap width
        :param height: remap height
        :return:
        """
        if not isinstance(width, int) or not isinstance(height, int):
            print("setRemap TypeError:{}, {}".format(type(width), type(height)))
            return False

        self.remap_width = width
        self.remap_height = height
        return True

    def mouseReleaseEvent(self, ev):
        # Send color changed signal
        if self.getBackgroundColor() != self.oldColor:
            color = self.getBackgroundColor()
            self.colorChanged.emit(color.red(), color.green(), color.blue())

        # Mouse release and cursor position changed send mouse pos
        if ev.button() == Qt.LeftButton:
            x = ev.pos().x()
            y = ev.pos().y()
            rx, ry = self.__remapCursor(x, y)
            self.cursorChanged.emit(rx, ry, self.getColorRawValue(self.getBackgroundColor()))
            self.cursorStopChange.emit(rx, ry, self.getColorRawValue(self.getBackgroundColor()))

    def paintEvent(self, ev):
        painter = QPainter(self)
        x, y = self.getCursorPos()
        rx, ry = self.__remapCursor(x, y)
        text = "X:{0:d}, Y:{1:d}".format(rx, ry)

        # Cursor changed
        self.cursorChanged.emit(rx, ry, self.getColorRawValue(self.getBackgroundColor()))

        # Draw cross line and cursor pos
        self.drawBackground(painter, self.getBackgroundColor())
        self.drawVerticalLine(painter, self.getForegroundColor(), x, 0, self.height())
        self.drawHorizontalLine(painter, self.getForegroundColor(), y, 0, self.width())
        self.drawDynamicText(painter, self.font, self.getForegroundColor(), text)


class RgbWidget(PaintWidget):
    # When r, g, b changed send this signal
    rgbChanged = Signal(bool, bool, bool)

    def __init__(self, parent=None):
        """ RGB color control widget, double click the color zone will turn of or turn off this color.

        When color states changed will send 'rgbChanged' signal

        Signal:rgbChanged(bool rState, bool gState, bool bState)

        :param parent:
        :return:
        """
        super(RgbWidget, self).__init__(parent)
        self.showFullScreen()
        self.rgb = [True, True, True]
        self.part = int(self.height() / 3)
        self.colorTable = (Qt.red, Qt.green, Qt.blue)
        self.rgbChanged.emit(self.rgb[0], self.rgb[1], self.rgb[2])

    def mouseDoubleClickEvent(self, ev):
        # Left button change background color
        if ev.button() == Qt.LeftButton:
            _, y = self.getCursorPos()
            if y < self.part:
                self.rgb[0] = not self.rgb[0]
            elif (y > self.part) and (y < self.part * 2):
                self.rgb[1] = not self.rgb[1]
            else:
                self.rgb[2] = not self.rgb[2]

            self.update()

        # Right button exit
        elif ev.button() == Qt.RightButton:
            self.close()

    def paintEvent(self, ev):
        painter = QPainter(self)
        self.rgbChanged.emit(self.rgb[0], self.rgb[1], self.rgb[2])

        for idx, rgb in enumerate(self.rgb):
            if rgb:
                color = self.colorTable[idx]
            else:
                color = Qt.black
                self.drawHorizontalLine(painter, QColor(Qt.white), idx * self.part - 1, 0, self.width())

            self.drawRectangle(painter, color, QPoint(0, idx * self.part), self.width(), self.part)


class LumWidget(PaintWidget):
    # Lum max value
    lumMax = 255.0

    # When lum changed will send this signal hi, low, mode
    lumChanged = Signal(int, int, int)
    lumStopChange = Signal(int, int, int)

    # Lum mode
    CE1_MODE = 1
    CE2_MODE = 2
    LF_MODE = 3
    UD_MODE = 4
    CT_MODE = 5
    LUM_MODE = (CE1_MODE, CE2_MODE, LF_MODE, UD_MODE, CT_MODE)

    def __init__(self, font=QFont("Times New Roman", 10), parent=None):
        """Luminance grab widget, double click mouse left button change mode, mouse moved change windows Luminance

        Press mouse left button, then move mouse will change the low luminance
        Press mouse right button, then move mouse will change the high luminance

        LumWidget provide 2 signal 'lumChanged' and 'lumStopChange', when mouse moved, the windows Luminance
        will changed, the 'lumChanged' signal will send. 'lumStopChange' signal will send when the mouse is stop .

        Signal: lumChanged(int hi, int low, int mode)
        Signal: lumStopChange(int hi, int low, int mode)

        :param font:Windows Luminance display font
        :param parent:
        :return:
        """
        super(LumWidget, self).__init__(parent)
        self.showFullScreen()

        if isinstance(font, QFont):
            self.font = QFont("Times New Roman", 10)

        # Default is center windows
        self.lumIndex = 0
        self.lumMode = self.CE1_MODE

        # Default adjust low lum
        self.adjustHigh = False
        self.lum = [0, int(self.lumMax)]
        self.oldLum = [int(self.lumMax), 0]

    def getLumMode(self):
        self.lumIndex += 1
        if self.lumIndex >= len(self.LUM_MODE):
            self.lumIndex = 0

        return self.LUM_MODE[self.lumIndex]

    def getLowLum(self):
        return QColor(self.lum[0], self.lum[0], self.lum[0])

    def getHighLum(self):
        return QColor(self.lum[1], self.lum[1], self.lum[1])

    def mouseMoveEvent(self, ev):
        self.lum[self.adjustHigh] = self.getXRatio(self.lumMax)
        self.update()

    def mousePressEvent(self, ev):
        # If left key press adjust low
        if ev.button() == Qt.LeftButton:
            self.adjustHigh = False
        # Right button press adjust high
        elif ev.button() == Qt.RightButton:
            self.adjustHigh = True

    def mouseReleaseEvent(self, ev):
        if self.lum != self.oldLum:
            self.oldLum = self.lum
            self.lumChanged.emit(self.lum[1], self.lum[0], self.lumMode)
            self.lumStopChange.emit(self.lum[1], self.lum[0], self.lumMode)

    def mouseDoubleClickEvent(self, ev):
        # Left button change background color
        if ev.button() == Qt.LeftButton:
            self.lumMode = self.getLumMode()
            self.lum = [0, int(self.lumMax)]
            self.update()

        # Right button exit
        elif ev.button() == Qt.RightButton:
            self.close()

    def paintEvent(self, ev):
        painter = QPainter(self)
        self.drawBackground(painter, self.getLowLum())
        textColor = Qt.white if self.getCursorLum() < 64 else Qt.black
        text = "Hi:{0:d} Low:{1:d}".format(int(self.lum[1]), int(self.lum[0]))

        # Send lum changed signal
        self.lumChanged.emit(self.lum[1], self.lum[0], self.lumMode)

        if self.lumMode == self.CE1_MODE:
            self.drawCenterSquare(painter, self.getHighLum(), self.height() / 2)
        elif self.lumMode == self.CE2_MODE:
            self.drawCenterRect(painter, self.getHighLum(), self.width() / 2, self.height() / 2)
        elif self.lumMode == self.LF_MODE:
            self.drawRectangle(painter, self.getHighLum(), QPoint(0, 0), self.width() / 2, self.height())
        elif self.lumMode == self.UD_MODE:
            self.drawRectangle(painter, self.getHighLum(), QPoint(0, 0), self.width(), self.height() / 2)
        elif self.lumMode == self.CT_MODE:
            side = self.height() / 7
            self.drawBackground(painter, QColor(127, 127, 127))
            self.drawCenterSquare(painter, self.getHighLum(), side)
            self.drawSquare(painter, self.getLowLum(), QPoint(self.width() / 2 - side / 2, side), side)
            self.drawSquare(painter, self.getLowLum(), QPoint(self.width() / 2 - side / 2, side * 5), side)
            self.drawSquare(painter, self.getLowLum(), QPoint(self.width() / 2 - side * 2.5, side * 3), side)
            self.drawSquare(painter, self.getLowLum(), QPoint(self.width() / 2 + side * 1.5, side * 3), side)

        self.drawDynamicText(painter, self.font, textColor, text)


class ImageWidget(PaintWidget):
    def __init__(self, width=0, height=0, zoomInRatio=0, zoomInArea=20, parent=None):
        """ImageWidget provide 3 method to draw a image

        drawFromFs  :   load a image from filesystem and show it
        drawFromMem :   load a image form memory data and show it
        drawFromText:   Dynamic draw a image with text

        :param width: widget fixed width
        :param height:widget fixed height
        :param zoomInRatio: zoom in ratio 0 is turn off
        :param zoomInArea: zoom in area width and height
        :param parent:
        :return:
        """
        super(ImageWidget, self).__init__(parent)
        self.supportFormats = [str(name) for name in QImageReader.supportedImageFormats()]

        # Default setting
        self.text = ""
        self.textColor = Qt.black
        self.bgColor = Qt.lightGray
        self.textFont = QFont("Times New Roman", width / 16)

        # Draw image using
        self.image = QImage()

        # For grab cursor position pixel
        self.zoomInX = 0
        self.zoomInY = 0
        self.zoomInFlag = False
        self.zoomInPattern = QPixmap()
        self.zoomInArea = zoomInArea if isinstance(zoomInArea, int) else 20
        self.zoomInRatio = zoomInRatio if isinstance(zoomInRatio, int) else 0

        self.setMinimumSize(width, height)

    @Slot(str)
    def drawFromFs(self, filePath):
        """Load a image from filesystem, then display it

        :param filePath: Image file path
        :return:
        """
        if not isinstance(filePath, str) or not os.path.isfile(filePath):
            print("File path:{} is not exist!".format(filePath))
            return False

        image = QImageReader(filePath)
        if not len(image.format()):
            print("File is not a image file:{}".format(image.errorString()))
            return False

        # Load image file to memory
        self.image = image.read()
        self.update()
        return True

    @Slot(object, object)
    def drawFromMem(self, data, imageFormat="bmp"):
        """Load image form memory

        :param data: Image data
        :param imageFormat: Image format
        :return:
        """
        if not isinstance(data, bytes) or len(data) == 0:
            print("Invalid image data:{}".format(type(data)))
            return False

        if not isinstance(imageFormat, str) or imageFormat not in self.supportFormats:
            print("Invalid image format:{}".format(imageFormat))
            return False

        # Clear loadImageFromFs data
        self.image = QImage.fromData(data, imageFormat)
        self.update()
        return True

    @Slot(str)
    def drawFromText(self, text, textColor=Qt.black, bgColor=Qt.lightGray, fontSize=40):
        """Draw a text message in the center of the widget

        :param text: Text context
        :param textColor: Text color
        :param bgColor: Widget background color
        :param fontSize: fontSize
        :return:
        """
        if not isinstance(text, str):
            print("text require :{!r}".format(text.__class__.__name__))
            return False

        if len(text) == 0:
            return False

        if self.isColor(bgColor):
            self.bgColor = bgColor

        if self.isColor(textColor):
            self.textColor = textColor

        if isinstance(fontSize, int):
            self.textFont.setPointSize(fontSize)

        # From text max length get max text size
        textMaxLength = max([len(t) for t in text.split('\n')])
        fontMaxWidth = round(self.width() / textMaxLength)

        if self.textFont.pointSize() > fontMaxWidth:
            self.textFont.setPointSize(fontMaxWidth)

        self.text = self.tr(text)
        self.image = QImage()
        self.update()

    def paintEvent(self, ev):
        painter = QPainter(self)

        # Is image show it
        if not self.image.isNull():
            painter.drawImage(self.rect(), self.image)
        # Draw text and show
        else:
            self.drawBackground(painter, self.bgColor)
            self.drawCenterText(painter, self.textFont, self.textColor, self.text)

        # If zoom in flag superimposed zoom in pattern
        if self.zoomInFlag:
            if self.zoomInX < self.width() / 2:
                x = self.zoomInX + 15
            else:
                x = self.zoomInX - 15 - self.zoomInPattern.width()

            if self.zoomInY < self.height() / 2:
                y = self.zoomInY + 15
            else:
                y = self.zoomInY - 15 - self.zoomInPattern.height()

            painter.drawPixmap(x, y, self.zoomInPattern)

    def mouseMoveEvent(self, ev):
        if not self.zoomInRatio:
            return

        # Clear zoom in flag
        self.zoomInFlag = False

        self.zoomInX = ev.x()
        self.zoomInY = ev.y()
        ratio = self.zoomInRatio

        # Cursor move out of the range
        if self.zoomInX < -8 or self.zoomInX >= self.width() \
                or self.zoomInY < -8 or self.zoomInY >= self.height():
            self.update()
            return

        # Grab cursor pointer pattern
        sample = QPixmap()
        sample = sample.grabWidget(self, self.zoomInX, self.zoomInY, self.zoomInArea, self.zoomInArea)
        self.zoomInPattern = sample.scaled(sample.width() * ratio, sample.height() * ratio, Qt.KeepAspectRatio)

        # Update call paintEvent
        self.zoomInFlag = True
        self.update()

    def mouseReleaseEvent(self, ev):
        # Mouse release will clear zoom in flag
        self.zoomInFlag = False
        self.update()


class TableWidget(QTableWidget):
    tableDataChanged = Signal()

    def __init__(self, max_column, hide_header=False, parent=None):
        """Create a QTableWidget

        :param max_column: max column number
        :param hide_header: hide vertical and horizontal header
        :param parent:
        :return:
        """
        super(TableWidget, self).__init__(parent)

        self.setColumnCount(max_column)
        self.hideHeaders(hide_header)
        self.__table_filters = dict()

    def __checkRow(self, row):
        if not isinstance(row, int):
            print("TypeError:{}".format(type(row)))
            return False

        if row >= self.rowCount() or row < 0:
            print("Row range error, max row: {0:d}".format(self.rowCount()))
            return False

        return True

    def __checkColumn(self, column):
        if not isinstance(column, int):
            print("TypeError:{}".format(type(column)))
            return False

        if column >= self.columnCount() or column < 0:
            print("Column range error, max column: {0:d}".format(self.columnCount()))
            return False

        return True

    @staticmethod
    def __copyWidget(widget):
        temp = widget
        if not isinstance(widget, QWidget):
            return widget

        if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            temp = QSpinBox() if isinstance(widget, QSpinBox) else QDoubleSpinBox()
            temp.setRange(widget.minimum(), widget.maximum())
            temp.setEnabled(widget.isEnabled())
            temp.setValue(widget.value())
        elif isinstance(widget, QCheckBox):
            temp = QCheckBox()
            temp.setText(widget.text())
            temp.setChecked(widget.isChecked())
            temp.setEnabled(widget.isEnabled())
        elif isinstance(widget, QComboBox):
            temp = QComboBox()
            temp.addItems([widget.itemText(x) for x in range(widget.count())])
            temp.setCurrentIndex(widget.currentIndex())
            temp.setEnabled(widget.isEnabled())
        elif isinstance(widget, QDateTimeEdit):
            temp = QDateTimeEdit()
            temp.setDateTime(widget.dateTime())
            temp.setEnabled(widget.isEnabled())
            temp.setCalendarPopup(widget.calendarPopup())
        elif isinstance(widget, QPushButton):
            temp = QPushButton(widget.text())
            widget.setHidden(True)
        elif isinstance(widget, QProgressBar):
            temp = QProgressBar()
            temp.setInvertedAppearance(widget.invertedAppearance())
            temp.setRange(widget.minimum(), widget.maximum())
            temp.setTextVisible(widget.isTextVisible())
            temp.setFormat(widget.format())
            temp.setValue(widget.value())

        # Copy widget property
        for key in widget.dynamicPropertyNames():
            key = str(key)
            temp.setProperty(key, widget.property(key))
            if key == "clicked" and isinstance(widget, QPushButton):
                temp.clicked.connect(widget.property(key))

        return temp

    def __slotWidgetDataChanged(self):
        self.tableDataChanged.emit()

    @Slot(bool)
    def hideHeaders(self, hide):
        self.hideRowHeader(hide)
        self.hideColumnHeader(hide)

    @Slot(bool)
    def hideRowHeader(self, hide):
        self.verticalHeader().setVisible(not hide)

    @Slot(bool)
    def hideColumnHeader(self, hide):
        self.horizontalHeader().setVisible(not hide)

    @Slot()
    def rowMoveUp(self):
        row = self.currentRow()
        if row == 0:
            return
        self.swapRow(row, row - 1)

    @Slot()
    def rowMoveDown(self):
        row = self.currentRow()
        if row == self.rowCount() - 1:
            return
        self.swapRow(row, row + 1)

    @Slot()
    def columnMoveLeft(self):
        column = self.currentColumn()
        if column == 0:
            return
        self.swapColumn(column, column - 1)

    @Slot()
    def columnMoveRight(self):
        column = self.currentColumn()
        if column == self.columnCount() - 1:
            return
        self.swapColumn(column, column + 1)

    @Slot()
    def setRowSelectMode(self):
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

    @Slot()
    def setItemSelectMode(self):
        self.setSelectionBehavior(QAbstractItemView.SelectItems)

    @Slot()
    def setColumnSelectMode(self):
        self.setSelectionBehavior(QAbstractItemView.SelectColumns)

    def frozenItem(self, row, column, frozen):
        """Frozen or unfroze a item

        :param row: item row number
        :param column: item column number
        :param frozen: True -> Frozen, False -> Unfrozen
        :return: True / False
        """
        if not self.__checkRow(row) or not self.__checkColumn(column):
            return False

        # Item
        item = self.takeItem(row, column)
        if isinstance(item, QTableWidgetItem):
            flags = QTableWidgetItem("").flags()
            flags = flags & ~Qt.ItemIsEditable if frozen else flags
            item.setFlags(flags)
            self.setItem(row, column, item)

        # Widget:
        widget = self.__copyWidget(self.cellWidget(row, column))
        if isinstance(widget, QWidget):
            widget.setDisabled(frozen)
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.valueChanged.connect(self.__slotWidgetDataChanged)
            elif isinstance(widget, QCheckBox):
                widget.stateChanged.connect(self.__slotWidgetDataChanged)
            elif isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(self.__slotWidgetDataChanged)
            elif isinstance(widget, QDateTimeEdit):
                widget.dateTimeChanged.connect(self.__slotWidgetDataChanged)
            elif isinstance(widget, QProgressBar):
                widget.valueChanged.connect(self.__slotWidgetDataChanged)

            self.cellWidget(row, column).setHidden(True)
            self.removeCellWidget(row, column)
            self.setCellWidget(row, column, widget)

        return True

    def frozenTable(self, frozen):
        for row in range(self.rowCount()):
            if not self.frozenRow(row, frozen):
                return False

        return True

    def frozenRow(self, row, frozen):
        """Frozen or unfrozen a row item

        :param row: row number start from 0
        :param frozen: True -> Frozen, False -> Unfrozen
        :return: True / False
        """
        for column in range(self.columnCount()):
            if not self.frozenItem(row, column, frozen):
                return False

        return True

    def frozenColumn(self, column, frozen):
        """Frozen or unfrozen a column item

        :param column: column number
        :param frozen: True -> Frozen, False -> Unfrozen
        :return: True / False
        """
        for row in range(self.rowCount()):
            if not self.frozenItem(row, column, frozen):
                return False

        return True

    def swapItem(self, src_row, src_column, dst_row, dst_column):
        if not self.__checkRow(src_row) or not self.__checkRow(dst_row):
            print("Row number[{0:d}, {1:d}] out of range".format(src_row, dst_row))
            return False

        if not self.__checkColumn(src_column) or not self.__checkColumn(dst_column):
            print("Column number[{0:d}, {1:d}] out of range".format(src_column, dst_column))
            return False

        src_item = self.takeItem(src_row, src_column)
        src_widget = self.__copyWidget(self.cellWidget(src_row, src_column))

        dst_item = self.takeItem(dst_row, dst_column)
        dst_widget = self.__copyWidget(self.cellWidget(dst_row, dst_column))

        # Both CellWidget
        if isinstance(src_widget, QWidget) and isinstance(dst_widget, QWidget):
            self.removeCellWidget(src_row, src_column)
            self.removeCellWidget(dst_row, dst_column)
            self.setCellWidget(src_row, src_column, dst_widget)
            self.setCellWidget(dst_row, dst_column, src_widget)
        # Src is CellWidget dst is not
        elif isinstance(src_widget, QWidget) and not isinstance(dst_widget, QWidget):
            self.removeCellWidget(src_row, src_column)
            self.setCellWidget(dst_row, dst_column, src_widget)
            if isinstance(dst_item, QTableWidgetItem):
                self.setItem(src_row, src_column, dst_item)
        # Dst is CellWidget src is not
        elif isinstance(dst_widget, QWidget) and not isinstance(src_widget, QWidget):
            self.removeCellWidget(dst_row, dst_column)
            self.setCellWidget(src_row, src_column, dst_widget)
            if isinstance(src_item, QTableWidgetItem):
                self.setItem(dst_row, dst_column, src_item)
        else:
            if isinstance(dst_item, QTableWidgetItem):
                self.setItem(src_row, src_column, dst_item)

            if isinstance(src_item, QTableWidgetItem):
                self.setItem(dst_row, dst_column, src_item)

    def swapRow(self, src, dst):
        """Swap src and dst row data

        :param src: src row number
        :param dst: dst row number
        :return:
        """

        for column in range(self.columnCount()):
            self.swapItem(src, column, dst, column)

        # Select dst row
        self.selectRow(dst)
        self.tableDataChanged.emit()

    def swapColumn(self, src, dst):
        """Swap src and dst column data

        :param src: source column number
        :param dst: destination column number
        :return:
        """

        for row in range(self.rowCount()):
            self.swapItem(row, src, row, dst)

        # Select destination column
        self.selectColumn(dst)
        self.tableDataChanged.emit()

    def addRow(self, data, property_=None):
        """Add a row and set row property data

        :param data: row data should be a iterable object
        :param property_: row hidden property data
        :return:
        """

        if not hasattr(data, "__iter__"):
            print("TypeError: item should a iterable")
            return False

        if len(data) > self.columnCount():
            print("Item length too much")
            return False

        # Increase row count
        row = self.rowCount()
        self.setRowCount(row + 1)

        # Add data to row
        for column, item_data in enumerate(data):
            try:

                item = QTableWidgetItem(self.tr(str(item_data)))
                if property_:
                    try:
                        item.setData(Qt.UserRole, property_[column])
                    except (AttributeError, IndexError):
                        pass
                self.setItem(row, column, item)

                # Get column filters
                filters = self.__table_filters.get(column)
                if filters:
                    self.setItemDataFilter(row, column, filters)
                    self.setItemData(row, column, item_data)

            except ValueError as e:
                print("TableWidget addItem error: {}".format(e))
                continue

        # Select current item
        self.selectRow(row)

    def setRowHeader(self, data):
        if not hasattr(data, "__iter__"):
            print("TypeError: item should a iterable")
            return False

        if len(data) > self.rowCount():
            print("Item length too much")
            return False

        for row, text in enumerate(data):
            if not isinstance(text, str):
                continue
            self.takeVerticalHeaderItem(row)
            header = QTableWidgetItem(self.tr(text))
            self.setVerticalHeaderItem(row, header)

        self.hideRowHeader(False)

    def setColumnHeader(self, data):
        if not hasattr(data, "__iter__"):
            print("TypeError: item should a iterable")
            return False

        if len(data) > self.columnCount():
            print("Item length too much")
            return False

        for column, text in enumerate(data):
            if not isinstance(text, str):
                continue
            self.takeHorizontalHeaderItem(column)
            header = QTableWidgetItem(self.tr(text))
            self.setHorizontalHeaderItem(column, header)

        self.hideColumnHeader(False)

    def setRowAlignment(self, row, alignment):
        if not isinstance(alignment, Qt.AlignmentFlag):
            print("TypeError:{}".format(type(alignment)))
            return False

        if not self.__checkRow(row):
            return False

        for column in range(self.columnCount()):
            try:
                item = self.takeItem(row, column)
                item.setTextAlignment(alignment)
                self.setItem(row, column, item)
            except AttributeError:
                continue

        return True

    def setColumnAlignment(self, column, alignment):
        if not isinstance(alignment, Qt.AlignmentFlag):
            print("TypeError:{}".format(type(alignment)))
            return False

        if not self.__checkColumn(column):
            return False

        for row in range(self.rowCount()):
            try:
                item = self.takeItem(row, column)
                item.setTextAlignment(alignment)
                self.setItem(row, column, item)
            except AttributeError:
                continue

        return True

    def setTableAlignment(self, alignment):
        for row in range(self.rowCount()):
            if not self.setRowAlignment(row, alignment):
                return False

        return True

    def setItemData(self, row, column, data):
        if not self.__checkRow(row) or not self.__checkColumn(column):
            return False

        try:

            item = self.takeItem(row, column)
            widget = self.__copyWidget(self.cellWidget(row, column))

            if isinstance(widget, (QSpinBox, QDoubleSpinBox)) and isinstance(data, (int, float)):
                widget.setValue(data)
                widget.valueChanged.connect(self.__slotWidgetDataChanged)
                self.cellWidget(row, column).setHidden(True)
                self.removeCellWidget(row, column)
                self.setCellWidget(row, column, widget)
            elif isinstance(widget, QCheckBox) and isinstance(data, bool):
                widget.setChecked(data)
                widget.stateChanged.connect(self.__slotWidgetDataChanged)
                self.cellWidget(row, column).setHidden(True)
                self.removeCellWidget(row, column)
                self.setCellWidget(row, column, widget)
            elif isinstance(widget, QComboBox) and isinstance(data, int) and data < widget.count():
                widget.setCurrentIndex(data)
                widget.currentIndexChanged.connect(self.__slotWidgetDataChanged)
                self.cellWidget(row, column).setHidden(True)
                self.removeCellWidget(row, column)
                self.setCellWidget(row, column, widget)
            elif isinstance(widget, QDateTimeEdit) and isinstance(data, datetime):
                date = QDate(data.year, data.month, data.day)
                time = QTime(data.hour, data.minute, data.second)
                widget.setDateTime(QDateTime(date, time))
                widget.dateTimeChanged.connect(self.__slotWidgetDataChanged)
                self.removeCellWidget(row, column)
                self.setCellWidget(row, column, widget)
            elif isinstance(widget, QPushButton) and isinstance(data, object):
                widget.setProperty("private", data)
                self.removeCellWidget(row, column)
                self.setCellWidget(row, column, widget)
            elif isinstance(widget, QProgressBar) and isinstance(data, (int, float)):
                widget.setValue(data)
                self.removeCellWidget(row, column)
                self.setCellWidget(row, column, widget)
            elif isinstance(item, QTableWidgetItem) and isinstance(data, str):
                item.setText(self.tr(data))
                self.setItem(row, column, item)
            else:
                return False

            return True

        except Exception as e:
            print("Set table item data error:{}".format(e))
            return False

    def setItemDataFilter(self, row, column, filters):
        if not self.__checkRow(row) or not self.__checkColumn(column):
            return False

        try:

            if not isinstance(filters, (list, tuple, str)):
                return False

            # Normal text
            if isinstance(filters, str):
                widget = self.cellWidget(row, column)
                if isinstance(widget, QWidget):
                    self.cellWidget(row, column).setHidden(True)
                    self.removeCellWidget(row, column)
                item = QTableWidgetItem(filters)
                self.takeItem(row, column)
                self.setItem(row, column, item)
            # Number type QSpinbox(int, int) or QDoubleSpinbox(float, float) set spinbox range
            elif len(filters) == 2 and type(filters[0]) is type(filters[1]) and isinstance(filters[0], (int, float)):
                spinbox = QSpinBox() if isinstance(filters[0], int) else QDoubleSpinBox()
                spinbox.setRange(filters[0], filters[1])
                value = self.getItemData(row, column)
                value = str2number(value) if isinstance(filters[0], int) else str2float(value)
                spinbox.setValue(value)
                spinbox.valueChanged.connect(self.__slotWidgetDataChanged)
                self.takeItem(row, column)
                self.setCellWidget(row, column, spinbox)
            # Bool type QCheckBox(bool, "Desc text")
            elif len(filters) == 2 and isinstance(filters[0], bool) and isinstance(filters[1], str):
                widget = QCheckBox(self.tr(filters[1]))
                widget.stateChanged.connect(self.__slotWidgetDataChanged)
                widget.setChecked(filters[0])
                self.takeItem(row, column)
                self.setCellWidget(row, column, widget)
            # Datetime type QDatetimeEdit (datetime.datetime, python_datetime_format, qt_datetime_format)
            elif len(filters) == 3 and isinstance(filters[0], datetime) and isinstance(filters[2], str):
                try:
                    value = self.getItemData(row, column)
                    datetime.strptime(value, filters[1])
                    dt = QDateTime.fromString(value, filters[2])
                except (TypeError, ValueError):
                    dt = filters[0]
                    date = QDate(dt.year, dt.month, dt.day)
                    time = QTime(dt.hour, dt.minute, dt.second)
                    dt = QDateTime(date, time)

                widget = QDateTimeEdit(dt)
                widget.setCalendarPopup(True)
                widget.setProperty("format", filters[2])
                widget.dateTimeChanged.connect(self.__slotWidgetDataChanged)
                self.takeItem(row, column)
                self.setCellWidget(row, column, widget)
            # Self-defined type data QPushButton (button_text, callback, private_data)
            elif len(filters) == 3 and isinstance(filters[0], str) and hasattr(filters[1], "__call__"):
                button = QPushButton(self.tr(filters[0]))
                button.clicked.connect(filters[1])
                button.setProperty("clicked", filters[1])
                button.setProperty("private", filters[2])
                button.setProperty("dataChanged", self.__slotWidgetDataChanged)
                self.takeItem(row, column)
                self.setCellWidget(row, column, button)
            # Label with color
            elif len(filters) == 2 and isinstance(filters[0], str) and isinstance(filters[1], QColor):
                item = QTableWidgetItem(filters[0])
                item.setBackground(QBrush(filters[1]))
                item.setTextAlignment(Qt.AlignCenter)
                self.takeItem(row, column)
                self.setItem(row, column, item)
                self.frozenItem(row, column, True)
            # Progress bar
            elif len(filters) == 3 and isinstance(filters[0], QProgressBar) and isinstance(filters[1], bool) \
                    and isinstance(filters[1], (int, float)):
                progress = QProgressBar()
                progress.setValue(filters[2])
                progress.setTextVisible(filters[1])
                self.takeItem(row, column)
                self.setCellWidget(row, column, progress)
            # QComboBox (list) or tuple
            elif isinstance(filters, (list, tuple)):
                widget = QComboBox()
                widget.addItems(filters)
                value = self.getItemData(row, column)
                try:
                    value = int(value)
                except ValueError:
                    value = filters.index(value) if value in filters else 0
                    widget.setProperty("format", "text")
                widget.setCurrentIndex(value)
                widget.currentIndexChanged.connect(self.__slotWidgetDataChanged)
                self.takeItem(row, column)
                self.setCellWidget(row, column, widget)
            else:
                return False

            return True

        except Exception as e:
            print("Set table item filter error:{}".format(e))
            return False

    def setRowData(self, row, data):
        try:
            if len(data) != self.colorCount() or not 0 <= row < self.rowCount():
                return False

            for column, item_data in enumerate(data):
                self.setItemData(row, column, item_data)
        except TypeError:
            return False

    def setRowDataFilter(self, row, filters):
        for column in range(self.columnCount()):
            if not self.setItemDataFilter(row, column, filters):
                return False

        return True

    def setColumnData(self, column, data):
        try:
            if len(data) != self.rowCount() or not 0 <= column < self.colorCount():
                return False

            for row, item_data in enumerate(data):
                self.setItemData(row, column, item_data)
        except TypeError:
            return False

    def setColumnDataFilter(self, column, filters):
        for row in range(self.rowCount()):
            if not self.setItemDataFilter(row, column, filters):
                return False

        return True

    def setTableDataFilter(self, filters):
        if not isinstance(filters, dict):
            return False

        self.__table_filters = filters
        return True

    def getItemData(self, row, column):
        if not self.__checkRow(row) or not self.__checkColumn(column):
            return None

        item = self.item(row, column)
        widget = self.cellWidget(row, column)
        if isinstance(widget, QSpinBox):
            return widget.value()
        elif isinstance(widget, QDoubleSpinBox):
            return widget.value()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QComboBox):
            return widget.currentText() if widget.property("format") else widget.currentIndex()
        elif isinstance(widget, QDateTimeEdit):
            return widget.dateTime().toString(widget.property("format"))
        elif isinstance(widget, QPushButton):
            return widget.property("private")
        elif isinstance(widget, QProgressBar):
            return widget.value()
        elif isinstance(item, QTableWidgetItem):
            return item.text()
        else:
            return ""

    def getItemProperty(self, row, column):
        if not self.__checkRow(row) or not self.__checkColumn(column):
            return None

        item = self.item(row, column)
        return item.data(Qt.UserRole) if isinstance(item, QTableWidgetItem) else None

    def getRowData(self, row):
        return [self.getItemData(row, column) for column in range(self.columnCount())]

    def getRowProperty(self, row):
        return [self.getItemProperty(row, column) for column in range(self.columnCount())]

    def getColumnData(self, column):
        return [self.getItemData(row, column) for row in range(self.rowCount())]

    def getColumnProperty(self, column):
        return [self.getItemProperty(row, column) for row in range(self.rowCount())]

    def getTableData(self):
        return [self.getRowData(row) for row in range(self.rowCount())]

    def getTableProperty(self):
        return [self.getRowProperty(row) for row in range(self.rowCount())]


class ListWidget(QListWidget):
    def __init__(self, unique=False, markColor=QColor(51, 153, 255), parent=None):
        super(ListWidget, self).__init__(parent)

        self.__unique = unique
        if isinstance(markColor, (QColor, Qt.GlobalColor)):
            self.__markColor = markColor
        else:
            self.__markColor = QColor(51, 153, 255)

    def __setItemBackground(self, index, background):
        if not isinstance(index, int) or not isinstance(background, QBrush):
            return False

        item = self.takeItem(index)
        if not isinstance(item, QListWidgetItem):
            return False

        item.setBackground(background)
        self.insertItem(index, item)
        return True

    def __setItemForeground(self, index, foreground):
        if not isinstance(index, int) or not isinstance(foreground, QBrush):
            return False

        item = self.takeItem(index)
        if not isinstance(item, QListWidgetItem):
            return False

        item.setForeground(foreground)
        self.insertItem(index, item)
        return True

    @Slot(object)
    def markItem(self, item, background=True):
        """Mark item background or foreground with different color

        :param item: witch item to marked
        :param background: if background set will mark background else foreground
        :return: success, return true else false
        """
        if not isinstance(item, QListWidgetItem):
            return False

        markItem = self.__setItemBackground if background else self.__setItemForeground

        # Get item row
        row = self.row(item)

        if row < 0 or row >= self.count():
            return False

        brush = QBrush(QColor(self.__markColor))

        # Clear old mark
        for index in range(self.count()):

            if background and self.item(index).background() == brush:
                self.__setItemBackground(index, QListWidgetItem("").background())
                break
            elif not background and self.item(index).foreground() == brush:
                self.__setItemForeground(index, QListWidgetItem("").foreground())
                break

        markItem(row, brush)
        self.setCurrentRow(row)
        return True

    def getMarkedItem(self, background=True):
        """Get marked item text

        :param background: if set will return marked background item text else foreground item text
        :return:
        """
        for index in range(self.count()):
            item = self.item(index)
            if not isinstance(item, QListWidgetItem):
                continue

            if background and item.background() == self.__markColor:
                return item.text()
            elif not background and item.foreground() == self.__markColor:
                return item.text()

        return None

    def addItem(self, name, data=None):
        if not isinstance(name, str):
            print("TypeError: {}".format(type(name)))
            return False

        if self.__unique and name in self.getItems():
            print("Same name item is exist")
            return False

        item = QListWidgetItem(name)
        if data is not None:
            item.setData(Qt.UserRole, data)

        super(ListWidget, self).addItem(item)
        self.setCurrentItem(item)
        return True

    def setItems(self, items):
        if not isinstance(items, (list, tuple)):
            print("Items data type error:{}".format(type(items)))
            return False

        # Remove old items
        self.clearItems()

        # Add items data to ListWidget
        for data in items:
            if isinstance(data, (tuple, list)) and len(data) == 2 and isinstance(data[0], str):
                self.addItem(data[0], data[1])
            elif isinstance(data, str):
                self.addItem(data)
            else:
                continue

        return True

    def clearItems(self):
        for _ in range(self.count()):
            item = self.takeItem(0)
            self.removeItemWidget(item)

    def getItems(self):
        return [self.item(i).text() for i in range(self.count())]

    def getItemsData(self):
        return [self.item(i).data(Qt.UserRole) for i in range(self.count())]


class SerialPortSettingWidget(QWidget):
    # Options
    OPTIONS = {

        "baudrate": {

            "text": "波特率",
            "values": Serial.BAUDRATES
        },

        "bytesize": {

            "text": "数据位",
            "values": Serial.BYTESIZES
        },

        "parity": {

            "text": "校验位",
            "values": Serial.PARITIES
        },

        "stopbits": {

            "text": "停止位",
            "values": Serial.STOPBITS
        },

        "timeout": {

            "text": "超时（ms）",
            "values": [0, 9999]
        }
    }
    ALL_OPTIONS = ("baudrate", "bytesize", "parity", "stopbits", "timeout")
    DEFAULTS = {"baudrate": 9600, "bytesize": 8, "parity": "N", "stopbits": 1, "timeout": 0}

    def __init__(self, settings=DEFAULTS, parent=None):
        """Serial port configure dialog

        :param settings: serial port settings
        :param parent:
        """
        settings = settings or self.DEFAULTS
        super(SerialPortSettingWidget, self).__init__(parent)

        layout = QGridLayout()

        # If specified port select it
        port = SerialPortSelector()
        port.setProperty("name", "port")
        select_port = settings.get("port")
        if select_port is not None:
            port.setSelectedPort(select_port)

        # Add port to dialog
        layout.addWidget(QLabel(self.tr("串口")), 0, 0)
        layout.addWidget(port, 0, 1)

        # If specified it add option to dialog
        for index, option in enumerate(self.ALL_OPTIONS):
            if option not in settings:
                continue

            # Get option settings
            value = settings.get(option)
            text = self.OPTIONS.get(option).get("text")
            values = self.OPTIONS.get(option).get("values")

            # Create option element
            element = QComboBox() if isinstance(values, tuple) else QSpinBox()
            if isinstance(element, QComboBox):
                # If user settings is invalid then using default settings
                value = self.DEFAULTS.get(option) if value not in values else value
                for v in values:
                    element.addItem(str(v), v)
                element.setCurrentIndex(values.index(value))
            else:
                element.setRange(values[0], values[1])
                element.setValue(value)

            # Set option property
            label = QLabel(self.tr(text))
            element.setProperty("name", option)

            # Layout direction setting
            layout.addWidget(label, index + 1, 0)
            layout.addWidget(element, index + 1, 1)

        self.setLayout(layout)
        self.__uiManager = ComponentManager(layout)

    def getSetting(self):
        settings = dict()
        for item in self.__uiManager.findKey("name"):
            if isinstance(item, QComboBox):
                value = item.property("name")
                if value == "port" and item.currentIndex() == 0:
                    settings[value] = None
                else:
                    settings[value] = item.itemData(item.currentIndex())
            elif isinstance(item, QSpinBox):
                settings[item.property("name")] = item.value()

        return settings


class BasicJsonSettingWidget(QWidget):
    settingChanged = Signal()

    def __init__(self, settings, parent=None):
        super(BasicJsonSettingWidget, self).__init__(parent)

        if not isinstance(settings, DynamicObject):
            raise TypeError("settings require {!r}".format(DynamicObject.__name__))

        try:
            layout = settings.layout
            self.settings = settings.dict
            self.settings_cls = settings.__class__
            self.layout = layout if isinstance(layout, UiLayout) else UiLayout(**layout)
            if not self.layout.check_layout(self.settings):
                raise ValueError("layout error")
        except AttributeError:
            raise ValueError("Do not found layout settings")
        except (json.JSONDecodeError, DynamicObjectDecodeError):
            raise TypeError("settings.layout must be {!r}".format(UiLayout.__name__))

    def getData(self):
        pass

    def setData(self, data):
        pass

    def resetDefaultData(self):
        pass

    def slotSettingChanged(self):
        pass


class JsonSettingWidget(BasicJsonSettingWidget):
    def __init__(self, settings, data=None, parent=None):
        super(JsonSettingWidget, self).__init__(settings, parent)

        # Convert layout to grid layout
        self.layout = self.layout.get_grid_layout(self.settings)

        self.__initUi()
        self.__initData(data)
        self.__initSignalAndSlots()

    def __initUi(self):
        row = 0
        layout = QGridLayout()
        for items in self.layout:
            column = 0
            for item in items:
                try:
                    dict_ = self.settings.get(item)
                    ui_input = UiInputSetting(**dict_)
                    widget = self.createInputWidget(ui_input, item)
                    if isinstance(widget, QWidget):
                        # Add label and widget
                        if ui_input.label_left:
                            layout.addWidget(QLabel(self.tr(ui_input.get_name())), row, column)
                            column += 1
                            layout.addWidget(widget, row, column)
                            column += 1
                        else:
                            widget.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding))
                            layout.addWidget(widget, row, column)
                            column += 1
                            layout.addWidget(QLabel(self.tr(ui_input.get_name())), row, column)
                            column += 1

                        # QLine edit special process re check
                        if isinstance(widget, QLineEdit):
                            widget.textChanged.connect(self.slotSettingChanged)
                    elif isinstance(widget, QLayout):
                        # Add label and layout
                        layout.addWidget(QLabel(self.tr(ui_input.get_name())), row, column)
                        column += 1
                        layout.addLayout(widget, row, column)
                        column += 1
                except (TypeError, ValueError, IndexError, json.JSONDecodeError, DynamicObjectDecodeError) as err:
                    print("{}".format(err))

            row += 1
        self.setLayout(layout)
        self.ui_manager = ComponentManager(layout)
        self.ui_manager.dataChanged.connect(self.slotSettingChanged)

    def __initData(self, data):
        self.setData(data)

    def __initSignalAndSlots(self):
        for button in self.ui_manager.findValue("clicked", "file", QPushButton):
            if isinstance(button, QPushButton):
                button.clicked.connect(self.slotSelectFile)

        for button in self.ui_manager.findValue("clicked", "font", QPushButton):
            if isinstance(button, QPushButton):
                button.clicked.connect(self.slotSelectFont)
                preview = self.ui_manager.getPrevSibling(button)
                if isinstance(preview, QLineEdit):
                    preview.textChanged.connect(self.slotPreviewFont)

        for button in self.ui_manager.findValue("clicked", "color", QPushButton):
            if isinstance(button, QPushButton):
                button.clicked.connect(self.slotSelectColor)
                preview = self.ui_manager.getPrevSibling(button)
                if isinstance(preview, QLineEdit):
                    preview.textChanged.connect(self.slotPreviewColor)

    def getSettings(self):
        data = self.getData()
        settings = self.settings
        for k, v in data.items():
            settings[k]["data"] = v
        return self.settings_cls(**settings)

    def getData(self):
        return self.ui_manager.getData("data")

    def setData(self, data):
        font_inputs = self.ui_manager.findValue("clicked", "font", QPushButton)
        color_inputs = self.ui_manager.findValue("clicked", "color", QPushButton)
        for button in font_inputs + color_inputs:
            if isinstance(button, QPushButton):
                preview = self.ui_manager.getPrevSibling(button)
                if isinstance(preview, QLineEdit) and data:
                    button.setProperty("private", "{}".format(data.get(preview.property("data"))))

        return self.ui_manager.setData("data", data)

    def resetDefaultData(self):
        data = dict()
        for key in self.getData().keys():
            data[key] = self.settings[key]["default"]
        self.ui_manager.setData("data", data)

    def slotSelectFile(self):
        sender = self.sender()
        file_format = " ".join(sender.property("private") or list())
        title = self.tr("请选择{}".format(sender.property("title")))
        path, ret = QFileDialog.getOpenFileName(self, title, "", self.tr(file_format))
        if not ret or not os.path.isfile(path):
            return

        path_edit = self.ui_manager.getPrevSibling(sender)
        if isinstance(path_edit, QLineEdit):
            path_edit.setText(path)

    def slotSelectFont(self):
        sender = self.sender()
        if not isinstance(sender, QPushButton):
            return
        title = self.tr("请选择{}".format(sender.property("title")))
        font_name, point_size, weight = UiFontInput.get_font(sender.property("private"))
        font, selected = QFontDialog.getFont(QFont(font_name, point_size, weight), self, title)
        if not selected or not isinstance(font, QFont):
            return

        font_edit = self.ui_manager.getPrevSibling(sender)
        if isinstance(font_edit, QLineEdit):
            font_setting = font.rawName(), font.pointSize(), font.weight()
            sender.setProperty("private", "{}".format(font_setting))
            font_edit.setText("{}".format(font_setting))

    def slotPreviewFont(self):
        sender = self.sender()
        if not isinstance(sender, QLineEdit):
            return

        font_setting = sender.text()
        sender.setStyleSheet(UiFontInput.get_stylesheet(font_setting))

    def slotSelectColor(self):
        sender = self.sender()
        title = self.tr("请选择{}".format(sender.property("title")))
        r, g, b = UiColorInput.get_color(sender.property("private"))
        color = QColorDialog.getColor(QColor(r, g, b), self, title)
        if not isinstance(color, QColor):
            return

        color_edit = self.ui_manager.getPrevSibling(sender)
        if isinstance(color_edit, QLineEdit):
            rgb = color.red(), color.green(), color.blue()
            sender.setProperty("private", "{}".format(rgb))
            color_edit.setText("{}".format(rgb))

    def slotPreviewColor(self):
        sender = self.sender()
        if not isinstance(sender, QLineEdit):
            return

        color = sender.text()
        sender.setStyleSheet("background-color: rgb{}; color: rgb{};".format(color, color))

    def slotSettingChanged(self):
        self.settingChanged.emit()

        sender = self.sender()
        # Line edit text content check
        if isinstance(sender, QLineEdit):
            filters = sender.property("filter")
            try:
                re.search(filters, sender.text(), re.S).group(0)
                sender.setStyleSheet("color: rgb(0, 0, 0);")
            except AttributeError:
                sender.setStyleSheet("color: rgb(255, 0, 0);")

    @staticmethod
    def createInputWidget(setting, name=None):
        if not isinstance(setting, UiInputSetting):
            return None

        try:
            widget = None

            if setting.is_int_type():
                widget = QSpinBox()
                widget.setValue(setting.get_data())
                widget.setMinimum(setting.get_check()[0])
                widget.setMaximum(setting.get_check()[1])
                widget.setSingleStep(setting.get_check()[2])
            elif setting.is_bool_type():
                widget = QCheckBox()
                widget.setCheckable(True)
                widget.setChecked(setting.get_data())
            elif setting.is_text_type():
                widget = QLineEdit()
                widget.setText(setting.get_data())
                widget.setPlaceholderText(setting.get_default())
                # Set regular expression and max length
                widget.setProperty("filter", setting.check[0])
                widget.setMaxLength(setting.check[1])
            elif setting.is_float_type():
                widget = QDoubleSpinBox()
                widget.setValue(setting.get_data())
                widget.setMinimum(setting.get_check()[0])
                widget.setMaximum(setting.get_check()[1])
                widget.setSingleStep(setting.get_check()[2])
            elif setting.is_select_type():
                widget = QComboBox()
                widget.addItems(setting.get_check())
                widget.setProperty("format", "text")
                widget.setCurrentIndex(setting.get_check().index(setting.get_data()))
            elif setting.is_serial_type():
                widget = SerialPortSelector()
                widget.setProperty("format", "text")
                widget.setCurrentIndex([widget.itemText(i) for i in range(widget.count())].index(setting.get_data()))
            elif setting.is_file_type():
                widget = QLineEdit()
                widget.setReadOnly(True)
                widget.setProperty("data", name)
                widget.setText(setting.get_data())
                button = QPushButton("请选择文件")
                button.setProperty("clicked", "file")
                button.setProperty("title", setting.get_name())
                button.setProperty("private", setting.get_check())
                layout = QHBoxLayout()
                layout.addWidget(widget)
                layout.addWidget(button)
                return layout
            elif setting.is_font_type():
                widget = QLineEdit()
                widget.setReadOnly(True)
                widget.setProperty("data", name)
                widget.setText(setting.get_data())
                widget.setStyleSheet(UiFontInput.get_stylesheet(setting.get_data()))
                button = QPushButton("请选择字体")
                button.setProperty("clicked", "font")
                button.setProperty("title", setting.get_name())
                button.setProperty("private", setting.get_data())
                layout = QHBoxLayout()
                layout.addWidget(widget)
                layout.addWidget(button)
                return layout
            elif setting.is_color_type():
                color = setting.get_data()
                widget = QLineEdit()
                widget.setReadOnly(True)
                widget.setProperty("data", name)
                widget.setText("{}".format(setting.get_data()))
                widget.setStyleSheet("background-color: rgb{}; color: rgb{};".format(color, color))
                button = QPushButton("请选择颜色")
                button.setProperty("clicked", "color")
                button.setProperty("title", setting.get_name())
                button.setProperty("private", setting.get_data())
                layout = QHBoxLayout()
                layout.addWidget(widget)
                layout.addWidget(button)
                return layout
        except (IndexError, ValueError):
            pass

        # Set property for ComponentManager get data
        if isinstance(name, str) and isinstance(widget, QWidget):
            widget.setProperty("data", name)

        # Set readonly option
        if setting.is_readonly():
            widget.setDisabled(True)

        return widget


class MultiJsonSettingsWidget(BasicJsonSettingWidget):
    def __init__(self, settings, data, parent=None):
        super(MultiJsonSettingsWidget, self).__init__(settings, parent)

        if not isinstance(data, (list, tuple)):
            raise TypeError("data require a list or tuple not {!r}".format(data.__class__.__name__))

        self.frozen_columns = list()
        self.layout = self.layout.get_vertical_layout(self.settings)

        self.__initUi()
        self.__initData(data)
        self.__initStyleSheet()
        self.ui_table.tableDataChanged.connect(self.slotSettingChanged)

    def __initUi(self):
        try:
            columns_header = [self.settings.get(x).name for x in self.layout]
        except AttributeError:
            columns_header = [self.settings.get(x).get("name") for x in self.layout]
        self.ui_table = TableWidget(len(columns_header))
        self.ui_table.setColumnHeader(columns_header)
        self.ui_table.setRowSelectMode()

        table_filters = dict()
        for column, item in enumerate(self.layout):
            try:

                dict_ = self.settings.get(item)
                ui_input = dict_ if isinstance(dict_, UiInputSetting) else UiInputSetting(**dict_)

                if ui_input.is_bool_type():
                    table_filters[column] = (ui_input.get_default(), ui_input.get_name())
                elif ui_input.is_int_type() or ui_input.is_float_type():
                    table_filters[column] = ui_input.get_check()[:2]
                elif ui_input.is_select_type():
                    table_filters[column] = ui_input.get_check()
                elif ui_input.is_file_type():
                    table_filters[column] = ("请选择文件", self.slotSelectFile, ui_input.get_check())

                if ui_input.is_readonly():
                    self.frozen_columns.append(column)
            except (TypeError, ValueError, json.JSONDecodeError, DynamicObjectDecodeError) as err:
                print("{}".format(err))

        # Set table filters
        self.ui_table.setTableDataFilter(table_filters)

        layout = QVBoxLayout()
        layout.addWidget(self.ui_table)
        self.setLayout(layout)

    def __initData(self, data):
        self.ui_table.setRowCount(0)
        # Add data to table
        for item in data:
            self.ui_table.addRow(item)

        # Frozen table readonly column
        for column in self.frozen_columns:
            self.ui_table.frozenColumn(column, True)

        # Move to first row
        self.ui_table.selectRow(0)

    def __initStyleSheet(self):
        total_width = 75
        for column in range(self.ui_table.columnCount()):
            total_width += self.ui_table.columnWidth(column)

        self.setMinimumWidth(total_width)

    def getData(self):
        return self.ui_table.getTableData()

    def setData(self, data):
        self.__initData(data)

    def resetDefaultData(self):
        try:
            data = [self.settings.get(k).default for k in self.layout]
        except AttributeError:
            data = [self.settings.get(k).get("default") for k in self.layout]

        self.setData([data for _ in range(self.ui_table.rowCount())])

    def slotSelectFile(self):
        sender = self.sender()
        file_format = "*"
        path, ret = QFileDialog.getOpenFileName(self, self.tr("请选择文件"), "", self.tr(file_format))
        if not ret or not os.path.isfile(path):
            return

        sender.setProperty("private", path)

    def slotSettingChanged(self):
        self.settingChanged.emit()

        sender = self.sender()
        # Line edit text content check
        if isinstance(sender, QLineEdit):
            filters = sender.property("filter")
            try:
                re.search(filters, sender.text(), re.S).group(0)
                sender.setStyleSheet("color: rgb(0, 0, 0);")
            except AttributeError:
                sender.setStyleSheet("color: rgb(255, 0, 0);")


class MultiGroupJsonSettingsWidget(BasicJsonSettingWidget):
    def __init__(self, settings, data, parent=None):
        super(MultiGroupJsonSettingsWidget, self).__init__(settings, parent)

        if not isinstance(data, dict):
            raise TypeError("data require a dict not {!r}".format(data.__class__.__name__))

        self.widget_list = list()
        self.layout = self.layout.get_vertical_layout(self.settings)

        self.__initUi()
        self.__initData(data)
        self.__initSignalAndSlots()

    def __initUi(self):
        widget_layout = QVBoxLayout()
        for group in self.layout:
            try:
                group_settings = self.settings.get(group)
                group_settings = group_settings if isinstance(group_settings, UiLayout) else UiLayout(**group_settings)
                if not group_settings.check_layout(self.settings):
                    continue

                box = QGroupBox()
                group_layout = QVBoxLayout()
                box.setTitle(group_settings.get_name())
                settings = {"layout": group_settings}
                for item_name in group_settings.get_layout():
                    settings[item_name] = self.settings.get(item_name)

                box_widget = JsonSettingWidget(DynamicObject(**settings))
                box_widget.setProperty("name", group_settings.get_name())
                group_layout.addWidget(box_widget)
                box.setLayout(group_layout)
                widget_layout.addWidget(box)
                self.widget_list.append(box_widget)
            except (TypeError, ValueError, IndexError, json.JSONDecodeError, DynamicObjectDecodeError) as err:
                print("{}".format(err))

        self.setLayout(widget_layout)

    def __initData(self, data):
        self.setData(data)

    def __initSignalAndSlots(self):
        [widget.settingChanged.connect(self.slotSettingChanged) for widget in self.widget_list]

    def getData(self):
        data = dict()
        [data.update(widget.getData()) for widget in self.widget_list]
        return data

    def setData(self, data):
        return set([widget.setData(data) for widget in self.widget_list]) == {True}

    def getSettings(self):
        data = self.getData()
        settings = self.settings
        for k, v in data.items():
            settings[k]["data"] = v
        return self.settings_cls(**settings)

    def resetDefaultData(self):
        [widget.resetDefaultData() for widget in self.widget_list]

    def slotSettingChanged(self):
        self.settingChanged.emit()


class MultiTabJsonSettingsWidget(QTabWidget):
    settingChanged = Signal()

    def __init__(self, settings, data, parent=None):
        super(MultiTabJsonSettingsWidget, self).__init__(parent)

        if not isinstance(settings, DynamicObject):
            raise TypeError("settings require {!r} not {!r}".format(
                DynamicObject.__name__, settings.__class__.__name__))

        if not isinstance(data, dict):
            raise TypeError("data require {!r} not {!r}".format(dict.__name__, data.__class__.__name__))

        try:
            layout = settings.layout
            self.settings = settings.dict
            self.settings_cls = settings.__class__
            self.layout = layout if isinstance(layout, UiLayout) else UiLayout(**layout)
            if not self.layout.check_layout(self.settings):
                raise ValueError("tabs layout error!")
        except AttributeError:
            raise ValueError("Do not found tabs settings")
        except (json.JSONDecodeError, DynamicObjectDecodeError):
            raise TypeError("settings.tabs must be {!r}".format(UiLayout.__name__))

        # Widget list for set/get data using
        self.widget_list = list()
        self.__initUi()
        self.__initData(data)
        self.__initSignalAndSlots()

    def __initUi(self):
        # Init tabs and group
        for tab in self.layout.get_layout():
            try:
                tab_widget = QWidget()
                tab_layout = QVBoxLayout()
                tab_setting = self.settings.get(tab)
                tab_setting = tab_setting if isinstance(tab_setting, UiLayout) else UiLayout(**tab_setting)
                if not tab_setting.check_layout(self.settings):
                    continue

                settings = {"layout": tab_setting}
                for group in tab_setting.get_layout():
                    group_setting = self.settings.get(group)
                    group_setting = group_setting if isinstance(group_setting, UiLayout) else UiLayout(**group_setting)
                    if not group_setting.check_layout(self.settings):
                        continue

                    settings[group] = group_setting
                    for item in group_setting.get_layout():
                        settings[item] = self.settings.get(item)

                widget = MultiGroupJsonSettingsWidget(DynamicObject(**settings), dict())
                self.widget_list.append(widget)
                tab_layout.addWidget(widget)
                tab_widget.setLayout(tab_layout)
                if tab_layout.count() >= 2:
                    self.insertTab(self.count(), tab_widget, tab_setting.name)
                else:
                    self.insertTab(self.count(), widget, tab_setting.name)
            except (TypeError, ValueError, IndexError, json.JSONDecodeError, DynamicObjectDecodeError) as err:
                print("{}".format(err))

    def __initData(self, data):
        self.setData(data)

    def __initSignalAndSlots(self):
        [widget.settingChanged.connect(self.slotSettingChanged) for widget in self.widget_list]

    def getData(self):
        data = dict()
        [data.update(widget.getData()) for widget in self.widget_list]
        return data

    def setData(self, data):
        return set([widget.setData(data) for widget in self.widget_list]) == {True}

    def getSettings(self):
        data = self.getData()
        settings = self.settings
        for k, v in data.items():
            settings[k]["data"] = v
        return self.settings_cls(**settings)

    def resetDefaultData(self):
        [widget.resetDefaultData() for widget in self.widget_list]

    def slotSettingChanged(self):
        self.settingChanged.emit()

    def getWidgetManager(self, name):
        for widget in self.widget_list:
            if widget.property("name") == name:
                return widget.ui_manager

        return None


class LogMessageWidget(QTextEdit):
    LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, filename, log_format="%(asctime)s %(levelname)s %(message)s", parent=None):
        super(LogMessageWidget, self).__init__(parent)

        self.logger = False
        self.setReadOnly(True)
        self.logFilename = filename
        self.startTime = datetime.now()
        self.textChanged.connect(self.slotAutoScroll)
        logging.basicConfig(filename=filename, format=log_format, level=logging.DEBUG)

    @Slot(object)
    def logging(self, message, write_to_log=True):
        if not isinstance(message, UiLogMessage):
            return

        # Show log
        self.append("<font color='{}' size={}>{}: {}</font>".format(
            message.color, message.font_size, logging.getLevelName(message.level), message.content)
        )

        # Write to log file if write_to_log set
        write_to_log and logging.log(message.level, message.content)

    @Slot(object)
    def filterLog(self, levels):
        # First read all log to memory
        with open(self.logFilename) as fp:
                text = fp.read()

        # Process data
        valid_record = list()
        for level in levels:

            level_name = logging.getLevelName(level)

            for record in text.split("\n"):
                record.strip()
                time_end = record.find(",")
                time_str = record[:time_end]

                try:
                    record_time = datetime.strptime(time_str, self.LOG_TIME_FORMAT)
                    record_time = record_time.replace(microsecond=int(record[time_end + 1: time_end + 4]) * 1000)
                except ValueError:
                    continue

                if record_time < self.startTime:
                    continue

                level_name_start = record.find(level_name)
                if level_name_start == -1:
                    continue

                # Append to record list
                valid_record.append(UiLogMessage.genDefaultMessage(record[level_name_start + len(level_name):], level))

        # Append to browser
        self.clear()
        for record in valid_record:
            self.logging(record, False)

    def slotAutoScroll(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
