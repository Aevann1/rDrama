function formkey() {
	let formkey = document.getElementById("formkey")
	if (formkey) return formkey.innerHTML;
	else return null;
}
	
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
tooltipTriggerList.map(function(element){
	return new bootstrap.Tooltip(element);
});

function post_toast(url, reload, data) {
	const xhr = new XMLHttpRequest();
	xhr.open("POST", url, true);
	xhr.setRequestHeader('xhr', 'xhr');
	var form = new FormData()
	form.append("formkey", formkey());

	if(typeof data === 'object' && data !== null) {
		for(let k of Object.keys(data)) {
			form.append(k, data[k]);
		}
	}

	xhr.onload = function() {
		let data
		try {data = JSON.parse(xhr.response)}
		catch(e) {console.log(e)}
		if (xhr.status >= 200 && xhr.status < 300 && data && data['message']) {
			document.getElementById('toast-post-success-text').innerText = data["message"];
			new bootstrap.Toast(document.getElementById('toast-post-success')).show();
			if (reload == 1) {location.reload(true)}
		} else {
			document.getElementById('toast-post-error-text').innerText = "Error, please try again later."
			if (data && data["error"]) document.getElementById('toast-post-error-text').innerText = data["error"];
			new bootstrap.Toast(document.getElementById('toast-post-error')).show();
		}
	};

	xhr.send(form);

}