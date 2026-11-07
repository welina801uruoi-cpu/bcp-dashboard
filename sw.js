self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  return self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // バックエンドAPI以外のリクエストを通過させる
  e.respondWith(fetch(e.request));
});