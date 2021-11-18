function post(url) {
	var xhr = new XMLHttpRequest();
	xhr.open("POST", url, true);
	var form = new FormData()
	form.append("formkey", formkey());
	xhr.withCredentials=true;
	xhr.send(form);
};

function post_toast3(url, button1, button2) {
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
			return true

		} else if (xhr.status >= 300 && xhr.status < 400) {
			window.location.href = JSON.parse(xhr.response)["redirect"]
		} else {

			try {
				data=JSON.parse(xhr.response);
			} catch(e) {}

			var myToast = new bootstrap.Toast(document.getElementById('toast-post-success'));
			myToast.hide();
			var myToast = new bootstrap.Toast(document.getElementById('toast-post-error'));
			myToast.show();
			return false
		}
	};

	xhr.send(form);

	document.getElementById(button1).classList.toggle("d-md-inline-block");
	document.getElementById(button2).classList.toggle("d-md-inline-block");
}

report_commentModal = function(id, author) {

document.getElementById("comment-author").textContent = author;

document.getElementById("reportCommentButton").onclick = function() {

	this.innerHTML='Reporting comment';
	this.disabled = true;
	var xhr = new XMLHttpRequest();
	xhr.open("POST", '/flag/comment/'+id, true);
	var form = new FormData()
	form.append("formkey", formkey());
	form.append("reason", document.getElementById("reason-comment").value);

	xhr.withCredentials=true;

	xhr.onload=function() {
		document.getElementById("reportCommentFormBefore").classList.add('d-none');
		document.getElementById("reportCommentFormAfter").classList.remove('d-none');
	};

	xhr.onerror=function(){alert(errortext)};
	xhr.send(form);
}

};

function openReplyBox(id) {
	const element = document.getElementById(`reply-to-${id}`);
	element.classList.remove('d-none')

	element.getElementsByTagName('textarea')[0].focus()
}

toggleEdit=function(id){
	comment=document.getElementById("comment-text-"+id);
	form=document.getElementById("comment-edit-"+id);
	box=document.getElementById('comment-edit-body-'+id);
	actions = document.getElementById('comment-' + id +'-actions');

	comment.classList.toggle("d-none");
	form.classList.toggle("d-none");
	actions.classList.toggle("d-none");
	autoExpand(box);
};


function delete_commentModal(id) {

	document.getElementById("deleteCommentButton").onclick = function() {	

		this.innerHTML='Deleting comment';	
		this.disabled = true; 

		var url = '/delete/comment/' + id
		var xhr = new XMLHttpRequest();
		xhr.open("POST", url, true);
		var form = new FormData()
		form.append("formkey", formkey());
		xhr.withCredentials=true;
		xhr.onload = function() {location.reload(true);};
		xhr.send(form);
}

};

post_reply=function(id){

	var form = new FormData();

	form.append('formkey', formkey());
	form.append('parent_id', id);
	form.append('body', document.getElementById('reply-form-body-'+id).value);
	var xhr = new XMLHttpRequest();
	xhr.open("post", "/reply");
	xhr.withCredentials=true;
	xhr.onload=function(){
		if (xhr.status==200) {
			commentForm=document.getElementById('comment-form-space-'+id);
			commentForm.innerHTML = xhr.response.replace(/data-src/g, 'src').replace(/data-cfsrc/g, 'src').replace(/style="display:none;visibility:hidden;"/g, '');
		}
		else {
			var myToast = new bootstrap.Toast(document.getElementById('toast-post-success'));
			myToast.hide();
			var myToast = new bootstrap.Toast(document.getElementById('toast-post-error'));
			myToast.show();
			try {document.getElementById('toast-post-error-text').innerText = JSON.parse(xhr.response)["error"];}
			catch {}
		}
	}
	xhr.send(form)
}

comment_edit=function(id){

	var form = new FormData();

	form.append('formkey', formkey());
	form.append('body', document.getElementById('comment-edit-body-'+id).value);
	form.append('file', document.getElementById('file-edit-reply-'+id).files[0]);

	var xhr = new XMLHttpRequest();
	xhr.open("post", "/edit_comment/"+id);
	xhr.withCredentials=true;
	xhr.onload=function(){
		if (xhr.status==200) {
			commentForm=document.getElementById('comment-text-'+id);
			commentForm.innerHTML = xhr.response.replace(/data-src/g, 'src').replace(/data-cfsrc/g, 'src').replace(/style="display:none;visibility:hidden;"/g, '');
			document.getElementById('cancel-edit-'+id).click()
		}
		else {
			var myToast = new bootstrap.Toast(document.getElementById('toast-post-success'));
			myToast.hide();
			var myToast = new bootstrap.Toast(document.getElementById('toast-post-error'));
			myToast.show();
			try {document.getElementById('toast-post-error-text').innerText = JSON.parse(xhr.response)["error"];}
			catch {}
		}
	}
	xhr.send(form)
}

post_comment=function(fullname){
	const btn = document.getElementById('save-reply-to-'+fullname)
	btn.classList.add('disabled');

	var form = new FormData();

	form.append('formkey', formkey());
	form.append('parent_fullname', fullname);
	form.append('submission', document.getElementById('reply-form-submission-'+fullname).value);
	form.append('body', document.getElementById('reply-form-body-'+fullname).value);
	form.append('file', document.getElementById('file-upload-reply-'+fullname).files[0]);

	var xhr = new XMLHttpRequest();
	xhr.open("post", "/comment");
	xhr.withCredentials=true;
	xhr.onload=function(){
		if (xhr.status==200) {
			commentForm=document.getElementById('comment-form-space-'+fullname);
			commentForm.innerHTML = xhr.response.replace(/data-src/g, 'src').replace(/data-cfsrc/g, 'src').replace(/style="display:none;visibility:hidden;"/g, '');
		}
		else {
			var myToast = new bootstrap.Toast(document.getElementById('toast-post-success'));
			myToast.hide();
			var myToast = new bootstrap.Toast(document.getElementById('toast-post-error'));
			myToast.show();
			try {document.getElementById('toast-post-error-text').innerText = JSON.parse(xhr.response)["error"];}
			catch {}
			btn.classList.remove('disabled');
		}
	}
	xhr.send(form)
}

document.onpaste = function(event) {
	var focused = document.activeElement;
	if (focused.id.includes('reply-form-body-')) {
		var fullname = focused.dataset.fullname;
		f=document.getElementById('file-upload-reply-' + fullname);
		files = event.clipboardData.files
		filename = files[0].name.toLowerCase()
		if (filename.endsWith(".jpg") || filename.endsWith(".jpeg") || filename.endsWith(".png") || filename.endsWith(".webp") || filename.endsWith(".gif"))
		{
			f.files = files;
			document.getElementById('filename-show-reply-' + fullname).textContent = filename;
		}
	}
	else if (focused.id.includes('comment-edit-body-')) {
		var id = focused.dataset.id;
		f=document.getElementById('file-edit-reply-' + id);
		files = event.clipboardData.files
		filename = files[0].name.toLowerCase()
		if (filename.endsWith(".jpg") || filename.endsWith(".jpeg") || filename.endsWith(".png") || filename.endsWith(".webp") || filename.endsWith(".gif"))
		{
			f.files = files;
			document.getElementById('filename-edit-reply-' + id).textContent = filename;
		}
	}
}

function markdown(first, second) {
	var input = document.getElementById(first).value;

	var emojis = Array.from(input.matchAll(/:(.{1,30}?):/gi))
	if(emojis != null){
		for(i = 0; i < emojis.length; i++){
			var emoji = emojis[i][0]
			var remoji = emoji.replace(/:/g,'');
			if (remoji.startsWith("!"))
			{
				input = input.replace(emoji, "<img height=30 src='/assets/images/emojis/" + remoji.substring(1) + ".webp' class='mirrored'>")
			} else {
				input = input.replace(emoji, "<img height=30 src='/assets/images/emojis/" + remoji + ".webp'>")
			}

		}
	}

	if (!first.includes('edit'))
	{
		var options = Array.from(input.matchAll(/\s*\$\$([^\$\n]+)\$\$\s*/gi))
		if(options != null){
			for(i = 0; i < options.length; i++){
				var option = options[i][0];
				var option2 = option.replace(/\$\$/g, '').replace(/\n/g, '')
				input = input.replace(option, '');
				input += '<div class="custom-control"><input type="checkbox" class="custom-control-input" id="' + option2 + '"><label class="custom-control-label" for="' + option2 + '">' + option2 + ' - <a>0 votes</a></label></div>';
			}
		}
	}
	
	document.getElementById(second).innerHTML = marked(input)
}