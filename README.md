# Test DISC — version française

Une application [Streamlit](https://streamlit.io) qui fait passer un test de personnalité
DISC (Dominance, Influence, Stabilité, Conformité) et restitue un profil détaillé,
avec sa marge d'incertitude plutôt que des chiffres présentés comme définitifs.

Pensée pour être envoyée à des stagiaires avant une formation (par exemple une
formation à la gestion du temps) : chacun passe le test depuis son navigateur,
voit et télécharge son propre profil (PDF ou JSON), et son résultat est envoyé
automatiquement dans un Google Sheet partagé avec le ou les formateurs, qui
peuvent ainsi consulter les profils de tout un groupe avant la session.

```bash
pip install -r requirements.txt
streamlit run disc_style.py
```

Python 3.10 à 3.12 (voir `runtime.txt` — Python 3.13/3.14 déclenchent un bug connu des
`dataclasses` figées de ce projet sur Streamlit Community Cloud, d'où l'épinglage).
Aucun compte, aucun serveur, aucune base de données.

## Ce que ça fait

- 40 affirmations, tirées au hasard dans une banque de 264, réparties équitablement
  entre les quatre dimensions et mélangeant des formulations positives et négatives
  (pour repérer les réponses données au hasard).
- Un profil DISC complet : dimension dominante, mélange des deux dimensions les
  plus fortes, angle mort, environnement de travail où la personne est la plus
  efficace, sources de friction avec les autres profils, conseils de communication.
- Un indice de confiance sur la cohérence des réponses (élevée / modérée / faible),
  avec les raisons quand la confiance est faible.
- Un export PDF et un export JSON (le JSON permet de reprendre le test plus tard,
  ou de comparer un nouveau passage à un ancien).
- Avant de commencer, le stagiaire indique son prénom, son nom et la session de
  formation concernée. À la fin du test, ces informations et son profil DISC
  sont envoyés dans un Google Sheet que vous partagez avec les formateurs (voir
  ci-dessous). Tout le calcul du profil, lui, se fait dans la session Streamlit
  du stagiaire — seul le résultat final part vers le Sheet.

## Pour le formateur : les 13 profils en un coup d'œil

[`docs/guide-formateur-profils-disc.md`](docs/guide-formateur-profils-disc.md) rassemble les
13 profils que l'application peut renvoyer (les 4 styles simples, leurs 8 combinaisons, et le
profil équilibré), avec pour chacun l'accroche, la description, les forces, les axes de progrès
et le rapport au temps. Pratique à garder sous la main pendant la session, sans avoir à passer
le test soi-même pour se rappeler ce que signifie tel ou tel profil. Ce guide est généré à
partir des mêmes textes que ceux montrés aux stagiaires (`data/disc_descriptions.json`) via
`python3 scripts/build_trainer_guide.py` — à relancer si vous modifiez les descriptions.

## Pourquoi seulement le module DISC ?

Le projet d'origine ([dzyla/disc-personality-assessment](https://github.com/dzyla/disc-personality-assessment),
licence MIT) proposait aussi des modules « forces », « sous pression » et
« motivateurs ». Le module « forces » reprend le référentiel des 34 thèmes
CliftonStrengths de Gallup, qui est une évaluation commerciale déposée — ce
n'est donc pas un contenu à diffuser librement. Cette version française ne
conserve que le module DISC, dont le contenu (les 264 affirmations et les
descriptions de profils) est original et n'appartient à aucun test propriétaire
(le modèle DISC lui-même, issu des travaux de William Marston, est dans le
domaine public ; ce qui est protégé, ce sont des formulations commerciales
précises comme le « DISC Classic »® que ce projet n'utilise pas).

Le code des modules retirés reste dans `assessment/scoring/` et
`data/*.json` au cas où on voudrait un jour les réactiver avec un contenu
maison — voir le commentaire dans `assessment/registry.py`.

## Récupérer les résultats des stagiaires (Google Sheet)

Les résultats de chaque stagiaire peuvent s'ajouter automatiquement comme une
ligne dans un Google Sheet, via un petit script Google Apps Script (le fichier
`docs/apps_script.gs` fourni dans ce dépôt) — pas besoin de compte Google Cloud
ni de clé d'API.

1. Créez un Google Sheet vide (par exemple « Résultats DISC »).
2. Menu **Extensions > Apps Script**, puis remplacez le contenu par celui de
   `docs/apps_script.gs` (ouvrez ce fichier pour le copier).
3. Menu **Déployer > Nouveau déploiement**, type **Application Web**,
   « Exécuter en tant que : Moi », « Qui a accès : Tout le monde ».
4. Copiez l'URL fournie (elle se termine par `/exec`).
5. Une fois l'application déployée sur Streamlit Community Cloud (étape
   suivante), allez dans **Settings > Secrets** de l'application et ajoutez :
   ```toml
   SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycb.../exec"
   ```
6. Partagez le Google Sheet (pas le script) avec les formateurs qui doivent
   voir les résultats.

Tant que ce secret n'est pas configuré, l'application fonctionne normalement
pour les stagiaires (test, profil, PDF) : seul l'envoi automatique vers le
Sheet est simplement ignoré.

## Déployer gratuitement, sans serveur (Streamlit Community Cloud)

1. Créez un compte sur [share.streamlit.io](https://share.streamlit.io) (gratuit,
   connexion avec votre compte GitHub).
2. Poussez ce dépôt sur votre propre compte GitHub (voir plus bas).
3. Sur Streamlit Community Cloud, cliquez sur **New app**, choisissez votre
   dépôt, la branche `main`, et indiquez `disc_style.py` comme fichier
   principal.
4. Streamlit installe automatiquement les dépendances (`requirements.txt`) et
   vous donne une URL publique du type `https://<nom>.streamlit.app` — c'est
   ce lien que vous envoyez à vos stagiaires avant la formation.

Chaque mise à jour poussée sur GitHub redéploie automatiquement l'application.

Si votre application a déjà été déployée une première fois **avant** l'ajout du fichier
`runtime.txt`, un simple `git push` ne suffit pas à changer la version de Python déjà
installée : ouvrez le menu **⋮** de l'application sur share.streamlit.io et choisissez
**Reboot app** pour qu'elle soit reprovisionnée avec la version épinglée.

## Mettre le dépôt sur votre GitHub

```bash
git init -b main
git add -A
git commit -m "Test DISC en français pour les formations"
git remote add origin https://github.com/<votre-compte>/<nom-du-depot>.git
git push -u origin main
```

(Si le dossier est déjà un dépôt git, remplacez les deux premières lignes par
`git add -A` et `git commit -m "..."`.)

## Tests

```bash
pip install -r requirements.txt
pytest
```

La suite couvre le tirage des questions, le calcul des scores, la génération
du rapport et du PDF, et le parcours complet de l'application (via le module
de test headless de Streamlit).

## Licence et origine

Ce projet est une adaptation française, pour Eric Falcon Formation, du projet
[dzyla/disc-personality-assessment](https://github.com/dzyla/disc-personality-assessment)
de Dawid Zyla, sous licence MIT (voir `LICENSE`). Le code de calcul et
l'architecture Streamlit viennent du projet d'origine ; les questions, les
descriptions de profils et l'interface ont été traduites et adaptées en
français, et les modules non liés au DISC ont été retirés (voir plus haut).

Ce test est un instrument d'auto-évaluation, pas un outil clinique ni de
recrutement : il mesure comment une personne se décrit elle-même à un instant
donné, ce qui est utile à connaître mais ne remplace pas un échange direct.
