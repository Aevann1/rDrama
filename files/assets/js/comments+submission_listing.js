function timestamp(str, ti) {
	date = new Date(ti*1000);
	document.getElementById(str).setAttribute("data-bs-original-title", date.toString());
};

function pinned_timestamp(id) {
	const el = document.getElementById(id)
	const time =  new Date(parseInt(el.dataset.timestamp)*1000)
	const pintooltip =  el.getAttribute("data-bs-original-title")
	if (!pintooltip.includes('until')) el.setAttribute("data-bs-original-title", `${pintooltip} until ${time}`)
}

function expandDesktopImage(image) {
	document.getElementById("desktop-expanded-image").src = image.replace("200w_d.webp", "giphy.webp");
	document.getElementById("desktop-expanded-image-link").href = image;
	document.getElementById("desktop-expanded-image-wrap-link").href=image;
};

function bs_trigger() {
	let tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
	tooltipTriggerList.map(function(element){
		return bootstrap.Tooltip.getOrCreateInstance(element);
	});

	const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
	popoverTriggerList.map(function(popoverTriggerEl) {
		const popoverId = popoverTriggerEl.getAttribute('data-content-id');
		const contentEl = document.getElementById(popoverId);
		if (contentEl) {
			return bootstrap.Popover.getOrCreateInstance(popoverTriggerEl, {
				content: contentEl.innerHTML,
				html: true,
			});
		}
	})
}

bs_trigger()

function popclick(author) {
	setTimeout(() => {
		let popover = document.getElementsByClassName("popover")
		popover = popover[popover.length-1]

		let badges = ''
		for (const x of author["badges"]) {
			badges += `<img alt="badge" width="32" loading="lazy" src="${x}">`
		}
		popover.getElementsByClassName('pop-banner')[0].src = author["bannerurl"]
		popover.getElementsByClassName('pop-picture')[0].src = author["profile_url"]
		popover.getElementsByClassName('pop-username')[0].innerHTML = author["username"]
		popover.getElementsByClassName('pop-bio')[0].innerHTML = author["bio_html"]
		popover.getElementsByClassName('pop-postcount')[0].innerHTML = author["post_count"]
		popover.getElementsByClassName('pop-commentcount')[0].innerHTML = author["comment_count"]
		popover.getElementsByClassName('pop-coins')[0].innerHTML = author["coins"]
		popover.getElementsByClassName('pop-viewmore')[0].href = author["url"]
		popover.getElementsByClassName('pop-badges')[0].innerHTML = badges
	; }, 1);
}

document.addEventListener("click", function(){
	active = document.activeElement.getAttributeNode("class");
	if (active && active.nodeValue == "user-name text-decoration-none"){
		pops = document.getElementsByClassName('popover')
		if (pops.length > 1) pops[0].remove()
	}
	else document.querySelectorAll('.popover').forEach(e => e.remove());
});