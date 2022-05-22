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

/** @type {HTMLImageElement} */
const popClickBadgeTemplateDOM = document.createElement("IMG");
popClickBadgeTemplateDOM.width = 32;
popClickBadgeTemplateDOM.loading = "lazy";
popClickBadgeTemplateDOM.alt = "badge";

/**
 * @param {MouseEvent} e 
 */
function popclick(e) {
	// We let through those methods
	if(e.ctrlKey || e.metaKey || e.shiftKey || e.altKey)
		return true;
	e.preventDefault();
	
	if(e.currentTarget.dataset.popInfo === undefined)
		throw new SyntaxError("ill formed HTML! data-pop-info not present!!!");

	const author = JSON.parse(e.currentTarget.dataset.popInfo);
	if(!(author instanceof Object))
		throw new SyntaxError("data-pop-info was not valid!");
	
	// This is terrible lol. in header.js:bs_trigger() we should add
	// to the ANCHOR element an event handler for "show.bs.tooltip" to build this
	// when the DOM is ready.
	// PROBLEM: IT DOES NOT WORK :MARSEYCRAZYTROLL: idk why it should work according to
	// boostrap docs!
	setTimeout(() => {
		let popover = document.getElementsByClassName("popover")
		popover = popover[popover.length-1]

		const badgesDOM = popover.getElementsByClassName('pop-badges')[0];
		badgesDOM.innerHTML = "";
		for (const badge of author["badges"]) {
			const badgeDOM = popClickBadgeTemplateDOM.cloneNode();
			badgeDOM.src = badge + "?v=1016";

			badgesDOM.append(badgeDOM);
		}

		popover.getElementsByClassName('pop-banner')[0].src = author["bannerurl"]
		popover.getElementsByClassName('pop-picture')[0].src = author["profile_url"]
		popover.getElementsByClassName('pop-username')[0].innerHTML = author["username"]
		popover.getElementsByClassName('pop-bio')[0].innerHTML = author["bio_html"]
		popover.getElementsByClassName('pop-postcount')[0].innerHTML = author["post_count"]
		popover.getElementsByClassName('pop-commentcount')[0].innerHTML = author["comment_count"]
		popover.getElementsByClassName('pop-coins')[0].innerHTML = author["coins"]
		popover.getElementsByClassName('pop-viewmore')[0].href = author["url"]
	}, 5);

	return false;
}

document.addEventListener("click", function(){
	active = document.activeElement.getAttributeNode("class");
	if (active && active.nodeValue == "user-name text-decoration-none"){
		pops = document.getElementsByClassName('popover')
		if (pops.length > 1) pops[0].remove()
	}
	else document.querySelectorAll('.popover').forEach(e => e.remove());
});

function post(url) {
	const xhr = new XMLHttpRequest();
	xhr.open("POST", url);
	xhr.setRequestHeader('xhr', 'xhr');
	var form = new FormData()
	form.append("formkey", formkey());
	xhr.send(form);
};

function poll_vote(cid, parentid) {
	for(let el of document.getElementsByClassName('presult-'+parentid)) {
		el.classList.remove('d-none');
	}
	var type = document.getElementById(cid).checked;
	var scoretext = document.getElementById('poll-' + cid);
	var score = Number(scoretext.textContent);
	if (type == true) scoretext.textContent = score + 1;
	else scoretext.textContent = score - 1;
	post('/vote/poll/' + cid + '?vote=' + type);
}

function choice_vote(cid, parentid) {
	for(let el of document.getElementsByClassName('presult-'+parentid)) {
		el.classList.remove('d-none');
	}
	
	let curr = document.getElementById(`current-${parentid}`)
	if (curr && curr.value)
	{
		var scoretext = document.getElementById('choice-' + curr.value);
		var score = Number(scoretext.textContent);
		scoretext.textContent = score - 1;
	}

	var scoretext = document.getElementById('choice-' + cid);
	var score = Number(scoretext.textContent);
	scoretext.textContent = score + 1;
	post('/vote/choice/' + cid);
	curr.value = cid
}

function bet_vote(cid) {
	for(let el of document.getElementsByClassName('bet')) {
		el.disabled = true;
	}
	for(let el of document.getElementsByClassName('cost')) {
		el.classList.add('d-none')
	}
	var scoretext = document.getElementById('bet-' + cid);
	var score = Number(scoretext.textContent);
	scoretext.textContent = score + 1;
	post('/bet/' + cid);
	document.getElementById("user-coins-amount").innerText = parseInt(document.getElementById("user-coins-amount").innerText) - 200;
}