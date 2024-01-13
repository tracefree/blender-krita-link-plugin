from multiprocessing.connection import Connection, Listener, Client
from threading import Thread, Event
from multiprocessing import shared_memory
import bpy
import numpy as np
from .image_manager import ImageManager
from .uv_extractor import getUvData
from pprint import pprint
from contextlib import contextmanager

@contextmanager
def shared_memory_context(name:str,size:int,destroy:bool,create=bool):
    shm = None
    if size == None:
        shm = shared_memory.SharedMemory(name=name,create=create)
    else:
        shm = shared_memory.SharedMemory(name=name,create=create,size=size)
    
    try:
        yield shm
    finally:
        if destroy:
            shm.unlink()
        else:
            shm.close()


class KritaConnection():
    PORT = 6000
    PASS = b'2137'
    LINK_INSTANCE = None
    STATUS: str

    def __init__(self) -> None:
        if not KritaConnection.LINK_INSTANCE:
            KritaConnection.LINK_INSTANCE = self

    def dell(self):
        print("delling")
        if KritaConnection.CONNECTION != None:
            print("sending close")
            self.__STOP_SIGNAL.set()
            # self.CONNECTION.send("close")
            # self.CONNECTION.close()
        elif self.listener != None:
            print("accepting")
            with Client(('localhost', KritaConnection.PORT), authkey=b"2137") as connection:
                self.__STOP_SIGNAL.set()
                connection.send('close')
            # self.listener.accept() 
            # self.listener.close()

    def start(self):
        self.__STOP_SIGNAL = Event()
        self.__THREAD = Thread(target=self.krita_listener)
        self.__THREAD.start()
        KritaConnection.CONNECTION: None | Connection = None
        KritaConnection.STATUS = 'listening'

    def update_message(self, message):
        if hasattr(bpy.context, 'scene') and hasattr(bpy.context.scene, 'test_prop') and bpy.context.scene.test_prop:
            bpy.context.scene.test_prop = message
        else:
            print("no scene??")

    @staticmethod
    def send_message(message):
        if KritaConnection.CONNECTION != None:
            KritaConnection.CONNECTION.send(message)
        else:
            print("no connection available")
            
    def krita_listener(self):
        self.update_message("listening")
        while not self.__STOP_SIGNAL.isSet():
            KritaConnection.LINK_INSTANCE = self
            # family is deduced to be 'AF_INET'
            address = ('localhost', KritaConnection.PORT)
            self.update_message("listening")
            self.listener = Listener(address, authkey=KritaConnection.PASS)
            listener = self.listener
            conn = listener.accept()
            self.update_message("connected")
            KritaConnection.CONNECTION = conn
            print("connection accepted")
            ImageManager.INSTANCE.set_image_name(None)
            # existing_shm = shared_memory.SharedMemory(name='krita-blender')
            try:
                self.update_message("connected")
                while not self.__STOP_SIGNAL.isSet():
                    pol = conn.poll(0.1)
                    if not pol: continue
                    msg = conn.recv()
                    self.update_message("message recived")
                    print(msg)
                    if msg == 'close':
                        print(msg)
                        conn.close()
                        ImageManager.INSTANCE.set_image_name(None)
                        self.update_message("closed")
                        break
                    elif isinstance(msg, object):
                        print("message is object UwU")
                        if "type" in msg and 'requestId' in msg:
                            type = msg["type"]
                            match type:
                                case "REFRESH":
                                    with shared_memory_context(name="krita-blender",size=None,destroy=False,create=False) as existing_shm:
                                        print("refresh initiated")
                                        self.update_message("got The Image")
                                        pixels_array = None
                                        match msg["depth"]:
                                            case "F32":
                                                pixels_array = np.frombuffer(
                                                    existing_shm.buf, dtype=np.float32)
                                            case "F16":
                                                pixels_array = np.frombuffer(
                                                    existing_shm.buf, dtype=np.float16)
                                            case "U8":
                                                pixels_array = np.frombuffer(
                                                    existing_shm.buf, dtype=np.uint8)
                                            case "U16":
                                                pixels_array = np.frombuffer(
                                                    existing_shm.buf, dtype=np.uint16)
                                    
                                        print("refresh initiated")
                                        ImageManager.INSTANCE.mirror_image(pixels_array)
                                        pixels_array = None
                                        print("refresh complete")
                                        self.update_message("connected")
                                        conn.send({
                                            "type": "REFRESH",
                                            "depth": msg["depth"],
                                            "requestId": msg['requestId']
                                        })

                                case "GET_IMAGES":
                                    data = []
                                    for image in bpy.data.images:
                                        data.append({
                                            "name": image.name,
                                            "path": bpy.path.abspath(image.filepath),
                                            "size": [image.size[0], image.size[1]],
                                            "isActive": ImageManager.INSTANCE.IMAGE_NAME == image.name
                                        })

                                    print(msg)
                                    conn.send({
                                        "type": "GET_IMAGES",
                                        "data": data,
                                        "requestId": msg['requestId']
                                    })
                                    print("message sent")

                                case "OPEN":
                                    print("dupaopen")
                                    conn.send({
                                        "type": "OPEN",
                                        "data": "",
                                        "requestId": msg['requestId']
                                    })

                                case "OVERRIDE_IMAGE":
                                    print("overriding image: ",
                                            msg['data']['name'])
                                    ImageManager.INSTANCE.set_image_name(
                                        msg['data']['name'])
                                    conn.send({
                                        "type": "OVERRIDE_IMAGE",
                                        "data": "",
                                        "requestId": msg['requestId']
                                    })
                                case "RECREATE_MEMORY":
                                    conn.send({
                                        "type": "RECREATE_MEMORY",
                                        "data": "",
                                        "requestId": msg['requestId']
                                    })
                                    
                                case "CLOSE_MEMORY":
                                    conn.send({
                                        "type": "CLOSE_MEMORY",
                                        "data": "",
                                        "requestId": msg['requestId']
                                    })

                                case "REMOVE_LINK":
                                    ImageManager.INSTANCE.set_image_name(None)
                                    conn.send({
                                        "type": "REMOVE_LINK",
                                        "data": None,
                                        "requestId": msg['requestId']
                                    })

                                case "SELECT_UVS":
                                    print("sending UV data: ")
                                    print(bpy.context.scene,bpy.context.view_layer,bpy.context.view_layer.objects.active)
                                    print("sending UV data2 ")
                                    data = getUvData()
                                    conn.send({
                                        "type": "SELECT_UVS",
                                        "data": data,
                                        "requestId": msg['requestId']
                                    })
                                
                                case "IMAGE_TO_LAYER":
                                    print("OMG krita requests blender image")
                                    # print(bpy.context.scene,bpy.context.view_layer,bpy.context.view_layer.objects.active)
                                    pprint(msg["data"])
                                    # pprint(data,data["imageName"],data["depth"])
                                    d = ImageManager.INSTANCE.get_image_to_krita(msg["data"]["image"],msg["data"]["depth"])
                                    print("siema z powodzeniem pobrano rzeczy")
                                    depth = d.depth
                                    l = len(d.pixels)
                                    with shared_memory_context( name='blender-krita', size= l * 4,destroy=False,create=True) as new_shm:                                        
                                        array = np.frombuffer(new_shm.buf,np.float32)
                                        d.pixels.foreach_get(array)
                                        
                                        print("siema z powodzeniem wpisano w pamiec rzeczy")
                                        conn.send({
                                            "type": "IMAGE_TO_LAYER",
                                            "data":"",
                                            # "size":d.size,
                                            "imageData": "",
                                            "requestId": msg['requestId']
                                        })

                                        array = None
                                        new_shm.close()
                                        
                                        print("siema z powodzeniem wyslano rzeczy")


                                case _:
                                    conn.send({
                                        "type": "nop",
                                        "data": None,
                                        "requestId": msg['requestId']
                                    })

                # conn.send('close')
                # # existing_shm.close()
                # conn.close()
            except Exception as e:
                pprint( e)
                if KritaConnection.CONNECTION != None:
                    KritaConnection.CONNECTION.send("close")
                    KritaConnection.CONNECTION.close()
                KritaConnection.CONNECTION = None

            listener.close()
            self.listener=None
            if self.__STOP_SIGNAL.is_set():
                KritaConnection.STATUS = "listening"
                listener.close()
                return
