document.getElementById('awardModal').addEventListener('show.bs.modal', function (event) {
  document.getElementById("awardTarget").action = event.relatedTarget.dataset.url;
});

function vote(type, id, dir, vid) {
	const upvotes = document.getElementsByClassName(type + '-' + id + '-up');
	const downvotes = document.getElementsByClassName(type + '-' + id + '-down');
	const scoretexts = document.getElementsByClassName(type + '-score-' + id);

	for (let i=0; i<upvotes.length; i++) {
		
		const upvote = upvotes[i]
		const downvote = downvotes[i]
		const scoretext = scoretexts[i]
		const score = Number(scoretext.textContent);

		if (dir == "1") {
			if (upvote.classList.contains('active')) {
				upvote.classList.remove('active')
				scoretext.textContent = score - 1
				votedirection = "0"
				if (vid && ['1','9'].includes(vid)) document.getElementById(id+'-title').classList.remove('visited')
			} else if (downvote.classList.contains('active')) {
				upvote.classList.add('active')
				downvote.classList.remove('active')
				scoretext.textContent = score + 2
				votedirection = "1"
			} else {
				upvote.classList.add('active')
				scoretext.textContent = score + 1
				votedirection = "1"
				if (vid && ['1','9'].includes(vid)) document.getElementById(id+'-title').classList.add('visited')
			}

			if (upvote.classList.contains('active')) {
				scoretext.classList.add('score-up')
				scoretext.classList.remove('score-down')
				scoretext.classList.remove('score')
			} else if (downvote.classList.contains('active')) {
				scoretext.classList.add('score-down')
				scoretext.classList.remove('score-up')
				scoretext.classList.remove('score')
			} else {
				scoretext.classList.add('score')
				scoretext.classList.remove('score-up')
				scoretext.classList.remove('score-down')
			}
		}
		else {
			if (downvote.classList.contains('active')) {
				downvote.classList.remove('active')
				scoretext.textContent = score + 1
				votedirection = "0"
				if (vid && ['1','9'].includes(vid)) document.getElementById(id+'-title').classList.remove('visited')
			} else if (upvote.classList.contains('active')) {
				downvote.classList.add('active')
				upvote.classList.remove('active')
				scoretext.textContent = score - 2
				votedirection = "-1"
			} else {
				downvote.classList.add('active')
				scoretext.textContent = score - 1
				votedirection = "-1"
				if (vid && ['1','9'].includes(vid)) document.getElementById(id+'-title').classList.add('visited')
			}

			if (upvote.classList.contains('active')) {
				scoretext.classList.add('score-up')
				scoretext.classList.remove('score-down')
				scoretext.classList.remove('score')
			} else if (downvote.classList.contains('active')) {
				scoretext.classList.add('score-down')
				scoretext.classList.remove('score-up')
				scoretext.classList.remove('score')
			} else {
				scoretext.classList.add('score')
				scoretext.classList.remove('score-up')
				scoretext.classList.remove('score-down')
			}
		}
	}
	
	const xhr = new XMLHttpRequest();
	xhr.open("POST", "/vote/" + type.replace('-mobile','') + "/" + id + "/" + votedirection);
	xhr.setRequestHeader('xhr', 'xhr');
	var form = new FormData()
	form.append("formkey", formkey());
	xhr.send(form);
}

function pick(kind, canbuy1, canbuy2) {
	let buy1 = document.getElementById('buy1')
	if (canbuy1 && kind != "grass") buy1.disabled=false;
	else buy1.disabled=true;
	let buy2 = document.getElementById('buy2')
	if (canbuy2 && kind != "benefactor") buy2.disabled=false;
	else buy2.disabled=true;
	let ownednum = Number(document.getElementById(`${kind}-owned`).textContent);
	document.getElementById('giveaward').disabled = (ownednum == 0);
	document.getElementById('kind').value=kind;
	try {document.getElementsByClassName('picked')[0].classList.toggle('picked');} catch(e) {console.log(e)}
	document.getElementById(kind).classList.toggle('picked')
	if (kind == "flairlock") {
		document.getElementById('notelabel').innerHTML = "New flair:";
		document.getElementById('note').placeholder = "Insert new flair here, or leave empty to add 1 day to the duration of the current flair. 100 characters max.";
		document.getElementById('note').maxLength = 100;
	}
	else {
		document.getElementById('notelabel').innerHTML = "Note (optional):";
		document.getElementById('note').placeholder = "Note to include in award notification";
		document.getElementById('note').maxLength = 200;
	}
}

function buy(mb) {
	const kind = document.getElementById('kind').value;
	const xhr = new XMLHttpRequest();
	url = `/buy/${kind}`
	if (mb) url += "?mb=true"
	xhr.open("POST", url);
	xhr.setRequestHeader('xhr', 'xhr');
	var form = new FormData()
	form.append("formkey", formkey());

	if(typeof data === 'object' && data !== null) {
		for(let k of Object.keys(data)) {
				form.append(k, data[k]);
		}
	}


	form.append("formkey", formkey());
	xhr.onload = function() {
		let data
		try {data = JSON.parse(xhr.response)}
		catch(e) {console.log(e)}
		if (xhr.status >= 200 && xhr.status < 300 && data && data["message"]) {
			document.getElementById('toast-post-success-text2').innerText = data["message"];
			bootstrap.Toast.getOrCreateInstance(document.getElementById('toast-post-success2')).show();
			document.getElementById('giveaward').disabled=false;
			let owned = document.getElementById(`${kind}-owned`)
			let ownednum = Number(owned.textContent);
			owned.textContent = ownednum + 1
		} else {
			document.getElementById('toast-post-error-text').innerText = "Error, please try again later."
			if (data && data["error"]) document.getElementById('toast-post-error-text2').innerText = data["error"];
			bootstrap.Toast.getOrCreateInstance(document.getElementById('toast-post-error2')).show();
		}
	};

	xhr.send(form);

}