function autoExpand (field) {
	xpos=window.scrollX;
	ypos=window.scrollY;

	field.style.height = 'inherit';

	var computed = window.getComputedStyle(field);

	var height = parseInt(computed.getPropertyValue('border-top-width'), 10)
	+ parseInt(computed.getPropertyValue('padding-top'), 10)
	+ field.scrollHeight
	+ parseInt(computed.getPropertyValue('padding-bottom'), 10)
	+ parseInt(computed.getPropertyValue('border-bottom-width'), 10);

	field.style.height = height + 'px';

	window.scrollTo(xpos,ypos);
};

document.addEventListener('input', function (event) {
	if (event.target.tagName.toLowerCase() !== 'textarea') return;
	autoExpand(event.target);
}, false);

function smoothScrollTop()
{
	window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Click navbar to scroll back to top
(() => {
	let toplisteners = [
		document.querySelector('nav')
	];

	for (let i of toplisteners)
	{
		i.addEventListener('click', (e) => {
			if (e.target.id === "navbar" ||
				e.target.classList.contains("container-fluid") ||
				e.target.id == "navbarResponsive" ||
				e.target.id == "logo-container" ||
				e.target.classList.contains("srd"))
				smoothScrollTop();
		}, false);
	}
})();

// Dynamic shadow when the user scrolls
document.addEventListener('scroll',function (event) {
	let nav = document.querySelector("nav");
	let i = (Math.min(20, window.scrollY/4)+1)/21;
	nav.style.boxShadow="0px 2px "+i*21+"px rgba(15,15,15,"+i*.3+")";
	if (window.scrollY <= 0)
	{
//		nav.classList.remove("shadow");
		nav.classList.remove("navbar-active");
		nav.style.boxShadow = "unset";
	}
	else
	{
//		nav.classList.add("shadow");
		nav.classList.add("navbar-active");
	}

}, false);

function formkey() {
	let formkey = document.getElementById("formkey")
	if (formkey) return formkey.innerHTML;
	else return null;
}


function bs_trigger(e) {
	const images = e.querySelectorAll('img[alt^="![]("]');

	for (const e of images) {
		e.setAttribute("data-bs-toggle", "modal")
		e.setAttribute("data-bs-target", "#expandImageModal")
		e.onclick = function(e) {
			const image = e.target.src
			document.getElementById("desktop-expanded-image").src = image.replace("200w_d.webp", "giphy.webp");
			document.getElementById("desktop-expanded-image-link").href = image;
			document.getElementById("desktop-expanded-image-wrap-link").href = image;	
		}
	}

    // TODO
	// let tooltipTriggerList = [].slice.call(e.querySelectorAll('[data-bs-toggle="tooltip"]'));
	// tooltipTriggerList.map(function(element){
	// 	return bootstrap.Tooltip.getOrCreateInstance(element);
	// });

	const popoverTriggerList = [].slice.call(e.querySelectorAll('[data-bs-toggle="popover"]'));
	popoverTriggerList.map(function(popoverTriggerEl) {
		const popoverId = popoverTriggerEl.getAttribute('data-content-id');
		let contentEl;
		try {contentEl = e.getElementById(popoverId);}
		catch(t) {contentEl = document.getElementById(popoverId);}
        // TODO
		// if (contentEl) {
		// 	return bootstrap.Popover.getOrCreateInstance(popoverTriggerEl, {
		// 		content: contentEl.innerHTML,
		// 		html: true,
		// 	});
		// }
	})
}

var bsTriggerOnReady = function() {
	bs_trigger(document);
}

if (document.readyState === "complete" || 
		(document.readyState !== "loading" && !document.documentElement.doScroll)) {
	bsTriggerOnReady();
} else {
	document.addEventListener("DOMContentLoaded", bsTriggerOnReady);
}


function expandDesktopImage(image) {
	document.getElementById("desktop-expanded-image").src = image.replace("200w_d.webp", "giphy.webp");
	document.getElementById("desktop-expanded-image-link").href = image;
	document.getElementById("desktop-expanded-image-wrap-link").href = image;
	this.event.preventDefault();
};

function post_toast(t, url, reload, data) {
	t.disabled = true;
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
		if (xhr.status >= 200 && xhr.status < 300 && data && data['message']) {
			document.getElementById('toast-post-success-text').innerText = data["message"];
			bootstrap.Toast.getOrCreateInstance(document.getElementById('toast-post-success')).show();
			if (reload == 1) {location.reload()}
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

function escapeHTML(unsafe) {
	return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function changename(s1,s2) {
	let files = document.getElementById(s2).files;
	let filename = '';
	for (const e of files) {
		filename += e.name.substr(0, 20) + ', ';
	}
	document.getElementById(s1).innerHTML = escapeHTML(filename.slice(0, -2));
}
