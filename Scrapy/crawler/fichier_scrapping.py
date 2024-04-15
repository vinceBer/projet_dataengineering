import scrapy
import json
import pandas as pd
from scrapy import signals
from twisted.internet import reactor
# On importe le module pymongo
import pymongo
from datetime import datetime, date

class OpenPowerliftingSpider(scrapy.Spider):
    name = 'openpowerlifting'
    allowed_domains = ['www.openpowerlifting.org']
    global_result_list = []  # Liste pour stocker les résultats globaux

    def __init__(self, *args, **kwargs):
        super(OpenPowerliftingSpider, self).__init__(*args, **kwargs)
        self.data_frames = []  # Liste pour stocker les DataFrames à chaque itération

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(OpenPowerliftingSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def start_requests(self):
        base_url = 'https://www.openpowerlifting.org/api/rankings?start={start}&end={end}&lang=fr&units=kg'
        start, end = 0, 99  # le scrapping ne peut faire que 100 lignes à la fois car les "100" lignes sont sur des urls différents (l'url change); c'est pourquoi on doit boucles pour avoir toutes les données présentes sur tous les urls

        while end <= 10000:#481000: #2000:  # Assurez-vous que la dernière valeur d'end est correcte
            yield scrapy.Request(url=base_url.format(start=start, end=end), callback=self.parse)
            start += 100
            end += 100

    def parse(self, response):
        data_dict = json.loads(response.text)

        # Extraction des données pertinentes
        rows = data_dict.get('rows', [])

        # Extraire les colonnes 4, 8 et 9 de chaque ligne
        selected_columns = [[row[i] for i in [0, 2, 6, 9, 14, 15, 18, 17, 13, 19, 20, 21, 22, 23]] for row in rows]

        # Créer un DataFrame avec les colonnes sélectionnées
        df = pd.DataFrame(selected_columns, columns=['athlete_rank', 'athlete_name', 'pays', 'annee', 'equipement', 'age', 'class', 'poids', 'sexe', 'squat', 'bench', 'deadlift', 'total', 'dots'])

        # Conversion des données
        colonnes_numeriques = ['age', 'poids', 'squat', 'bench', 'deadlift', 'total', 'dots']
        colonnes_float = ['poids', 'squat', 'bench', 'deadlift', 'total', 'dots']
        colonne_class = ['class']
        colonnes_int = ['age']

        ##### conversion pour les données numériques
        # remplacer les virgules par des points
        df[colonnes_numeriques  + colonne_class] = df[colonnes_numeriques + colonne_class].replace(',', '.', regex=True)
        # remplacer les caractères qui ne correspondent pas à un réel
        df[colonnes_numeriques] = df[colonnes_numeriques].replace(r'[^0-9.]', '', regex=True)
        # remplacer les strings vides
        df[colonnes_numeriques] = df[colonnes_numeriques].replace('', -1)
        # remplace les Na par -1
        df[colonnes_numeriques] = df[colonnes_numeriques].fillna(-1)
        # convertir en donnnées numériques
        df[colonnes_float] = df[colonnes_float].astype(float)
        df[colonnes_int] = df[colonnes_int].astype(int)

        ##### conversion pour les données strings
        colonnes_strings = ['athlete_name', 'pays', 'equipement']
        colonne_sexe = ['sexe']
        # remplacer les strings vides
        df[colonnes_strings + colonne_class + colonne_sexe] = df[colonnes_strings + colonne_class + colonne_sexe].replace('', 'inconnue')
        # remplace les Na par inconnue
        df[colonnes_strings + colonne_class + colonne_sexe] = df[colonnes_strings + colonne_class + colonne_sexe].fillna('inconnue')
        # conversion de type 
        df[colonnes_strings] = df[colonnes_strings].astype(str)

        # Convertissez la colonne 'date' en type datetime
        df['annee'] = pd.to_datetime(df['annee'])

        # Extrayez l'année dans une nouvelle colonne 'year'
        df['annee'] = df['annee'].apply(lambda x: x.year)
        # remplacer les strings vides
        df['annee'] = df['annee'].replace('', -1)
        # remplace les Na par -1
        df['annee'] = df['annee'].fillna(-1)
        # convertir en entier les années (plus simple à utiliser pour ce qu'on va en faire après)
        df['annee'] = df['annee'].astype(int)

        self.global_result_list.append(df.to_dict(orient='records'))

        # Ajouter le DataFrame à la liste
        self.data_frames.append(df)

    def spider_closed(self, spider, reason):
        # Concaténer tous les DataFrames en un seul
        final_df = pd.concat(self.data_frames, ignore_index=True)

        # Convertir le DataFrame en dictionnaire
        result_dict = final_df.to_dict(orient='records')

        client = pymongo.MongoClient('mongo', 27017) # connexion à la base mongo
        client.drop_database("Powerlifting") # on supprime la base de DO si elle existe déjà (car on fait comme si on voulait qu'il n'y ait rien dedans par défaut mais ça pourait être un autre cas dans un contexte différent)
        db = client["Powerlifting"] # on crée la base de DO
        collection = db["power"] # on crée une nouvelle collection
        collection.insert_many(result_dict) # on ajoute toutes les données en même temps dans la base de Do Mongo

        # Arrêter le réacteur
        reactor.stop()