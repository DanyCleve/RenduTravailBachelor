#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import time
import datetime
import calendar
import logging
import os
import uuid

from random import *
from grovepi import *
from grove_rgb_lcd import *
from time import sleep
from math import isnan
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

# connexion du capteur de temperature sur le port D7
dht_sensor_port = 7 
# type du capteur: 0 pour la couleur bleu et 1 pour le blanc 
dht_sensor_type = 0 

# Connexion du capteur de gaz sur le port A0
gas_sensor = 0

# affiche le message au format JSON
def printMessage(message):
    print('Received message on topic %s: %s\n' %(message.topic, message.payload))

# Lecture des données passées en paramètre
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-n", "--thingName", action="store", dest="thingName", default="test1", help="Targeted thing name")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="sensors/cloud/dataStore", help="Targeted topic")
parser.add_argument("-m", "--mode", action="store", dest="mode", default="both",
                    help="Operation mode: publish")

args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
clientId = args.thingName
topic = args.topic

# vérification si le mode passé en paramètre est correct
if args.mode != 'publish':
    parser.error("Unknown --mode option %s. Must be %s" % (args.mode, 'publish'))
    exit(2)

# vérification des données d'authentification du périphérique avec AWS IOT
if not args.certificatePath or not args.privateKeyPath:
    parser.error("Missing credentials for authentication.")
    exit(2)

# configuration de la journalisation 
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# établissement de la connexion MQTT
myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
myAWSIoTMQTTClient.onMessage = printMessage
myAWSIoTMQTTClient.configureEndpoint(host, 8883)
myAWSIoTMQTTClient.connect()


"""
@summary:		 Cette méthode permet de générer des UUID dans un fichier en fonction
                 du nombre de capteur passés en paramètres et de lire le meme fichier
                 afin de retourner les UUID stockés
				 
@param points: 	 sensorNb: nombre de capteur dans la maison 

@returns : 		 uuid    : liste des UUID générés
"""
def generateUUID(sensorNb):
    # nom du fichier dans lequel sera stocké nos différents UUID
    nameFile = "UUIDList.txt"
    path = "./" + nameFile
    UUIDList = []
    if sensorNb != 0:
        while sensorNb:
            file = open(nameFile,"a")
            uuidSensor = str(uuid.uuid4()) + "\n"
            file.write(uuidSensor)
            file.close()
            sensorNb -= 1
        
        with open(nameFile) as file:
            for line in file:
                UUIDList.append(line.strip())
        return UUIDList
    if sensorNb == 0 and os.path.exists(path):
        with open(nameFile) as file:
            for line in file:
                UUIDList.append(line.strip())
        return UUIDList

"""
@summary:		 Cette méthode permet de publier un message json sur la
                 rubrique passé en paramètre portant le nom de "topic"
				 
@param points: 	  type    : type du capteur 
                  value   : valeur délivrée par le capteur
                  location: lieu oû se situe le capteur dans la maison
                  uuid    : identificateur unique pour chaque capteur

@returns : 		  -------
"""
def publishValue(type, value, location, uuid):

    message = {}
    # uuid du capteur
    message['uuid'] = uuid
    date = datetime.datetime.now()
    # récupération du timestamp sous le format POSIX
    message['time'] = calendar.timegm(date.timetuple())
    # recupération de la valeur délivrée par le capteur 
    message['value'] = value
    # type de capteur délivrant la valeur ci-dessus
    message['type'] = type
    # localisation du capteur
    message['location'] = location
    global topic
    messageJson = json.dumps(message)
    myAWSIoTMQTTClient.publish(topic, messageJson, 0)
    if args.mode == 'publish':
        print('Published on topic %s: %s\n' % (topic, messageJson))

# création et affectation de la liste des UUID
# si le programme est redemarré veuillez mettre sensorNb à 0 afin de lire le fichier
# si ajout de capteur veuillez entrer le nombre de capteur ajouté
# initialisation du nombre de capteur
sensorNb = 0
UUIDList = []
UUIDList = generateUUID(sensorNb)
# boucle infinie permettant de publier des valeurs générer par chaque capteur
while True:
    if args.mode == 'publish':
        # Génération des UUID en fonction du nombre de capteur
        
        # récupération des valeurs de gaz depuis le capteur de gaz
        pinMode(gas_sensor,"INPUT")
        sensorValue = analogRead(gas_sensor)
        
        if isnan(sensorValue) == False:
            s = sensorValue
            # calcul de la densité du gaz (une grande valeur signifie que le gaz est dense)
            density = (float)(sensorValue / 1024)
            print("sensorValue =", sensorValue, " density =", density)

        # récupération des données de température et de pression depuis le capteur
        [ temp,hum ] = dht(dht_sensor_port,dht_sensor_type)

        if isnan(temp) == False and isnan(hum) == False:
            print("temp =", temp, "C\thumidity =", hum,"%")
            t = temp
            h = hum
        
        # génération de deux valeurs aléatoire de température
        t1 = round(uniform(22,28), 1)
        t2 = round(uniform(22,28), 1)
        # génération aléatoire de valeurs de pression
        p = randint(10,30)
        
        # affichage de nos données sur l'écran LCD
        setRGB(0,128,64)
        setText_norefresh("T1:" + str(temp) + " " + "T2:" + str(t1) + " \n" + "T3:" + str(t2) + " " + "Sm:" + str(s) + "%")
        
        publishValue("temperature", t, "001 salon", UUIDList[0])
        publishValue("temperature", t1, "001 chambre", UUIDList[1])
        publishValue("temperature", t2, "001 cuisine", UUIDList[2])
        publishValue("humidity", h, "001 chambre", UUIDList[3])
        publishValue("smoke", s, "001 cuisine", UUIDList[4])
        publishValue("pressure", p, "001 salon", UUIDList[5])
    # nous publions des données chaque 30 secondes mais ce temps peut etre changer à notre guise
    time.sleep(30)
