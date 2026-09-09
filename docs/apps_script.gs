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
 */

var EN_TETES = [
  "Horodatage", "Prénom", "Nom", "Session / formation",
  "Style DISC", "Titre du profil", "Intensité", "Confiance",
  "Score D", "Score I", "Score S", "Score C",
];

function doPost(e) {
  var feuille = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  assurerEnTetes(feuille);

  var donnees = JSON.parse(e.postData.contents);

  feuille.appendRow([
    donnees.horodatage || new Date().toISOString(),
    donnees.prenom || "",
    donnees.nom || "",
    donnees.session || "",
    donnees.style_code || "",
    donnees.style_titre || "",
    donnees.intensite || "",
    donnees.confiance || "",
    donnees.score_D,
    donnees.score_I,
    donnees.score_S,
    donnees.score_C,
  ]);

  return ContentService
    .createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}

// Permet de vérifier que le déploiement fonctionne en ouvrant l'URL /exec
// directement dans un navigateur.
function doGet() {
  return ContentService
    .createTextOutput("Le webhook DISC fonctionne. Utilisez une requête POST pour envoyer un résultat.")
    .setMimeType(ContentService.MimeType.TEXT);
}

function assurerEnTetes(feuille) {
  if (feuille.getLastRow() === 0) {
    feuille.appendRow(EN_TETES);
    feuille.setFrozenRows(1);
  }
}
