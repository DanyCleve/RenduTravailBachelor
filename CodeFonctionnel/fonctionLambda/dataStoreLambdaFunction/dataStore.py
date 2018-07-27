#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Fonctionnement : Cette fonction a pour but de créer une table de donnée
"                  portant le nom de fire_data_store dans la base de donnée couchDB
"                  qui contiendra les données de nos capteurs. Ces données sont
"                  reçues dans la variable "event" et passer en parametre
"                  dans notre gestionnaire de fonction (function_handler)
"
"
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import logging
import couchdb


# Connnexion à la base de donnée en utilisant comme nom d'utilisateur 'admin' et mot de passe 'admin'
couch = couchdb.Server('http://admin:admin@raspberrypi.home:5985')


# nous verifions si notre base de donnée existe dans le cas contraire nous la créons
dataBaseName = "fire_data_store"

# nous effectuons le test afin de déterminer si la base de donnée fire_data_store existe
# si c'est le cas on la sélectionne dans le cas contraire on la crée
if dataBaseName in couch:
    # Selection de notre base de donnée
    dataBase = couch[dataBaseName]
else:
    # Création de notre base de donnée
    dataBase = couch.create(dataBaseName)

# Initialisation du logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

"""
@summary:		 Cette méthode permet d'écrire des données dans la table
                 fire_data_store

@param points: 	  event: données d'évenement dans lequel on retrouve les données
                  à écrire dans la table
                  context: informations d'execution de notre fonction

@returns : 		  -------
"""
def function_handler(event, context):

    # affichage de l'évenement reçu dans les logs
    logger.info(event)

    # extraction des valeurs de l'objet 'event' représenté sous forme clé: valeur
    uuid      = event["uuid"]
    time      = event["time"]
    value     = event["value"]
    valueType = event["type"]
    location  = event["location"]
    # affichage des valeurs recupérées dans les logs pour
    # débuggage ou analyse
    logger.info("uuid : " + uuid)
    logger.info("time : " + str(time))
    logger.info("value : " + str(value))
    logger.info("type : " + valueType)
    logger.info("location : " + location)

    # objet JSON qui sera sauvegardé dans la base de donnée couchdb
    Data={
        'uuid':uuid,
        'time':time,
        'value':value,
        'type':valueType,
        'location':location
    }
    # sauvegarde des données dans la base de données
    dataBase.save(Data)

    return
