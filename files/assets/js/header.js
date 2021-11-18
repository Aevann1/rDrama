document.addEventListener("DOMContentLoaded", function(){
	var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
	tooltipTriggerList.map(function(element){
		return new bootstrap.Tooltip(element);
	});
});

function post_toast(url, reload, data) {
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
		if (xhr.status >= 200 && xhr.status < 300) {
			var myToast = new bootstrap.Toast(document.getElementById('toast-post-success'));
			myToast.show();
			try {
				document.getElementById('toast-post-success-text').innerText = JSON.parse(xhr.response)["message"];
			} catch(e) {
				document.getElementById('toast-post-success-text').innerText = "Action successful!";
			}

			if (reload == 1) {location.reload(true)}
			return true

		} else if (xhr.status >= 300 && xhr.status < 400) {
			window.location.href = JSON.parse(xhr.response)["redirect"]
		} else {
			try {
				data=JSON.parse(xhr.response);

				var myToast = new bootstrap.Toast(document.getElementById('toast-post-error'));
				myToast.show();
				document.getElementById('toast-post-error-text').innerText = data["error"];
				return false
			} catch(e) {
				var myToast = new bootstrap.Toast(document.getElementById('toast-post-success'));
				myToast.hide();
				var myToast = new bootstrap.Toast(document.getElementById('toast-post-error'));
				myToast.show();
				return false
			}
		}
	};

	xhr.send(form);

}