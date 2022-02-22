function hide_image() {
	x=document.getElementById('image-upload-block');
	url=document.getElementById('post-url').value;
	if (url.length>=1){
		x.classList.add('d-none');
	}
	else {
		x.classList.remove('d-none');
	}
}

document.onpaste = function(event) {
	files = event.clipboardData.files
	filename = files[0].name.toLowerCase()

	if (filename.endsWith(".jpg") || filename.endsWith(".jpeg") || filename.endsWith(".png") || filename.endsWith(".webp") || filename.endsWith(".gif"))
	{
		if (document.activeElement.id == 'post-text') {
			document.getElementById('file-upload-submit').files = files;
			document.getElementById('filename-show-submit').textContent = filename;
		}
		else {
			f=document.getElementById('file-upload');
			f.files = files;
			document.getElementById('filename-show').textContent = filename;
			document.getElementById('urlblock').classList.add('d-none');
			var fileReader = new FileReader();
			fileReader.readAsDataURL(f.files[0]);
			fileReader.addEventListener("load", function () {document.getElementById('image-preview').setAttribute('src', this.result);});  
			document.getElementById('file-upload').setAttribute('required', 'false');	
		}
		checkForRequired();
	}
}

document.getElementById('file-upload').addEventListener('change', function(){
	f=document.getElementById('file-upload');
	document.getElementById('urlblock').classList.add('d-none');
	document.getElementById('filename-show').textContent = document.getElementById('file-upload').files[0].name.substr(0, 20);
	filename = f.files[0].name.toLowerCase().substr(0, 20)
	if (filename.endsWith(".jpg") || filename.endsWith(".jpeg") || filename.endsWith(".png") || filename.endsWith(".webp") || filename.endsWith(".webp"))
	{
		var fileReader = new FileReader();
		fileReader.readAsDataURL(f.files[0]);
		fileReader.addEventListener("load", function () {document.getElementById('image-preview').setAttribute('src', this.result);});  
		checkForRequired();
	}
})

function savetext() {
	localStorage.setItem("post_title", document.getElementById('post-title').value)
	localStorage.setItem("post_text", document.getElementById('post-text').value)
	localStorage.setItem("post_url", document.getElementById('post-url').value)
	let sub = document.getElementById('sub')
	if (sub) localStorage.setItem("sub", sub.value)
}


function autoSuggestTitle()	{

    var urlField = document.getElementById("post-url");

    var titleField = document.getElementById("post-title");

    var isValidURL = urlField.checkValidity();

    if (isValidURL && urlField.value.length > 0 && titleField.value === "") {

        var x = new XMLHttpRequest();
        x.withCredentials=true;
        x.onreadystatechange = function() {
            if (x.readyState == 4 && x.status == 200) {

                title=JSON.parse(x.responseText)["title"];
                titleField.value=title;

                checkForRequired()
            }
        }
        x.open('get','/submit/title?url=' + urlField.value);
        x.send(null);

    };

};