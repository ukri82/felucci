var startItems;
var request;


$(document).ready(function() {

var $form = $("#PredictionForm");

startItems = convertSerializedArrayToHash($form.serializeArray()); 

Object.size = function(obj) {
    var size = 0, key;
    for (key in obj) {
        if (obj.hasOwnProperty(key)) size++;
    }
    return size;
};

});


function submitForm(){
    
    if (request) {
        request.abort();
    }
    
    var $form = $("#PredictionForm");
    var $inputs = $form.find("input, select, button, textarea");
    
    var currentItems = convertSerializedArrayToHash($form.serializeArray());
    var itemsToSubmit = hashDiff( startItems, currentItems);
    
    if (Object.size(itemsToSubmit) > 0)
    {
        $inputs.prop("disabled", true);
        
        // fire off the request
        request = $.ajax({
            url: $form.attr('action'),
            type: "post",
            data: itemsToSubmit
        });
        
        request.done(function (response, textStatus, jqXHR){
            // log a message to the console
            //console.log("Hooray, it worked!");
        });

        // callback handler that will be called on failure
        request.fail(function (jqXHR, textStatus, errorThrown){
            // log the error to the console
            console.error("The following error occured: " + textStatus, errorThrown);
        });
        
        request.always(function () {
            // reenable the inputs
            $inputs.prop("disabled", false);
            startItems = convertSerializedArrayToHash($form.serializeArray());
        });
    }
    return false;
}

function hashDiff(h1, h2) {
  var d = {};
  for (k in h2) {
    if (h1[k] !== h2[k]) d[k] = h2[k];
  }
  return d;
}

function convertSerializedArrayToHash(a) { 

  var r = {}; 
  
  for (var i = 0;i<a.length;i++) { 
    r[a[i].name] = a[i].value;
  }
  
  return r;
}