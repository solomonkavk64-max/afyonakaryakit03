// Afyon Akaryakıt - Arka Plan Servis İşçisi (Service Worker)

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// İnternet isteklerini yönetme (Mevcut yapıyı koruyoruz)
self.addEventListener('fetch', (event) => {
  event.respondWith(fetch(event.request));
});

// Bildirime tıklandığında uygulamayı açma
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (let i = 0; i < clientList.length; i++) {
        let client = clientList[i];
        if ('focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('/');
      }
    })
  );
});
