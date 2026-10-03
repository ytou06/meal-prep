# Meal prep à deux

Appli web (iPhone, écran d’accueil) du meal prep mensuel. Les plans sont chiffrés (AES-256-GCM, clé dérivée par PBKDF2) ; l’appli demande le mot de passe une fois par téléphone.

- `index.html` : l'appli
- `data/index.json` : liste des mois publiés
- `data/AAAA-MM.json` : le plan chiffré de chaque mois (mis à jour automatiquement le 1er du mois)
- `tools/crypt.py` : chiffrement et déchiffrement des plans (mot de passe dans `MP_PASSWORD`, jamais dans le dépôt)
