function LoadNextChunk(aURL_in, aParams_in, aTargetDivId_in, aMoreLinkId_in, aMoreFlagId_in, aFirst_in, aDataCallback_in)
{
    aURL = aURL_in;
    aNextChunk = "false";
    if(aFirst_in == false)
    {
        aNextChunk = "true";
    }
    aURL += "?";
    if(aParams_in != "")
    {
        aURL += aParams_in + "&";
    }
    aURL += "NextChunk=" + aNextChunk;
    
    $.web2py.component(aURL, aTargetDivId_in);
    
    (function () {
        
        if ($.active == 0)  //  Are still some ajax calls active?
        {
            aMoreFlag = $("#" + aTargetDivId_in + " input").filter("#" + aMoreFlagId_in).val();
            $("#" + aTargetDivId_in + " input").filter("#" + aMoreFlagId_in).remove();
            
            if(aMoreFlag == "True")
            {
                $("#" + aMoreLinkId_in).show();
            }
            else
            {
                $("#" + aMoreLinkId_in).hide();
            }
            
            aDataCallback_in(aFirst_in);
        }
        else 
        {
            setTimeout(arguments.callee, 50); // call myself again in 50 msecs and check if still some ajax is running.
        }
    }());
 }

function LoadOnDemand(aURL_in, aParams_in, aTargetDivId_in, aMoreLinkId_in, aMoreFlagId_in, aDataCallback_in)
{
    $(document).ready(function(){
        
        LoadNextChunk(aURL_in, aParams_in, aTargetDivId_in, aMoreLinkId_in, aMoreFlagId_in, true, aDataCallback_in);
        
        $("#" + aMoreLinkId_in).click(function(){  
            LoadNextChunk(aURL_in, aParams_in, aTargetDivId_in, aMoreLinkId_in, aMoreFlagId_in, false, aDataCallback_in);
        });

    });
}