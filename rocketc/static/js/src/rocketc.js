/* Javascript for RocketChatXBlock. */
function RocketChatXBlock(runtime, element) {

    $(function ($) {
        /* Here's where you'd do things on page load. */
        $( document ).ajaxStop(function() {
            var beacon_rc = localStorage.getItem("beacon_rc");
            var beacon = $(".rocketc_block .embed-container").attr("data-beacon-rc");
            if (beacon_rc != null && beacon_rc != beacon && beacon != null) {
                var  logoutUser= runtime.handlerUrl(element, "logout_user");
                var data = {"key": beacon_rc};
                $.ajax({
                    type: "GET",
                    url: logoutUser,
                    data: {beacon_rc},
                });
                localStorage.setItem("beacon_rc", beacon);
            } else if (beacon != null) {
                localStorage.setItem("beacon_rc", beacon);
            }
        });
    });

    var setDefaultChannel = runtime.handlerUrl(element, "set_default_channel");
    var getGroups = runtime.handlerUrl(element, "get_list_of_groups");

    if ( $("body").find(".chromeless")[0] && !/Android|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent)){
        $("body").append($(".vert-mod"));
        $("#content").remove();
        $(".message-xblock").hide();
        $(".message-team").show();
        $("#tool-buttons").show();

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
        loadGroups();
    } else {
        $("#myframe").on("load", function() {
            if (!isScrolledIntoView($(".rocketc_block"))) {
                $("#myframe").hide();
            }
        });
        window.onscroll = function() {
          if (isScrolledIntoView($(".rocketc_block"))) {
            $("#myframe").show();
          }
        };
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
        loadGroups();
        if (data["success"]) {
            $("input").val("");
            $(".message").text("The Chat Has Been Created").
            css("color", "green");
        }else{
            $(".message").text(data["error"]).
            css("color", "red");
        }

    };

    function responseLeave(data){
        loadGroups();
        if (data["success"]) {
            $("input").val("");
            $(".message").text("You have left the channel").
            css("color", "green");
            $("#select-channel").val($("#tool-buttons").attr("data-default"));
            $("#select-channel").change();
        }else{
            $(".message").text(data["error"]).
            css("color", "red");
        }

    };

    var createGroup = runtime.handlerUrl(element, "create_group");

    $("#button-create").click(function(eventObject) {
        var groupName = $("#group-name-create").val();
        var description = $("#group-description").val();
        var topic = $("#group-topic").val();
        var teamGroup = true;
        var data = {groupName, description, topic, teamGroup};
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

    function responseGetGroups(data){
        var channel = $("#select-channel").val();
        $("#select-channel").empty();
        $("#group-names").empty();
        for (var i in data){
            var item =  $("<option value="+data[i]+">"+data[i].split("__")[0]+"</option>");
            $("#select-channel").append(item);
            $("#group-names").append($("<option value="+data[i].split("__")[0]+">"));
            if(channel == item.val()){
                $("#select-channel").val(channel);
            }
        };
        if(channel==null){
            $("#select-channel").val($("#tool-buttons").attr("data-default"));
        }
        $("#select-channel").change(function(){
            url = $("#tool-buttons").attr("data-domain") + $("#select-channel").val() +"?layout=embedded";
            $("#myframe").attr("src", url);
        });
    };

    function loadGroups(){
        data = {"userId": $("#tool-buttons").attr("data-user-id"),
                "authToken": $("#tool-buttons").attr("data-token")};
        $.ajax({
            type: "POST",
            url: getGroups,
            data: JSON.stringify(data),
            success: responseGetGroups
        })
    };

    function isScrolledIntoView(elem){
        if (elem[0]==null){
            return false;
        }
        var docViewTop = $(window).scrollTop();
        var docViewBottom = docViewTop + $(window).height();

        var elemTop = $(elem).offset().top;
        var elemBottom = elemTop + $(elem).height();

        return ((elemBottom <= docViewBottom) && (elemTop >= docViewTop));
    };

}
