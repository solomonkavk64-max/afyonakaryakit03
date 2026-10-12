importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyAql3eWJREPdKPK5BLhqd9CeYgr15Uvbi4",
  authDomain: "afyon-akaryakit.firebaseapp.com",
  projectId: "afyon-akaryakit",
  storageBucket: "afyon-akaryakit.firebasestorage.app",
  messagingSenderId: "19128335580",
  appId: "1:19128335580:web:26da6ae3a97e10b11e4819",
  measurementId: "G-3V2PHB2JL2"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Arka planda mesaj alındı: ', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/icon.png'
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});
