function removeFollower(event, username) {
	post_toast(event.target,'/remove_follow/' + username); 
	let table = document.getElementById("followers-table");
	table.removeChild(event.target.parentElement.parentElement);
}