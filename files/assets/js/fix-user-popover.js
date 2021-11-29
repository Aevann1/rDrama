function eventasdf(value){
  var content_id = value.getAttributeNode("data-content-id").value;
  value.addEventListener("click", function(){jhkj(content_id)});
}

function checkIfBussy(){
  if (document.getElementById("bussy") != null){
    document.body.removeChild(document.getElementById("bussy"));
  }
}

function dfgh(e){
  active = document.activeElement;
  if (active.getAttributeNode("class") == null || active.getAttributeNode("class").nodeValue != "user-name text-decoration-none"){
    checkIfBussy();
  }
}

function jhkj(value){
  checkIfBussy();
  var popover_shit = document.getElementsByClassName("popover")[0];
  var uiop = document.createElement("DIV");
  
  uiop.innerHTML = popover_shit.outerHTML;
  uiop.id = "bussy";
  
  document.body.appendChild(uiop);
  document.body.removeChild(popover_shit);
}

var usernames = document.querySelectorAll("a.user-name");
usernames.forEach(eventasdf);

document.addEventListener("click", function(e){dfgh(e)});
