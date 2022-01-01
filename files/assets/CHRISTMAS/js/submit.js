function hide_image() {
	x=document.getElementById('image-upload-block');
	url=document.getElementById('post-URL').value;
	if (url.length>=1){
		x.classList.add('hidden');
	}
	else {
		x.classList.remove('hidden');
	}
}

function checkForRequired() {

	var title = document.getElementById("post-title");

	var url = document.getElementById("post-URL");

	var text = document.getElementById("post-text");

	var button = document.getElementById("create_button");

	var image = document.getElementById("file-upload");

	if (url.value.length > 0 || image.value.length > 0) {
		text.required = false;
		url.required=false;
	} else if (text.value.length > 0 || image.value.length > 0) {
		url.required = false;
	} else {
		text.required = true;
		url.required = true;
	}

	var isValidTitle = title.checkValidity();

	var isValidURL = url.checkValidity();

	var isValidText = text.checkValidity();

	if (isValidTitle && (isValidURL || image.value.length>0)) {
		button.disabled = false;
	} else if (isValidTitle && isValidText) {
		button.disabled = false;
	} else {
		button.disabled = true;
	}
}

document.onpaste = function(event) {
	f=document.getElementById('file-upload');
	files = event.clipboardData.files
	filename = files[0].name.toLowerCase()
	if (filename.endsWith(".jpg") || filename.endsWith(".jpeg") || filename.endsWith(".png") || filename.endsWith(".webp") || filename.endsWith(".gif"))
	{
		f.files = files;
		document.getElementById('filename-show').textContent = filename;
		document.getElementById('urlblock').classList.add('hidden');
		var fileReader = new FileReader();
		fileReader.readAsDataURL(f.files[0]);
		fileReader.addEventListener("load", function () {document.getElementById('image-preview').setAttribute('src', this.result);});  
		document.getElementById('file-upload').setAttribute('required', 'false');
		checkForRequired();
	}
}

document.getElementById('file-upload').addEventListener('change', function(){
	f=document.getElementById('file-upload');
	document.getElementById('urlblock').classList.add('hidden');
	document.getElementById('filename-show').textContent = document.getElementById('file-upload').files[0].name;
	filename = f.files[0].name.toLowerCase()
	if (filename.endsWith(".jpg") || filename.endsWith(".jpeg") || filename.endsWith(".png") || filename.endsWith(".webp") || filename.endsWith(".webp"))
	{
		var fileReader = new FileReader();
		fileReader.readAsDataURL(f.files[0]);
		fileReader.addEventListener("load", function () {document.getElementById('image-preview').setAttribute('src', this.result);});  
		checkForRequired();
	}
})

window.onload = function() {
	const storage = window.localStorage;
	const input = document.getElementById('post-text');

	if (storage.getItem('bodyText') !== null) {
		input.value = JSON.parse(storage.getItem('bodyText'));
	}
}

// Get the input box
let bodyInput = document.getElementById('post-text');

// Init a timeout variable to be used below
let timeout = null;

// Listen for keystroke events
bodyInput.addEventListener('keyup', function (e) {
    // Clear the timeout if it has already been set.
    // This will prevent the previous task from executing
    // if it has been less than <MILLISECONDS>
    clearTimeout(timeout);

    // Make a new timeout set to go off in 1000ms (1 second)
    timeout = setTimeout(function () {
    	const storage = window.localStorage;
    	const helper = document.getElementById('draft-text');

    	storage.setItem('bodyText', JSON.stringify(bodyInput.value));

    	helper.innerText = 'Draft saved';
    	console.log(storage.getItem('bodyText'))
    }, 1000);
});

// Clear local storage on form submit, use "bind()" method to pass key paramater to specifcy with storage to clear
document.getElementById('submitform').addEventListener('submit', emptyStorage.bind(event, 'bodyText'));

// clear local storage by key name
function emptyStorage(key) {
	window.localStorage.removeItem(key);
	console.log('local storage cleared')
}