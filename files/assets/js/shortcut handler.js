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

Copyright (C) 2022 Dr Steven Transmisia, anti-evil engineer
*/
"use strict";

/**
 * shortcut handler for CTRL + ENTER; if a text area of class 'comment-box' is active
 * the we submit the new post online.
 * 
 * @param {KeyboardEvent} e
 */
document.addEventListener('keydown', (e) => {
	if(!(e.ctrlKey && e.key == "Enter"))
		return;
	
	/** @type {HTMLTextAreaElement} */
	const targetDOM = document.activeElement;
	if(!(targetDOM instanceof HTMLTextAreaElement) || !targetDOM.classList.contains("comment-box"))
		return;
	
	/** @type {HTMLFormElement} */
	const formDOM = targetDOM.parentElement;
	if(!(formDOM instanceof HTMLFormElement))
		throw new TypeError("the text area should be child of a FORM. Contact the head custodian immediately.");

	const submitButtonDOMs = formDOM.getElementsByClassName("btn-primary");
	if(submitButtonDOMs.length === 0)
		throw new TypeError("I am unable to find the submit button :(. Contact the head custodian immediately.")
	
	// go!
	submitButtonDOMs[0].click();
});