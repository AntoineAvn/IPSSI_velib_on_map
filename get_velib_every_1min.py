import pymongo
from pymongo import MongoClient
import webbrowser
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
import schedule
import time
from threading import Thread


# Fonction pour obtenir les coordonnées d'une adresse
def get_coordinates(address):
    geolocator = Nominatim(user_agent="velib_locator")
    location = geolocator.geocode(address)
    if location:
        return (location.latitude, location.longitude)
    else:
        print("Adresse non trouvée.")
        return None


# Connexion à MongoDB
client = MongoClient('localhost', 27017)
db = client['velib']
velib_collection = db['velib']

# URL de l'API Velib
velib_api_url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/records?limit=-1"

# Demande à l'utilisateur de saisir une adresse
adresse = input("Saisissez une adresse: ")
coords = get_coordinates(adresse)


# Fonction pour récupérer les données de l'API Velib
def fetch_velib_data():
    try:
        response = requests.get(velib_api_url)
        response.raise_for_status()
        data = response.json()['results']
        return data
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des données de l'API : {e}")
        return []


# Fonction pour créer et sauvegarder la carte
def create_and_save_map():
    if not coords:
        print("Coordonnées invalides, carte non générée.")
        return

    # Calculer la distance entre l'adresse et chaque station
    stations = []
    for station in velib_collection.find():
        fields = station
        coordinates = fields.get('coordonnees_geo')
        if coordinates:
            station_coords = (coordinates['lat'], coordinates['lon'])
            distance = geodesic(coords, station_coords).kilometers
            stations.append((distance, fields))

    # Trier les stations par distance et prendre les 10 plus proches
    stations = sorted(stations, key=lambda x: x[0])[:10]

    # Créer une carte centrée sur l'adresse saisie
    m = folium.Map(location=coords, zoom_start=14)

    # Ajouter un marqueur pour l'adresse saisie
    folium.Marker(
        location=coords,
        popup="Vous êtes ici",
        icon=folium.Icon(color='blue', icon='location-pin', prefix='fa')
    ).add_to(m)

    # Ajouter les marqueurs des 10 stations les plus proches
    for distance, station in stations:
        name = station.get('name')
        coordinates = station.get('coordonnees_geo')
        num_bikes = station.get('numbikesavailable', 0)
        num_docks = station.get('numdocksavailable', 0)
        mechanical = station.get('mechanical', 0)
        ebike = station.get('ebike', 0)
        capacity = station.get('capacity', 0)
        arrondissement = station.get('nom_arrondissement_communes')
        is_renting = station.get('is_renting', 'Non')

        # Créer un message popup personnalisé
        popup_message = f"""
        <b>Station:</b> {name}<br>
        <b>Arrondissement:</b> {arrondissement}<br>
        <b>Capacité totale:</b> {capacity}<br>
        <b>Vélos disponibles:</b> {num_bikes} (Mécaniques: {mechanical}, Électriques: {ebike})<br>
        <b>Places libres:</b> {num_docks}<br>
        <b>En location:</b> {is_renting}<br>
        <b>Distance:</b> {distance:.2f} km
        """

        # Déterminer la couleur du marqueur
        marker_color = 'green' if num_bikes > 5 else 'orange' if num_bikes > 0 else 'red'

        # Ajouter un marqueur pour chaque station
        folium.Marker(
            location=[coordinates['lat'], coordinates['lon']],
            popup=popup_message,
            icon=folium.Icon(color=marker_color, icon='bicycle', prefix='fa')
        ).add_to(m)

    # Sauvegarder la carte en tant que fichier HTML
    m.save('velib_map.html')
    print("Carte régénérée : velib_map.html")


# Fonction pour insérer les données dans MongoDB et régénérer la carte
def insert_data_to_mongodb():
    data = fetch_velib_data()
    if data:
        # Supprimer l'ancienne collection
        velib_collection.drop()
        # Insérer les nouvelles données
        velib_collection.insert_many(data)
        print("Données mises à jour dans MongoDB.")
        # Régénérer la carte après mise à jour des données
        create_and_save_map()


# Fonction pour démarrer le job de mise à jour
def start_scheduled_job():
    schedule.every(1).minutes.do(insert_data_to_mongodb)
    while True:
        schedule.run_pending()
        time.sleep(1)


# Démarrer la récupération des données dans un thread séparé
data_thread = Thread(target=start_scheduled_job)
data_thread.start()

# Générer la carte initiale
create_and_save_map()

# Open the map in the default web browser
webbrowser.open('velib_map.html')
