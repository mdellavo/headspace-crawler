$(document).ready(function() {

    var timeout = null;

    var State = {
        
    };

    function trim(i) {
        return i.replace(/^\s+|\s+$/g, '');
    }

    $('#search').keyup(function() {
        var value = window.escape(trim(this.value));
        
        if(value == '') {
            $('#results').html('');
        } else if(value.length>2) {

            if(timeout){
                window.clearTimeout(timeout);
                timeout = null;
            }

            timeout = window.setTimeout(function() {
                timeout = null;
                $('#results').load('/search?q=' + value);
            }, 200);
        }
         
        return false;
    });

    $('a.play').live('click', function() {
        $.getJSON(this.href, function(data) {
            console.log(data);
            $('#player').attr('src', data.url);
            
            $('#now-playing').html($('#now-playing-template').tmpl(data.data));
        });
        return false;
    });
    
    $('.controls').live({
        'mouseover' : function() {
            $(this).find('span').show();
        },
        'mouseout' : function() {
            $(this).find('span').hide();
        }
    });

    $('a.more').live('click', function(){
         $.get(this.href, function(data) {
             $('p.more').replaceWith(data);
         });
        return false;
    });

});