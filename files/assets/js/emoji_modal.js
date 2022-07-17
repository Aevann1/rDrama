/*
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2022 Dr Steven Transmisia, anti-evil engineer,
              2022 Nekobit, king autist
*/

// Status
let emojiEngineStarted = false;

// DOM stuff
const classesSelectorDOM = document.getElementById("emoji-modal-tabs");
const emojiButtonTemplateDOM = document.getElementById("emoji-button-template");
const emojiResultsDOM = document.getElementById("tab-content");

/** @type {HTMLInputElement[]} */
const emojiSelectSuffixDOMs = document.getElementsByClassName("emoji-suffix");
/** @type {HTMLInputElement[]} */
const emojiSelectPostfixDOMs= document.getElementsByClassName("emoji-postfix");

const emojiNotFoundDOM = document.getElementById("no-emojis-found");
const emojiWorkingDOM = document.getElementById("emojis-work");
const emojiNewUserDOM = document.getElementById("emoji-new-user");

/** @type {HTMLInputElement} */
const emojiSearchBarDOM = document.getElementById('emoji_search');

/** @type {HTMLInputElement} */
let emojiInputTargetDOM = undefined;

// Emojis usage stats. I don't really like this format but I'll keep it for backward comp.
const favorite_emojis = JSON.parse(localStorage.getItem("favorite_emojis")) || {};
const emojiFirstBoot = Object.keys(favorite_emojis).length === 0;

emojiNewUserDOM.hidden = !emojiFirstBoot;

/** Associative array of all the emojis' DOM */
let emojiDOMs = {};

const EMOIJ_SEARCH_ENGINE_MIN_INTERVAL = 350;
let emojiSearcher = {
	working: false,
	queries: [],
	
	addQuery: function(query)
	{
		this.queries.push(query);
		if(!this.working)
			this.work();
	},
	
	work: async function work() {
		this.working = true;

		while(this.queries.length > 0)
		{
			const startTime = Date.now();

			// Get last input
			const query = this.queries[this.queries.length - 1].toLowerCase();
			this.queries = [];

			// To improve perf we avoid showing all emojis at the same time.
			if(query === "")
			{
				await classesSelectorDOM.children[0].children[0].click();
				classesSelectorDOM.children[0].children[0].classList.add("active");
				continue;
			}
			// Hide welcome message
			emojiNewUserDOM.hidden = true;

			// Search
			const resultSet = emojisSearchDictionary.completeSearch(query);

			// update stuff 
			for(const [emojiName, emojiDOM] of Object.entries(emojiDOMs))
				emojiDOM.hidden = !resultSet.has(emojiName);

			emojiNotFoundDOM.hidden = resultSet.size !== 0;

			let sleepTime = EMOIJ_SEARCH_ENGINE_MIN_INTERVAL - (Date.now() - startTime);
			if(sleepTime > 0)
				await new Promise(r => setTimeout(r, sleepTime));
		}

		this.working = false;
	}
};

// tags dictionary. KEEP IT SORT
class EmoijsDictNode
{
	constructor(tag, name) {
		this.tag = tag;
		this.emojiNames = [name];
	}
}
const emojisSearchDictionary = {
	dict: [],

	updateTag: function(tag, emojiName) {
		if(tag === undefined || emojiName === undefined)
			return;

		let low = 0;
		let high = this.dict.length;

		while (low < high) {
			let mid = (low + high) >>> 1;
			if (this.dict[mid].tag < tag)
				low = mid + 1;
			else
				high = mid;
		}

		let target = low;
		if(this.dict[target] !== undefined && this.dict[target].tag === tag)
			this.dict[target].emojiNames.push(emojiName);
		else
			this.dict.splice(target ,0,new EmoijsDictNode(tag, emojiName));
	},

	/**
	 * We find the name of each emojis that has a tag that starts with query.
	 * 
	 * Basically I run a binary search to find a tag that starts with a query, then I look left and right
	 * for other tags tat start with the query. As the array is ordered this algo is sound.
	 * @param {String} tag
	 * @returns {Set}
	 */
	searchFor: function(query) {
		if(this.dict.length === 0)
			return new Set();

		const result = new Set();

		let low = 0;
		let high = this.dict.length;

		while (low < high) {
			let mid = (low + high) >>> 1;
			if (this.dict[mid].tag < query)
				low = mid + 1;
			else
				high = mid;
		}

		let target = low;
		for(let i = target; i >= 0 && this.dict[i].tag.startsWith(query); i--)
			for(let j = 0; j < this.dict[i].emojiNames.length; j++)
				result.add(this.dict[i].emojiNames[j]);
		
		for(let i = target + 1; i < this.dict.length && this.dict[i].tag.startsWith(query); i++)
			for(let j = 0; j < this.dict[i].emojiNames.length; j++)
				result.add(this.dict[i].emojiNames[j]);
		
		return result;
	},

	/**
	 * We also check for substrings! (sigh)
	 * @param {String} tag
	 * @returns {Set}
	 */
	completeSearch: function(query) {
		const result = new Set();

		for(let i = 0; i < this.dict.length; i++)
			if(this.dict[i].tag.includes(query))
				for(let j = 0; j < this.dict[i].emojiNames.length; j++)
					result.add(this.dict[i].emojiNames[j])
		
		return result;
	}
};

// get public emojis list
const emojiRequest = new XMLHttpRequest();
emojiRequest.open("GET", '/marsey_list.json');
emojiRequest.onload = async (e) => {
	let emojis  = JSON.parse(emojiRequest.response);
	if(! (emojis instanceof Array ))
		throw new TypeError("[EMOIJ DIALOG] rDrama's server should have sent a JSON-coded Array!");

	let classes = new Set();
	const bussyDOM = document.createElement("div");
	let startTime = Date.now();

	for(let i = 0; i < emojis.length; i++)
	{
		const emoji = emojis[i];

		emojisSearchDictionary.updateTag(emoji.name, emoji.name);
		if(emoji.author !== undefined && emoji.author !== null)
			emojisSearchDictionary.updateTag(emoji.author.toLowerCase(), emoji.name);

		if(emoji.tags instanceof Array)
			for(let i = 0; i < emoji.tags.length; i++)
				emojisSearchDictionary.updateTag(emoji.tags[i], emoji.name);

		classes.add(emoji.class);

		// Create emoji DOM
		const emojiDOM = document.importNode(emojiButtonTemplateDOM.content, true).children[0];

		emojiDOM.title = emoji.name
		if(emoji.author !== undefined && emoji.author !== null)
			emojiDOM.title += "\nauthor\t" + emoji.author
		if(emoji.count !== undefined)
			emojiDOM.title += "\nused\t" + emoji.count;
		emojiDOM.dataset.className = emoji.class;
		emojiDOM.dataset.emojiName = emoji.name;
		emojiDOM.onclick = emojiAddToInput;
		emojiDOM.hidden = true; 

		const emojiIMGDOM = emojiDOM.children[0];
		emojiIMGDOM.src = "/e/" + emoji.name + ".webp";
		emojiIMGDOM.alt = emoji.name;
		/** Disableing lazy loading seems to reduce cpu usage somehow (?)
		  * idk it is difficult to benchmark */
		emojiIMGDOM.loading = "lazy";

		// Save reference
		emojiDOMs[emoji.name] = emojiDOM;

		// Add to the document!
		bussyDOM.appendChild(emojiDOM);
	}

	// Create header
	for(let className of classes)
	{
		let classSelectorDOM = document.createElement("li");
		classSelectorDOM.classList.add("nav-item");

		let classSelectorLinkDOM = document.createElement("a");
		classSelectorLinkDOM.href = "#";
		classSelectorLinkDOM.classList.add("nav-link", "emojitab");
		classSelectorLinkDOM.dataset.bsToggle = "tab";
		classSelectorLinkDOM.dataset.className = className;
		classSelectorLinkDOM.innerText = className;
		classSelectorLinkDOM.onclick = switchEmojiTab;

		classSelectorDOM.appendChild(classSelectorLinkDOM);
		classesSelectorDOM.appendChild(classSelectorDOM);
	}

	// Show favorite for start.
	await classesSelectorDOM.children[0].children[0].click();
	
	// Send it to the render machine! 
	emojiResultsDOM.appendChild(bussyDOM);

	emojiResultsDOM.hidden = false;
	emojiWorkingDOM.hidden = true;
	emojiSearchBarDOM.disabled = false;
}

/**
 * 
 * @param {Event} e
 */
function switchEmojiTab(e)
{
	const className = e.currentTarget.dataset.className;

	emojiSearchBarDOM.value = "";
	emojiSearchBarDOM.focus();
	emojiNotFoundDOM.hidden = true;

	// Special case: favorites
	if(className === "favorite")
	{
		if(emojiFirstBoot)
			emojiNewUserDOM.hidden = false;

		for(const emojiDOM of Object.values(emojiDOMs))
			emojiDOM.hidden = true;

		// copied from the old one
		// For new users we show anton-d's emojis
		const favs = emojiFirstBoot ? emojisSearchDictionary.searchFor("anton-d") : Object.keys(Object.fromEntries(
			Object.entries(favorite_emojis).sort(([,a],[,b]) => b-a)
		)).slice(0, 25);
		
		for (const emoji of favs)
			if(emojiDOMs[emoji] instanceof HTMLElement)
				emojiDOMs[emoji].hidden = false;
		
		return;
	}
	
	emojiNewUserDOM.hidden = true;

	for(const emojiDOM of Object.values(emojiDOMs))
		emojiDOM.hidden = emojiDOM.dataset.className !== className;
}

async function start_search() {
	emojiSearcher.addQuery(emojiSearchBarDOM.value);

	// Remove any selected tab, now it is meaningless
	for(let i = 0; i < classesSelectorDOM.children.length; i++)
		classesSelectorDOM.children[i].children[0].classList.remove("active");
}

/**
 * Add the selected emoji to the targeted text area
 * @param {Event} event 
 */
function emojiAddToInput(event)
{
	// This should not happen if used properly but whatever
	if(!(emojiInputTargetDOM instanceof HTMLTextAreaElement) && !(emojiInputTargetDOM instanceof HTMLInputElement))
		return;
	
	// If a range is selected, setRangeText will overwrite it. Maybe better to ask the r-slured if he really wants this behaviour
	if(emojiInputTargetDOM.selectionStart !== emojiInputTargetDOM.selectionEnd && !confirm("You've selected a range of text.\nThe emoji will overwrite it! Do you want to continue?"))
		return;
		
	let strToInsert =  event.currentTarget.dataset.emojiName;

	for(let i = 0; i < emojiSelectPostfixDOMs.length; i++)
		if(emojiSelectPostfixDOMs[i].checked)
			strToInsert = strToInsert + emojiSelectPostfixDOMs[i].value;
	
	for(let i = 0; i < emojiSelectSuffixDOMs.length; i++)
		if(emojiSelectSuffixDOMs[i].checked)
			strToInsert = emojiSelectSuffixDOMs[i].value + strToInsert;

	strToInsert = ":" + strToInsert + ":"
	const newPos =  emojiInputTargetDOM.selectionStart + strToInsert.length;
	
	emojiInputTargetDOM.setRangeText(strToInsert);
	
	// Sir, come out and drink your Chromium complaint web
	// I HATE CHROME. I HATE CHROME
	if(window.chrome !== undefined)
		setTimeout(function(){
			console.warn("Chrome detected, r-slured mode enabled.");
		
			// AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
			// JUST WORK STUPID CHROME PIECE OF SHIT
			emojiInputTargetDOM.focus();
			for(let i = 0; i < 2; i++)
				emojiInputTargetDOM.setSelectionRange(newPos, newPos);
			
			emojiInputTargetDOM.focus();
			for(let i = 0; i < 2; i++)
				emojiInputTargetDOM.setSelectionRange(newPos, newPos);
		}, 1);
	else
		emojiInputTargetDOM.setSelectionRange(newPos, newPos);
	
	// kick-start the preview
	emojiInputTargetDOM.dispatchEvent(new Event('input'));

	// Update favs. from old code
	if (favorite_emojis[event.currentTarget.dataset.emojiName])
		favorite_emojis[event.currentTarget.dataset.emojiName] += 1;
	else
		favorite_emojis[event.currentTarget.dataset.emojiName] = 1;
	localStorage.setItem("favorite_emojis", JSON.stringify(favorite_emojis));
}

(function() {
    const insertAt = (str, sub, pos) => `${str.slice(0, pos)}${sub}${str.slice(pos)}`;
    
    let emoji_typing_state = false;

    function update_ghost_div_textarea(text)
    {
        let ghostdiv = text.parentNode.querySelector(".ghostdiv");
        if (!ghostdiv) return;

        ghostdiv.innerText = text.value.substring(0, text.selectionStart);
        ghostdiv.innerHTML += "<span></span>";

        // Now lets get coordinates
        
        ghostdiv.style.display = "initial";
        let end = ghostdiv.querySelector("span");
        const carot_coords = end.getBoundingClientRect();
        const ghostdiv_coords = ghostdiv.getBoundingClientRect();
        ghostdiv.style.display = "none";
        return { pos: text.selectionStart, x: carot_coords.x, y: carot_coords.y - ghostdiv_coords.y };
    }

    // Used for anything where a user is typing, specifically for the emoji modal
    // Just leave it global, I don't care
    let speed_carot_modal = document.createElement("div");
    speed_carot_modal.id = "speed-carot-modal";
    speed_carot_modal.style.position = "absolute";
    speed_carot_modal.style.left = "0px";
    speed_carot_modal.style.top = "0px";
    speed_carot_modal.style.display = "none";
    document.body.appendChild(speed_carot_modal);

    let e

    let current_word = "";
    let emojo_index = 0;

    function curr_word_is_emoji()
    {
        return current_word && current_word.charAt(0) == ":" &&
            current_word.charAt(current_word.length-1) != ":";
    }

    function populate_speed_emoji_modal(results, textbox)
    {
        if (!results || results.size === 0)
        {
            speed_carot_modal.style.display = "none";
            return -1;
        }

        emojo_index = 0;
        speed_carot_modal.innerHTML = "";
        const MAXXX = 25;
        // Not sure why the results is a Set... but oh well
        let i = 0;
        for (let result of results)
        {
            if (i++ > MAXXX) return i;
            let emoji_option = document.createElement("div");
            emoji_option.className = "speed-modal-option emoji-option " + (i === 1 ? "selected" : "");
            emoji_option.tabIndex = 0;
            let emoji_option_img = document.createElement("img");
            emoji_option_img.className = "speed-modal-image emoji-option-image";
            // This is a bit 
            emoji_option_img.src = `/e/${result}.webp`;
            let emoji_option_text = document.createElement("span");
            emoji_option_text.title = result;
            emoji_option_text.innerText = result;

            emoji_option.onclick = (e) => {
                speed_carot_modal.style.display = "none";
                textbox.value = textbox.value.replace(new RegExp(current_word+"(?=\\s|$)", "g"), `:${result}:`)
            };
            // Pack
            emoji_option.appendChild(emoji_option_img);
            emoji_option.appendChild(emoji_option_text);
            speed_carot_modal.appendChild(emoji_option);
        }
        if (i === 0) speed_carot_modal.style.display = "none";
        else speed_carot_modal.style.display = "initial";
        return i;
    }

    function update_speed_emoji_modal(event)
    {
        const box_coords = update_ghost_div_textarea(event.target);

        let text = event.target.value;

        // Unused, but left incase anyone wants to use this more efficient method for emojos
        switch (event.data)
        {
            case ':':
            emoji_typing_state = true;
            break;
            case ' ':
            emoji_typing_state = false;
            break;
            default:
            break;
        }

        // Get current word at string, such as ":marse" or "word"
        let coords = text.indexOf(' ',box_coords.pos);
        current_word = /\S+$/.exec(text.slice(0, coords === -1 ? text.length : coords));
        if (current_word) current_word = current_word.toString();

        /* We could also check emoji_typing_state here, which is less accurate but more efficient. I've
         * kept it unless someone wants to provide an option to toggle it for performance */
        if (curr_word_is_emoji() && current_word != ":")
        {
            loadEmojis(null);
            let modal_pos = event.target.getBoundingClientRect();
            modal_pos.x += window.scrollX;
            modal_pos.y += window.scrollY;

            speed_carot_modal.style.display = "initial";
            speed_carot_modal.style.left = box_coords.x - 35 + "px";
            speed_carot_modal.style.top = modal_pos.y + box_coords.y + 14 + "px";
            
            // Do the search (and do something with it)
            populate_speed_emoji_modal(emojisSearchDictionary.searchFor(current_word.substr(1)), event.target);

        }
        else {
            speed_carot_modal.style.display = "none";
        }
    }

    function speed_carot_navigate(e)
    {
        let select_items = speed_carot_modal.querySelectorAll(".speed-modal-option");
        if (!select_items || !curr_word_is_emoji()) return false;
        // Up or down arrow or enter
        if (e.keyCode == 38 || e.keyCode == 40 || e.keyCode == 13)
        {
            if (emojo_index > select_items.length)
                emojo_index = select_items;
            
            select_items[emojo_index].classList.remove("selected");
            switch (e.keyCode)
            {
                case 38: // Up arrow
                if (emojo_index)
                    emojo_index--;
                break;
                
                case 40: // Down arrow
                if (emojo_index < select_items.length-1) emojo_index++;
                break;

                case 13:
                select_items[emojo_index].click();
                
                default:
                break;
            }

            select_items[emojo_index].classList.add("selected");
            e.preventDefault();
        }
    }

    // Let's get it running now
    let forms = document.querySelectorAll("textarea, .allow-emojis");
    forms.forEach(i => {
        let pseudo_div = document.createElement("div");
        pseudo_div.className = "ghostdiv";
        i.after(pseudo_div);
        i.addEventListener('input', update_speed_emoji_modal, false);
        i.addEventListener('keydown', speed_carot_navigate, false);
    });
})();


function loadEmojis(inputTargetIDName)
{
	if(!emojiEngineStarted)
	{
		emojiEngineStarted = true;
		emojiRequest.send();
	}

    if (inputTargetIDName)
	    emojiInputTargetDOM = document.getElementById(inputTargetIDName);
}

document.getElementById('emojiModal').addEventListener('shown.bs.modal', function () {
	emojiSearchBarDOM.focus();
});
