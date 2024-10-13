from .src.image_processing import ImageProcessing
from .src.mask_image import Mask
from .src.compressor import Compressor
from shapely.geometry import Polygon
import folium
import requests
import pandas as pd
import os

class INPE:

    def __init__(self, polygon):
        self.polygon = polygon
        self.email_cadastrado = "?email=bruno.aqnrocha@gmail.com"

    def insere_parametro(self, link):
        return link + self.email_cadastrado  

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

        # Obtendo todas as imagens disponíveis
        link = "http://www.dgi.inpe.br/lgi-stac/collections/CBERS4A_WPM_L4_DN/items?page=1&limit=1000000000"
        response = requests.get(link)
        data = response.json()
        
        # Organizando as informações importantes para o projeto
        dicionario = []
        for item in data['features']:
            coordList = item['geometry']['coordinates']
            tupla = list([point for point in coordList[0]])

            cloud_cover_t = item['properties']['cloud_cover']

            if cloud_cover_t is None:
                cloud_cover = 0
            else:
                cloud_cover = cloud_cover_t

            dicionario.append({
                "id": item['id'],
                "colecao": item['collection'],
                "coordenadas": tupla,
                "data/hora": item['properties']['datetime'],
                "satelite": item['properties']['satellite'],
                "cloud_cover": cloud_cover,
                "banda_vermelho": self.insere_parametro(item['assets']['red']['href']),
                "banda_nir": self.insere_parametro(item['assets']['nir']['href']),
                "thumbnail": item["assets"]["thumbnail"]["href"]
            })

        # Verificando quais imagens sobrepõe o polígono informado
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
