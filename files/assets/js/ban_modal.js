function banModal(link, id, name) {
    document.getElementById("banModalTitle").innerHTML = `Ban @${name}`;
    document.getElementById("ban-modal-link").value = link;
    document.getElementById("banUserButton").innerHTML = `Ban @${name}`;

    document.getElementById("banUserButton").onclick = function() {
        let fd = new FormData(document.getElementById("banModalForm"));
        fd.append("formkey", formkey());

        const xhr = new XMLHttpRequest();
        xhr.open("POST", `/ban_user/${id}?form`, true);
        xhr.setRequestHeader('xhr', 'xhr');

        xhr.onload = function(){
            var myToast = new bootstrap.Toast(document.getElementById('toast-post-success'));
            myToast.show();
            document.getElementById('toast-post-success-text').innerHTML = `@${name} banned`;
        }

        xhr.send(fd);
    }
};