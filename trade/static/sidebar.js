var req;

// Sends a new request to update the sidebar
function sendRequest() {
    if (window.XMLHttpRequest) {
        req = new XMLHttpRequest();
    } else {
        req = new ActiveXObject("Microsoft.XMLHTTP");
    }
    req.onreadystatechange = handleResponse;
    req.open("GET", "/blog/update", true);
    req.send(); 
}

// This function is called for each request readystatechange,
// and it will eventually parse the XML response for the request
function handleResponse() {
    if (req.readyState != 4 || req.status != 200) {
        return;
    }

    // Parses the XML response to get a list of DOM nodes representing items
    var xmlData = req.responseXML;
    var cur_user = xmlData.getElementsByTagName("curuser")[0];
    var users = xmlData.getElementsByTagName("username");
    var btn_styles = xmlData.getElementsByTagName("btnstyle");
    var is_auth = xmlData.getElementsByTagName("authenticated")[0];
    var sidebar = $("#following");
    // clear sidebar
    sidebar.html("");

console.log(is_auth);
    // redraw sidebar
    //var users = Array.prototype.slice.call(usernames, 0);
    //users.sort(function(x,y){x.textContent < y.textContent});
    var num_users = users.length+1;
    if (is_auth.textContent) {
        for (i=0; i<users.length; i++) {
            usname = users[i].textContent;
            btn_style = btn_styles[i].textContent;
            jQuery('<a/>', {
                class: 'btn' + btn_style + 'btn-block',
                href: '/blog/follow/'+usname,
                text: usname
            }).appendTo(sidebar);
        }
    }
    else {
        for (i=0; i<users.length; i++) {
            usname = users[i].textContent;
            btn_style = btn_styles[i].textContent;
            var link = $("<a>");
            link.attr({
                class: 'btn' + btn_style + 'btn-block',
                href: '/blog/user/'+usname,
                text: usname
            });
            sidebar.append(link);
        }
    }
}