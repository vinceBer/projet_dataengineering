FROM python:3.10
# définit l'image de base à utiliser

WORKDIR /crawler
# définit le repertoire de travail à l'intérieur du conteneur comme crawler

COPY . .
# copie tous les fichier du repertoire local vers le repertoire crawler

RUN pip install -r requirements.txt
# install les dépendances spécifiques

CMD ["python", "crawler/exec.py"]
# commande a executer par défaut quand le conteneur est lancé