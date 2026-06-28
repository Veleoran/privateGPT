// CR Fibre v4.2 — JS minimal (aucune dépendance externe)

// --- PWA : enregistre le service worker servi à la racine -------------------
if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function () {});
  });
}

// --- Affiche le champ DPR (date prochain RDV) seulement pour les travaux -----
(function () {
  var statut = document.getElementById("statut");
  var wrap = document.getElementById("note-wrap");
  if (!statut || !wrap) return;
  function toggle() {
    wrap.style.display = /travaux/i.test(statut.value) ? "block" : "none";
  }
  statut.addEventListener("change", toggle);
  toggle();
})();

// --- Dictée vocale terrain (Web Speech API, fr-FR) --------------------------
// Mains libres sur chantier : un micro par champ texte / nombre / zone de texte.
// Dégradation propre : si le navigateur ne supporte pas, aucun micro n'apparaît
// et la saisie clavier reste 100 % fonctionnelle.
(function () {
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  var form = document.querySelector(".cr-form");
  if (!SR || !form) return;

  var fields = form.querySelectorAll('input[type="text"], input[type="number"], textarea');
  if (!fields.length) return;

  var active = null; // reconnaissance en cours

  // "moins vingt-deux virgule quatre" / "-22,4" -> "-22.4"
  function normalizeNumber(s) {
    return String(s)
      .toLowerCase()
      .replace(/\bmoins\b/g, "-")
      .replace(/\bvirgule\b/g, ".")
      .replace(/,/g, ".")
      .replace(/[^\d.\-]/g, "")
      .replace(/(?!^)-/g, "");
  }

  function stop() {
    if (active) { try { active.rec.stop(); } catch (e) {} }
  }

  function start(field, btn) {
    stop();
    var rec = new SR();
    rec.lang = "fr-FR";
    rec.interimResults = true;
    rec.continuous = field.tagName === "TEXTAREA";
    var isNumber = field.type === "number";
    var base = field.value ? field.value.trim() + " " : "";
    var finalText = "";

    active = { rec: rec, field: field, btn: btn };
    btn.classList.add("rec");

    function apply(extra) {
      var txt = (base + finalText + extra).trim();
      field.value = isNumber ? normalizeNumber(txt) : txt;
    }
    function cleanup() {
      btn.classList.remove("rec");
      active = null;
    }

    rec.onresult = function (e) {
      var fin = "", interim = "";
      for (var i = 0; i < e.results.length; i++) {
        var t = e.results[i][0].transcript;
        if (e.results[i].isFinal) fin += t + " "; else interim += t;
      }
      finalText = fin;
      apply(interim);
    };
    rec.onerror = function () { cleanup(); };
    rec.onend = function () {
      apply("");
      field.dispatchEvent(new Event("change", { bubbles: true }));
      cleanup();
    };

    try { rec.start(); } catch (e) { cleanup(); }
  }

  fields.forEach(function (field) {
    var label = field.closest("label") || field.parentNode;
    label.classList.add("has-mic");
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "mic";
    btn.setAttribute("aria-label", "Dicter ce champ");
    btn.textContent = "🎤";
    field.insertAdjacentElement("afterend", btn);
    btn.addEventListener("click", function () {
      if (active && active.field === field) { stop(); return; }
      start(field, btn);
    });
  });
})();

// --- Bouton "Copier le CR" (page ticket) ------------------------------------
(function () {
  var btn = document.getElementById("copy-cr");
  var pre = document.getElementById("cr-body");
  if (!btn || !pre) return;
  btn.addEventListener("click", function () {
    var text = pre.innerText;
    var done = function () {
      var old = btn.textContent;
      btn.textContent = "Copié ✓";
      setTimeout(function () { btn.textContent = old; }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(function () {});
    } else {
      var r = document.createRange(); r.selectNode(pre);
      var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
      try { document.execCommand("copy"); done(); } catch (e) {}
      sel.removeAllRanges();
    }
  });
})();

// --- Bouton "Partager" (Web Share Android → coller dans Praxedo, Notes…) -----
(function () {
  var btn = document.getElementById("share-cr");
  var pre = document.getElementById("cr-body");
  if (!btn || !pre) return;
  if (!navigator.share) { btn.style.display = "none"; return; } // desktop : masqué
  btn.addEventListener("click", function () {
    var title = (document.getElementById("cr-code") || {}).textContent || "CR Fibre";
    navigator.share({ title: title.trim(), text: pre.innerText }).catch(function () {});
  });
})();
