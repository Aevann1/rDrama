function viewmore(pid,sort,offset) {
    btn = document.getElementById("viewbtn");
    btn.disabled = true;
    btn.innerHTML = "Requesting...";
    var form = new FormData();
	form.append("formkey", formkey());
    const xhr = new XMLHttpRequest();
    xhr.open("post", `/viewmore/${pid}/${sort}/${offset}`);
    xhr.setRequestHeader('xhr', 'xhr');
    xhr.onload=function(){
        if (xhr.status==200) {
            document.getElementById(`viewmore-${offset}`).innerHTML = xhr.response.replace(/data-src/g, 'src').replace(/data-cfsrc/g, 'src').replace(/style="display:none;visibility:hidden;"/g, '');
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function(element){
                return new bootstrap.Tooltip(element);
            });
            popovertrigger()
            btn.disabled = false;
        }
    }
    xhr.send(form)
}