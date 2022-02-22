function collapse_comment(comment_id) {
	const comment = "comment-" + comment_id
	const element = document.getElementById(comment)
	const closed = element.classList.toggle("collapsed")
	const top = element.getBoundingClientRect().y

	document.querySelectorAll(`#${comment} .collapsed`).forEach(n => n.classList.remove('collapsed'))

	if (closed && top < 0) {
		element.scrollIntoView()
		window.scrollBy(0, - 100)
	}
};

function poll_vote_no_v() {
	document.getElementById('toast-post-error-text').innerText = "Only logged-in users can vote!";
	bootstrap.Toast.getOrCreateInstance(document.getElementById('toast-post-error')).show();
}

function morecomments(cid) {
	btn = document.getElementById(`btn-${cid}`);
	btn.disabled = true;
	btn.innerHTML = "Requesting...";
	var form = new FormData();
	form.append("formkey", formkey());
	const xhr = new XMLHttpRequest();
	xhr.open("get", `/morecomments/${cid}`);
	xhr.setRequestHeader('xhr', 'xhr');
	xhr.onload=function(){
		if (xhr.status==200) {
			document.getElementById(`morecomments-${cid}`).innerHTML = xhr.response.replace(/data-src/g, 'src').replace(/data-cfsrc/g, 'src').replace(/style="display:none;visibility:hidden;"/g, '');
			bs_trigger()
		}
		btn.disabled = false;
	}
	xhr.send(form)
}

function expandMarkdown(id) {
	document.getElementById('markdown-'+id).classList.toggle('d-none');
	document.getElementsByClassName('text-expand-icon-'+id)[0].classList.toggle('fa-expand-alt');
	document.getElementsByClassName('text-expand-icon-'+id)[0].classList.toggle('fa-compress-alt');
	document.getElementById('view-'+id).classList.toggle('d-none');
	document.getElementById('hide-'+id).classList.toggle('d-none');
};