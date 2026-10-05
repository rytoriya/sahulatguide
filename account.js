/*
 * Sahulat Guide accounts and saved details ("My details").
 *
 * Include on any page:   <script src="account.js" defer></script>  (adjust the path)
 * Header button slot:    <span data-sg-account></span>  (data-sg-account="on-dark compact" also works)
 * Autofill a form field: <input data-profile="name">  (keys: name father mobile email cnic dob city district province address)
 *
 * Accounts use Firebase (settings in firebase-config.js). Without settings, details are saved in
 * this browser only. CNIC is never sent to the server: it stays on the person's device.
 */
(function () {
  "use strict";
  if (window.SahulatAccount) return;

  var me = document.currentScript || document.querySelector('script[src*="account.js"]');
  var BASE = new URL(".", me ? me.src : location.href).href;
  var SDK = "https://www.gstatic.com/firebasejs/10.12.2/";

  var FIELDS = [
    { k: "name", label: "Full name (as on CNIC)", ur: "پورا نام", type: "text", auto: "name" },
    { k: "father", label: "Father's / husband's name", ur: "والد / شوہر کا نام", type: "text" },
    { k: "cnic", label: "CNIC number", ur: "شناختی کارڈ نمبر", type: "text", device: true, placeholder: "12345-1234567-1", inputmode: "numeric" },
    { k: "mobile", label: "Mobile number", ur: "موبائل نمبر", type: "tel", auto: "tel", placeholder: "03xx-xxxxxxx" },
    { k: "email", label: "Email", ur: "ای میل", type: "email", auto: "email" },
    { k: "dob", label: "Date of birth", ur: "تاریخ پیدائش", type: "date", auto: "bday" },
    { k: "city", label: "City / town", ur: "شہر", type: "text", auto: "address-level2" },
    { k: "district", label: "District", ur: "ضلع", type: "text" },
    { k: "province", label: "Province / territory", ur: "صوبہ", type: "select", options: ["", "Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan", "Islamabad", "Azad Jammu & Kashmir", "Gilgit-Baltistan"] },
    { k: "address", label: "Home address", ur: "گھر کا پتا", type: "textarea", auto: "street-address" },
  ];
  var CLOUD_KEYS = FIELDS.filter(function (f) { return !f.device; }).map(function (f) { return f.k; });

  /* ---------- local storage (never throws) ---------- */
  function lsGet(k) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : null; } catch (e) { return null; } }
  function lsSet(k, v) { try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }

  var state = { mode: "device", ready: false, user: null, profile: {}, error: null };
  var fb = null; // { auth, db }

  function cnicKey() { return "sg-cnic:" + (state.user ? state.user.uid : "device"); }
  function profileKey() { return state.user ? "sg-profile:" + state.user.uid : "sg-profile:device"; }

  function loadLocal() {
    var p = lsGet(profileKey()) || {};
    var c = lsGet(cnicKey());
    if (c) p.cnic = c;
    state.profile = p;
  }

  function emit() {
    try { window.dispatchEvent(new CustomEvent("sg-account", { detail: api.status() })); } catch (e) {}
    renderButtons();
    autofill();
  }

  /* ---------- validation & formatting ---------- */
  function fmtCnic(v) {
    var d = String(v || "").replace(/\D/g, "").slice(0, 13);
    if (d.length > 12) return d.slice(0, 5) + "-" + d.slice(5, 12) + "-" + d.slice(12);
    if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
    return d;
  }
  function fmtMobile(v) {
    var d = String(v || "").replace(/\D/g, "");
    if (d.indexOf("92") === 0 && d.length === 12) d = "0" + d.slice(2);
    if (d.length === 11) return d.slice(0, 4) + "-" + d.slice(4);
    return String(v || "").trim();
  }
  function validate(p) {
    var errs = {};
    if (p.cnic && !/^\d{5}-\d{7}-\d$/.test(p.cnic)) errs.cnic = "CNIC must have 13 digits, like 12345-1234567-1.";
    if (p.mobile && !/^03\d{2}-\d{7}$/.test(p.mobile)) errs.mobile = "Enter a Pakistani mobile number, like 0300-1234567.";
    if (p.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p.email)) errs.email = "Enter a valid email address.";
    return errs;
  }
  function clean(p) {
    var out = {};
    FIELDS.forEach(function (f) {
      var v = p[f.k];
      if (v == null) return;
      v = String(v).trim();
      if (f.k === "cnic") v = fmtCnic(v);
      if (f.k === "mobile") v = fmtMobile(v);
      if (v) out[f.k] = v.slice(0, f.k === "address" ? 400 : 120);
    });
    return out;
  }

  /* ---------- Firebase ---------- */
  function loadScript(src) {
    return new Promise(function (res, rej) {
      var s = document.createElement("script");
      s.src = src; s.onload = res; s.onerror = function () { rej(new Error("load " + src)); };
      document.head.appendChild(s);
    });
  }
  function initFirebase() {
    var cfg = window.SG_FIREBASE_CONFIG;
    if (!cfg || !cfg.apiKey) { state.mode = "device"; loadLocal(); state.ready = true; emit(); return; }
    state.mode = "cloud";
    loadLocal(); emit(); // show cached details at once while Firebase loads
    loadScript(SDK + "firebase-app-compat.js")
      .then(function () { return Promise.all([loadScript(SDK + "firebase-auth-compat.js"), loadScript(SDK + "firebase-firestore-compat.js")]); })
      .then(function () {
        var app = window.firebase.apps.length ? window.firebase.app() : window.firebase.initializeApp(cfg);
        fb = { auth: app.auth(), db: app.firestore() };
        fb.auth.onAuthStateChanged(onUser);
      })
      .catch(function () {
        state.error = "Sign-in is unavailable right now. Your details are still saved on this device.";
        state.mode = "device"; loadLocal(); state.ready = true; emit();
      });
  }
  function onUser(u) {
    if (!u) { state.user = null; loadLocal(); state.ready = true; emit(); return; }
    state.user = { uid: u.uid, email: u.email || "", name: u.displayName || "" };
    // Move a CNIC saved before signing in to this account on this device.
    var devC = lsGet("sg-cnic:device");
    if (devC && !lsGet(cnicKey())) { lsSet(cnicKey(), devC); lsSet("sg-cnic:device", null); }
    loadLocal();
    var ref = fb.db.collection("users").doc(u.uid);
    ref.get().then(function (snap) {
      var cloud = snap.exists ? snap.data() : null;
      if (!cloud) {
        // First sign-in: seed the account from details saved on this device.
        var dev = lsGet("sg-profile:device") || {};
        var seed = {};
        CLOUD_KEYS.forEach(function (k) { if (dev[k]) seed[k] = dev[k]; });
        if (!seed.email && u.email) seed.email = u.email;
        if (!seed.name && u.displayName) seed.name = u.displayName;
        seed.updated = new Date().toISOString();
        cloud = seed;
        ref.set(seed).catch(function () {});
      }
      var p = {};
      CLOUD_KEYS.forEach(function (k) { if (cloud[k]) p[k] = cloud[k]; });
      lsSet(profileKey(), p);
      loadLocal();
      state.ready = true; emit();
    }).catch(function () {
      state.error = "Couldn't load your saved details. Check your connection.";
      state.ready = true; emit();
    });
  }

  var ERR = {
    "auth/email-already-in-use": "An account with this email already exists. Sign in instead.",
    "auth/invalid-credential": "Email or password is wrong.",
    "auth/wrong-password": "Email or password is wrong.",
    "auth/user-not-found": "No account uses this email. Create one instead.",
    "auth/invalid-email": "Enter a valid email address.",
    "auth/weak-password": "Use a password of at least 8 characters.",
    "auth/missing-password": "Enter your password.",
    "auth/too-many-requests": "Too many attempts. Wait a few minutes and try again.",
    "auth/popup-closed-by-user": "Google sign-in was closed before finishing.",
    "auth/popup-blocked": "Your browser blocked the Google window. Allow pop-ups and try again.",
    "auth/network-request-failed": "No internet connection. Try again.",
    "auth/requires-recent-login": "For your safety, sign out, sign in again, then retry.",
  };
  function friendly(e) { return ERR[e && e.code] || "Something went wrong. Please try again."; }
  function needCloud() {
    if (!fb) return Promise.reject({ code: "no-cloud", message: "Accounts aren't switched on for this site yet." });
    return Promise.resolve();
  }

  /* ---------- public API ---------- */
  var api = {
    FIELDS: FIELDS,
    status: function () { return { mode: state.mode, ready: state.ready, signedIn: !!state.user, user: state.user, error: state.error }; },
    get: function () { var o = {}; for (var k in state.profile) o[k] = state.profile[k]; return o; },
    validate: function (p) { return validate(clean(p)); },
    format: { cnic: fmtCnic, mobile: fmtMobile },
    save: function (input) {
      var p = clean(input), errs = validate(p);
      if (Object.keys(errs).length) return Promise.reject({ fields: errs });
      lsSet(cnicKey(), p.cnic || null);
      var rest = {};
      CLOUD_KEYS.forEach(function (k) { if (p[k]) rest[k] = p[k]; });
      lsSet(profileKey(), rest);
      loadLocal(); emit();
      if (!state.user || !fb) return Promise.resolve({ where: "device" });
      var doc = {}; CLOUD_KEYS.forEach(function (k) { doc[k] = rest[k] || window.firebase.firestore.FieldValue.delete(); });
      doc.updated = new Date().toISOString();
      return fb.db.collection("users").doc(state.user.uid).set(doc, { merge: true })
        .then(function () { return { where: "account" }; })
        .catch(function () { return Promise.reject({ message: "Saved on this device, but couldn't sync to your account. Check your connection and save again." }); });
    },
    signUp: function (email, password, name) {
      return needCloud().then(function () { return fb.auth.createUserWithEmailAndPassword(email, password); })
        .then(function (cred) { if (name) return cred.user.updateProfile({ displayName: name }); })
        .catch(function (e) { return Promise.reject({ message: e.message && e.code === "no-cloud" ? e.message : friendly(e) }); });
    },
    signIn: function (email, password) {
      return needCloud().then(function () { return fb.auth.signInWithEmailAndPassword(email, password); })
        .catch(function (e) { return Promise.reject({ message: e.code === "no-cloud" ? e.message : friendly(e) }); });
    },
    google: function () {
      return needCloud().then(function () { return fb.auth.signInWithPopup(new window.firebase.auth.GoogleAuthProvider()); })
        .catch(function (e) { return Promise.reject({ message: e.code === "no-cloud" ? e.message : friendly(e) }); });
    },
    reset: function (email) {
      return needCloud().then(function () { return fb.auth.sendPasswordResetEmail(email); })
        .catch(function (e) { return Promise.reject({ message: e.code === "no-cloud" ? e.message : friendly(e) }); });
    },
    signOut: function (forgetDevice) {
      if (forgetDevice && state.user) { lsSet(cnicKey(), null); lsSet(profileKey(), null); }
      return fb ? fb.auth.signOut() : Promise.resolve();
    },
    forgetDevice: function () {
      lsSet(cnicKey(), null); lsSet(profileKey(), null); loadLocal(); emit();
    },
    deleteAccount: function () {
      if (!state.user || !fb) return Promise.reject({ message: "You're not signed in." });
      var u = fb.auth.currentUser, uid = state.user.uid;
      return fb.db.collection("users").doc(uid).delete()
        .then(function () { return u.delete(); })
        .then(function () { lsSet("sg-cnic:" + uid, null); lsSet("sg-profile:" + uid, null); })
        .catch(function (e) { return Promise.reject({ message: friendly(e) }); });
    },
    accountUrl: BASE + "account/",
  };
  window.SahulatAccount = api;

  /* ---------- autofill ---------- */
  function autofill() {
    var p = state.profile, els = document.querySelectorAll("[data-profile]");
    for (var i = 0; i < els.length; i++) {
      var el = els[i], k = el.getAttribute("data-profile"), v = p[k];
      if (!v || el.value || el.hasAttribute("data-sg-filled") || el.closest("[data-no-autofill]")) continue;
      el.value = v;
      el.setAttribute("data-sg-filled", "");
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  /* ---------- header button ---------- */
  var css = [
    ".sga{--a-bg:#fff;--a-ink:#17232e;--a-line:#dde3e1;--a-accent:#0d6b52;--a-soft:#e2f1ec}",
    "@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .sga{--a-bg:#172129;--a-ink:#e6ecea;--a-line:#2b3a43;--a-accent:#4fc39d;--a-soft:#163a31}}",
    ":root[data-theme=dark] .sga{--a-bg:#172129;--a-ink:#e6ecea;--a-line:#2b3a43;--a-accent:#4fc39d;--a-soft:#163a31}",
    ".sga-btn{display:inline-flex;align-items:center;gap:8px;min-height:40px;padding:6px 14px 6px 8px;border-radius:999px;border:1px solid var(--a-line);background:var(--a-bg);color:var(--a-ink);font-family:inherit;font-weight:600;font-size:14px;line-height:1;text-decoration:none;white-space:nowrap}",
    ".sga-btn:hover{border-color:var(--a-accent)}",
    ".sga-btn:focus-visible{outline:3px solid var(--a-accent);outline-offset:2px}",
    ".sga-av{width:28px;height:28px;border-radius:50%;display:grid;place-items:center;background:var(--a-soft);color:var(--a-accent);font-size:12px;font-weight:700;flex:none}",
    ".sga-av svg{width:16px;height:16px}",
    ".sga-btn.sga-dark{background:rgba(255,255,255,.16);border-color:rgba(255,255,255,.35);color:#fff;backdrop-filter:blur(8px)}",
    ".sga-btn.sga-dark .sga-av{background:rgba(255,255,255,.22);color:#fff}",
    "@media (max-width:560px){.sga-btn.sga-compact .sga-l{display:none}.sga-btn.sga-compact{padding:6px}}",
  ].join("\n");
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  var ICON_USER = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg>';
  function initials(s) { return String(s || "").trim().split(/\s+/).slice(0, 2).map(function (w) { return w[0] || ""; }).join("").toUpperCase(); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function renderButtons() {
    var slots = document.querySelectorAll("[data-sg-account]");
    for (var i = 0; i < slots.length; i++) {
      var slot = slots[i], v = " " + (slot.getAttribute("data-sg-account") || "") + " ";
      var label, av, aria;
      var first = (state.profile.name || (state.user && state.user.name) || "").split(" ")[0];
      if (state.user) { label = first || "My account"; av = esc(initials(state.profile.name || state.user.name || state.user.email)) || ICON_USER; aria = "My account and saved details"; }
      else if (state.mode === "cloud") { label = "Sign in"; av = ICON_USER; aria = "Sign in or create an account"; }
      else { label = "My details"; av = ICON_USER; aria = "My saved details"; }
      var cls = "sga sga-btn" + (v.indexOf(" on-dark ") >= 0 ? " sga-dark" : "") + (v.indexOf(" compact ") >= 0 ? " sga-compact" : "");
      slot.innerHTML = '<a class="' + cls + '" href="' + api.accountUrl + '" aria-label="' + aria + '"><span class="sga-av">' + av + '</span><span class="sga-l">' + esc(label) + "</span></a>";
    }
  }

  function boot() {
    renderButtons();
    var cfgScript = document.querySelector('script[src*="firebase-config.js"]');
    if (window.SG_FIREBASE_CONFIG !== undefined || cfgScript) initFirebase();
    else loadScript(BASE + "firebase-config.js").then(initFirebase, initFirebase);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
