/**
 *
 * @param input: What to change
 * @description Turns "Foo" into ":marseyalphaf::marseyalphao::marseyalphao:".
 */
function marseyfy(input) {
  return input
    .split("")
    .map((letter) => `:marseyalpha${letter.toLowerCase()}:`)
    .join("");
}

/**
 * @description Replaces highlighted text with marsey alphabet images for convenience.
 */
let lastSelectionText = "",
  lastSelectionContainer = null;

function storeSelectionText() {
  try {
    const selection = window.getSelection();

    if (selection.rangeCount > 0) {
      lastSelectionText = selection.toString();
      lastSelectionContainer = getSelectionBoundaryElement();
    } else {
      lastSelectionText = "";
      lastSelectionContainer = null;
    }
  } catch (error) {
    console.error("Unable to store selection text.", error);
  }
}

document.addEventListener("selectionchange", storeSelectionText);

function marseyfyHighlightedText(event) {
  try {
    event.stopPropagation();

    if (lastSelectionText && lastSelectionContainer) {
      const textarea = lastSelectionContainer.querySelector("textarea");

      console.log(textarea, textarea.value, textarea.textContent);

      textarea.value = textarea.value.replace(
        lastSelectionText,
        marseyfy(lastSelectionText)
      );
    }
  } catch (error) {
    console.error("Unable to marseyfy.", error);
  }
}

/**
 * @link https://stackoverflow.com/questions/1335252/how-can-i-get-the-dom-element-which-contains-the-current-selection
 */
function getSelectionBoundaryElement(isStart) {
  var range, sel, container;
  if (document.selection) {
    range = document.selection.createRange();
    range.collapse(isStart);
    return range.parentElement();
  } else {
    sel = window.getSelection();
    if (sel.getRangeAt) {
      if (sel.rangeCount > 0) {
        range = sel.getRangeAt(0);
      }
    } else {
      // Old WebKit
      range = document.createRange();
      range.setStart(sel.anchorNode, sel.anchorOffset);
      range.setEnd(sel.focusNode, sel.focusOffset);

      // Handle the case when the selection was selected backwards (from the end to the start in the document)
      if (range.collapsed !== sel.isCollapsed) {
        range.setStart(sel.focusNode, sel.focusOffset);
        range.setEnd(sel.anchorNode, sel.anchorOffset);
      }
    }

    if (range) {
      container = range[isStart ? "startContainer" : "endContainer"];

      // Check if the container is a text node and return its parent if so
      return container.nodeType === 3 ? container.parentNode : container;
    }
  }
}
