FROM python:3.10
# définit l'image de base à utiliser

WORKDIR /app
# définit le repertoire de travail à l'intérieur du conteneur comme app

COPY ./ ./
# copie tous les fichier du repertoire local vers le repertoire app

RUN pip install -r requirements.txt
# install les dépendances spécifiques

EXPOSE 5000
# expose le port 5000 du conteneur

CMD ["python", "/app/app/appli.py"]
# commande a executer par défaut quand le conteneur est lancé