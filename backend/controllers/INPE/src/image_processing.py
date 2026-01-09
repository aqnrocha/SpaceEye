import os
import asyncio
import aiohttp
import rasterio
import numpy as np
from rasterio.warp import reproject, Resampling


class ImageProcessing:

    def __init__(self, redBand: str, nirBand: str, panBand: str, id: str):
        self.id = id

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

        os.makedirs("controllers/INPE/imgs", exist_ok=True)

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
        ndvi_path = f"controllers/INPE/imgs/NDVI-PAN-{self.id}.tif"

        if os.path.exists(ndvi_path):
            return ndvi_path

        with rasterio.open(self.imgs["RED"]["path"]) as red, \
             rasterio.open(self.imgs["NIR"]["path"]) as nir, \
             rasterio.open(self.imgs["PAN"]["path"]) as pan:

            profile = pan.profile
            profile.update(
                dtype=rasterio.float32,
                count=1,
                compress="lzw"
            )

            with rasterio.open(ndvi_path, "w", **profile) as dst:

                for _, window in pan.block_windows(1):

                    pan_data = pan.read(1, window=window).astype(np.float32)

                    red_resampled = np.empty_like(pan_data, dtype=np.float32)
                    nir_resampled = np.empty_like(pan_data, dtype=np.float32)

                    reproject(
                        source=rasterio.band(red, 1),
                        destination=red_resampled,
                        src_transform=red.transform,
                        src_crs=red.crs,
                        dst_transform=pan.window_transform(window),
                        dst_crs=pan.crs,
                        resampling=Resampling.bilinear
                    )

                    reproject(
                        source=rasterio.band(nir, 1),
                        destination=nir_resampled,
                        src_transform=nir.transform,
                        src_crs=nir.crs,
                        dst_transform=pan.window_transform(window),
                        dst_crs=pan.crs,
                        resampling=Resampling.bilinear
                    )
                    
                    soma = red_resampled + nir_resampled
                    mask = soma != 0

                    red_ps = np.zeros_like(red_resampled)
                    nir_ps = np.zeros_like(nir_resampled)

                    red_ps[mask] = (red_resampled[mask] / soma[mask]) * pan_data[mask]
                    nir_ps[mask] = (nir_resampled[mask] / soma[mask]) * pan_data[mask]

                    # NDVI
                    ndvi = np.zeros_like(pan_data, dtype=np.float32)
                    mask_ndvi = (nir_ps + red_ps) != 0

                    ndvi[mask_ndvi] = (
                        (nir_ps[mask_ndvi] - red_ps[mask_ndvi]) /
                        (nir_ps[mask_ndvi] + red_ps[mask_ndvi])
                    )

                    dst.write(ndvi, 1, window=window)

        return ndvi_path
