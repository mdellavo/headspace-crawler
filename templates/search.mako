
%if not xhr:
<div class="span-1">
  <br/>
</div>
<div class="span-5">
  Title
</div>
<div class="span-5">
  Artist
</div>
<div class="span-5 last">
  Album
</div>
%endif

%for i, source in enumerate(sources[offset:offset+limit]):
<div class="clear span-1 controls">
    <a class="add-playlist" href="/source/${source.uid}">Play</a>
</div>
<div class="span-5 title">
  ${source.data.get('title', '')}
</div>
<div class="span-5 artist">
  ${source.data.get('artist', '')}
</div>
<div class="span-5 last album">
  ${source.data.get('album', '')}
</div>
%endfor

<p class="more clear prepend-top">

  ${count} Matches 
  
  %if count > limit+offset:
  <a class="more" href="/search?q=${query}&offset=${offset+limit}&limit=${limit}">
    More
  </a>
  %endif
</p>
