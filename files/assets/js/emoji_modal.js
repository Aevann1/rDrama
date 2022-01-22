let marsey_list, EMOJIS_STRINGS;
const xhr = new XMLHttpRequest();
xhr.open("GET", '/marsey_list', true);
xhr.setRequestHeader('xhr', 'xhr');
var form = new FormData()
xhr.onload = function() {
	marsey_list = JSON.parse(xhr.response)
	EMOJIS_STRINGS = [
		{
			type:'marsey',
			emojis: marsey_list
		},
		{
			type:'platy',
			emojis: ['plarsy','platyabused','platyblizzard','platyboxer','platydevil','platyfear','platygirlmagic','platygolong','platyhaes','platyking','platylove','platyneet','platyold','platypatience','platypopcorn','platyrich','platysarcasm','platysilly','platysleeping','platythink','platytired','platytuxedomask','platyblush','platybruh','platycaveman','platycheer','platydown','platyeyes','platyheart','platylol','platymicdrop','platynooo','platysalute','platyseethe','platythumbsup','platywave']
		},
		{
			type: 'tay',
			emojis: ['taylove','tayaaa','tayadmire','taycat','taycelebrate','taychefkiss','taychristmas','tayclap','taycold','taycrown','tayflex','tayflirt','taygrimacing','tayhappy','tayheart','tayhmm','tayhuh','tayhyperdab','tayjammin','taylaugh','taymindblown','tayno','taynod','taypeace','taypray','tayrun','tayscrunch','tayshake','tayshrug','taysilly','tayslide','taysmart','taystop','taytantrum','taytea','taythink','tayvibin','taywhat','taywine','taywine2','taywink','tayyes']
		},
		{
			type: 'classic',
			emojis: ['idhitit','2thumbsup','aliendj','ambulance','angry','angrywhip','argue','aroused','ashamed','badass','banana','band','banghead','batman','bigeyes','bite','blind','blowkiss','blush','bong','bounce','bow','breakheart','bs','cartwheel','cat','celebrate','chainsaw','cheers','clap','cold','confused','crazyeyes','cry','cthulhu','cute','laughing','daydream','ddr','deadpool','devilsmile','diddle','die','distress','disturbing','dizzy','domo','doughboy','drink','drool','dudeweedlmao','edward','electro','elephant','embarrassed','emo','emo2','evil','evilclown','evilgrin','facepalm','fap','flamethrower','flipbird','flirt','frown','gasp','glomp','go','gooby','grr','gtfo','guitar','haha','handshake','happydance','headbang','heart','heartbeat','hearts','highfive','hmm','hmph','holdhands','horny','hug','hugging','hugs','hump','humpbed','hysterical','ily','inlove','jason','jawdrop','jedi','jester','kaboom','kick','kiss','kitty','laughchair','lick','link','lol','lolbeat','loving','makeout','medal','megaman','megamanguitar','meow','metime','mooning','mummy','na','nauseous','nervous','ninja','nod','nono','omg','onfire','ooo','orly','tongueout','paddle','panda','pandabutt','paranoid','party','pat','peek','pikachu','pimp','plzdie','poke','popcorn','pout','probe','puke','punch','quote','raccoon','roar','rofl','roflmao','rolleyes','sad','sadeyes','sadhug','samurai','sarcasm','scoot','scream','shmoopy','shrug','skull','slap','slapfight','sleepy','smackfish','smackhead','smh','smile','smoke','sonic','spank','sparta','sperm','spiderman','stab','star','stare','stfu','suicide','surprisehug','suspicious','sweat','swordfight','taco','talk2hand','tantrum','teehee','thinking','threesome','throw','throwaway','tickle','typing','uhuh','vampbat','viking','violin','vulgar','wah','wat','whip','whipping','wink','witch','wizard','woah','worm','woo','work','worship','wow','xd','yay','zzz']
		},
		{
			type: 'rage',
			emojis: ['trolldespair','clueless','troll','bitchplease','spit','challengeaccepted','contentiouscereal','cryingatcuteness','derp','derpcornsyrup','derpcrying','derpcute','derpdumb','derpeuphoria','derpinahd','derpinapokerface','derpinasnickering','derpprocessing','derprealization','derpsnickering','derptalking','derpthinking','derpthumbsup','derpunimpressed','derpwhy','donotwant','epicfacefeatures','fancywithwine','fffffffuuuuuuuuuuuu','flipthetable','foreveralone','foreveralonehappy','hewillnever','idontknow','interuptedreading','iseewhatyoudidthere','killherkillher','ledesire','leexcited','legenius','lelolidk','lemiddlefinger','lemindblown','leokay','lepanicrunning','lepokerface','lepokerface2','lerageface','leseriousface','likeaboss','lolface','longwhiskers','manymiddlefingers','megusta','motherfucker','motherofgod','mysides','ohgodwhy','pervertedspiderman','picard','ragestrangle','rukiddingme','tfwyougettrolled','trollolol','truestorybro','xallthey','yuno']
		},
		{
			type: 'wojak',
			emojis: ['sciencejak','soyjakanimeglasses','soymad','boomerportrait','soycry','punchjak','seethejak','chadyes','chadno','abusivewife','ancap','bardfinn','bloomer','boomer','boomermonster','brainletbush','brainletcaved','brainletchair','brainletchest','brainletmaga','brainletpit','chad','chadarab','chadasian','chadblack','chadjesus','chadjew','chadjihadi','chadlatino','chadlibleft','chadnordic','chadsikh','chadusa','coomer','doomer','doomerfront','doomergirl','ethot','fatbrain','fatpriest','femboy','gogetter','grug','monke','nazijak','npc','npcfront','npcmaga','psychojak','ragejak','ragemask','ramonajak','soyjackwow','soyjak','soyjakfront','soyjakhipster','soyjakmaga','soyjakyell','tomboy','zoomer','zoomersoy']
		},
		{
			type: 'flags',
			emojis: ['niger','lgbt','saudi','animesexual','blacknation','blm','blueline','dreamgender','fatpride','incelpride','israel','kazakhstan','landlordlove','scalperpride','superstraight','trans','translord','transracial','usa']
		},
		{
			type: 'wolf',
			emojis: ['wolfangry','wolfbrains','wolfcry','wolfdead','wolfdevilish','wolffacepalm','wolfhappy','wolfidea','wolfkoala','wolflaugh','wolflove','wolfmeditate','wolfphone','wolfrainbow','wolfroses','wolfsad','wolfsfear','wolfsleep','wolftear','wolfthink','wolfthumbsup','wolfupsidedown','wolfvictory','wolfwave','wolfwink']
		},
		{
			type: 'misc',
			emojis: ['etika','sneed','retardedchildren','bruh','autism','doot','kylieface','queenyes','wholesomeseal','chadyescapy','gigachadglow','gigachadorthodox','gigachad','gigachad2','gigachad3']
		},
	]
};
xhr.send(form);

var commentFormID;

function commentForm(form) {
	commentFormID = form;
};

function getEmoji(searchTerm) {
	const form = document.getElementById('EMOJIS_favorite').getAttribute('data-form-destination')
	const commentBox = document.getElementById(form);
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

	if (typeof checkForRequired === "function") checkForRequired();

	const favorite_emojis = JSON.parse(localStorage.getItem("favorite_emojis")) || {}
	if (favorite_emojis[searchTerm]) favorite_emojis[searchTerm] += 1
	else favorite_emojis[searchTerm] = 1
	localStorage.setItem("favorite_emojis", JSON.stringify(favorite_emojis))	
}

function loadEmojis(form) {

	let search_bar = document.getElementById("emoji_search");
	let search_container = document.getElementById('emoji-tab-search')

	const fav = document.getElementById('EMOJIS_favorite')
	fav.setAttribute('data-form-destination', form)

	const commentBox = document.getElementById(form);
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

		const marseys = document.getElementById("EMOJIS_marsey")
		if (marseys.innerHTML == "")
		{
			for (let i = 0; i < EMOJIS_STRINGS.length; i++) {
				let type = EMOJIS_STRINGS[i].type
				let container = document.getElementById(`EMOJIS_${type}`)
				let str = ''
				let arr = EMOJIS_STRINGS[i].emojis
				if (i == 0)
					{
						for (const [key, value] of Object.entries(arr)) {
							str += `<button class="btn m-1 px-0 emoji2" onclick="getEmoji('${key}')" style="background: None!important; width:60px; overflow: hidden; border: none;" data-bs-toggle="tooltip" title=":${key}:" delay:="0"><img loading="lazy" width=50 src="/static/assets/images/emojis/${key}.webp" alt="${key}-emoji"></button>`;
						}
					}
				else {
					for (let j = 0; j < arr.length; j++) {
						str += `<button class="btn m-1 px-0 emoji2" onclick="getEmoji('${arr[j]}')" style="background: None!important; width:60px; overflow: hidden; border: none;" data-bs-toggle="tooltip" title=":${arr[j]}:" delay:="0"><img loading="lazy" width=50 src="/static/assets/images/emojis/${arr[j]}.webp" alt="${arr[j]}-emoji"></button>`;
					}
				}

				container.innerHTML = str
				search_container.innerHTML = ""
			}
		}
	} else {
		let str = ''
		for (let i = 0; i < EMOJIS_STRINGS.length; i++) {
			let arr = EMOJIS_STRINGS[i].emojis

			let container = document.getElementById(`EMOJIS_${EMOJIS_STRINGS[i].type}`)
			for (let j = 0; j < arr.length; j++) {
				if (arr[j].match(search_bar.value.toLowerCase()) || search_bar.value.toLowerCase().match(arr[j])) {
					str += `<button class="btn m-1 px-0 emoji2" onclick="getEmoji('${arr[j]}')" style="background: None!important; width:60px; overflow: hidden; border: none;" data-bs-toggle="tooltip" title=":${arr[j]}:" delay:="0"><img loading="lazy" width=50 src="/static/assets/images/emojis/${arr[j]}.webp" alt="${arr[j]}-emoji"></button>`;
				}
			}

			if (i == 0)
			{
				let arr2 = EMOJIS_STRINGS[i].emojis;
				for (const [key, value] of Object.entries(arr2)) {
					if (str.includes(`'${key}'`)) continue;
					let realvalue = Object.values(value)
					realvalue = realvalue[0] + realvalue[1]
					if (key.match(search_bar.value.toLowerCase()) || search_bar.value.toLowerCase().match(key) || realvalue.match(search_bar.value.toLowerCase())) {
						str += `<button class="btn m-1 px-0 emoji2" onclick="getEmoji('${key}')" data-bs-toggle="tooltip" title=":${key}:" delay:="0"><img loading="lazy" width=50 src="/static/assets/images/emojis/${key}.webp" alt="${key}-emoji"></button>`;
					}
				}
				container.innerHTML = ""
			}
		}
		search_container.innerHTML = str
	}
	search_bar.oninput = function () {
		loadEmojis(form);
	};
}