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