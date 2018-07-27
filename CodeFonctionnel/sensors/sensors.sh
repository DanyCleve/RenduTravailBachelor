# Script Bash permettant l'éxécution en ligne de commande de notre script python en lui passant les identifiants de connexion en arguments

# arrete le script si une erreur survient
set -e

# exécute le script python sensors.py
python2.7 sensors.py --endpoint a19taqm0wo1suf.iot.eu-central-1.amazonaws.com --rootCA root-ca-cert.pem --cert sensors.cert.pem --key sensors.private.key --mode publish
