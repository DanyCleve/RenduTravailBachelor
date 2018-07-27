# Script Bash permettant l'éxécution en ligne de commande de notre script python en lui passant les identifiants de connexion en arguments

# arrete le script si une erreur survient
set -e

# exécute le script python button.py
python2.7 button.py --endpoint a19taqm0wo1suf.iot.eu-central-1.amazonaws.com --rootCA root-ca-cert.pem --cert button.cert.pem --key button.private.key --thingName fireCheck --clientId alarm
