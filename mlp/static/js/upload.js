function getUUID(){
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
        return v.toString(16);
    });
}

// init the resumable file object
var r = new Resumable({
    target: "/files/store/",
    testChunks: false,
    maxChunkRetries: 3,
    chunkRetryInterval: 1000,
    generateUniqueIdentifier: getUUID,
    chunkSize: CHUNK_SIZE,
    query: {"main_file_slug": window.location.toString().replace(/\/$/, '').split("/").pop()}
});

// update the progress bar
r.on('progress', function(){
    var percent = Math.ceil(this.progress()*100) + "%"
    $('#progress-bar').css('width', percent);
    $('#progress-bar').text(percent)
});

// when a new file is added, list it in the dropbox area
r.on('fileAdded', listFiles)

// if there is a problem uploading a file, we just quit and submit the form
// with the error listed
r.on('fileError', function(file, message){
    console.log(message)
    $('#error-message').val(message)
    $('#form').submit();
    r.cancel();
})

r.on('complete', function(){
    // we delay this a bit so the progress bar is updated to 100%
    setTimeout(function(){
        $('#form').submit();
    }, 500);
})

function listFiles(){
    var html = ["<ul>"]
    for(var i = 0; i < r.files.length; i++){
        html.push("<li><span data-index='" + i + "' class='remove-file glyphicon glyphicon-remove'></span>" + r.files[i].fileName + "</li>")
    }
    html.push("</ul>")
    $('#dropbox').html(html.join(""))
}

$(document).ready(function(){
    // init these DOM objects for the file upload
    r.assignBrowse(document.getElementById("file"))
    r.assignDrop(document.getElementById("dropbox"))

    // start the upload process
    $('#submit').on("click", function(e){
        var agree = $('#agree').prop("checked")
        if(!agree){
            alert("Please check the box to indicate you have the permission to upload this video");
        } else if(r.files.length == 0){
            alert("Please add some files to upload!")
        } else {
            r.upload();
            $(this).hide();
            $(".progress").show();
        }
    });

    $('#dropbox').on("click", function(e){
        $('#file').click();
    })

    $('#dropbox').on('click', '.remove-file', function(e){
        e.stopPropagation();
        var index = parseInt($(this).data("index"))
        r.removeFile(r.files[index])
        listFiles();
    });
});

