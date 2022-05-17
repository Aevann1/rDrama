function post_toast3(t, url, button1, button2) {
	t.disabled=true;
	t.classList.add("disabled");
	const xhr = new XMLHttpRequest();
	xhr.open("POST", url);
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
		if (xhr.status >= 200 && xhr.status < 300 && data && data["message"]) {
			document.getElementById('toast-post-success-text').innerText = data["message"];
			bootstrap.Toast.getOrCreateInstance(document.getElementById('toast-post-success')).show();

			document.getElementById(button1).classList.toggle("d-md-inline-block");
			document.getElementById(button2).classList.toggle("d-md-inline-block");
		
		} else {
			document.getElementById('toast-post-error-text').innerText = "Error, please try again later."
			if (data && data["error"]) document.getElementById('toast-post-error-text').innerText = data["error"];
			bootstrap.Toast.getOrCreateInstance(document.getElementById('toast-post-error')).show();
		}
		setTimeout(() => {
			t.disabled = false;
			t.classList.remove("disabled");
		}, 2000);
	};

	xhr.send(form);
}

function report_commentModal(id, author) {

	document.getElementById("comment-author").textContent = author;

	document.getElementById("reportCommentFormBefore").classList.remove('d-none');
	document.getElementById("reportCommentFormAfter").classList.add('d-none');

	btn = document.getElementById("reportCommentButton")
	btn.innerHTML='Report comment';
	btn.disabled = false;
	btn.classList.remove('disabled');

	reason = document.getElementById("reason-comment")
	reason.value = ""
	
	btn.onclick = function() {
		this.innerHTML='Reporting comment';
		this.disabled = true;
		this.classList.add('disabled');
		const xhr = new XMLHttpRequest();
		xhr.open("POST", '/report/comment/'+id);
		xhr.setRequestHeader('xhr', 'xhr');
		var form = new FormData()
		form.append("formkey", formkey());
		form.append("reason", reason.value);

		xhr.onload=function() {
			document.getElementById("reportCommentFormBefore").classList.add('d-none');
			document.getElementById("reportCommentFormAfter").classList.remove('d-none');
		};

		xhr.onerror=function(){alert(errortext)};
		xhr.send(form);
	}

};

// Returns the selection text based on the range with the HTML
function getSelectionTextHtml() {
    let html = "";
    let sel = getSelection();
    if (sel.rangeCount) {
        let container = document.createElement("div");
        container.appendChild(sel.getRangeAt(0).cloneContents());
        html += container.innerHTML;
    }
    return html;
}

function openReplyBox(id) {
	const element = document.getElementById(id);
	const textarea = element.getElementsByTagName('textarea')[0]
	let text = getSelectionTextHtml()
  		
	if (text)
	{
		textarea.value = '>' + text.replace(/\n<img /g,"<img ")
			.replace(/<img.*?alt=\"(.*?)\".*?>\n/g,"$1\r\n>") // Emojis with newline
			.replace(/<img.*?alt=\"(.*?)\".*?>/g,"$1") // Emojis
			.replace(/\n<p>/g,"")
			.replace(/<p>/g,"")
			.replace(/<\/p>/g,"\n>")
			.replace(/\*/g,"\\*")
			.replace(/\*\*/g,"\\*\\*")
			.replace(/\_/g,"\\_")
			.replace(/\~\~/g,"\\~\\~")
			.replace(/<i>|<\/i>/g,"*")
			.replace(/<b>|<\/b>/g,"**")
			.replace(/<u>|<\/u>/g,"_")
			.replace(/<strike>|<\/strike>/g,"~~")
			.replace(/\n>$/g,"")
			.replace(/\n\n([^$])/g,"\n\n>$1")
		if (!textarea.value.endsWith('\n\n')) textarea.value += '\n\n'
	}
	element.classList.remove('d-none')
	textarea.focus()
}

function toggleEdit(id){
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
	document.getElementById("deleteCommentButton").onclick =  function() {
		const xhr = new XMLHttpRequest();
		xhr.open("POST", `/delete/comment/${id}`);
		xhr.setRequestHeader('xhr', 'xhr');
		var form = new FormData()
		form.append("formkey", formkey());
		xhr.onload = function() {
			let data
			try {data = JSON.parse(xhr.response)}
			catch(e) {console.log(e)}
			if (xhr.status >= 200 && xhr.status < 300 && data && data['message']) {
				document.getElementsByClassName(`comment-${id}-only`)[0].classList.add('deleted');
				document.getElementById(`delete-${id}`).classList.add('d-none');
				document.getElementById(`undelete-${id}`).classList.remove('d-none');
				document.getElementById(`delete2-${id}`).classList.add('d-none');
				document.getElementById(`undelete2-${id}`).classList.remove('d-none');
				document.getElementById('toast-post-success-text').innerText = data["message"];
				bootstrap.Toast.getOrCreateInstance(document.getElementById('toast-post-success')).show();
			} else {
				document.getElementById('toast-post-error-text').innerText = "Error, please try again later."
				if (data && data["error"]) document.getElementById('toast-post-error-text').innerText = data["error"];
				bootstrap.Toast.getOrCreateInstance(document.getElementById('toast-post-error')).show();
			}
		};
		xhr.send(form);
	};
}

function post_reply(id){
	const btn = document.getElementById(`save-reply-to-${id}`)
	btn.disabled = true;
	btn.classList.add('disabled');

	var form = new FormData();
	form.append('formkey', formkey());
	form.append('parent_id', id);
	form.append('body', document.getElementById('reply-form-body-'+id).value);

	try {
		for (const e of document.getElementById('file-upload').files)
			form.append('file', e);
	}
	catch(e) {}

	const xhr = new XMLHttpRequest();
	xhr.open("post", "/reply");
	xhr.setRequestHeader('xhr', 'xhr');
	xhr.onload=function(){
		let data
		try {data = JSON.parse(xhr.response)}
		catch(e) {console.log(e)}
		if (data && data["comment"]) {
			commentForm=document.getElementById('comment-form-space-'+id);
			commentForm.innerHTML = data["comment"].replace(/data-src/g, 'src').replace(/data-cfsrc/g, 'src').replace(/style="display:none;visibility:hidden;"/g, '').replace('comment-collapse-desktop d-none d-md-block','d-none').replace('border-left: 2px solid','padding-left:0;border-left: 0px solid');
			bs_trigger(commentForm);
		}
		else {
			if (data && data["error"]) document.getElementById('toast-post-error-text').innerText = data["error"];
			else document.getElementById('toast-post-error-text').innerText = "Error, please try again later."
			bootstrap.Toast.getOrCreateInstance(document.getElementById('toast-post-error')).show();
		}
		setTimeout(() => {
			btn.disabled = false;
			btn.classList.remove('disabled');
		}, 2000);
	}
	xhr.send(form)
}

function comment_edit(id){
	const btn = document.getElementById(`edit-btn-${id}`)
	btn.disabled = true
	btn.classList.add('disabled');

	var form = new FormData();

	form.append('formkey', formkey());
	form.append('body', document.getElementById('comment-edit-body-'+id).value);

	try {
		for (const e of document.getElementById('file-edit-reply-'+id).files)
			form.append('file', e);
	}
	catch(e) {}

	const xhr = new XMLHttpRequest();
	xhr.open("post", "/edit_comment/"+id);
	xhr.setRequestHeader('xhr', 'xhr');
	xhr.onload=function(){
		let data
		try {data = JSON.parse(xhr.response)}
		catch(e) {console.log(e)}
		if (data && data["comment"]) {
			commentForm=document.getElementById('comment-text-'+id);
			commentForm.innerHTML = data["comment"].replace(/data-src/g, 'src').replace(/data-cfsrc/g, 'src').replace(/style="display:none;visibility:hidden;"/g, '')
			document.getElementById('cancel-edit-'+id).click()
			bs_trigger(commentForm);
		}
		else {
			if (data && data["error"]) document.getElementById('toast-post-error-text').innerText = data["error"];
			else document.getElementById('toast-post-error-text').innerText = "Error, please try again later."
			bootstrap.Toast.getOrCreateInstance(document.getElementById('toast-post-error')).show();
		}
		setTimeout(() => {
			btn.disabled = false;
			btn.classList.remove('disabled');
		}, 2000);
	}
	xhr.send(form)
}

function post_comment(fullname){
	const btn = document.getElementById('save-reply-to-'+fullname)
	btn.disabled = true
	btn.classList.add('disabled');

	var form = new FormData();

	form.append('formkey', formkey());
	form.append('parent_fullname', fullname);
	form.append('submission', document.getElementById('reply-form-submission-'+fullname).value);
	form.append('body', document.getElementById('reply-form-body-'+fullname).value);

	try {
		for (const e of document.getElementById('file-upload-reply-'+fullname).files)
			form.append('file', e);
	}
	catch(e) {}
	
	const xhr = new XMLHttpRequest();
	xhr.open("post", "/comment");
	xhr.setRequestHeader('xhr', 'xhr');
	xhr.onload=function(){
		let data
		try {data = JSON.parse(xhr.response)}
		catch(e) {console.log(e)}
		if (data && data["comment"]) {
			commentForm=document.getElementById('comment-form-space-'+fullname);
			commentForm.innerHTML = data["comment"].replace(/data-src/g, 'src').replace(/data-cfsrc/g, 'src').replace(/style="display:none;visibility:hidden;"/g, '');
			bs_trigger(commentForm);
		}
		else {
			if (data && data["error"]) document.getElementById('toast-post-error-text').innerText = data["error"];
			else document.getElementById('toast-post-error-text').innerText = "Error, please try again later."
			bootstrap.Toast.getOrCreateInstance(document.getElementById('toast-post-error')).show();
		}
		setTimeout(() => {
			btn.disabled = false;
			btn.classList.remove('disabled');
		}, 2000);
	}
	xhr.send(form)
}

document.onpaste = function(event) {
	var focused = document.activeElement;
	if (focused.id.includes('reply-form-body-')) {
		var fullname = focused.dataset.fullname;
		f=document.getElementById('file-upload-reply-' + fullname);
		files = event.clipboardData.files
		try {
			filename = files[0].name.toLowerCase()
			if (filename.endsWith(".jpg") || filename.endsWith(".jpeg") || filename.endsWith(".png") || filename.endsWith(".webp") || filename.endsWith(".gif"))
			{
				f.files = files;
				document.getElementById('filename-show-reply-' + fullname).textContent = filename;
			}
		}
		catch(e) {console.log(e)}
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
	else if (focused.id.includes('post-edit-box-')) {
		var id = focused.dataset.id;
		f=document.getElementById('file-upload-edit-' + id);
		files = event.clipboardData.files
		filename = files[0].name.toLowerCase()
		if (filename.endsWith(".jpg") || filename.endsWith(".jpeg") || filename.endsWith(".png") || filename.endsWith(".webp") || filename.endsWith(".gif"))
		{
			f.files = files;
			document.getElementById('filename-show-edit-' + id).textContent = filename;
		}
	}
}

function handle_action(type, cid, thing) {


	const btns = document.getElementsByClassName(`action-${cid}`)
	for (const btn of btns)
	{
		btn.disabled = true;
		btn.classList.add('disabled');
	}

	const form = new FormData();
	form.append('formkey', formkey());
	form.append('comment_id', cid);
	form.append('thing', thing);
	
	const xhr = new XMLHttpRequest();
	xhr.open("post", `/${type}/${cid}`);
	xhr.setRequestHeader('xhr', 'xhr');



	xhr.onload=function(){
		let data
		try {data = JSON.parse(xhr.response)}
		catch(e) {console.log(e)}
		if (data && data["response"]) {
			const element = document.getElementById(`${type}-${cid}`);
			element.innerHTML = data["response"]
		}
		else {
			if (data && data["error"]) document.getElementById('toast-post-error-text').innerText = data["error"];
			else document.getElementById('toast-post-error-text').innerText = "Error, please try again later."
			bootstrap.Toast.getOrCreateInstance(document.getElementById('toast-post-error')).show();
		}
		setTimeout(() => {
			for (const btn of btns)
			{		
				btn.disabled = false;
				btn.classList.remove('disabled');
			}
		}, 2000);
	}
	xhr.send(form)
}
