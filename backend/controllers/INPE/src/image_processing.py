import os
import asyncio
import aiohttp
import rasterio
import numpy as np
from rasterio.warp import reproject, Resampling
from rasterio.mask import mask
from shapely.geometry import shape, mapping
import geopandas as gpd


class ImageProcessing:

    def __init__(self, 
        redBand: str, 
        nirBand: str, 
        panBand: str, 
        id: str,
        userPolygon
    ):
        self.id = id
        self.userPolygon = userPolygon
        self.imgs = {
            "RED": {
                "path": f"controllers/INPE/imgs/RED-{self.id}.tif",
                "link": redBand
            },
            "NIR": {
                "path": f"controllers/INPE/imgs/NIR-{self.id}.tif",
                "link": nirBand
            },
            "PAN": {
                "path": f"controllers/INPE/imgs/PAN-{self.id}.tif",
                "link": panBand
            }
        }

        os.makedirs("controllers/INPE/imgs/masks", exist_ok=True)

    async def _download_one(self, session, img):
        if os.path.exists(img["path"]):
            return

        timeout = aiohttp.ClientTimeout(total=600)

        async with session.get(img["link"], timeout=timeout) as resp:
            resp.raise_for_status()
            with open(img["path"], "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 1024):
                    f.write(chunk)

    async def _download_all(self):
        connector = aiohttp.TCPConnector(limit=4)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [
                self._download_one(session, self.imgs[key])
                for key in self.imgs
            ]
            await asyncio.gather(*tasks)

    def getImages(self):
        asyncio.run(self._download_all())

    def ndviGenerator(self):
        ndvi_path = f"controllers/INPE/imgs/masks/{self.id}.tif"

        if os.path.exists(ndvi_path):
            return ndvi_path

        try:
            with rasterio.open(self.imgs["PAN"]["path"]) as pan, \
                rasterio.open(self.imgs["RED"]["path"]) as red, \
                rasterio.open(self.imgs["NIR"]["path"]) as nir:

                # POLÍGONO
                user_polygon_gdf = gpd.GeoDataFrame(
                    {'geometry': [self.userPolygon]},
                    crs='EPSG:4326'
                )

                if user_polygon_gdf.crs != pan.crs:
                    user_polygon_gdf = user_polygon_gdf.to_crs(pan.crs)

                geom = [mapping(user_polygon_gdf.geometry.iloc[0])]

                # RECORTE DO PAN
                pan_crop, transform = mask(
                    pan,
                    geom,
                    crop=True,
                    nodata=0
                )

                pan_data = pan_crop[0].astype(np.float32)

                profile = pan.profile
                profile.update(
                    dtype=rasterio.float32,
                    count=1,
                    height=pan_data.shape[0],
                    width=pan_data.shape[1],
                    transform=transform,
                    nodata=0,
                    compress="lzw"
                )

                # buffers para RED e NIR reprojetados
                red_resampled = np.zeros_like(pan_data, dtype=np.float32)
                nir_resampled = np.zeros_like(pan_data, dtype=np.float32)

                # REPROJECT
                reproject(
                    source=rasterio.band(red, 1),
                    destination=red_resampled,
                    src_transform=red.transform,
                    src_crs=red.crs,
                    dst_transform=transform,
                    dst_crs=pan.crs,
                    resampling=Resampling.bilinear
                )

                reproject(
                    source=rasterio.band(nir, 1),
                    destination=nir_resampled,
                    src_transform=nir.transform,
                    src_crs=nir.crs,
                    dst_transform=transform,
                    dst_crs=pan.crs,
                    resampling=Resampling.bilinear
                )

                # PAN SHARPENING
                soma = red_resampled + nir_resampled
                mask_soma = soma != 0

                red_ps = np.zeros_like(pan_data)
                nir_ps = np.zeros_like(pan_data)

                red_ps[mask_soma] = (red_resampled[mask_soma] / soma[mask_soma]) * pan_data[mask_soma]
                nir_ps[mask_soma] = (nir_resampled[mask_soma] / soma[mask_soma]) * pan_data[mask_soma]

                # NDVI
                ndvi = np.zeros_like(pan_data, dtype=np.float32)
                mask_ndvi = (nir_ps + red_ps) != 0

                ndvi[mask_ndvi] = (
                    (nir_ps[mask_ndvi] - red_ps[mask_ndvi]) /
                    (nir_ps[mask_ndvi] + red_ps[mask_ndvi])
                )

                with rasterio.open(ndvi_path, "w", **profile) as dst:
                    dst.write(ndvi, 1)

            return ndvi_path

        except Exception as exception:
            print(
                {
                    "Erro NDVI": exception
                }
            )
            raise

