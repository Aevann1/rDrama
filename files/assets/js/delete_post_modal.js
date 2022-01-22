function delete_postModal(id) {

    function delete_post(){	

        this.innerHTML='Deleting post';	
        this.disabled = true; 

        var url = '/delete_post/' + id
        const xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader('xhr', 'xhr');
        var form = new FormData()
        form.append("formkey", formkey());
        xhr.onload = function() {location.reload(true);};
        xhr.send(form);
    }

    document.getElementById("deletePostButton-mobile").onclick = delete_post;

    document.getElementById("deletePostButton").onclick =  delete_post;

};