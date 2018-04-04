window.onload = function () {

    "use strict";

    var urlString, url, authToken, userId;

    urlString = window.location.href;
    url = new URL(urlString);
    authToken = url.searchParams.get("authToken");
    userId = url.searchParams.get("userId");

    if (authToken !== null && userId !== null) {
        localStorage.setItem("Meteor.loginToken", authToken);
        localStorage.setItem("Meteor.userId", userId);
    } else {
        console.warn("Some parameters are missing. Please provide them");
    }
};
