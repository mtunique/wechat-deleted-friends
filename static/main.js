var $loadingToast = $('#loadingToast');
$loadingToast.show();
setTimeout(function () {
    $loadingToast.hide();
}, 20000);


function getUUID() {
    $.get('uuid', function(data){
        $('#qr').attr("src", data);
        $loadingToast.hide();
    });
}

var $dialog = $('#dialog');

$dialog.find('.weui_btn_dialog').on('click', function () {
    $dialog.hide();
});

$('#submit').click(function () {
    $('#qr').hide();
    $('#loading').text('正在计算 稍等片刻');
    $loadingToast.show();
    $.get('submit', function (data) {
        $loadingToast.hide();
        if(data.length = 0) {
            $('#title').text('哎呦喂,没有好友把你删除')
        }
        $('#list').text(data);
        $dialog.show();
    })
});

getUUID();
