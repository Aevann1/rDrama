report_postModal = function(id) {

	submitbutton=document.getElementById("reportPostButton");

	submitbutton.onclick = function() {

		this.innerHTML='Reporting post';
		this.disabled = true;

		var xhr = new XMLHttpRequest();
		xhr.open("POST", '/flag/post/'+id, true);
		var form = new FormData()
		form.append("formkey", formkey());
		form.append("reason", document.getElementById("reason").value);

		xhr.withCredentials=true;

		xhr.onload=function() {
			document.getElementById("reportPostFormBefore").classList.add('d-none');
			document.getElementById("reportPostFormAfter").classList.remove('d-none');
		};

		xhr.onerror=function(){alert(errortext)};
		xhr.send(form);

	}
};