function togglePostEdit(id){
	body=document.getElementById("post-body");
	title=document.getElementById("post-title");
	form=document.getElementById("edit-post-body-"+id);
	box=document.getElementById("post-edit-box-"+id);

	body.classList.toggle("d-none");
	title.classList.toggle("d-none");
	form.classList.toggle("d-none");
	autoExpand(box);
};