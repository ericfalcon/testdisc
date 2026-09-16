/**
 * Reçoit les résultats du test DISC (envoyés par l'application Streamlit) et
 * les ajoute comme une nouvelle ligne dans la feuille active.
 *
 * Installation :
 * 1. Ouvrez (ou créez) le Google Sheet qui doit recevoir les résultats.
 * 2. Menu Extensions > Apps Script.
 * 3. Collez ce fichier à la place du contenu par défaut (Code.gs).
 * 4. Menu Déployer > Nouveau déploiement > type "Application Web".
 *    - Exécuter en tant que : Moi.
 *    - Qui a accès : Tout le monde.
 * 5. Copiez l'URL fournie (se termine par /exec) : c'est SHEET_WEBHOOK_URL.
 * 6. Sur Streamlit Community Cloud : Settings > Secrets, ajoutez :
 *      SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycb.../exec"
 * 7. Partagez le Google Sheet (pas le script) avec les formateurs qui doivent
 *    voir les résultats.
 *
 * Si vous modifiez le script après un premier déploiement, utilisez
 * Déployer > Gérer les déploiements > icône crayon > Nouvelle version, sinon
 * l'URL /exec continue de pointer vers l'ancienne version du code.
 *
 * Pourquoi doGet et pas doPost ? Une requête POST envoyée à une URL /exec est
 * en réalité redirigée en interne vers une URL script.googleusercontent.com,
 * et la plupart des clients HTTP (dont la bibliothèque Python "requests",
 * comme un navigateur) transforment alors cette redirection en GET et
 * perdent le corps de la requête au passage — doPost() se retrouve appelé
 * sans aucune donnée, ce qui provoque justement une erreur du type
 * "Cannot read properties of undefined (reading 'postData')" dans le journal
 * d'exécution. Le contenu envoyé ici tient dans quelques dizaines de
 * caractères, donc l'application Streamlit l'envoie en paramètres d'URL
 * (GET) : une redirection GET → GET ne pose pas ce problème. doPost() est
 * conservé ci-dessous par sécurité (au cas où un autre client l'utiliserait
 * un jour), mais ce n'est plus le chemin emprunté par cette application.
 *
 * Remarque sur le journal d'exécution : si vous testez ce script en cliquant
 * sur ▶ Exécuter dans l'éditeur (en choisissant doPost ou doGet), il n'y a
 * alors aucune requête HTTP réelle, donc pas de paramètres — vous obtiendrez
 * la même erreur "requete_vide" ci-dessous, ce qui est normal et ne veut pas
 * dire que le webhook est cassé. Pour vraiment tester : ouvrez l'URL /exec
 * dans un navigateur (déclenche doGet et doit afficher le message de
 * confirmation), ou faites passer le test DISC en entier depuis l'application
 * Streamlit et regardez la ligne apparaître dans la feuille.
 */

var EN_TETES = [
  "Horodatage", "Prénom", "Nom", "Session / formation",
  "Style DISC", "Titre du profil", "Intensité", "Confiance",
  "Score D", "Score I", "Score S", "Score C",
];

function doGet(e) {
  var parametres = e && e.parameter;
  if (parametres && parametres.style_code) {
    return enregistrerResultat(parametres);
  }
  return ContentService
    .createTextOutput("Le webhook DISC fonctionne. Utilisez une requête GET avec des paramètres pour enregistrer un résultat.")
    .setMimeType(ContentService.MimeType.TEXT);
}

// Conservé par sécurité — voir la remarque en haut de ce fichier sur
// pourquoi l'application Streamlit utilise désormais doGet.
function doPost(e) {
  var corps = e && e.postData && e.postData.contents;
  if (!corps) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, erreur: "requete_vide" }))
      .setMimeType(ContentService.MimeType.JSON);
  }
  return enregistrerResultat(JSON.parse(corps));
}

function enregistrerResultat(donnees) {
  var feuille = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  assurerEnTetes(feuille);

  feuille.appendRow([
    donnees.horodatage || new Date().toISOString(),
    donnees.prenom || "",
    donnees.nom || "",
    donnees.session || "",
    donnees.style_code || "",
    donnees.style_titre || "",
    donnees.intensite || "",
    donnees.confiance || "",
    Number(donnees.score_D),
    Number(donnees.score_I),
    Number(donnees.score_S),
    Number(donnees.score_C),
  ]);

  return ContentService
    .createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}

function assurerEnTetes(feuille) {
  if (feuille.getLastRow() === 0) {
    feuille.appendRow(EN_TETES);
    feuille.setFrozenRows(1);
  }
}
