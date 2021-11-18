function toggleElement(group, id) {
	for(let el of document.getElementsByClassName(group)) {
		if(el.id != id) {
			el.classList.add('d-none');
		}
	}

	document.getElementById(id).classList.toggle('d-none');
}

function post_toast_callback(url, data, callback) {
	var xhr = new XMLHttpRequest();
	xhr.open("POST", url, true);
	var form = new FormData()

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
				document.getElementById('toast-post-success-text').innerText = "Action successful!";
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