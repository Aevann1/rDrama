document.addEventListener("DOMContentLoaded", function () {

	document.getElementById('password-register').addEventListener('input', function () {

		var charCount = document.getElementById("password-register").value;
		var id = document.getElementById("passwordHelpRegister");
		var successID = document.getElementById("passwordHelpSuccess");

		if (charCount.length >= 8) {
			id.classList.add("d-none");
			successID.classList.remove("d-none");
		} else {
			id.classList.remove("d-none");
			successID.classList.add("d-none");
		}
	});

	document.getElementById('username-register').addEventListener('input', function () {

		const userName = document.getElementById("username-register").value;
		const id = document.getElementById("usernameHelpRegister");

		const API = '/is_available/' + userName;
		if (userName.length >= 3) {
			fetch(API)
				.then(res => res.json())
				.then(json => {
					if (!json[userName]) {
						id.innerHTML = '<span class="form-text font-weight-bold text-danger mt-1">Username already taken :(</span>';
					}
				})
		}

		if (!/[^a-zA-Z0-9_\-$]/.test(userName)) {
			id.innerHTML = '<span class="form-text font-weight-bold text-success mt-1">Username is a-okay!</span>';

			if (userName.length < 3) {
				id.innerHTML = '<span class="form-text font-weight-bold text-muted mt-1">Username must be at least 3 characters long.</span>';
			} else if (userName.length > 25) {
				id.innerHTML = '<span class="form-text font-weight-bold text-danger mt-1">Username must be 25 characters or less.</span>';
			}
		} else {
			id.innerHTML = '<span class="form-text font-weight-bold text-danger mt-1">No special characters or spaces allowed.</span>';
		}

	});

});