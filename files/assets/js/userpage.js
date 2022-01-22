const playing = localStorage.getItem("playing")

let u_username = document.getElementById('u_username')

if (u_username)
{
	u_username = u_username.innerHTML

	let audio = new Audio(`/@${u_username}/song`);
	audio.loop=true;

	function toggle() {
		if (audio.paused)
		{
			audio.play()
			localStorage.setItem("playing", "1")
		}
		else
		{
			audio.pause()
			localStorage.setItem("playing", "")
		}
	}

	if (!playing)
	{
		audio.play();
		document.getElementById('userpage').addEventListener('click', () => {
			if (audio.paused) audio.play(); 
		}, {once : true});

		localStorage.setItem("playing", "1")
		window.addEventListener("unload", function(e) {
			localStorage.setItem("playing", "")
		});
	}
}
else
{
	let v_username = document.getElementById('v_username')
	if (v_username)
	{
		v_username = v_username.innerHTML

		const paused = localStorage.getItem("paused")

		let audio = new Audio(`/@${v_username}/song`);
		audio.loop=true;
	
		function toggle() {
			if (audio.paused)
			{
				audio.play()
				localStorage.setItem("paused", "")
				localStorage.setItem("playing", "1")
			}
			else
			{
				audio.pause()
				localStorage.setItem("paused", "1")
				localStorage.setItem("playing", "")
			}
		}
	
		if (!paused && !playing)
		{
			audio.play();
			document.getElementById('userpage').addEventListener('click', () => {
				if (audio.paused) audio.play(); 
			}, {once : true});

			localStorage.setItem("playing", "1")
			window.addEventListener("unload", function(e) {
				localStorage.setItem("playing", "")
			});
		}
	}
}