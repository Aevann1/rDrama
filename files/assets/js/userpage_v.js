function post_toast_callback(url, data, callback) {
	var xhr = new XMLHttpRequest();
	xhr.open("POST", url, true);
	var form = new FormData()
	form.append("formkey", formkey());

	if(typeof data === 'object' && data !== null) {
		for(let k of Object.keys(data)) {
			form.append(k, data[k]);
		}
	}

	form.append("formkey", formkey());
	xhr.withCredentials=true;

	xhr.onload = function() {
		let result = callback(xhr);
		if (xhr.status >= 200 && xhr.status < 300) {
			var myToast = new bootstrap.Toast(document.getElementById('toast-post-error'));
			myToast.hide();

			var myToast = new bootstrap.Toast(document.getElementById('toast-post-success'));
			myToast.show();

			try {
				if(typeof result == "string") {
					document.getElementById('toast-post-success-text').innerText = result;
				} else {
					document.getElementById('toast-post-success-text').innerText = JSON.parse(xhr.response)["message"];
				}
			} catch(e) {
			}

			return true;
		} else {
			var myToast = new bootstrap.Toast(document.getElementById('toast-post-success'));
			myToast.hide();

			var myToast = new bootstrap.Toast(document.getElementById('toast-post-error'));
			myToast.show();

			try {
				if(typeof result == "string") {
					document.getElementById('toast-post-error-text').innerText = result;
				} else {
					document.getElementById('toast-post-error-text').innerText = JSON.parse(xhr.response)["error"];
				}
				return false
			} catch(e) {}

			return false;
		}
	};

	xhr.send(form);

}

function toggleElement(group, id) {
	for(let el of document.getElementsByClassName(group)) {
		if(el.id != id) {
			el.classList.add('d-none');
		}
	}

	document.getElementById(id).classList.toggle('d-none');
}

let TRANSFER_TAX = document.getElementById('tax').innerHTML

function updateTax(mobile=false) {
	let suf = mobile ? "-mobile" : "";
	let amount = parseInt(document.getElementById("coins-transfer-amount" + suf).value);
	if(isNaN(amount) || amount < 0) {
	amount = 0;
	}
	document.getElementById("coins-transfer-taxed" + suf).innerText = amount - Math.ceil(amount*TRANSFER_TAX);
}

function transferCoins(mobile=false) {
	let t = event.target;
	t.disabled = true;

	let amount = parseInt(document.getElementById("coins-transfer-amount").value);
	let transferred = amount - Math.ceil(amount*TRANSFER_TAX);
	let username = document.getElementById('username').innerHTML

	post_toast_callback(`/@${username}/transfer_coins`,
		{"amount": document.getElementById(mobile ? "coins-transfer-amount-mobile" : "coins-transfer-amount").value},
		(xhr) => {
		if(xhr.status == 200) {
			document.getElementById("user-coins-amount").innerText = parseInt(document.getElementById("user-coins-amount").innerText) - amount;
			document.getElementById("profile-coins-amount-mobile").innerText = parseInt(document.getElementById("profile-coins-amount-mobile").innerText) + transferred;
			document.getElementById("profile-coins-amount").innerText = parseInt(document.getElementById("profile-coins-amount").innerText) + transferred;
		}
		}
	);

	setTimeout(_ => t.disabled = false, 2000);
}