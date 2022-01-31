function report_postModal(id) {

	submitbutton=document.getElementById("reportPostButton");

	submitbutton.onclick = function() {

		this.innerHTML='Reporting post';
		this.disabled = true;

		const xhr = new XMLHttpRequest();
		xhr.open("POST", '/report/post/'+id, true);
		xhr.setRequestHeader('xhr', 'xhr');
		var form = new FormData()
		form.append("formkey", formkey());
		form.append("reason", document.getElementById("reason").value);

		xhr.onload=function() {
			document.getElementById("reportPostFormBefore").classList.add('d-none');
			document.getElementById("reportPostFormAfter").classList.remove('d-none');
			this.disabled = false;
		};

		xhr.onerror=function(){alert(errortext)};
		xhr.send(form);

	}
};