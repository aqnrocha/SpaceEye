import requests
import rasterio
import numpy as np
import os
from joblib import Parallel, delayed

class ImageProcessing:
    
    def __init__(self, redBand:str, nirBand:str, id:str):
        self.id = id
        self.redBand = redBand
        self.nirBand = nirBand
        self.imgs = {
            "RED": {
                "path": fr"controllers/INPE/imgs/RED-{self.id}.tif",
                "link": self.redBand
            },
            "NIR": {
                "path": fr"controllers/INPE/imgs/NIR-{self.id}.tif",
                "link": self.nirBand
            }
        }        

    def download(self, img):
        if os.path.exists(img["path"]):
            pass
        else:
            response = requests.get(img["link"])
            self.save(img["path"], response.content)
    
    def save(self, path, content):
        with open(path, "wb") as file:
            file.write(content)
    
    def getImages(self):
        Parallel(n_jobs=2)(delayed(self.download)(self.imgs[img]) for img in self.imgs)
    
    def ndviGenerator(self):
        imagePath = rf"controllers/INPE/imgs/NDVI-{self.id}.tif"

        if os.path.exists(imagePath):
            return imagePath
        else:
            with rasterio.open(self.imgs["RED"]["path"], "r") as red, rasterio.open(self.imgs["NIR"]["path"], "r") as nir:
                d_red = red.read(1)
                d_nir = nir.read(1)

                ndvi = np.zeros_like(d_nir, dtype=np.float32)
                mascara_valida = (d_nir + d_red) != 0
                ndvi[mascara_valida] = (d_nir[mascara_valida] - d_red[mascara_valida]) / (d_nir[mascara_valida] + d_red[mascara_valida])

                perfil = red.profile
                perfil.update(dtype=rasterio.float32)
                
                
                with rasterio.open(imagePath, "w", **perfil) as output_ndvi:
                    output_ndvi.write(ndvi.astype(rasterio.float32), 1)

                return imagePath
