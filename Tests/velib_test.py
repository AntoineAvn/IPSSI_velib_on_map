import webbrowser
import folium

coordparis = [48.856578, 2.351828]
coordBrassens = [48.831575, 2.304856]
carte = folium.Map(location=coordparis, zoom_start=13)
# webbrowser.open(carte.save('carte_velib.html'))

# add a marker
folium.Marker(coordBrassens, popup='Georges Brassens').add_to(carte)
# add another marker
folium.Marker(coordparis, popup='Paris').add_to(carte)

# save it as html
carte.save('carte_velib.html')

# open it in a browser
webbrowser.open('carte_velib.html')