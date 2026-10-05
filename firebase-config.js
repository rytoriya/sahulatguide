/*
 * Sahulat Guide: Firebase project settings for sign-up and log in.
 *
 * Leave this as null and the site works in "device only" mode: people can still
 * save their details, but only in their own browser.
 *
 * To switch accounts on, create a free Firebase project and paste its web app
 * config below (see README → "Accounts"). These values are public by design;
 * the security comes from firestore.rules.
 */
window.SG_FIREBASE_CONFIG = null;

/* Example:
window.SG_FIREBASE_CONFIG = {
  apiKey: "AIza...",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project",
  appId: "1:1234567890:web:abc123"
};
*/
