const fav = document.getElementById('EMOJIS_favorite')
const search_bar = document.getElementById('emoji_search')
const search_container = document.getElementById('emoji-tab-search')
let emojis = 1


function loadEmojis(form) {
	if (emojis == 1)
	{
		const xhr = new XMLHttpRequest();
		xhr.open("GET", '/marsey_list');
		xhr.setRequestHeader('xhr', 'xhr');
		var f = new FormData();
		xhr.onload = function() {
			emojis = {
				'marsey': JSON.parse(xhr.response),

				'marseyalphabet': ['marseyalphaa','marseyalphab','marseyalphac','marseyalphad','marseyalphae','marseyalphaf','marseyalphag','marseyalphah','marseyalphai','marseyalphaj','marseyalphak','marseyalphal','marseyalpham','marseyalphan','marseyalphao','marseyalphap','marseyalphaq','marseyalphar','marseyalphas','marseyalphat','marseyalphau','marseyalphav','marseyalphaw','marseyalphax','marseyalphay','marseyalphaz','marseyalphanumeric0','marseyalphanumeric1','marseyalphanumeric2','marseyalphanumeric3','marseyalphanumeric4','marseyalphanumeric5','marseyalphanumeric6','marseyalphanumeric7','marseyalphanumeric8','marseyalphanumeric9','marseyalphazexclamationpoint','marseyalphazperiod','marseyalphazquestionmark'],
		
				'platy': ['platytrans','platyfuckyou','plarsy','platyabused','platyblizzard','platyboxer','platydevil','platyfear','platygirlmagic','platygolong','platyhaes','platyking','platylove','platyneet','platyold','platypatience','platypopcorn','platyrich','platysarcasm','platysilly','platysleeping','platythink','platytired','platytuxedomask','platyblush','platybruh','platycaveman','platycheer','platydown','platyeyes','platyheart','platylol','platymicdrop','platynooo','platysalute','platyseethe','platythumbsup','platywave'],
		
				'tay': ['taylove','tayaaa','tayadmire','taycat','taycelebrate','taychefkiss','taychristmas','tayclap','taycold','taycrown','tayflex','tayflirt','taygrimacing','tayhappy','tayheart','tayhmm','tayhuh','tayhyperdab','tayjammin','taylaugh','taymindblown','tayno','taynod','taypeace','taypray','tayrun','tayscrunch','tayshake','tayshrug','taysilly','tayslide','taysmart','taystop','taytantrum','taytea','taythink','tayvibin','taywhat','taywine','taywine2','taywink','tayyes'],
		
				'classic': ['scootlgbt','idhitit','2thumbsup','aliendj','ambulance','angry','angrywhip','argue','aroused','ashamed','badass','banana','band','banghead','batman','bigeyes','bite','blind','blowkiss','blush','bong','bounce','bow','breakheart','bs','cartwheel','cat','celebrate','chainsaw','cheers','clap','cold','confused','crazyeyes','cry','cthulhu','cute','laughing','daydream','ddr','deadpool','devilsmile','diddle','die','distress','disturbing','dizzy','domo','doughboy','drink','drool','dudeweedlmao','edward','electro','elephant','embarrassed','emo','emo2','evil','evilclown','evilgrin','facepalm','fap','flamethrower','flipbird','flirt','frown','gasp','glomp','go','gooby','grr','gtfo','guitar','haha','handshake','happydance','headbang','heart','heartbeat','hearts','highfive','hmm','hmph','holdhands','horny','hug','hugging','hugs','hump','humpbed','hysterical','ily','inlove','jason','jawdrop','jedi','jester','kaboom','kick','kiss','kitty','laughchair','lick','link','lol','lolbeat','loving','makeout','medal','megaman','megamanguitar','meow','metime','mooning','mummy','na','nauseous','nervous','ninja','nod','nono','omg','onfire','ooo','orly','tongueout','paddle','panda','pandabutt','paranoid','party','pat','peek','pikachu','pimp','plzdie','poke','popcorn','pout','probe','puke','punch','quote','raccoon','roar','rofl','roflmao','rolleyes','sad','sadeyes','sadhug','samurai','sarcasm','scoot','scream','shmoopy','shrug','skull','slap','slapfight','sleepy','smackfish','smackhead','smh','smile','smoke','sonic','spank','sparta','sperm','spiderman','stab','star','stare','stfu','suicide','surprisehug','suspicious','sweat','swordfight','taco','talk2hand','tantrum','teehee','thinking','threesome','throw','throwaway','tickle','typing','uhuh','vampbat','viking','violin','vulgar','wah','wat','whip','whipping','wink','witch','wizard','woah','worm','woo','work','worship','wow','xd','yay','zzz'],
		
				'rage': ['trolldespair','clueless','troll','bitchplease','spit','challengeaccepted','contentiouscereal','cryingatcuteness','derp','derpcornsyrup','derpcrying','derpcute','derpdumb','derpeuphoria','derpinahd','derpinapokerface','derpinasnickering','derpprocessing','derprealization','derpsnickering','derptalking','derpthinking','derpthumbsup','derpunimpressed','derpwhy','donotwant','epicfacefeatures','fancywithwine','fffffffuuuuuuuuuuuu','flipthetable','foreveralone','foreveralonehappy','hewillnever','idontknow','interuptedreading','iseewhatyoudidthere','killherkillher','ledesire','leexcited','legenius','lelolidk','lemiddlefinger','lemindblown','leokay','lepanicrunning','lepokerface','lepokerface2','lerageface','leseriousface','likeaboss','lolface','longwhiskers','manymiddlefingers','megusta','motherfucker','motherofgod','mysides','ohgodwhy','pervertedspiderman','picard','ragestrangle','rukiddingme','tfwyougettrolled','trollolol','truestorybro','xallthey','yuno'],
		
				'wojak': ['soyconsoomer','soyjaktalking','soyquack','tradboy','sciencejak','soyjakanimeglasses','soymad','boomerportrait','soycry','punchjak','seethejak','chadyes','chadno','abusivewife','ancap','bardfinn','bloomer','boomer','boomermonster','brainletbush','brainletcaved','brainletchair','brainletchest','brainletmaga','brainletpit','chad','chadarab','chadasian','chadblack','chadjesus','chadjew','chadjihadi','chadlatino','chadlibleft','chadnordic','chadsikh','chadusa','coomer','doomer','doomerfront','doomergirl','ethot','fatbrain','fatpriest','femboy','gogetter','grug','monke','nazijak','npc','npcfront','npcmaga','psychojak','ragejak','ragemask','ramonajak','soyjackwow','soyjak','soyjakfront','soyjakhipster','soyjakmaga','soyjakyell','tomboy','zoomer','zoomersoy'],
		
				'flags': ['niger','lgbt','saudi','animesexual','blacknation','blm','blueline','dreamgender','fatpride','incelpride','israel','kazakhstan','landlordlove','scalperpride','superstraight','trans','translord','transracial','usa'],
					
				'wolf': ['wolfcumjar','wolflgbt','wolfmarseyhead','wolfnoir','wolfsherifssmoking','wolftrans','wolfvaporwave','wolfangry','wolfbrains','wolfcry','wolfdead','wolfdevilish','wolffacepalm','wolfhappy','wolfidea','wolfkoala','wolflaugh','wolflove','wolfmeditate','wolfphone','wolfrainbow','wolfroses','wolfsad','wolfsfear','wolfsleep','wolftear','wolfthink','wolfthumbsup','wolfupsidedown','wolfvictory','wolfwave','wolfwink'],
		
				'misc': ['yotsubafish','yotsubalol','sigmatalking','zoroarkconfused','zoroarkhappy','zoroarkpout','zoroarksleepy','casanovanova','deuxwaifu','flairlessmong','hardislife','redditgigachad','rfybear','etika','sneed','retardedchildren','bruh','autism','doot','kylieface','queenyes','wholesomeseal','chadyescapy','gigachadglow','gigachadorthodox','gigachad','gigachad2','gigachad3']
			}

			ruqq = document.getElementById('EMOJIS_ruqqie')
			if (ruqq)
				emojis['ruqqie'] = ['ruqqiecowboy','ruqqielove','ruqqiepensive','ruqqiesip','ruqqiesmile','ruqqieupvote','ruqqiewizard']
			
			loadEmojis(form);
		}
		xhr.send(f);
	}
	else {
		fav.setAttribute('data-form-destination', form)

		const commentBox = document.getElementById(form)
		commentBox.setAttribute('data-curr-pos', commentBox.selectionStart);
	
		if (fav.innerHTML == "")
		{
			let str = ""
			const favorite_emojis = JSON.parse(localStorage.getItem("favorite_emojis"))
			if (favorite_emojis)
			{
				const sortable = Object.fromEntries(
					Object.entries(favorite_emojis).sort(([,a],[,b]) => b-a)
				);
						
				for (const emoji of Object.keys(sortable).slice(0, 25))
					str += `<button class="btn m-1 px-0 emoji2" onclick="getEmoji('${emoji}')" data-bs-toggle="tooltip" title=":${emoji}:" delay:="0"><img loading="lazy" width=50 src="/static/assets/images/emojis/${emoji}.webp" alt="${emoji}-emoji"></button>`
			
				fav.innerHTML = str
			}
		}
		if (search_bar.value == "") {
			search_container.innerHTML = ""
			document.getElementById("tab-content").classList.remove("d-none");
			if (document.getElementById("EMOJIS_marsey").innerHTML == "")
			{
				for (const [k, v] of Object.entries(emojis)) {
					let container = document.getElementById(`EMOJIS_${k}`)
					let str = ''
					if (k == 'marsey')
						{
							for (const e of v) {
								let k = e.toLowerCase().split(" : ")[0];
								str += `<button class="btn m-1 px-0 emoji2" onclick="getEmoji('${k}')" style="background: None!important; width:60px; overflow: hidden; border: none;" data-bs-toggle="tooltip" title=":${k}:" delay:="0"><img loading="lazy" width=50 src="/static/assets/images/emojis/${k}.webp" alt="${k}-emoji"></button>`;
							}
						}
					else {
						for (const e of v) {
							str += `<button class="btn m-1 px-0 emoji2" onclick="getEmoji('${e}')" style="background: None!important; width:60px; overflow: hidden; border: none;" data-bs-toggle="tooltip" title=":${e}:" delay:="0"><img loading="lazy" width=50 src="/static/assets/images/emojis/${e}.webp" alt="${e}-emoji"></button>`;
						}
					}
	
					container.innerHTML = str
				}
			}
		}
		else {
			let str = ''
			for (const [key, value] of Object.entries(emojis)) {
				if (key == "marsey")
				{
					for (const e of value) {
						let arr = e.toLowerCase().split(" : ");
						let k = arr[0];
						let v = arr[1];
						if (str.includes(`'${k}'`)) continue;
						if (k.match(search_bar.value.toLowerCase()) || search_bar.value.toLowerCase().match(k) || v.match(search_bar.value.toLowerCase())) {
							str += `<button class="btn m-1 px-0 emoji2" onclick="getEmoji('${k}')" data-bs-toggle="tooltip" title=":${k}:" delay:="0"><img loading="lazy" width=50 src="/static/assets/images/emojis/${k}.webp" alt="${k}-emoji"></button>`;
						}
					}
				}
				else
				{
					for (const e of value) {
						if (e.match(search_bar.value.toLowerCase()) || search_bar.value.toLowerCase().match(e)) {
							str += `<button class="btn m-1 px-0 emoji2" onclick="getEmoji('${e}')" style="background: None!important; width:60px; overflow: hidden; border: none;" data-bs-toggle="tooltip" title=":${e}:" delay:="0"><img loading="lazy" width=50 src="/static/assets/images/emojis/${e}.webp" alt="${e}-emoji"></button>`;
						}
					}
				}
			}
			document.getElementById("tab-content").classList.add("d-none");
			search_container.innerHTML = str
		}
		search_bar.oninput = function () {
			loadEmojis(form);
		};		
	}
}




function getEmoji(searchTerm) {
	const form = fav.getAttribute('data-form-destination')
	const commentBox = document.getElementById(form)
	const old = commentBox.value;
	const curPos = parseInt(commentBox.getAttribute('data-curr-pos'));

	const firstHalf = old.slice(0, curPos)
	const lastHalf = old.slice(curPos)

	let emoji = ':' + searchTerm + ':'
	const previousChar = firstHalf.slice(-1)
	if (firstHalf.length > 0 && previousChar !== " " && previousChar !== "\n") {
		emoji = " " + emoji
	}
	if (lastHalf.length > 0 && lastHalf[0] !== " ") {
		emoji = emoji + " "
	}

	commentBox.value = firstHalf + emoji + lastHalf;

	const newPos = curPos + emoji.length

	commentBox.setAttribute('data-curr-pos', newPos.toString());

	commentBox.dispatchEvent(new Event('input'));

	const favorite_emojis = JSON.parse(localStorage.getItem("favorite_emojis")) || {}
	if (favorite_emojis[searchTerm]) favorite_emojis[searchTerm] += 1
	else favorite_emojis[searchTerm] = 1
	localStorage.setItem("favorite_emojis", JSON.stringify(favorite_emojis))	
}