function removeComment(post_id,button1,button2) {
	url="/ban_comment/"+post_id

	post(url)

	try {
		document.getElementById("comment-"+post_id+"-only").classList.add("banned");
	} catch(e) {
		document.getElementById("context").classList.add("banned");
	}

	var button=document.getElementById("remove-"+post_id);
	button.onclick=function(){approveComment(post_id)};
	button.innerHTML='<i class="fas fa-clipboard-check"></i>Approve'

	if (typeof button1 !== 'undefined') {
		document.getElementById(button1).classList.toggle("d-md-inline-block");
		document.getElementById(button2).classList.toggle("d-md-inline-block");
	}
};

function approveComment(post_id,button1,button2) {
	url="/unban_comment/"+post_id

	post(url)

	try {
		document.getElementById("comment-"+post_id+"-only").classList.remove("banned");
	} catch(e) {
		document.getElementById("context").classList.remove("banned");
	}

	var button=document.getElementById("remove-"+post_id);
	button.onclick=function(){removeComment(post_id)};
	button.innerHTML='<i class="fas fa-trash-alt"></i>Remove'

	if (typeof button1 !== 'undefined') {
		document.getElementById(button1).classList.toggle("d-md-inline-block");
		document.getElementById(button2).classList.toggle("d-md-inline-block");
	}
}

function lockComment(post_id,button1,button2) {
	url="/lock_comment/"+post_id

	post(url)

	try {
		document.getElementById("comment-"+post_id+"-only").classList.add("locked");
	} catch(e) {
		document.getElementById("context").classList.add("locked");
	}

	var button=document.getElementById("lock-"+post_id);
	button.onclick=function(){unlockComment(post_id)};
	button.innerHTML='<i class="fas fa-clipboard-check"></i>Unlock'

	if (typeof button1 !== 'undefined') {
		document.getElementById(button1).classList.toggle("d-md-inline-block");
		document.getElementById(button2).classList.toggle("d-md-inline-block");
	}
};

function unlockComment(post_id,button1,button2) {
	url="/unlock_comment/"+post_id

	post(url)

	try {
		document.getElementById("comment-"+post_id+"-only").classList.remove("locked");
	} catch(e) {
		document.getElementById("context").classList.remove("locked");
	}

	var button=document.getElementById("lock-"+post_id);
	button.onclick=function(){lockComment(post_id)};
	button.innerHTML='<i class="fas fa-trash-alt"></i>Lock'

	if (typeof button1 !== 'undefined') {
		document.getElementById(button1).classList.toggle("d-md-inline-block");
		document.getElementById(button2).classList.toggle("d-md-inline-block");
	}
}


function removeComment2(post_id,button1,button2) {
	url="/ban_comment/"+post_id

	post(url)

	document.getElementById("comment-"+post_id+"-only").classList.add("banned");
	var button=document.getElementById("remove-"+post_id);
	button.onclick=function(){approveComment(post_id)};
	button.innerHTML='<i class="fas fa-clipboard-check"></i>Approve'

	if (typeof button1 !== 'undefined') {
		document.getElementById(button1).classList.toggle("d-none");
		document.getElementById(button2).classList.toggle("d-none");
	}
};

function approveComment2(post_id,button1,button2) {
	url="/unban_comment/"+post_id

	post(url)

	document.getElementById("comment-"+post_id+"-only").classList.remove("banned");
	var button=document.getElementById("remove-"+post_id);
	button.onclick=function(){removeComment(post_id)};
	button.innerHTML='<i class="fas fa-trash-alt"></i>Remove'

	if (typeof button1 !== 'undefined') {
		document.getElementById(button1).classList.toggle("d-none");
		document.getElementById(button2).classList.toggle("d-none");
	}
}