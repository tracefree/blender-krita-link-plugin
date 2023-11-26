import typing
import asyncio
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, QSize
from .ImageItem import ImageItem
from KritaBlenderLink.connection import ConnectionManager
# from connection import ConnectionManager


class ImageList(QScrollArea):
    l = []
    refresh_signal = pyqtSignal(object)
    instance = None

    def __init__(self, con_manager: ConnectionManager, parent: QWidget | None = ...) -> None:
        ImageList.instance = self
        self.conn_manager = con_manager
        super().__init__(parent)
        self.image_list = []
        self.setObjectName(u"ImageList")
        self.setObjectName("scrollArea")
        self.setMinimumSize(QSize(0, 100))
        self.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setMinimumSize(QSize(0, 0))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.setWidget(self.scrollAreaWidgetContents)
        self.refresh_signal.connect(self.update_images_list)

    def update_images_list(self, images_list):
        print("update time")
        for i in reversed(range(self.verticalLayout_2.count())):
            widget_to_remove = self.verticalLayout_2.itemAt(i).widget()
            widget_to_remove.moveToThread(self.thread())
            if widget_to_remove is not None:
                widget_to_remove.deleteLater()
        print("items removed", len(images_list))
        self.l.clear()
        for image in images_list:
            item = ImageItem(image=image, on_open=lambda: asyncio.run(self.conn_manager.request(
                {"data": "", "type": "OPEN"})), on_override=self.override_image, parent=self.scrollAreaWidgetContents)

            # item = ImageItem(item_text, "0x0", self.scrollAreaWidgetContents,
            #                  on_open=asyncio.run(con_manager.request({"data": "", "type": "NONE"})))

            self.l.append(item)
            print("item created")
            self.verticalLayout_2.moveToThread(self.thread())
            self.verticalLayout_2.addWidget(item)
            print("item added")

    def override_image(self, image):
        doc = Krita.instance().activeDocument()
        size = [doc.width(), doc.height()]
        print(size, "memsize", self.conn_manager.shm.size, size[0]*size[1]*16)
        if size[0]*size[1]*16 > self.conn_manager.shm.size:
            print("resizing")
            self.conn_manager.resize_memory(size[0]*size[1]*16)
        asyncio.run(self.conn_manager.request(
                    {"data": image, "type": "OVERRIDE_IMAGE"}))

        # custom_item = QPushButton(item_text, self.scrollAreaWidgetContents)
