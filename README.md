# Test DISC — Eric Falcon Formation

🔗 **Application en ligne : [testdisc-ericfalcon.streamlit.app](https://testdisc-ericfalcon.streamlit.app/)**
— c'est ce lien qui est à envoyer aux stagiaires avant la formation.

*Ce dépôt est la version personnelle et indépendante du test, avec ses cinq modules
complémentaires. Il n'a aucun lien avec le dépôt du CAFOC (`disctest-cafoc.streamlit.app`),
qui reste volontairement limité au seul module DISC de base et évolue séparément.*

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
- Cinq modules complémentaires, facultatifs et décochés par défaut (le module DISC
  seul suffit pour une formation) :
  - Les modules dits « à choix forcés » (Ce qui vous motive, Vos forces naturelles,
    Ennéagramme, Votre instinct dominant) montrent deux affirmations et une échelle
    graduée à 5 points entre elles (« complètement la phrase du haut » … « autant
    l'une que l'autre » … « complètement la phrase du bas »), pas un simple clic
    sur l'une des deux — la réponse peut nuancer plutôt que trancher net. Chaque
    échelon vaut une fraction de point pour le thème visé (1 / 0,75 / 0,5 / 0,25 /
    0 et son complément pour l'autre thème), donc un ancien export qui ne
    connaissait que les deux extrêmes se recalcule à l'identique.
  - **DISC — votre style au travail** : les mêmes 40 affirmations, répondues cette
    fois pour le poste actuel. L'écart avec le profil naturel donne un indice de
    tension (« charge d'adaptation ») et affiche les deux profils sur la même roue.
  - **Sous pression** : 20 affirmations sur une semaine vraiment difficile, notées
    selon quatre modes de réaction (contrôle, persuasion, absorption, retrait).
  - **Ce qui vous motive** : 16 choix forcés (tirés d'une banque de 28 — le
    round robin complet entre les 8 moteurs) entre deux façons de travailler, sur
    8 moteurs (autonomie, maîtrise, reconnaissance, sécurité, sens, lien, statut,
    variété) — chaque moteur affronte plusieurs des autres, avec une exposition
    équilibrée. Un tirage complet de 28 paires (chaque moteur contre chacun des
    autres exactement une fois) est plus rigoureux mais donne l'impression de
    répéter la même comparaison ; réduire à 16 tout en gardant l'équilibre garde
    l'essentiel du signal pour beaucoup moins de lassitude.
  - **Vos forces naturelles** : 24 choix forcés (tirés d'une banque de 36) entre
    deux façons de travailler, sur 12 thèmes originaux répartis en 4 domaines
    (Construire, Mobiliser, Relier, Éclairer) — voir ci-dessous pourquoi ce
    référentiel est original plutôt que repris d'un test du commerce.
  - **Vos moteurs profonds (Ennéagramme)** : les 36 choix forcés de la banque
    en entier — le round robin complet, chaque type comparé une fois à chacun
    des 8 autres, sans exception — entre deux façons de réagir, sur 9 types
    répartis en 3 centres (Corps, Cœur, Tête). Administrer le round robin
    entier plutôt qu'un sous-ensemble (24 items dans une version antérieure)
    élimine toute possibilité qu'un tirage particulier laisse deux types
    jamais comparés l'un à l'autre pour une personne donnée. Le DISC décrit
    le comportement observable ; l'ennéagramme cherche la motivation
    derrière — les deux se complètent sans se recouvrir, et le rapport le
    rappelle explicitement, avec un avertissement sur le fait que ce cadre
    n'a jamais été validé aussi solidement que le DISC. Les résultats sont
    aussi positionnés sur le schéma circulaire traditionnel (les 9 points, le
    triangle 3-9-6 et l'hexagone 1-4-2-8-5-7), pas seulement listés par ordre
    de classement. Référentiel et formulations originaux, pas une reprise
    d'un test existant comme le RHETI de Riso-Hudson (protégé). Noms des 9
    types alignés sur la tradition narrative de l'ennéagramme (Helen Palmer &
    David Daniels, narrativeenneagram.org) : Perfectionniste, Altruiste,
    Performeur, Individualiste, Observateur, Questionneur, Enthousiaste,
    Protecteur, Médiateur. La description de chaque type (vision du monde,
    moteur profond, peur de base — ce qu'il évite structurellement —, forces,
    ce que ça coûte, piste de progression) est nettement plus étoffée que
    dans les autres modules, et se déploie en entier dans la section « Pour
    affiner : lisez les 9 profils complets », classée du score le plus haut
    au plus bas plutôt que par numéro. Le rapport ajoute aussi, pour le type
    dominant (le premier du classement), ses deux « ailes » (les types
    voisins sur le cercle, qui le colorent en permanence) ainsi que son
    point de stress et son point de développement — les deux bouts des
    flèches déjà visibles sur le schéma (le triangle et l'hexagone), lus
    comme des connexions plutôt qu'une simple forme. Cette lecture des
    flèches (stress dans un sens, développement dans l'autre) est
    l'heuristique la plus reproduite dans l'enseignement de l'ennéagramme ;
    comme le reste du module, un cadre public et une écriture originale, pas
    plus validé scientifiquement que le score lui-même. Chacune de ces
    quatre connexions (deux ailes, stress, développement) est en plus
    détaillée pour les 9 types dans une section dépliable : comment elle se
    manifeste concrètement au quotidien pour le type dominant concerné, avec
    un bénéfice et un piège identifiés pour chacune — pas seulement le nom
    du type voisin. Une note dépliable rappelle aussi, avant les résultats,
    qu'un score élevé sur plusieurs types n'a rien d'anormal (tout le monde a
    accès aux 9 structures à des degrés divers) et que c'est la façon
    d'habiter le type qui varie avec le contexte, pas le type lui-même.
  - **Votre instinct dominant** : un complément rapide (9 choix forcés) à
    l'Ennéagramme — lequel des 3 instincts de survie (conservation, social,
    sexuel/un-à-un — affiché « Intimité » côté stagiaire) capte le plus
    l'attention en premier. Cette couche est
    propre à la tradition narrative citée ci-dessus ; le concept lui-même
    (Naranjo) n'appartient à aucune école en particulier. Ne s'active que si
    le module Ennéagramme est aussi pris, la comparaison n'ayant de sens
    qu'une fois le type de base connu. Chaque instinct a, comme les 9 types,
    une description étoffée (ce que ça donne de bien, ce que ça coûte, piste
    de progression), pas seulement une phrase de résumé.

  Quand plusieurs de ces modules sont pris ensemble, le rapport ajoute des
  sections qui croisent leurs résultats (par exemple : qui vous devenez sous
  charge, au regard de votre style naturel).

## Pour le formateur : les 13 profils en un coup d'œil

[`docs/guide-formateur-profils-disc.md`](docs/guide-formateur-profils-disc.md) rassemble les
13 profils que l'application peut renvoyer (les 4 styles simples, leurs 8 combinaisons, et le
profil équilibré), avec pour chacun l'accroche, la description, les forces, les axes de progrès
et le rapport au temps. Pratique à garder sous la main pendant la session, sans avoir à passer
le test soi-même pour se rappeler ce que signifie tel ou tel profil. Ce guide est généré à
partir des mêmes textes que ceux montrés aux stagiaires (`data/disc_descriptions.json`) via
`python3 scripts/build_trainer_guide.py` — à relancer si vous modifiez les descriptions.

## Le module « Forces » : un référentiel original, pas CliftonStrengths

Le projet d'origine ([dzyla/disc-personality-assessment](https://github.com/dzyla/disc-personality-assessment),
licence MIT) proposait un module « forces » (Signature strengths) qui reprenait le
référentiel des 34 thèmes CliftonStrengths de Gallup (les noms des thèmes eux-mêmes,
et les 4 domaines qui les regroupent) — une évaluation commerciale déposée, donc pas
un contenu à diffuser librement, même traduit.

Cette version française a donc remplacé ce référentiel par une taxonomie maison de
12 thèmes originaux, répartis en 4 domaines (Construire, Mobiliser, Relier,
Éclairer), avec ses propres noms, descriptions et 36 questions de choix forcé
(`data/strengths_themes.json`, `data/strengths_items.json`). Aucun nom de thème ni
de domaine de Gallup n'y figure ; seul le principe général (des choix forcés entre
deux façons de travailler pour dégager un profil de points forts) est conservé,
comme la même distinction existe pour le modèle DISC lui-même, entre le modèle de
William Marston, qui est dans le domaine public, et des formulations commerciales
précises comme le « DISC Classic »® que ce projet n'utilise pas.

## Le module « Ennéagramme » : cadre public, formulations originales

Contrairement à CliftonStrengths, l'ennéagramme (9 types répartis en 3 centres —
Corps, Cœur, Tête) n'appartient à aucun éditeur : c'est un cadre partagé par de
nombreuses écoles depuis des décennies, sans nomenclature déposée unique. Ce qui
est protégé, en revanche, ce sont des instruments précis construits dessus —
notamment le RHETI (Riso-Hudson Enneagram Type Indicator). Ce module ne reprend
aucune question ni formulation d'un test existant : les 9 types, leurs
descriptions et les 36 questions de choix forcé (`data/enneagram_types.json`,
`data/enneagram_items.json`) sont une écriture originale de ce cadre public.
Le schéma circulaire (9 points, triangle et hexagone) utilisé pour positionner
les résultats est le symbole public de l'ennéagramme lui-même, pas un visuel
propre à un test commercial. Les 3 instincts de survie (conservation, social,
sexuel/un-à-un) suivent la même logique : le concept est public (Naranjo),
seule la formulation des 9 questions (`data/instinct_items.json`) est
originale.

À noter aussi, pour cadrer avec les stagiaires : l'ennéagramme n'a jamais fait
l'objet d'une validation scientifique aussi solide que le DISC lui-même (qui
n'est déjà pas un instrument clinique). Le rapport le rappelle explicitement à
côté des résultats — ce module est une piste de réflexion complémentaire au
DISC, pas un diagnostic.

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

**Ce qui part vers le Sheet.** Les huit premières colonnes (style, titre,
intensité, confiance, scores D/I/S/C) partent dès que le module DISC est
terminé — c'est le seul module obligatoire. Si un·e stagiaire fait aussi l'un
des six modules complémentaires (facultatifs), huit colonnes de plus
s'ajoutent avec un résumé de chacun (style au travail, indice de tension,
mode sous pression, moteurs principaux, points forts principaux, type
Ennéagramme principal, instinct dominant) ; elles restent vides sinon. Un·e stagiaire peut voir
ses résultats DISC, puis revenir en ajouter un depuis la même page (« Pour
aller plus loin ») : l'application renvoie alors une seconde ligne, plus
complète que la première — pour une même personne, c'est donc la ligne la
plus récente (colonne Horodatage) qui compte. Si vous aviez déjà ce Sheet en
service avant ces colonnes, aucune reprise n'est nécessaire : redéployez
simplement le script mis à jour (voir ci-dessous) et il complète tout seul la
ligne d'en-têtes existante à la prochaine réponse enregistrée, sans toucher
aux lignes déjà là.

**Si le secret est configuré mais que les stagiaires voient quand même
l'avertissement « problème technique » :**

- Rouvrez `docs/apps_script.gs` **et redéployez-le** (Déployer > Gérer les
  déploiements > icône crayon > Nouvelle version) — un simple enregistrement
  dans l'éditeur ne suffit pas, l'URL `/exec` continue sinon de pointer vers
  l'ancienne version du script tant qu'une nouvelle version n'est pas
  publiée.
- Vérifiez que le déploiement est bien configuré avec « Qui a accès : Tout
  le monde » (pas « Tout le monde sauf les utilisateurs anonymes »), sinon
  Google répond par une page de connexion au lieu d'enregistrer la ligne.
- Regardez les journaux de l'application sur Streamlit Community Cloud
  (menu **⋮ > Manage app**, puis l'onglet des logs) : une ligne commençant
  par « Sheet sync » y indique la cause exacte de l'échec (code HTTP renvoyé
  par Apps Script, ou erreur réseau).
- Un test depuis le journal d'exécution d'Apps Script (bouton ▶ Exécuter sur
  `doPost` ou `doGet` directement dans l'éditeur) déclenche toujours une
  erreur « requete_vide », même quand le webhook fonctionne très bien
  autrement : ce test simule un appel sans aucune requête HTTP réelle, donc
  sans aucune donnée à lire. Ce n'est pas un signe que le webhook est cassé.
  Pour un vrai test, ouvrez l'URL `/exec` dans un navigateur, ou faites
  passer le test DISC en entier depuis l'application.

## Analyser une session (formateur qui n'a que le Google Sheet)

[`docs/portrait-session-formateur.html`](docs/portrait-session-formateur.html) est un outil
autonome pour le formateur qui n'a accès qu'au Google Sheet des résultats (pas à l'application,
ni aux PDF envoyés par les stagiaires). C'est un simple fichier HTML : pas d'installation, pas de
serveur, pas de compte à créer. Quand le CSV contient les colonnes des modules complémentaires
(voir ci-dessus), la fiche de chaque stagiaire les affiche aussi, dans une section « Modules
complémentaires » — absente pour qui n'a fait que le DISC.

1. Dans le Google Sheet, **Fichier > Télécharger > Valeurs séparées par des virgules (.csv)**.
2. Ouvrez `docs/portrait-session-formateur.html` en double-cliquant dessus (il s'ouvre dans le
   navigateur).
3. Déposez le fichier CSV téléchargé sur la page.

L'outil regroupe les lignes par session, affiche une lecture d'ensemble du groupe (répartition
des styles, points d'attention, profils à confiance faible) et la fiche complète de chaque
stagiaire — les mêmes textes que ceux du rapport remis au stagiaire et du guide formateur
ci-dessus. Tout se lit et se calcule dans le navigateur : rien n'est envoyé sur un serveur, et
rien n'est conservé une fois la page fermée — un choix voulu, puisque le fichier contient les
noms et les scores des stagiaires.

Comme le guide formateur, cet outil est généré à partir de `data/disc_descriptions.json` via
`python3 scripts/build_portrait_session.py` — à relancer si vous modifiez les descriptions.

**En cliquant sur le fichier depuis le site GitHub, vous voyez le code au lieu de la page.**
C'est normal : GitHub affiche toujours le contenu source d'un fichier `.html`, il ne l'exécute
jamais dans la page. Deux façons d'avoir la vraie page :

- **Le plus simple** : sur la page du fichier, cliquez sur **Raw** (au-dessus du code), puis
  enregistrez la page (**Ctrl/Cmd+S**) ou faites un clic droit **Enregistrer sous** — vous obtenez
  le fichier `.html` sur votre ordinateur, à ouvrir ensuite en double-cliquant.
- **Pour un lien à partager sans rien télécharger** : activez GitHub Pages une fois pour toutes —
  **Settings** du dépôt **> Pages**, source **Deploy from a branch**, branche `main`, dossier
  `/docs`, **Save**. GitHub vous donne alors une adresse du type
  `https://<votre-compte>.github.io/<nom-du-depot>/portrait-session-formateur.html`, qui affiche
  la page directement (elle se met à jour à chaque `git push`). Le guide formateur
  (`guide-formateur-profils-disc.md`) restera lui affiché en Markdown par GitHub, comme
  aujourd'hui — cette activation ne change que le rendu des fichiers `.html`.

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

**Important — la version de Python d'une application ne peut pas être changée après son
premier déploiement**, même avec `runtime.txt` : Streamlit Community Cloud choisit la
version de Python une seule fois, au moment où vous cliquez sur **Deploy** la toute
première fois (par défaut la dernière version, actuellement Python 3.14, à moins de la
changer explicitement) — ni un `git push`, ni **Reboot app** dans le menu **⋮**, ne la
changent ensuite. Si votre application a déjà été déployée une première fois avec la
mauvaise version, il faut :

1. Noter ses réglages : sous-domaine personnalisé, dépôt/branche/fichier GitHub, et les
   secrets déjà configurés (`Settings > Secrets`).
2. La supprimer (menu **⋮ > Delete app**).
3. La redéployer à l'identique (**New app**, mêmes dépôt/branche/fichier), mais avant de
   cliquer sur **Deploy**, ouvrir **Advanced settings** et choisir **Python version :
   3.12** dans le menu déroulant — c'est ce menu, pas `runtime.txt`, qui fixe la version
   réellement utilisée. Redonnez le même sous-domaine et recollez les secrets dans ce
   même écran.

`runtime.txt` reste dans ce dépôt à titre indicatif, mais ne comptez que sur le menu
**Advanced settings** au moment du déploiement pour obtenir Python 3.12.

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
français. Le module « Forces » du projet d'origine, lui, a été remplacé par un
référentiel entièrement original plutôt que traduit (voir plus haut).

Ce test est un instrument d'auto-évaluation, pas un outil clinique ni de
recrutement : il mesure comment une personne se décrit elle-même à un instant
donné, ce qui est utile à connaître mais ne remplace pas un échange direct.
