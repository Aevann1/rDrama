window.onload = function () {
	var prevScrollpos = window.pageYOffset;
	window.onscroll = function () {
		var currentScrollPos = window.pageYOffset;

		var topBar = document.getElementById("fixed-bar-mobile");

		var bottomBar = document.getElementById("mobile-bottom-navigation-bar");

		var dropdown = document.getElementById("mobileSortDropdown");

		var navbar = document.getElementById("navbar");

		if (bottomBar != null) {
			if (prevScrollpos > currentScrollPos && (window.innerHeight + currentScrollPos) < (document.body.offsetHeight - 65)) {
				bottomBar.style.bottom = "0px";
			} 
			else if (currentScrollPos <= 125 && (window.innerHeight + currentScrollPos) < (document.body.offsetHeight - 65)) {
				bottomBar.style.bottom = "0px";
			}
			else if (prevScrollpos > currentScrollPos && (window.innerHeight + currentScrollPos) >= (document.body.offsetHeight - 65)) {
				bottomBar.style.bottom = "-50px";
			}
			else {
				bottomBar.style.bottom = "-50px";
			}
		}

		if (topBar != null && dropdown != null) {
			if (prevScrollpos > currentScrollPos) {
				topBar.style.top = "48px";
				navbar.classList.remove("shadow");
			} 
			else if (currentScrollPos <= 125) {
				topBar.style.top = "48px";
				navbar.classList.remove("shadow");
			}
			else {
				topBar.style.top = "-48px";
				dropdown.classList.remove('show');
				navbar.classList.add("shadow");
			}
		}
		prevScrollpos = currentScrollPos;
	}
}