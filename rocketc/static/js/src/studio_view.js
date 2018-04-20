/* Javascript for StudioView. */
function StudioViewEdit(runtime, element) {
    "use strict";

    /*eslint no-undef: "error"*/
    StudioEditableXBlockMixin(runtime, element);

    function responseCreate(data){
        if (data["success"]) {
            $("#message").text("Group Created").
            css("color", "green");
        }else{
            $("#message").text(data["error"]).
            css("color", "red");
        }

    }

    var createGroup = runtime.handlerUrl(element, "create_group");

    $("#button-create").click(function(eventObject) {
        var groupName = $("#group-name").val();
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

    $(".action-modes").append($("#options"));

    $("#select-default").on("click",function(){
        $(".editor-with-buttons").css("display", "block");
        $(".rocketc_block .editor-with-buttons").css("display", "none");
        $("#select-create").attr("class", "button");
        $("#select-default").attr("class", "button action-primary");
    });

    $("#select-create").on("click",function(){
        $(".editor-with-buttons").css("display", "none");
        $(".rocketc_block .editor-with-buttons").css("display", "block");
        $("#select-create").attr("class", "button action-primary");
        $("#select-default").attr("class", "button");
    });

}
