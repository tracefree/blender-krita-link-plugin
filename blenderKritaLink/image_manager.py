import bpy
import numpy as np
class ImageManager():
    INSTANCE = None
    def __init__(self) -> None:
        if ImageManager.INSTANCE:
           return
        self.IMAGE: str = "Untitled"
        ImageManager.INSTANCE = self
    
    def mirror_image(self,image_pixels):
        print("hello from mirror_image")
        image = self.get_image()
        if not self.IMAGE or image.type != 'IMAGE':
            print("object is not image.")
            return
        print("hello from mirror_image")
        width = image.size[0]
        height = image.size[1]
        print("hello from mirror_image")
        
        pixels_reshaped = image_pixels.reshape((height, width, 4))
        mirrored_pixels = np.flipud(pixels_reshaped).flatten()
        print("hello from mirror_image")
        image.pixels.foreach_set(mirrored_pixels)
        
        print("hello from mirror_image")
        print(f"Image mirrored{image.name}")
        for obj in bpy.context.scene.objects: obj.update_tag()
        print("hello from mirror_image")

    def update_image(self,bytes_array):
        image =  self.get_image()
        if not self.IMAGE or not image:
            return
        fp32_array = np.frombuffer(bytes_array, dtype=np.float32)
        image.pixels.foreach_set(fp32_array)    
        image.pack()
        for obj in bpy.context.scene.objects:
            obj.update_tag()
    
    def get_image(self):
        return bpy.data.images[self.IMAGE]
    
    def get_image_size(self):
        image =  self.get_image()
        if self.IMAGE:
            return image.size
        else: 
            return None