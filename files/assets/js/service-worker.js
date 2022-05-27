importScripts("https://js.pusher.com/beams/service-worker.js");

// offline static page handler
// @crgd

const CACHE_NAME = "offlineCache-v1";
const OFFLINE_URL = "/assets/offline.html";

self.addEventListener("install", (event) => {
	const cacheOfflinePage = async () => {
		const cache = await caches.open(CACHE_NAME);
		await cache.add(new Request(OFFLINE_URL, {cache: "reload"}));
	};

	cacheOfflinePage().then(() => {
		this.skipWaiting();
	});
});

self.addEventListener("activate", (event) => {
	const expectedCaches = [CACHE_NAME];

	event.waitUntil(
		caches.keys().then(keys => Promise.all(
			keys.map(key => {
				if (!expectedCaches.includes(key)) {
					return caches.delete(key);
				}
			})
		))
	);
});

self.addEventListener("fetch", (event) => {
	if (event.request.mode === "navigate") {
		event.respondWith((async () => {
			try {
				const preloadResponse = await event.preloadResponse;
				if (preloadResponse) return preloadResponse;

				const networkResponse = await fetch(event.request);
				return networkResponse;
			} catch (error) {
				console.log("Fetch failed; returning offline page instead.", error);

				const cachedResponse = await caches.match(OFFLINE_URL);
				return cachedResponse;
			}
		})());
	}
});