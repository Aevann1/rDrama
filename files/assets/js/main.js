
/* Handles enter press */
if (window.location.pathname != '/submit')
{
	document.addEventListener('keydown', (e) => {
		if(!((e.ctrlKey || e.metaKey) && e.key === "Enter")) return;

		const targetDOM = document.activeElement;
		if(!(targetDOM instanceof HTMLTextAreaElement || targetDOM instanceof HTMLInputElement)) return;

		const formDOM = targetDOM.parentElement;
		if(!(formDOM instanceof HTMLFormElement))
			throw new TypeError("the text area should be child of a FORM. Contact the head custodian immediately.");

		const submitButtonDOMs = formDOM.querySelectorAll('input[type=submit], .btn-primary');
		if(submitButtonDOMs.length === 0)
			throw new TypeError("I am unable to find the submit button :(. Contact the head custodian immediately.")

		const btn = submitButtonDOMs[0]
		btn.click();
		btn.disabled = true;
		btn.classList.add('disabled');
		setTimeout(() => {
			btn.disabled = false;
			btn.classList.remove('disabled');
		}, 2000);
	});
}
