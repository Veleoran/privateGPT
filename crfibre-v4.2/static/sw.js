// CR Fibre v4.2 — service worker (offline-friendly, simple et correct)
const CACHE = "crfibre-v4.2-1";
const ASSETS = [
  "/",
  "/static/style.css",
  "/static/app.js",
  "/static/icon-192.png",
  "/static/icon-512.png",
  "/manifest.webmanifest",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return; // ne jamais intercepter les POST (envoi de CR)

  const url = new URL(req.url);

  // Statiques : cache-first
  if (url.pathname.startsWith("/static/") || url.pathname === "/manifest.webmanifest") {
    e.respondWith(caches.match(req).then((r) => r || fetch(req)));
    return;
  }

  // Navigation/pages : réseau d'abord, repli cache
  e.respondWith(
    fetch(req)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        return res;
      })
      .catch(() => caches.match(req).then((r) => r || caches.match("/")))
  );
});
