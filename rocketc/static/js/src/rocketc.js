/* Javascript for RocketChatXBlock. */
function RocketChatXBlock(runtime, element) {

    $(function ($) {
        /* Here's where you'd do things on page load. */
    });

    var setDefaultChannel = runtime.handlerUrl(element, "set_default_channel");

    if ( $("body").find(".chromeless")[0]){
        $("body").append($(".vert-mod"));
        $("#content").remove();
        $(".message-xblock").hide();
        $(".message-team").show();
    }

    $("#button", element).click(function(eventObject) {
        var channel = $("#name", element).val();
        var data = {channel};
        $.ajax({
            type: "POST",
            url: setDefaultChannel,
            data: JSON.stringify(data),
        });
    });
}
