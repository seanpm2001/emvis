
import os
import PyQt5.QtWidgets as qtw
from PyQt5.QtGui import QImage

import datavis as dv

from ._box import ImageBox
from ..utils import MOVIE_SIZE, getHighlighterClass, EmPath, ImageManager
from ..models import ModelsFactory


class EmBrowser(dv.widgets.FileBrowser):
    """ """
    def __init__(self, **kwargs):
        """
        Creates a EmBrowser instance
        Keyword Args:
            textLines: The first and last lines to be shown in text file preview
            :class:`FileBrowser <dv.widgets.FileBrowser>` params
        """
        self._lines = kwargs.get('textLines', 100)

        dv.widgets.FileBrowser.__init__(self, **kwargs)

        self._dataView.sigCurrentTableChanged.connect(
            self.__onDataViewTableChanged)

        self.updateViewPanel()

    def __onDataViewTableChanged(self):
        model = self._dataView.getModel()
        if model is not None:
            info = dict()
            info["Type"] = "TABLE"
            dimTuple = (model.totalRowCount(), model.columnCount())
            info["Dimensions (Rows x Columns)"] = "%d x %d" % dimTuple
            self.__showInfo(info)

    def __showMsgBox(self, text, icon=None, details=None):
        """
        Show a message box with the given text, icon and details.
        The icon of the message box can be specified with one of the Qt values:
            QMessageBox.NoIcon
            QMessageBox.Question
            QMessageBox.Information
            QMessageBox.Warning
            QMessageBox.Critical
        """
        msgBox = qtw.QMessageBox()
        msgBox.setText(text)
        msgBox.setStandardButtons(qtw.QMessageBox.Ok)
        msgBox.setDefaultButton(qtw.QMessageBox.Ok)
        if icon is not None:
            msgBox.setIcon(icon)
        if details is not None:
            msgBox.setDetailedText(details)

        msgBox.exec_()

    def __showInfo(self, info):
        """
        Show the information in the corresponding widget.
        info is a dict
        """
        self.__clearInfoWidget()
        if isinstance(info, dict):
            for key in info.keys():
                self._infoWidget.addItem("%s: %s" % (str(key).capitalize(),
                                                     str(info[key])))

    def __clearInfoWidget(self):
        """ Clear the info widget """
        self._infoWidget.clear()

    def __showVolumeSlice(self):
        """Show the Volume Slicer component"""
        self._stackLayout.setCurrentWidget(self._volumeView)

    def __showDataView(self):
        """Show the Table View component"""
        self._stackLayout.setCurrentWidget(self._dataView)

    def __showImageView(self):
        """ Show the dv.views.ImageView component """
        self._stackLayout.setCurrentWidget(self._imageView)

    def __showSlicesView(self):
        """ Show the dv.views.SlicesView component """
        self._stackLayout.setCurrentWidget(self._slicesView)

    def __showTextView(self):
        """ Show the TextView component """
        self._stackLayout.setCurrentWidget(self._textView)

    def __showBoxWidget(self):
        """ Show the ImageBox component """
        self._stackLayout.setCurrentWidget(self._box)

    def __showEmptyWidget(self):
        """ Show an empty widget"""
        self._stackLayout.setCurrentWidget(self._emptyWidget)

    def _createViewPanel(self, **kwargs):
        viewPanel = qtw.QWidget(self)
        kwargs['parent'] = viewPanel
        self._dataView = dv.views.DataView(dv.models.EmptyTableModel(),
                                           **kwargs)

        self._imageView = dv.views.ImageView(**kwargs)

        self._slicesView = dv.views.SlicesView(dv.models.EmptySlicesModel(),
                                               **kwargs)

        self._volumeView = dv.views.VolumeView(dv.models.EmptyVolumeModel(),
                                               **kwargs)

        self._textView = dv.widgets.TextView(viewPanel, True)

        self._box = ImageBox(parent=viewPanel)

        self._emptyWidget = qtw.QWidget(parent=viewPanel)

        layout = qtw.QHBoxLayout(viewPanel)
        self._stackLayout = qtw.QStackedLayout(layout)
        self._stackLayout.addWidget(self._volumeView)
        self._stackLayout.addWidget(self._dataView)
        self._stackLayout.addWidget(self._imageView)
        self._stackLayout.addWidget(self._slicesView)
        self._stackLayout.addWidget(self._textView)
        self._stackLayout.addWidget(self._emptyWidget)
        self._stackLayout.addWidget(self._box)

        return viewPanel

    def _createInfoPanel(self, **kwargs):
        self._infoWidget = qtw.QListWidget(self)
        return self._infoWidget

    def showFile(self, imagePath):
        """
        This method display an image using of pyqtgraph dv.views.ImageView,
        a volume using the VOLUME-SLICER or dv.views.GALLERY-VIEW components,
        a image stack or
        a Table characteristics.

        pageBar provides:

        1. A zoomable region for displaying the image
        2. A combination histogram and gradient editor (HistogramLUTItem) for
           controlling the visual appearance of the image
        3. Tools for very basic analysis of image data (see ROI and Norm
           buttons)

        :param imagePath: the image path
        """
        try:
            info = {'Type': 'UNKNOWN'}
            if EmPath.isTable(imagePath):
                model = ModelsFactory.createTableModel(imagePath)
                self._dataView.setModel(model)
                if not model.getRowsCount() == 1:
                    self._dataView.setView(dv.views.COLUMNS)
                else:
                    self._dataView.setView(dv.views.ITEMS)

                self.__showDataView()
                # Show the Table dimensions
                info['Type'] = 'TABLE'
                dimStr = "%d x %d" % (model.getRowsCount(),
                                      model.getColumnsCount())
                info['Dimensions (Rows x Columns)'] = dimStr
            elif EmPath.isStandardImage(imagePath):
                image = QImage(imagePath)
                self._box.setImage(image)
                info['dim'] = (image.width(), image.height())
                info['ext'] = EmPath.getExt(imagePath)
                info['Type'] = 'STANDARD-IMAGE'
                self.__showBoxWidget()
                self._box.fitToSize()
            elif EmPath.isData(imagePath):
                info = ImageManager().getInfo(imagePath)
                d = info['dim']
                if d.n == 1:  # Single image or volume
                    if d.z == 1:  # Single image
                        model = ModelsFactory.createImageModel(imagePath)
                        self._imageView.setModel(model)
                        self._imageView.setImageInfo(
                            path=imagePath, format=info['ext'],
                            data_type=str(info['data_type']))
                        info['Type'] = 'SINGLE-IMAGE'
                        self.__showImageView()
                    else:  # Volume
                        # The image has a volume. The data is a numpy 3D array.
                        # In this case, display the Top, Front and the Right
                        # View planes.
                        info['type'] = "VOLUME"
                        model = ModelsFactory.createVolumeModel(imagePath)
                        self._volumeView.setModel(model)
                        self.__showVolumeSlice()
                else:
                    # Image stack
                    if d.z > 1:  # Volume stack
                        raise Exception("Volume stack is not supported")
                    elif d.x <= MOVIE_SIZE:
                        info['type'] = 'IMAGES STACK'
                        model = ModelsFactory.createTableModel(imagePath)
                        self._dataView.setModel(model)
                        self._dataView.setView(dv.views.GALLERY)
                        self.__showDataView()
                    else:
                        info['type'] = 'MOVIE'
                        model = ModelsFactory.createStackModel(imagePath)
                        self._slicesView.setModel(model)
                        self.__showSlicesView()
                    # TODO Show the image type
            elif EmPath.isTextFile(imagePath):
                extType = EmPath.getExtType(imagePath)
                cl = getHighlighterClass(extType)
                h = cl(None) if cl is not None else None
                self._textView.setHighlighter(h)
                info['Type'] = 'TEXT FILE'
                self._textView.setPlainText("")

                fl, ll, size = readLinesFromFile(imagePath, self._lines,
                                                 self._lines)
                d = {i + 1: i + 1 for i in range(len(fl))}
                self._textView.setLinesDict(d)

                self._textView.setPlainText("".join(fl))
                if ll:
                    self._textView.appendPlainText(".\n.\n.\n")
                    for i in range(len(ll)):
                        d[self._lines + i + 6] = size - self._lines + i + 1

                    self._textView.appendPlainText("".join(ll))

                self.__showTextView()
            else:
                self.__showEmptyWidget()
                info.clear()

            self.__showInfo(info)
        except Exception as ex:
            self.__showMsgBox("Error opening the file",
                              qtw.QMessageBox.Critical,
                              str(ex))
            self.__showEmptyWidget()
            self.__clearInfoWidget()
        except RuntimeError as ex:
            self.__showMsgBox("Error opening the file",
                              qtw.QMessageBox.Critical,
                              str(ex))
            self.__showEmptyWidget()
            self.__clearInfoWidget()

    def updateViewPanel(self):
        """
        Update the information of the view panel.
        """
        index = self._treeModelView.currentIndex()
        model = self._treeModelView.model()
        path = model.filePath(index)
        self.showFile(path)



def readLinesFromFile(fname, fi, la):
    """
    Read the first fi lines and last la lines from the given file

    Args:
        fname: (str) The file name
        fi:    (int) The first lines to be read
        la:    (int) The last lines to be read

    Returns:
         A tupple with two list: first and last lines, and the number of lines
    """

    fsize = os.stat(fname).st_size

    with open(fname) as f:
        lines = []
        for _ in range(fi):
            line = f.readline()
            if line:
                lines.append(line)
            else:
                break

        s = f.tell()
        size = len(lines)
        for _ in f:
            size += 1

        f.seek(s)

        if s < fsize:
            i = 0
            bufsize = 8192
            if bufsize > fsize:
                bufsize = fsize - 1

            data = []
            while True:
                i += 1
                seek = fsize - bufsize * i
                if seek < s:
                    seek = s

                f.seek(seek)

                data.extend(f.readlines())
                if len(data) >= la or seek == s:
                    return lines, data[-la:], size
        else:
            return lines, [], size
