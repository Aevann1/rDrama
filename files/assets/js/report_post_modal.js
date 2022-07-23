const reason_post = document.getElementById("reason_post")
const reportPostButton = document.getElementById("reportPostButton");

reason_post.addEventListener('keydown', (e) => {
	if(!((e.ctrlKey || e.metaKey) && e.key === "Enter")) return;

	const targetDOM = document.activeElement;
	if(!(targetDOM instanceof HTMLInputElement)) return;

	reportPostButton.click()
	bootstrap.Modal.getOrCreateInstance(document.getElementById('reportPostModal')).hide()
});

function report_postModal(id) {

	document.getElementById("reportPostFormBefore").classList.remove('d-none');
	document.getElementById("reportPostFormAfter").classList.add('d-none');
	reportPostButton.disabled = false;
	reportPostButton.classList.remove('disabled');
	reportPostButton.innerHTML='Report post';

	reason_post.value = ""
	setTimeout(() => {
		reason_post.focus()
	}, 500);

	reportPostButton.onclick = function() {

		this.innerHTML='Reporting post';
		this.disabled = true;
		this.classList.add('disabled');

		const xhr = new XMLHttpRequest();
		xhr.open("POST", '/report/post/'+id);
		xhr.setRequestHeader('xhr', 'xhr');
		const form = new FormData()
		form.append("formkey", formkey());
		form.append("reason", reason_post.value);

		xhr.onload=function() {
			document.getElementById("reportPostFormBefore").classList.add('d-none');
			document.getElementById("reportPostFormAfter").classList.remove('d-none');
		};

		xhr.onerror=function(){alert(errortext)};
		xhr.send(form);

	}
};