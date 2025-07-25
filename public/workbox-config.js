module.exports = {
  globDirectory: 'public/',
  globPatterns: [
    '**/*.{html,js,css,json}'
  ],
  swDest: 'public/sw.js',
  runtimeCaching: [
    {
      urlPattern: /^https:\/\/cdn\.tailwindcss\.com/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'tailwind-cache',
        expiration: {
          maxEntries: 10,
          maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
        }
      }
    },
    {
      urlPattern: /^https:\/\/unpkg\.com\/dexie/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'dexie-cache',
        expiration: {
          maxEntries: 10,
          maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
        }
      }
    }
  ]
};
