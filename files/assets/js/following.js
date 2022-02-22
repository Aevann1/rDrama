function removeFollowing(event, username) {
	post_toast(event.target,'/unfollow/' + username); 
	let table = document.getElementById("followers-table");
	table.removeChild(event.target.parentElement.parentElement);
}