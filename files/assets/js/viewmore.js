function viewmore(pid,sort,offset,ids) {
    btn = document.getElementById("viewbtn");
    btn.disabled = true;
    btn.innerHTML = "Requesting...";
    var form = new FormData();
    const xhr = new XMLHttpRequest();
    xhr.open("get", `/viewmore/${pid}/${sort}/${offset}?ids=${ids}`);
    xhr.setRequestHeader('xhr', 'xhr');
    xhr.onload=function(){
        if (xhr.status==200) {
            document.getElementById(`viewmore-${offset}`).innerHTML = xhr.response.replace(/data-src/g, 'src').replace(/data-cfsrc/g, 'src').replace(/style="display:none;visibility:hidden;"/g, '');
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function(element){
                return bootstrap.Tooltip.getOrCreateInstance(element);
            });
            popovertrigger()
            btn.disabled = false;
        }
    }
    xhr.send(form)
}