if (typeof showNewCommentCounts === 'undefined') {
	function showNewCommentCounts(postId, newTotal) {
		const comments = JSON.parse(localStorage.getItem("comment-counts")) || {}

		const lastCount = comments[postId]
		if (lastCount) {
			const newComments = newTotal - lastCount.c
			if (newComments > 0) {
				document.querySelectorAll(`#post-${postId} .new-comments`).forEach(elem => {
					elem.textContent = ` (+${newComments})`
					elem.classList.remove("d-none")
				})
			}
		}
	}

	const LAST_CACHE_CLEAN_ID = "last-cache-clean"
	const EXPIRE_INTERVAL_MILLIS = 5 * 24 * 60 * 60 * 1000
	const CACHE_CLEAN_INTERVAL = 60 * 60 * 1000

	function cleanCache() {
		const lastCacheClean = JSON.parse(localStorage.getItem(LAST_CACHE_CLEAN_ID)) || Date.now()
		const now = Date.now()

		if (now - lastCacheClean > CACHE_CLEAN_INTERVAL) {
			const comments = JSON.parse(localStorage.getItem("comment-counts")) || {}

			for (let [key, value] of Object.entries(comments)) {
				if (now - value.t > EXPIRE_INTERVAL_MILLIS) {
					delete comments[key]
				}
			}
			localStorage.setItem("comment-counts", JSON.stringify(comments))
		}
		localStorage.setItem(LAST_CACHE_CLEAN_ID, JSON.stringify(now))
	}

	setTimeout(cleanCache, 500)
}