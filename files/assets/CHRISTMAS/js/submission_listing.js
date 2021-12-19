function timestamp(str, ti) {
    date = new Date(ti*1000);
    document.getElementById(str).setAttribute("data-bs-original-title", date.toString());
};

function expandText(id) {
	const el = document.getElementById('post-text-'+id);
    ['gradient-mask', 'max-h-12', 'overflow-hidden', 'pointer-events-none', 'text-gray-600', 'dark:text-gray-400'].map(v=> el.classList.toggle(v));
    ['text-black', 'dark:text-gray-100'].map(v=> el.classList.toggle(v));

    const trigger = document.getElementsByClassName('text-expand-icon-'+id);
    for (let i = 0; i < trigger.length; i++) {
    	trigger[i].classList.toggle('fa-expand-alt');
    	trigger[i].classList.toggle('fa-compress-alt');
    }
};