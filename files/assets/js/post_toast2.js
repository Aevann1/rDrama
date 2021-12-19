function post_toast2(url, button1, button2) {
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
		data = JSON.parse(xhr.response)
		if (xhr.status >= 200 && xhr.status < 300 && !data["error"]) {
			try {
				document.getElementById('toast-post-success-text').innerText = data["message"];
			} catch(e) {}
			var myToast = new bootstrap.Toast(document.getElementById('toast-post-success'));
			myToast.show();
			return true

		} else if (xhr.status >= 300 && xhr.status < 400) {
			window.location.href = data["redirect"]
		} else {
			try {
				document.getElementById('toast-post-error-text').innerText = data["error"];
			} catch(e) {}
			var myToast = new bootstrap.Toast(document.getElementById('toast-post-error'));
			myToast.show();
			return false
		}
	};

	xhr.send(form);

	document.getElementById(button1).classList.toggle("d-none");
	document.getElementById(button2).classList.toggle("d-none");
}