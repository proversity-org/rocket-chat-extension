/* Javascript for StudioView. */
function StudioViewEdit(runtime, element) {
    "use strict";

    /*eslint no-undef: "error"*/
    StudioEditableXBlockMixin(runtime, element);

    function responseCreate(data){
        if (data["success"]) {
            $("#message").text("Group Created").
            css("color", "green");

            if ($("#as-team").val()==="true"){
                var name = "(Team Group)"+ $("#group-name").val();
            }
            else{
                var name = $("#group-name").val();
            }
            var option = new Option(name, name, true, true);
            $("#xb-field-edit-default_channel").append(option);

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
        var asTeam = $("#as-team").val() == "true"? true:false;
        var data = {groupName, description, topic, asTeam};
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

    $("#xb-field-edit-selected_view").on("change", function() {

        if(this.value === "Specific Channel"){
            $("#xb-field-edit-default_channel").prop("disabled", false);
        }else{
            $("#xb-field-edit-default_channel").prop("disabled", true);
        }
    });

    $(function ($) {

        if( $("#xb-field-edit-graded_activity").val() === "0"){
            $("#xb-field-edit-emoji").parents("li").hide();
            $("#xb-field-edit-target_reaction").parents("li").hide();
            $("#xb-field-edit-oldest").parents("li").hide();
            $("#xb-field-edit-latest").parents("li").hide();
            $("#xb-field-edit-weight").parents("li").hide();
            $("#xb-field-edit-count_messages").parents("li").hide();
        };

        $("#xb-field-edit-graded_activity").change(function(){
            $("#xb-field-edit-emoji").parents("li").toggle();
            $("#xb-field-edit-target_reaction").parents("li").toggle();
            $("#xb-field-edit-oldest").parents("li").toggle();
            $("#xb-field-edit-latest").parents("li").toggle();
            $("#xb-field-edit-weight").parents("li").toggle();
            $("#xb-field-edit-count_messages").parents("li").toggle();
        });

        if( $( "#xb-field-edit-selected_view" ).val() === "Specific Channel"){
            $("#xb-field-edit-default_channel").prop("disabled", false);
        }else{
            $("#xb-field-edit-default_channel").prop("disabled", true);
        }

    });
}
