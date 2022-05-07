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

Copyright (C) 2022 Dr Steven Transmisia, anti-hate engineer
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

/** @type {HTMLInputElement} */
const emojiSearchBarDOM = document.getElementById('emoji_search');

/** @type {HTMLInputElement} */
let emojiInputTargetDOM = undefined;

// Emojis usage stats. I don't really like this format but I'll keep it for backward comp.
const favorite_emojis = JSON.parse(localStorage.getItem("favorite_emojis")) || {};

/** Associative array of all the emojis' DOM */
let emojiDOMs = {};

const EMOIJ_SEARCH_ENGINE_MIN_INTERVAL = 350;
class EmojiSearchEngine {
	constructor () {
		this.working = false;
		this.queries = [];
	}

	addQuery(query) {
		this.queries.push(query);
		if(!this.working)
			this.work();
		
	}

	async work() {
		this.working = true;

		while(this.queries.length > 0)
		{
			const startTime = Date.now();

			// Get last input
			const query = this.queries[this.queries.length - 1];
			this.queries = [];

			// To improve perf we avoid showing all emojis at the same time.
			if(query === "")
			{
				await classesSelectorDOM.children[0].children[0].click();
				classesSelectorDOM.children[0].children[0].classList.add("active");
				continue;
			}

			// Search
			const resultSet = emojisSearchDictionary.searchFor(query);

			// update stuff 
			for(const [emojiName, emojiDOM] of Object.entries(emojiDOMs))
				emojiDOM.hidden = !resultSet.has(emojiName);

			emojiNotFoundDOM.hidden = resultSet.size !== 0;

			console.log("Search time: " + (Date.now() - startTime) + "ms");
			let sleepTime = EMOIJ_SEARCH_ENGINE_MIN_INTERVAL - (Date.now() - startTime);
			if(sleepTime > 0)
				await new Promise(r => setTimeout(r, sleepTime));
		}

		this.working = false;
	}
}
let emojiSearcher = new EmojiSearchEngine();

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

		let result = new Set();

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
				result = result.add(this.dict[i].emojiNames[j]);
		
		for(let i = target + 1; i < this.dict.length && this.dict[i].tag.startsWith(query); i++)
			for(let j = 0; j < this.dict[i].emojiNames.length; j++)
				result = result.add(this.dict[i].emojiNames[j]);
		
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
		let emoji = emojis[i];

		emojisSearchDictionary.updateTag(emoji.name, emoji.name);
		if(emoji.author !== undefined)
			emojisSearchDictionary.updateTag(emoji.author.toLowerCase(), emoji.name);

		if(emoji.tags instanceof Array)
			for(let i = 0; i < emoji.tags.length; i++)
				emojisSearchDictionary.updateTag(emoji.tags[i], emoji.name);

		classes.add(emoji.class);

		// Create emoji DOM
		const emojiDOM = document.importNode(emojiButtonTemplateDOM.content, true).children[0];

		emojiDOM.title = emoji.name
		if(emoji.author !== undefined)
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
	const sortable = Object.fromEntries(
		Object.entries(favorite_emojis).sort(([,a],[,b]) => b-a)
	);
			
	for (const emoji of Object.keys(sortable).slice(0, 25))
		if(emojiDOMs[emoji] instanceof HTMLElement)
			emojiDOMs[emoji].hidden = false;
	
	// Send it to the render machine! 
	emojiResultsDOM.appendChild(bussyDOM);
	console.log("Ho impiegato " + (Date.now() - startTime) + " ms per generare il DOM delle emoji (bussy)");

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
	emojiNotFoundDOM.hidden = true;

	// Special case: favorites
	if(className === "favorite")
	{
		for(const emojiDOM of Object.values(emojiDOMs))
			emojiDOM.hidden = true;

		// copied from the old one
		const sortable = Object.fromEntries(
			Object.entries(favorite_emojis).sort(([,a],[,b]) => b-a)
		);
		
		for (const emoji of Object.keys(sortable).slice(0, 25))
			if(emojiDOMs[emoji] instanceof HTMLElement)
				emojiDOMs[emoji].hidden = false;
		
		return;
	}

	for(const emojiDOM of Object.values(emojiDOMs))
		emojiDOM.hidden = emojiDOM.dataset.className !== className;

}

emojiSearchBarDOM.oninput = async function(event) {
	emojiSearcher.addQuery(emojiSearchBarDOM.value.toLowerCase());

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

	strToInsert = " :" + strToInsert + ": "
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

function loadEmojis(inputTargetIDName)
{
	if(!emojiEngineStarted)
	{
		emojiEngineStarted = true;
		emojiRequest.send();
	}

	emojiInputTargetDOM = document.getElementById(inputTargetIDName);
}
