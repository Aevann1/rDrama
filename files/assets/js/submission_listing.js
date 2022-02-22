function expandText(id) {
	document.getElementById('post-text-'+id).classList.toggle('d-none');
	for (const e of document.getElementsByClassName('text-expand-icon-'+id))
	{
		e.classList.toggle('fa-expand-alt');
		e.classList.toggle('fa-compress-alt');
	}
};

function togglevideo(pid) {
	let vid = document.getElementById(`video-${pid}`).classList
	vid.toggle('d-none')
	let vid2 = document.getElementById(`video2-${pid}`)
	if (vid.contains('d-none')) vid2.pause()
	else vid2.play()
}