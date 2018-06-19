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
        $(".tool-buttons").show();

        $("#create-channel").click(function(){
            $(".container-input").hide();
            $(".message").text("");
            $(".create").show();
        });

        $("#leave-channel").click(function(){
            $(".container-input").hide();
            $(".message").text("");
            $(".leave").show();
        });

        $(".cancel").click(function(){
            $("input").val("");
            $(".message").text("");
            $(".container-input").hide();
        });
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

    function responseCreate(data){
        if (data["success"]) {
            $("input").val("");
            $(".message").text("The Chat Has Been Created").
            css("color", "green");
        }else{
            $("#message").text(data["error"]).
            css("color", "red");
        }

    };

    function responseLeave(data){
        if (data["success"]) {
            $("input").val("");
            $(".message").text("You have left the channel").
            css("color", "green");
        }else{
            $(".message").text(data["error"]).
            css("color", "red");
        }

    }


    var createGroup = runtime.handlerUrl(element, "create_group");

    $("#button-create").click(function(eventObject) {
        var groupName = $("#group-name-create").val();
        var description = $("#group-description").val();
        var topic = $("#group-topic").val();
        var data = {groupName, description, topic};
        $.ajax({
            type: "POST",
            url: createGroup,
            data: JSON.stringify(data),
            success: responseCreate
        });
    });

    var leaveGroup = runtime.handlerUrl(element, "leave_group");

    $("#button-leave").click(function(eventObject) {
        var groupName = $("#group-name-leave").val();
        var data = {groupName};
        $.ajax({
            type: "POST",
            url: leaveGroup,
            data: JSON.stringify(data),
            success: responseLeave
        });
    });

}
