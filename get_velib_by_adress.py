import pymongo
from pymongo import MongoClient
import webbrowser
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic


# Fonction pour obtenir les coordonnées d'une adresse
def get_coordinates(address):
    geolocator = Nominatim(user_agent="velib_locator")
    location = geolocator.geocode(address)
    if location:
        return (location.latitude, location.longitude)
    else:
        print("Adresse non trouvée.")
        return None


# Create connection to MongoDB
client = MongoClient('localhost', 27017)
db = client['velib']

# Retrieve the collection
velib = db['velib']

# Demande à l'utilisateur de saisir une adresse
adresse = input("Saisissez une adresse: ")
coords = get_coordinates(adresse)

if coords:
    # Calculer la distance entre l'adresse et chaque station
    stations = []
    for station in velib.find():
        coordinates = station.get('coordonnees_geo')
        if coordinates:
            station_coords = (coordinates.get('lat'), coordinates.get('lon'))
            distance = geodesic(coords, station_coords).kilometers
            stations.append((distance, station))

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
            location=[coordinates.get('lat'), coordinates.get('lon')],
            popup=popup_message,
            icon=folium.Icon(color=marker_color, icon='bicycle', prefix='fa')
        ).add_to(m)

    # Sauvegarder la carte en tant que fichier HTML
    m.save('velib_map.html')
    print("Carte générée : velib_map.html")
else:
    print("Impossible de géocoder l'adresse.")

# Open the map in the default web browser
# webbrowser.open('velib_map.html')