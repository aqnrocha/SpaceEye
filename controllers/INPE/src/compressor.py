import numpy as np
import pyproj
import matplotlib.pyplot as plt
import tempfile
import rasterio


class Compressor:

    def __init__(self, imagePath):
        self.imagePath = f"controllers/INPE/imgs/masks/{imagePath}.tif"
    
    def compress_raster(self):

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