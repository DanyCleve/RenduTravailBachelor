
# arrête le script si une erreur est détectée
set -e

# connexion à l'instance EC2 pour afficher l'interface graphique

ssh -L 5901:localhost:5901 -i "Serverless_TB-key-pair-uefrankfurt.pem" ubuntu@ec2-35-158-181-75.eu-central-1.compute.amazonaws.com
