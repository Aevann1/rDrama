// Using mouse

document.body.addEventListener('mousedown', function() {
	document.body.classList.add('using-mouse');
});

document.body.addEventListener('keydown', function(event) {
	if (event.keyCode === 9) {
		document.body.classList.remove('using-mouse');
	}
});

//GIFS

	// Identify which comment form to insert GIF into

	var commentFormID;

	function commentForm(form) {
		commentFormID = form;
	};


	// Insert EMOJI markdown into comment box function

	function getEmoji(searchTerm, form) {

		var emoji = ' :'+searchTerm+': '
			
		var commentBox = document.getElementById(form);

		var old	= commentBox.value;

		commentBox.value = old + emoji;

	}

	function loadEmojis(form) {

		const emojis = [
		{
			type:'marsey',
			emojis: ['marseyasian','marseyblm','marseyburger','marseydildo','marseyfacepalm','marseygrilling','marseyjanny','marseymermaid','marseyrentfree','marseyretard','marseysadcat','marseysick','marseysmug','marseytrain', 'marseysipping', 'marseyjamming','marseyangel','marseyblowkiss','marseycry','marseydead','marseyexcited','marseygift','marseyinabox','marseylaugh','marseylove','marseymad','marseyparty','marseyrain','marseyreading','marseyready','marseysad','marseyscarf','marseyshook','marseysleep','marseythumbsup','marseywave', 'marsey69', 'marseycomrade', 'marseyira', 'marseyisis', 'marseymerchant', 'marseynut', 'marseyreich', 'marseyglam', 'marseycowboy', 'marseypat', 'marseypanties', 'marseybingus', 'marseydepressed', 'marseygift']
		},
		{
			type:'platy',
			emojis: ['platyblush','platybruh','platycaveman','platycheer','platydown','platyeyes','platyheart','platylol','platymicdrop','platynooo','platysalute','platyseethe','platythumbsup','platywave']
		},
		{
			type:'tay',
			emojis: ['tayaaa','tayadmire','taycat','taycelebrate','taychefkiss','taychristmas','tayclap','taycold','taycrown','tayflex','tayflirt','taygrimacing','tayhappy','tayheart','tayhmm','tayhuh','tayhyperdab','tayjammin','taylaugh','taymindblown','tayno','taynod','taypeace','taypray','tayrun','tayscrunch','tayshake','tayshrug','taysilly','tayslide','taysmart','taystop','taytantrum','taytea','taythink','tayvibin','taywhat','taywine','taywine2','taywink','tayyes']
		},
		{
			type:'classic',
			emojis: ['2thumbsup','aliendj','ambulance','angry','angrywhip','argue','aroused','ashamed','badass','banana','band','banghead','batman','bigeyes','bite','blind','blowkiss','blush','bong','bounce','bow','breakheart','bs','cartwheel','cat','celebrate','chainsaw','cheers','clap','cold','confused','crazyeyes','cry','cthulhu','cute','D','daydream','ddr','deadpool','devilsmile','diddle','die','distress','disturbing','dizzy','domo','doughboy','drink','drool','dudeweedlmao','edward','electro','elephant','embarrassed','emo','emo2','evil','evilclown','evilgrin','facepalm','fap','flamethrower','flipbird','flirt','frown','gasp','glomp','go','gooby','grr','gtfo','guitar','haha','handshake','happydance','headbang','heart','heartbeat','hearts','highfive','hmm','hmph','holdhands','horny','hug','hugging','hugs','hump','humpbed','hysterical','ily','inlove','jason','jawdrop','jedi','jester','kaboom','kick','kiss','kitty','laughchair','lick','link','lol','lolbeat','loving','makeout','medal','megaman','megamanguitar','meow','metime','mooning','mummy','na','nauseous','nervous','ninja','nod','nono','omg','onfire','ooo','orly','p','paddle','panda','pandabutt','paranoid','party','pat','peek','pikachu','pimp','plzdie','poke','popcorn','pout','probe','puke','punch','quote','raccoon','roar','rofl','roflmao','rolleyes','sad','sadeyes','sadhug','samurai','sarcasm','scoot','scream','shmoopy','shrug','skull','slap','slapfight','sleepy','smackfish','smackhead','smh','smile','smoke','sonic','spank','sparta','sperm','spiderman','stab','star','stare','stfu','suicide','surprisehug','suspicious','sweat','swordfight','taco','talk2hand','tantrum','teehee','thinking','threesome','throw','throwaway','tickle','typing','uhuh','vampbat','viking','violin','vulgar','wah','wat','whip','whipping','wink','witch','wizard','woah','worm','woo','work','worship','wow','XD','yay','zzz']
		},
		{
			type:'rage',
			emojis: ['troll','bitchplease','spit','challengeaccepted','contentiouscereal','cryingatcuteness','derp','derpcornsyrup','derpcrying','derpcute','derpdumb','derpeuphoria','derpinahd','derpinapokerface','derpinasnickering','derpprocessing','derprealization','derpsnickering','derptalking','derpthinking','derpthumbsup','derpunimpressed','derpwhy','donotwant','epicfacefeatures','fancywithwine','fffffffuuuuuuuuuuuu','flipthetable','foreveralone','foreveralonehappy','hewillnever','idontknow','interuptedreading','iseewhatyoudidthere','killherkillher','ledesire','leexcited','legenius','lelolidk','lemiddlefinger','lemindblown','leokay','lepanicrunning','lepokerface','lepokerface2','lerageface','leseriousface','likeaboss','lolface','longwhiskers','manymiddlefingers','megusta','motherfucker','motherofgod','mysides','ohgodwhy','pervertedspiderman','picard','ragestrangle','rukiddingme','tfwyougettrolled','trollolol','truestorybro','xallthey','yuno']
		},
		{
			type:'wojak',
			emojis: ['gigachad','chadyes','chadno','abusivewife','ancap','bardfinn','bloomer','boomer','boomermonster','brainletbush','brainletcaved','brainletchair','brainletchest','brainletmaga','brainletpit','chad','chadarab','chadasian','chadblack','chadjesus','chadjew','chadjihadi','chadlatino','chadlibleft','chadnordic','chadsikh','chadusa','coomer','doomer','doomerfront','doomergirl','ethot','fatbrain','fatpriest','femboy','gogetter','grug','monke','nazijak','npc','npcfront','npcmaga','psychojak','ragejak','ragemask','ramonajak','soyjackwow','soyjak','soyjakfront','soyjakhipster','soyjakmaga','soyjakyell','tomboy','zoomer','zoomersoy']
		},
		{
			type:'flags',
			emojis: ['niger', 'lgbt', 'saudi', 'animesexual','blacknation','blm','blueline','dreamgender','fatpride','incelpride','israel','kazakhstan','landlordlove','scalperpride','superstraight','trans','translord','transracial','usa']
		}
		]

		for (i=0; i < emojis.length; i++) {

			let container = document.getElementById(`EMOJIS_${emojis[i].type}`)
			let str = ''
			let arr = emojis[i].emojis

			for (j=0; j < arr.length; j++) { 
				str += `<button class="btn m-1 px-0" onclick="getEmoji(\'${arr[j]}\', \'${form}\')" style="width:40px; overflow: hidden; border: none;" data-toggle="tooltip" title=":${arr[j]}:" delay:="0"><img width=30 src="/assets/images/emojis/${arr[j]}.gif" alt="${arr[j]}-emoji"/></button>`;
			}

			container.innerHTML = str
		}
	}


	function getGif(searchTerm) {

		if (searchTerm !== undefined) {
			document.getElementById('gifSearch').value = searchTerm;
		}
		else {
			document.getElementById('gifSearch').value = null;
		}

		// load more gifs div

		var loadGIFs = document.getElementById('gifs-load-more');

		// error message div

		var noGIFs = document.getElementById('no-gifs-found');

		// categories div

		var cats = document.getElementById('GIFcats');

		// container div

		var container = document.getElementById('GIFs');

		// modal body div

		var modalBody = document.getElementById('gif-modal-body')

		// UI buttons

		var backBtn = document.getElementById('gifs-back-btn');

		var cancelBtn = document.getElementById('gifs-cancel-btn');

		container.innerHTML = '';

		if (searchTerm == undefined) {
			container.innerHTML = '<div class="card" onclick="getGif(\'agree\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Agree</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/200w_d.gif"> </div> <div class="card" onclick="getGif(\'laugh\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Laugh</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/O5NyCibf93upy/200w_d.gif"> </div> <div class="card" onclick="getGif(\'confused\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Confused</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/3o7btPCcdNniyf0ArS/200w_d.gif"> </div> <div class="card" onclick="getGif(\'sad\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Sad</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/ISOckXUybVfQ4/200w_d.gif"> </div> <div class="card" onclick="getGif(\'happy\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Happy</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/XR9Dp54ZC4dji/200w_d.gif"> </div> <div class="card" onclick="getGif(\'awesome\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Awesome</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/3ohzdIuqJoo8QdKlnW/200w_d.gif"> </div> <div class="card" onclick="getGif(\'yes\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Yes</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/J336VCs1JC42zGRhjH/200w_d.gif"> </div> <div class="card" onclick="getGif(\'no\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">No</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/1zSz5MVw4zKg0/200w_d.gif"> </div> <div class="card" onclick="getGif(\'love\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Love</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/4N1wOi78ZGzSB6H7vK/200w_d.gif"> </div> <div class="card" onclick="getGif(\'please\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Please</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/qUIm5wu6LAAog/200w_d.gif"> </div> <div class="card" onclick="getGif(\'scared\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Scared</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/bEVKYB487Lqxy/200w_d.gif"> </div> <div class="card" onclick="getGif(\'angry\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Angry</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/12Pb87uq0Vwq2c/200w_d.gif"> </div> <div class="card" onclick="getGif(\'awkward\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Awkward</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/unFLKoAV3TkXe/200w_d.gif"> </div> <div class="card" onclick="getGif(\'cringe\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Cringe</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/1jDvQyhGd3L2g/200w_d.gif"> </div> <div class="card" onclick="getGif(\'omg\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">OMG</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/3o72F8t9TDi2xVnxOE/200w_d.gif"> </div> <div class="card" onclick="getGif(\'why\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Why</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/1M9fmo1WAFVK0/200w_d.gif"> </div> <div class="card" onclick="getGif(\'gross\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Gross</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/pVAMI8QYM42n6/200w_d.gif"> </div> <div class="card" onclick="getGif(\'meh\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Meh</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/xT77XTpyEzJ4OJO06c/200w_d.gif"> </div>'

			backBtn.innerHTML = null;

			cancelBtn.innerHTML = null;

			noGIFs.innerHTML = null;

			loadGIFs.innerHTML = null;
		}
		else {
			backBtn.innerHTML = '<button class="btn btn-link pl-0 pr-3" id="gifs-back-btn" onclick="getGif();"><i class="fas fa-long-arrow-left text-muted"></i></button>';

			cancelBtn.innerHTML = '<button class="btn btn-link pl-3 pr-0" id="gifs-cancel-btn" onclick="getGif();"><i class="fas fa-times text-muted"></i></button>';

			$.ajax({
			url: "/giphy?searchTerm=" + searchTerm + "&limit=48",
			type: "GET",
			success: function(response) {
			var max = response.data.length - 1 //length of response, minus 1 (cuz array starts at index 0)
			var randomNumber = Math.round(Math.random() * 6) //random number between 0 and max -1
			// GIF array
			var gifURL = [];

			// loop for fetching mutliple GIFs and creating the card divs
			if (max < 48 && max > 0) {
				for (var i = 0; i <= max; i++) {
				gifURL[i] = "https://media.giphy.com/media/" + response.data[i].id + "/200w_d.gif";
				if (response.data[i].username==''){
					container.innerHTML += ('<div class="card bg-white" style="overflow: hidden" data-dismiss="modal" aria-label="Close" onclick="insertGIF(\'' + 'https://media.giphy.com/media/' + response.data[i].id + '/100w.gif' + '\',\'' + commentFormID + '\')"><div class="gif-cat-overlay"></div><img class="img-fluid" src="' + gifURL[i] + '"></div>');
				}
				else {
					container.innerHTML += ('<div class="card bg-white" style="overflow: hidden" data-dismiss="modal" aria-label="Close" title="by '+response.data[i].username+' on GIPHY" onclick="insertGIF(\'' + 'https://media.giphy.com/media/' + response.data[i].id + '/100w.gif' + '\',\'' + commentFormID + '\')"><div class="gif-cat-overlay"></div><img class="img-fluid" src="' + gifURL[i] + '"></div>');
				}
				noGIFs.innerHTML = null;
				loadGIFs.innerHTML = '<div class="text-center py-3"><div class="mb-3"><i class="fad fa-grin-beam-sweat text-gray-500" style="font-size: 3.5rem;"></i></div><p class="font-weight-bold text-gray-500 mb-0">Thou&#39;ve reached the end of the list!</p></div>';
				}
			}
			else if (max <= 0) {
				noGIFs.innerHTML = '<div class="text-center py-3 mt-3"><div class="mb-3"><i class="fad fa-frown text-gray-500" style="font-size: 3.5rem;"></i></div><p class="font-weight-bold text-gray-500 mb-0">Aw shucks. No GIFs found...</p></div>';
				container.innerHTML = null;
				loadGIFs.innerHTML = null;
			}
			else {
				for (var i = 0; i <= 48; i++) {
				gifURL[i] = "https://media.giphy.com/media/" + response.data[i].id + "/200w_d.gif";
				if (response.data[i].username==''){
					container.innerHTML += ('<div class="card bg-white" style="overflow: hidden" data-dismiss="modal" aria-label="Close" onclick="insertGIF(\'' + 'https://media.giphy.com/media/' + response.data[i].id + '/100w.gif' + '\',\'' + commentFormID + '\')"><div class="gif-cat-overlay"></div><img class="img-fluid" src="' + gifURL[i] + '"></div>');
				}
				else {
					container.innerHTML += ('<div class="card bg-white" style="overflow: hidden" data-dismiss="modal" aria-label="Close" title="by '+response.data[i].username+' on GIPHY" onclick="insertGIF(\'' + 'https://media.giphy.com/media/' + response.data[i].id + '/100w.gif' + '\',\'' + commentFormID + '\')"><div class="gif-cat-overlay"></div><img class="img-fluid" src="' + gifURL[i] + '"></div>');
				}
				noGIFs.innerHTML = null;
				loadGIFs.innerHTML = '<div class="text-center py-3"><div class="mb-3"><i class="fad fa-grin-beam-sweat text-gray-500" style="font-size: 3.5rem;"></i></div><p class="font-weight-bold text-gray-500 mb-0">Thou&#39;ve reached the end of the list!</p></div>';
				}
			}
			},
			error: function(e) {
			alert(e);
			}
		});
		};
		}

		// Insert GIF markdown into comment box function

		function insertGIF(url,form) {

		var gif = "![](" + url +")";

		var commentBox = document.getElementById(form);

		var old	= commentBox.value;

		commentBox.value = old + gif;

		}

		// When GIF keyboard is hidden, hide all GIFs

		$('#gifModal').on('hidden.bs.modal', function (e) {

		document.getElementById('gifSearch').value = null;

		// load more gifs div

		var loadGIFs = document.getElementById('gifs-load-more');

		// no GIFs div

		var noGIFs = document.getElementById('no-gifs-found');

		// container div

		var container = document.getElementById('GIFs');

		// UI buttons

		var backBtn = document.getElementById('gifs-back-btn');

		var cancelBtn = document.getElementById('gifs-cancel-btn');

		// Remove inner HTML from container var

		container.innerHTML = '<div class="card" onclick="getGif(\'agree\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Agree</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/wGhYz3FHaRJgk/200w_d.gif"> </div> <div class="card" onclick="getGif(\'laugh\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Laugh</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/O5NyCibf93upy/200w_d.gif"> </div> <div class="card" onclick="getGif(\'confused\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Confused</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/3o7btPCcdNniyf0ArS/200w_d.gif"> </div> <div class="card" onclick="getGif(\'sad\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Sad</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/ISOckXUybVfQ4/200w_d.gif"> </div> <div class="card" onclick="getGif(\'happy\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Happy</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/XR9Dp54ZC4dji/200w_d.gif"> </div> <div class="card" onclick="getGif(\'awesome\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Awesome</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/3ohzdIuqJoo8QdKlnW/200w_d.gif"> </div> <div class="card" onclick="getGif(\'yes\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Yes</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/J336VCs1JC42zGRhjH/200w_d.gif"> </div> <div class="card" onclick="getGif(\'no\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">No</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/1zSz5MVw4zKg0/200w_d.gif"> </div> <div class="card" onclick="getGif(\'love\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Love</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/4N1wOi78ZGzSB6H7vK/200w_d.gif"> </div> <div class="card" onclick="getGif(\'please\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Please</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/qUIm5wu6LAAog/200w_d.gif"> </div> <div class="card" onclick="getGif(\'scared\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Scared</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/bEVKYB487Lqxy/200w_d.gif"> </div> <div class="card" onclick="getGif(\'angry\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Angry</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/12Pb87uq0Vwq2c/200w_d.gif"> </div> <div class="card" onclick="getGif(\'awkward\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Awkward</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/unFLKoAV3TkXe/200w_d.gif"> </div> <div class="card" onclick="getGif(\'cringe\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Cringe</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/1jDvQyhGd3L2g/200w_d.gif"> </div> <div class="card" onclick="getGif(\'omg\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">OMG</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/3o72F8t9TDi2xVnxOE/200w_d.gif"> </div> <div class="card" onclick="getGif(\'why\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Why</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/1M9fmo1WAFVK0/200w_d.gif"> </div> <div class="card" onclick="getGif(\'gross\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Gross</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/pVAMI8QYM42n6/200w_d.gif"> </div> <div class="card" onclick="getGif(\'meh\');" style="overflow: hidden;"> <div class="gif-cat-overlay"> <div style="position: relative;top: 50%;transform: translateY(-50%);color: #ffffff;font-weight: bold;">Meh</div> </div> <img class="img-fluid" src="https://media.giphy.com/media/xT77XTpyEzJ4OJO06c/200w_d.gif"> </div>'

		// Hide UI buttons

		backBtn.innerHTML = null;

		cancelBtn.innerHTML = null;

		// Remove inner HTML from no gifs div

		noGIFs.innerHTML = null;

		// Hide no more gifs div

		loadGIFs.innerHTML = null;

		});


//iOS webapp stuff

(function(document,navigator,standalone) {
						// prevents links from apps from oppening in mobile safari
						// this javascript must be the first script in your <head>
						if ((standalone in navigator) && navigator[standalone]) {
							var curnode, location=document.location, stop=/^(a|html)$/i;
							document.addEventListener('click', function(e) {
								curnode=e.target;
								while (!(stop).test(curnode.nodeName)) {
									curnode=curnode.parentNode;
								}
										// Condidions to do this only on links to your own app
										// if you want all links, use if('href' in curnode) instead.
										if('href' in curnode && ( curnode.href.indexOf('http') || ~curnode.href.indexOf(location.host) ) ) {
											e.preventDefault();
											location.href = curnode.href;
										}
									},false);
						}
					})(document,window.navigator,'standalone');

//POST

function post(url, callback, errortext) {
	var xhr = new XMLHttpRequest();
	xhr.open("POST", url, true);
	var form = new FormData()
	form.append("formkey", formkey());
	xhr.withCredentials=true;
	xhr.onerror=function() { alert(errortext); };
	xhr.onload = function() {
		if (xhr.status >= 200 && xhr.status < 300) {
			callback();
		} else {
			xhr.onerror();
		}
	};
	xhr.send(form);
};

function request_toast(method, url, callback, data) {
	var xhr = new XMLHttpRequest();
	xhr.open(method, url, true);
	var form = new FormData()

	if(typeof data === 'object' && data !== null) {
		for(let k of Object.keys(data)) {
				form.append(k, data[k]);
		}
	}


	form.append("formkey", formkey());
	xhr.withCredentials=true;

	xhr.onload = function() {
		if (xhr.status >= 200 && xhr.status < 300) {
			$('#toast-post-success').toast('dispose');
			$('#toast-post-success').toast('show');
			try {
				document.getElementById('toast-post-success-text').innerText = JSON.parse(xhr.response)["message"];
			} catch(e) {
				document.getElementById('toast-post-success-text').innerText = "Action successful!";
			}
			try {callback(xhr)}
			catch(e) {}
			return true

		} else if (xhr.status >= 300 && xhr.status < 400) {
			window.location.href = JSON.parse(xhr.response)["redirect"]
		} else {
			try {
				data=JSON.parse(xhr.response);

				$('#toast-post-error').toast('dispose');
				$('#toast-post-error').toast('show');
				document.getElementById('toast-post-error-text').innerText = data["error"];
				return false
			} catch(e) {
				$('#toast-post-success').toast('dispose');
				$('#toast-post-error').toast('dispose');
				$('#toast-post-error').toast('show');
				document.getElementById('toast-post-error-text').innerText = "Error. Try again later.";
				return false
			}
		}
	};

	xhr.send(form);

}

function post_toast(url, callback, data) {
	return request_toast("POST", url, callback, data);
}


// Search Icon
// Change navbar search icon when form is in focus, active states

$(".form-control").focus(function () {
	$(this).prev('.input-group-append').removeClass().addClass('input-group-append-focus');
	$(this).next('.input-group-append').removeClass().addClass('input-group-append-focus');
});

$(".form-control").focusout(function () {
	$(this).prev('.input-group-append-focus').removeClass().addClass('input-group-append');
	$(this).next('.input-group-append-focus').removeClass().addClass('input-group-append');
});

//spinner effect

$(document).ready(function() {
	$('#login').submit(function() {
			// disable button
			$("#login_button").prop("disabled", true);
			// add spinner to button
			$("#login_button").html('<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>Signing in');
		});
});

$(document).ready(function() {
	$('#signup').submit(function() {
			// disable button
			$("#register_button").prop("disabled", true);
			// add spinner to button
			$("#register_button").html('<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>Registering');
		});
});

// Mobile bottom navigation bar

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

	// Execute if bottomBar exists

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

// Tooltips

$(document).ready(function(){
	$('[data-toggle="tooltip"]').tooltip(); 
});


$('.mention-user').click(function (event) {

	if (event.which != 1) {
		return
	}

	event.preventDefault();

	window.location.href='/@' + $(this).data('original-name');

});
