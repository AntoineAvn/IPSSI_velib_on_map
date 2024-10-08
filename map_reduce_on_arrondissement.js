var map = function() {
    emit(this.nom_arrondissement_communes, 1); // Émettre chaque arrondissement comme clé avec 1 comme valeur
};

var reduce = function(key, values) {
    return Array.sum(values); // Additionner les valeurs pour obtenir le nombre de stations par arrondissement
};

var count = db.velib.mapReduce(map, reduce, { out: "arrondissement_count" });

// Afficher les résultats
db.arrondissement_count.find();