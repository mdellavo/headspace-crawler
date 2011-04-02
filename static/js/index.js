$(document).ready(function() {

    var timeout = null;

    var player = $('#player').get(0);

    $(player).bind('source-ended', function() {
        var item = $('#playlist .playing ~ .item');
        if(item.length)
            $(player).trigger('play-source', item);
    });

    $(player).bind('play-source', function(e, item) {
        $(item).addClass('playing');
        var source = $(item).data('source');
        $('#now-playing').html($('#now-playing-template').tmpl(source));        
        player.src = source.url;
    });

    player.addEventListener('ended', function() {
        $(player).trigger('source-ended');
    });
    
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
        $(player).trigger('play-source', $(this).parent('.item'));
        return false;
    });

    $('a.add-playlist').live('click', function() {
        $.getJSON(this.href, function(source) {
            var item = $('#playlist-item-template').tmpl(source);
            item.data('source', source);
            $('#playlist').append(item);

            if($('#playlist .item').length == 1)
                $(player).trigger('play-source', item);
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