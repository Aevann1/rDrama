function popoverEventListener(value){
  //get the id of the popover that will be created for this user
  var content_id = value.getAttributeNode("data-content-id").value;
  //add an event listener that will trigger the creation of a replacement popover when the username is clicked
  value.addEventListener("click", function(){createNewPopover(content_id)});
}

function checkIfPopover(){
  //check if a replacement popover already exists and remove it if so
  if (document.getElementById("popover-fix") != null){
    document.body.removeChild(document.getElementById("popover-fix"));
  }
}

function closePopover(e){
  //get the element that was clicked on
  active = document.activeElement;
  //if the element is not a username then check if a popover replacement already exists
  if (active.getAttributeNode("class") == null || active.getAttributeNode("class").nodeValue != "user-name text-decoration-none"){
    checkIfPopover();
  }
}

function createNewPopover(value){
  //check for an existing replacement popover and then copy the original popover node
  checkIfPopover();
  var popover_old = document.getElementsByClassName("popover")[0];
  var popover_new = document.createElement("DIV");
  
  //copy the contents of the original popover
  popover_new.innerHTML = popover_old.outerHTML;
  popover_new.id = "popover-fix";
  
  //append the replacement popover to the document and remove the original one
  document.body.appendChild(popover_new);
  document.body.removeChild(popover_old);
}

window.addEventListener('load', (e) => {
  //grab all of the usernames on the page and create event listeners for them 
  var usernames = document.querySelectorAll("a.user-name");
  usernames.forEach(popoverEventListener);

  //create an event listener to check if a clicked element is a username
  document.addEventListener("click", function(e){closePopover(e)});
});
