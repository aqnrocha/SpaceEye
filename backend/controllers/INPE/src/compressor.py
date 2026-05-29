import numpy as np
import pyproj
import matplotlib.pyplot as plt
import tempfile
import rasterio
import os


class Compressor:

    def __init__(self, imagePath, product):
        self.product = product
        self.imagePath = f"controllers/INPE/imgs/masks/{product}_{imagePath}.tif"
    
    def compress_raster(self):
        if self.product == "NDVI":
            return self.compress_ndvi()
        elif self.product == "TCI":
            return self.compress_tci()

    def compress_ndvi(self):

        with rasterio.open(self.imagePath) as img:

            ndvi_data = img.read(1)
            mask = (ndvi_data == 0)

            ndvi_data = np.where(mask, np.nan, ndvi_data)
            vmin, vmax = -1, 1
            
            bounds = img.bounds

            utm_proj = f'+proj=utm +zone=22 +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs'
            utm_to_latlon = pyproj.Transformer.from_crs(utm_proj, "EPSG:4326", always_xy=True).transform

            left, bottom = utm_to_latlon(bounds.left, bounds.bottom)
            right, top = utm_to_latlon(bounds.right, bounds.top)

            bounds2 = [[bottom, left], [top, right]]

            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            temp_file_path = temp_file.name
            temp_file.close()
            plt.imsave(temp_file_path, ndvi_data, cmap='RdYlGn', vmin=vmin, vmax=vmax)
        
        return {
            "bounds": bounds2,
            "path": temp_file_path
        }
    
    def compress_tci(self):

        with rasterio.open(self.imagePath) as img:

            # Lê bandas RGB
            red = img.read(1)
            green = img.read(2)
            blue = img.read(3)

            # Empilha bandas
            rgb = np.dstack((red, green, blue))

            # Máscara para pixels pretos
            mask = np.all(rgb == 0, axis=-1)

            # Define transparência opcional
            rgb = rgb.astype(np.float32)

            # Normaliza valores
            rgb_min = np.nanmin(rgb)
            rgb_max = np.nanmax(rgb)

            rgb = (
                (rgb - rgb_min) /
                (rgb_max - rgb_min) * 255
            ).astype(np.uint8)

            # Remove fundo preto
            rgb[mask] = [255, 255, 255]

            bounds = img.bounds

            utm_proj = (
                '+proj=utm +zone=22 +south '
                '+ellps=WGS84 +datum=WGS84 +units=m +no_defs'
            )

            utm_to_latlon = pyproj.Transformer.from_crs(
                utm_proj,
                "EPSG:4326",
                always_xy=True
            ).transform

            left, bottom = utm_to_latlon(bounds.left, bounds.bottom)
            right, top = utm_to_latlon(bounds.right, bounds.top)

            bounds2 = [[bottom, left], [top, right]]

            # Ajuste correto
            fd, temp_file_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)

            # Salva RGB
            plt.imsave(temp_file_path, rgb)

        return {
            "bounds": bounds2,
            "path": temp_file_path
        }