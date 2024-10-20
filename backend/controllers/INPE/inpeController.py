from .src.image_processing import ImageProcessing
from .src.mask_image import Mask
from .src.compressor import Compressor
from shapely.geometry import Polygon
import folium
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

class INPE:

    def __init__(self, polygon):
        self.polygon = polygon
        self.email = os.getenv("email_inpe")

    def insere_parametro(self, link):
        return link + "?email=" + self.email  

    def verifica_sobreposicao(self, poligono):
        poligono_interesse = self.polygon
        return Polygon(poligono).contains_properly(poligono_interesse)
    
    def ndviGenerator(self, imageId):
        df = self.findImage()
        image = df[df["id"] == imageId].iloc[0]

        instance = ImageProcessing(
            redBand=image["banda_vermelho"],
            nirBand=image["banda_nir"],
            id=image["id"]
        )

        instance.getImages()
        imagePath = instance.ndviGenerator()

        instance_mask = Mask(
            userPolygon=self.polygon, 
            imagePath=imagePath, 
            imageName=image["id"]
        )
        
        instance_mask.applyingMask()        
    
    def findImage(self):

        link = "http://www.dgi.inpe.br/lgi-stac/collections/CBERS4A_WPM_L4_DN/items?page=1&limit=1000000000"
        response = requests.get(link)
        data = response.json()

        dicionario = [{
            "id": item['id'],
            "colecao": item['collection'],
            "coordenadas": [point for point in item['geometry']['coordinates'][0]],
            "data/hora": item['properties']['datetime'],
            "satelite": item['properties']['satellite'],
            "cloud_cover": item['properties'].get('cloud_cover', 0),
            "banda_vermelho": self.insere_parametro(item['assets']['red']['href']),
            "banda_nir": self.insere_parametro(item['assets']['nir']['href']),
            "thumbnail": item["assets"]["thumbnail"]["href"]
        } for item in data['features']]

        df = pd.DataFrame(dicionario)
        relevant_images = df[df["coordenadas"].apply(self.verifica_sobreposicao)]
        return relevant_images
    
    def map_with_raster(self, imageId):
        img_info = Compressor(imageId).compress_raster()

        centro = self.polygon.centroid
        m = folium.Map(
            location=[centro.y, centro.x], 
            zoom_start=15, 
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
            attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
        )

        polygon_coords_flipped = [(lat, lon) for lon, lat in self.polygon.exterior.coords]

        folium.raster_layers.ImageOverlay(
            image=img_info['path'],
            bounds=polygon_coords_flipped,
            zindex=1
        ).add_to(m)
        os.remove(img_info['path'])

        return m._repr_html_()    
