window.onload = function () {

    "use strict";

    var url_string, url, auth_token, user_id;

    url_string = window.location.href;
    url = new URL(url_string);
    auth_token = url.searchParams.get("authToken");
    user_id = url.searchParams.get("userId");

    if (auth_token !== null && user_id !== null) {
        localStorage.setItem("Meteor.loginToken", auth_token);
        localStorage.setItem("Meteor.userId", user_id);
    } else {
        console.warn("Some parameters are missing. Please provide them");
    }
};
