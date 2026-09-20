# -*- coding: utf-8 -*-
"""Builds two targets from one source:
   dist/index.html      -> standalone PWA (GitHub Pages / Vercel), localStorage
   dist/artifact.html   -> claude.ai artifact body (no <head>), cloud db
"""
import os, re, pathlib

ROOT = pathlib.Path(__file__).parent
head = (ROOT / "src" / "head.html").read_text(encoding="utf-8")
body = (ROOT / "src" / "body.html").read_text(encoding="utf-8")

dist = ROOT / "docs"
dist.mkdir(exist_ok=True)

# ---------- standalone ----------
standalone = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#080B0A">
<meta name="description" content="Project 65 — Bangkok Protocol. Suivi quotidien 55 kg vers 65 kg.">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Project 65">
<link rel="manifest" href="./manifest.webmanifest">
<link rel="apple-touch-icon" href="./icons/icon-180.png">
<link rel="icon" href="./icons/icon-192.png">
{head}
<style>
  :root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
</style>
</head>
<body>
{body}
</body>
</html>
"""
(dist / "index.html").write_text(standalone, encoding="utf-8")

# ---------- artifact ----------
(dist / "artifact.html").write_text(head + "\n" + body, encoding="utf-8")

# ---------- manifest ----------
manifest = """{
  "name": "Project 65 — Bangkok Protocol",
  "short_name": "Project 65",
  "description": "Suivi quotidien 55 kg vers 65 kg : poids, repas, training, calories, budget.",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#080B0A",
  "theme_color": "#080B0A",
  "lang": "fr",
  "icons": [
    { "src": "./icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "./icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "./icons/icon-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
"""
(dist / "manifest.webmanifest").write_text(manifest, encoding="utf-8")

# ---------- service worker ----------
sw = """const CACHE = "p65-v1";
const ASSETS = ["./", "./index.html", "./manifest.webmanifest",
  "./icons/icon-192.png", "./icons/icon-512.png", "./icons/icon-180.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  // Google Fonts: cache-first, they never change
  if (url.hostname.endsWith("googleapis.com") || url.hostname.endsWith("gstatic.com")) {
    e.respondWith(caches.match(req).then(hit => hit ||
      fetch(req).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => hit)));
    return;
  }
  if (url.origin !== location.origin) return;
  // app shell: network-first so updates land, cache as offline fallback
  e.respondWith(fetch(req).then(res => {
    const copy = res.clone();
    caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
    return res;
  }).catch(() => caches.match(req).then(hit => hit || caches.match("./index.html"))));
});
"""
(dist / "sw.js").write_text(sw, encoding="utf-8")

print("built:", ", ".join(sorted(p.name for p in dist.iterdir() if p.is_file())))
print("index.html  %d KB" % ((dist / "index.html").stat().st_size // 1024))
print("artifact.html %d KB" % ((dist / "artifact.html").stat().st_size // 1024))
