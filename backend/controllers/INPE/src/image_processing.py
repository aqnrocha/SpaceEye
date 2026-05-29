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
        id,                 
        userPolygon,        
        panBand,                  
        redBand=None, 
        greenBand=None,
        blueBand=None,
        nirBand=None
    ):
        self.id = id
        self.userPolygon = userPolygon
        self.imgs = {
            "RED": {
                "path": f"controllers/INPE/imgs/RED-{self.id}.tif",
                "link": redBand
            },
            "GREEN": {
                "path": f"controllers/INPE/imgs/GREEN-{self.id}.tif",
                "link": greenBand
            },
            "BLUE": {
                "path": f"controllers/INPE/imgs/BLUE-{self.id}.tif",
                "link": blueBand
            },
            "NIR": {
                "path": f"controllers/INPE/imgs/PAN-{self.id}.tif",
                "link": nirBand
            },            
            "PAN": {
                "path": f"controllers/INPE/imgs/PAN-{self.id}.tif",
                "link": panBand
            }
        }

        os.makedirs("controllers/INPE/imgs/masks", exist_ok=True)

    async def _download_one(self, session, img):

        if not isinstance(img["link"], str):
            pass
        else:
            temp_path = f'{img["path"]}.part'

            if os.path.exists(temp_path):
                os.remove(temp_path)

            if os.path.exists(img["path"]):

                if os.path.getsize(img["path"]) > 0:
                    print(f'Arquivo já existe: {img["path"]}')
                    return

                os.remove(img["path"])

            timeout = aiohttp.ClientTimeout(total=600)

            try:

                async with session.get(img["link"], timeout=timeout) as resp:

                    resp.raise_for_status()

                    with open(temp_path, "wb") as f:

                        async for chunk in resp.content.iter_chunked(1024 * 1024):
                            f.write(chunk)

                        f.flush()
                        os.fsync(f.fileno())

                os.replace(temp_path, img["path"])

                print(f'Download concluído: {img["path"]}')

            except Exception as e:

                if os.path.exists(temp_path):
                    os.remove(temp_path)

                print(f'Erro download {img["path"]}: {e}')
                raise


    async def _download_all(self):

        connector = aiohttp.TCPConnector(limit=4)

        async with aiohttp.ClientSession(connector=connector) as session:

            tasks = [
                asyncio.create_task(
                    self._download_one(session, self.imgs[key])
                )
                for key in self.imgs
            ]

            # captura exceções corretamente
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    raise result

        print("TODOS DOWNLOADS FINALIZADOS")


    def getImages(self):

        asyncio.run(self._download_all())

        # valida existência após await
        for key in self.imgs:

            path = self.imgs[key]["path"]

            if not os.path.exists(path):
                raise Exception(f'Arquivo ausente: {path}')

            if os.path.getsize(path) == 0:
                raise Exception(f'Arquivo vazio: {path}')

        print("Arquivos prontos para processamento")

    def trueColorGenerator(self):

        rgb_path = f"controllers/INPE/imgs/masks/TCI_{self.id}.tif"

        if os.path.exists(rgb_path):
            return rgb_path

        try:

            def normalize_band(band):

                valid = band[np.isfinite(band)]

                if valid.size == 0:
                    return np.zeros_like(band)

                p2, p98 = np.percentile(valid, (2, 98))

                if p98 <= p2:
                    return np.zeros_like(band)

                band = np.clip(band, p2, p98)

                return (band - p2) / (p98 - p2)

            with rasterio.open(self.imgs["RED"]["path"]) as red, \
                rasterio.open(self.imgs["GREEN"]["path"]) as green, \
                rasterio.open(self.imgs["BLUE"]["path"]) as blue:

                # --------------------------------
                # Polígono
                # --------------------------------
                gdf = gpd.GeoDataFrame(
                    geometry=[self.userPolygon],
                    crs="EPSG:4326"
                )

                if gdf.crs != red.crs:
                    gdf = gdf.to_crs(red.crs)

                geom = [mapping(gdf.geometry.iloc[0])]

                # --------------------------------
                # Crop RED
                # --------------------------------
                r_crop, transform = mask(
                    red,
                    geom,
                    crop=True,
                    filled=False
                )

                height = r_crop.shape[1]
                width = r_crop.shape[2]

                r = r_crop[0].astype(np.float32)

                # --------------------------------
                # Reproject G
                # --------------------------------
                g = np.zeros((height, width), dtype=np.float32)

                reproject(
                    source=rasterio.band(green, 1),
                    destination=g,
                    src_transform=green.transform,
                    src_crs=green.crs,
                    dst_transform=transform,
                    dst_crs=red.crs,
                    dst_width=width,
                    dst_height=height,
                    resampling=Resampling.cubic
                )

                # --------------------------------
                # Reproject B
                # --------------------------------
                b = np.zeros((height, width), dtype=np.float32)

                reproject(
                    source=rasterio.band(blue, 1),
                    destination=b,
                    src_transform=blue.transform,
                    src_crs=blue.crs,
                    dst_transform=transform,
                    dst_crs=red.crs,
                    dst_width=width,
                    dst_height=height,
                    resampling=Resampling.cubic
                )

                # --------------------------------
                # Máscara
                # --------------------------------
                r[r <= 0] = np.nan
                g[g <= 0] = np.nan
                b[b <= 0] = np.nan

                # --------------------------------
                # Normalize individual
                # --------------------------------
                r = normalize_band(r)
                g = normalize_band(g)
                b = normalize_band(b)

                # --------------------------------
                # Gamma
                # --------------------------------
                gamma = 1 / 2.2

                r = np.power(r, gamma)
                g = np.power(g, gamma)
                b = np.power(b, gamma)

                rgb = np.stack([r, g, b])

                # --------------------------------
                # Perfil
                # --------------------------------
                profile = red.profile.copy()

                profile.update(
                    driver="GTiff",
                    dtype=rasterio.uint8,
                    count=3,
                    height=height,
                    width=width,
                    transform=transform,
                    compress="lzw"
                )

                with rasterio.open(rgb_path, "w", **profile) as dst:

                    dst.write(
                        (np.nan_to_num(rgb) * 255).astype(np.uint8)
                    )

            return rgb_path

        except Exception as e:
            raise RuntimeError(f"Erro ao gerar TCI: {e}")

    def ndviGenerator(self):
        ndvi_path = f"controllers/INPE/imgs/masks/NDVI_{self.id}.tif"

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
