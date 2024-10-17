from flask import Blueprint, request
from controllers.INPE.inpeController import INPE
from shapely.geometry import Polygon
import folium
from folium.plugins import Draw
import ast
from geopy.geocoders import Nominatim
from json import load

api = Blueprint('api', __name__)

@api.route("/api/map")
def map():

    m = folium.Map(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
        attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
        zoom_start=3,
        location=[3.359202, 23.211370]
    )
    Draw(export=True).add_to(m)

    return {"HTML": m._repr_html_()}

@api.route("/api/map/<string:uf>/<string:cidade>")
def mapWithLoc(uf, cidade):
    geolocator = Nominatim(user_agent="SpaceEye")
    location = geolocator.geocode(f"{cidade}-{uf}")

    m = folium.Map(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
        attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
        zoom_start=15,
        location=[location.latitude, location.longitude]
    )
    Draw(export=True).add_to(m)

    return {"HTML": m._repr_html_()}

@api.route("/api/images", methods=["POST"])
def getImages():
    if request.json:
        try:
            polygon = Polygon(request.get_json()["Coordenadas"][0])
            catalogo = INPE(polygon).findImage()
            return catalogo.to_json(orient="records")
    
        except Exception as e:
            print(e)
            return {"Erro": str(e)}, 400

@api.route("/api/processImage", methods=["POST"])
def processImage():
    body = request.get_json()
    pol = ast.literal_eval(body["coordinates"])
    if request.json:
        try:
            gdf = INPE(Polygon(pol[0]))    
            gdf.ndviGenerator(body["imageId"])
            return "ok"
        
        except Exception as e:
            print(e)
            return {"Erro": str(e)}, 400

@api.route("/api/raster_view", methods=["POST"])
def rasterView():
    body = request.get_json()
    pol = ast.literal_eval(body["coordinates"])
    gdf = INPE(Polygon(pol[0]))    
    return {"html": gdf.map_with_raster(body["imageId"])}

@api.route("/api/IBGE/uf")
def return_uf():
    with open("datasets/cidades_brasileiras.json", "r", encoding="utf-8") as arq:
        return list(load(arq).keys())

@api.route("/api/IBGE/cidades/<string:uf>")
def return_city(uf):
    with open("datasets/cidades_brasileiras.json", "r", encoding="utf-8") as arq:
        return list(load(arq)[uf])
