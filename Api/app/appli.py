from flask import Flask, render_template
#from pymongo import MongoClient
import pymongo
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

# Connexion à la base de données MongoDB
client = pymongo.MongoClient('mongo', 27017)
db = client["Powerlifting"]
collection = db["power"]

# Fonction pour générer les graphiques
def generate_graphs():
    # Pipeline et exécution pour les hommes
    pipeline_hommes =  [
    {"$match": {"sexe": "H"}},
    {"$project": {"_id": 0, "poids": 1}},
    {"$bucket": {
        "groupBy": "$poids",
        "boundaries": [-float('inf'), 59, 66, 74, 83, 93, 105, 120, float('inf')],
        "default": "Unknown",
        "output": {"count": {"$sum": 1}}
    }}
] # Votre pipeline pour les hommes
    resultats_hommes = list(collection.aggregate(pipeline_hommes))
    categories_hommes = [result["count"] for result in resultats_hommes]

    # Pipeline et exécution pour les femmes
    pipeline_femmes = [
    {"$match": {"sexe": "F"}},
    {"$project": {"_id": 0, "poids": 1}},
    {"$bucket": {
        "groupBy": "$poids",
        "boundaries": [-float('inf'), 47, 52, 57, 63, 69, 76, 84, float('inf')],
        "default": "Unknown",
        "output": {"count": {"$sum": 1}}
    }}
]  # Votre pipeline pour les femmes
    resultats_femmes = list(collection.aggregate(pipeline_femmes))
    categories_femmes = [result["count"] for result in resultats_femmes]

    # Création des graphiques
    plt.figure(figsize=(15, 8))

    # Graphique 1 - Hommes
    plt.subplot(4, 3, 1)
    labels_hommes = ["- 59 kg", "- 66 kg", "- 74 kg", "- 83 kg", "- 93 kg", "- 105 kg", "- 120 kg", "+ 120 kg"]
    plt.bar(labels_hommes, categories_hommes, color='blue')
    plt.title("Répartition des poids des hommes")
    plt.xlabel("Catégorie de poids")
    plt.ylabel("Nombre de participants")
    plt.xticks(rotation='vertical')

    # Ajouter un commentaire sous le graphique des femmes
    plt.annotate("""Vous pouvez voir au dessus la répartition des hommes dans les différentes catégories. 
                 En effet, la catégorie est primordiale car la performance dans ce sport est très liée au poids.
                 Pour comparer, des athlètes entre les différents genre et poids on utilise 
                 le "goodlift" qui est une sorte de rapport poids-puissance qui dépends aussi du sexe.""",
             xy=(0.5, -1), xycoords="axes fraction",
             ha="center", va="center", fontsize=10, color='gray')


    # Graphique 2 - Femmes
    plt.subplot(5, 3, 3)
    labels_femmes = ["- 47 kg", "- 52 kg", "- 57 kg", "- 63 kg", "- 69 kg", "- 76 kg", "- 84 kg", "+ 84 kg"]
    plt.bar(labels_femmes, categories_femmes, color='pink')
    plt.title("Répartition des poids des femmes")
    plt.xlabel("Catégorie de poids")
    plt.ylabel("Nombre de participantes")
    plt.xticks(rotation='vertical')

    # Ajouter un commentaire sous le graphique des femmes
    plt.annotate("""Vous pouvez voir au dessus la répartition des femmes dans les différentes catégories. 
                 """,
             xy=(0.4, -1), xycoords="axes fraction",
             ha="center", va="center", fontsize=10, color='gray')


    # Graphique 3 - Mon choix
    ### début
    # Calculer la répartition du sexe (hommes, femmes, inconnu)
    plt.subplot(5, 3, 10)
    pipeline = [
        {"$group": {"_id": "$sexe", "count": {"$sum": 1}}},
        {"$project": {"sexe": "$_id", "count": 1, "_id": 0}},
    ]

    resultats = list(collection.aggregate(pipeline))

    # Création du graphique camembert
    labels = [resultat["sexe"] if resultat["sexe"] is not None else "Inconnu" for resultat in resultats]
    sizes = [resultat["count"] for resultat in resultats]
    colors = ['blue', 'pink', 'gray']  # Couleurs pour les tranches du camembert

    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title("Répartition des participants par sexe")
    plt.axis('equal')  # Assure l'aspect circulaire du camembert

    # Ajouter un commentaire sous le graphique des femmes
    plt.annotate("""On peut voir ici que ce sport est pratiqué en grande majorité par des hommes.
                 En effet, plus de 3/4 des participants aux compétitions sont des hommes.""",
             xy=(0.4, -0.3), xycoords="axes fraction",
             ha="center", va="center", fontsize=10, color='gray')
    


    # Graphique 4 - Mon choix
    ### début
    # Répartition de l'age des participants aux compétitions
    # Récupération des âges des participants (en excluant les valeurs -1 = age inconnue)
    plt.subplot(5, 3, 9)
    ages = [athlete["age"] for athlete in collection.find({"age": {"$exists": True, "$ne": -1}})]

    # Création de l'histogramme
    plt.hist(ages, bins=20, color='blue', edgecolor='black')
    plt.title("Histogramme d'âge des participants")
    plt.xlabel("Âge")
    plt.ylabel("Nombre de participants")
    #plt.show()
        # Ajouter un commentaire sous le graphique des femmes
    plt.annotate("""Grâce à l'histogram qui représente l'age des participants au Powerlifting.
                 On constate que c'est un sport qui est exclusivement pratiqué par des jeunes.
                 C'est un sport très jeune, en pleine évolution.""",
             xy=(0.5, -0.8), xycoords="axes fraction",
             ha="center", va="center", fontsize=10, color='gray')


    # Graphique 5 - Mon choix
    ### début
    # Evolution du nombre de compétiteurs de powerlifting au cours des années
    # Récupération des année des participants (en excluant les valeurs -1 = age inconnue)
    plt.subplot(5, 3, 15)
    ####
    pipeline = [
        {"$match": {"annee": {"$type": "int"}}},  # Filtrer les documents où 'age' est un entier
        {"$group": {"_id": "$annee", "count": {"$sum": 1}}},  # Compter le nombre d'apparitions de chaque entier
        {"$sort": {"_id": 1}}  # Trier les résultats par ordre croissant de l'entier
    ]

    # Exécuter la requête d'agrégation
    resultats = list(collection.aggregate(pipeline))

    # Extraire les données pour l'axe des x et des y
    x = [entry["_id"] for entry in resultats]
    y = [entry["count"] for entry in resultats]

    # Créer le graphique
    plt.plot(x, y, linestyle='-')

    # Ajouter des labels et un titre
    plt.xlabel('Année')
    plt.ylabel('Nombre de Compétitions')
    plt.title('Evolution du nombre de compétitions par année')

       # Ajouter un commentaire sous le graphique des femmes
    plt.annotate("""On peut voir que le nombre de compétiteurs et aussi de compétition croît chaque année.
                 On peut constater une chute au moment du covid. 
                 La descente à la fin s'explique par le fait qu'on est seulement au mois de janvier 2024.""",
             xy=(0.3, -0.6), xycoords="axes fraction",
             ha="center", va="center", fontsize=10, color='gray')
    ####

    # Enregistrement du graphique dans un objet BytesIO
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    # Conversion de l'objet BytesIO en base64 pour affichage dans HTML
    img_str = "data:image/png;base64," + base64.b64encode(buffer.read()).decode()
    return img_str

# Route principale pour afficher les graphiques
@app.route('/')
def index():
    graphs = generate_graphs()
    return render_template('index.html', graphs=graphs)

if __name__ == '__main__':
    app.run(debug=True, host = "0.0.0.0")
