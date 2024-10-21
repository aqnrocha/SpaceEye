import rasterio
from rasterio.mask import mask
from shapely.geometry import shape, mapping
import geopandas as gpd

class Mask:
    
    def __init__(self, userPolygon, imagePath, imageName):
        self.userPolygon = userPolygon
        self.imagePath = imagePath
        self.imageName = imageName

    def applyingMask(self):
        with rasterio.open(self.imagePath, "r") as src:
            try:
                image_crs = src.crs
                user_polygon_gdf = gpd.GeoDataFrame({'geometry': [self.userPolygon]}, crs='EPSG:4326')

                if user_polygon_gdf.crs != image_crs:
                    user_polygon_gdf = user_polygon_gdf.to_crs(image_crs)

                user_polygon_transformed = user_polygon_gdf.geometry.iloc[0]
                imagem_recortada, transformacao = mask(src, [mapping(user_polygon_transformed)], crop=True)

                perfil_recorte = {
                    'driver': 'GTiff',
                    'count': 1,
                    'dtype': rasterio.float32,
                    'width': imagem_recortada.shape[2],
                    'height': imagem_recortada.shape[1],
                    'crs': src.crs,
                    'transform': transformacao,
                    'nodata': 0,
                    'compress': 'lzw'
                }

                maskPath = rf"controllers/INPE/imgs/masks/{self.imageName}.tif"

                with rasterio.open(maskPath, 'w', **perfil_recorte) as arq:
                    arq.write(imagem_recortada)
                    
            except Exception as exception:
                print(
                    {
                        "imageName": self.imageName,
                        "Erro": exception
                    }
                )
                pass
