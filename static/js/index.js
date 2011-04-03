$(document).ready(function() {

    var timeout = null;
    var player = $('#player').get(0);
    var playlist = $('#playlist').get(0);

    window.onbeforeunload = function() { 
        return 'unload?';
    }

    $(window).unload(function() {        
        var playlist = $('#playlist .item').map(function(n,i) { 
            return $(i).data('source') 
        });

        localStorage.setItem('playlist', JSON.stringify($.makeArray(playlist)));
    });

    $(player).bind('play-next-source', function() {
        var item = $('#playlist .playing').removeClass('playing').next('.item');
        if(item.length)
            $(player).trigger('play-source', item);
    });

    $(player).bind('play-previous-source', function() {
        var item = $('#playlist .playing').removeClass('playing').next('.item');
        if(item.length)
            $(player).trigger('play-source', item);
    });

    $(player).bind('play-source', function(e, item) {
        var source = $(item).data('source');
        $(item).addClass('playing');
        $('#now-playing').html($('#now-playing-template').tmpl(source));        
        player.src = source.url;
    });

    player.addEventListener('ended', function() {
        $(player).trigger('play-next-source');
    });

    $(playlist).bind('add-item', function(e, source) {
        var i = $('#playlist-item-template').tmpl(source);
        i.data('source', source);
        $(playlist).append(i);
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

    $('#skip-backward').click(function() {
        $(player).trigger('play-previous-source');
    });

    $('#skip-foreward').click(function() {
        $(player).trigger('play-next-source');        
    });

    $('a.play').live('click', function() {
        $(player).trigger('play-source', $(this).parent('.item'));
        return false;
    });

    $('a.add-playlist').live('click', function() {
        $.getJSON(this.href, function(source) {
            $(playlist).trigger('add-item', source)
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

    if('playlist' in localStorage) {
        var data = JSON.parse(localStorage.getItem('playlist'));
        for(var i=0; i<data.length; i++)
            $(playlist).trigger('add-item', data[i]);
    }
});