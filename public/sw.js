importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.4.1/workbox-sw.js');

const { precacheAndRoute, cleanupOutdatedCaches } = workbox.precaching;
const { registerRoute } = workbox.routing;
const { CacheFirst, NetworkFirst } = workbox.strategies;
const { BackgroundSync } = workbox.backgroundSync;

// Precache static assets
precacheAndRoute([
  { url: '/', revision: '1' },
  { url: '/index.html', revision: '1' },
  { url: '/app.js', revision: '1' },
  { url: '/styles.css', revision: '1' },
  { url: '/manifest.json', revision: '1' }
]);

cleanupOutdatedCaches();

// Cache Tailwind CSS
registerRoute(
  /^https:\/\/cdn\.tailwindcss\.com/,
  new CacheFirst({
    cacheName: 'tailwind-cache'
  })
);

// Cache Dexie
registerRoute(
  /^https:\/\/unpkg\.com\/dexie/,
  new CacheFirst({
    cacheName: 'dexie-cache'
  })
);

// Background sync for offline API requests
const bgSync = new BackgroundSync('api-queue', {
  maxRetentionTime: 24 * 60 // Retry for 24 hours
});

// Handle offline API requests
registerRoute(
  /\/api\//,
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [bgSync]
  }),
  'POST'
);

registerRoute(
  /\/api\//,
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [bgSync]
  }),
  'PUT'
);

registerRoute(
  /\/api\//,
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [bgSync]
  }),
  'DELETE'
);

// Handle background sync
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-sessions') {
    event.waitUntil(syncOfflineData());
  }
});

async function syncOfflineData() {
  // This will be handled by the app's sync mechanism
  const clients = await self.clients.matchAll();
  clients.forEach(client => {
    client.postMessage({ type: 'SYNC_DATA' });
  });
}

// Install event
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});
