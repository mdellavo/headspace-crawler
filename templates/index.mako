<%inherit file="base.mako"/>

<%def name="head()">
<script src="/static/js/jquery.tmpl.js"></script>
</%def>

<%def name="tail()">
<script src="/static/js/index.js"></script>
</%def>

<div class="container">

  <div id="header" class="span-24 last">
    <strong>HeadSpace</strong>
    <span id="now-playing"></span>
  </div>

  <div id="playlists" class="span-8">   
    <audio id="player" controls="controls" 
           autoplay="autoplay" preload="auto" src=""/>
  </div>

  <div class="span-16 last">
    <div>
      <label for="search">Search</search>
      <input type="text" id="search" name="query" value="" class="text"/>
    </div>

    <div id="results"></div>
  </div>

  <div id="footer" class="span-24 last">
  </div>

</div>

<script id="now-playing-template" type="text/x-jquery-tmpl">
<%text>
  Now Playing: <span class="artist">${title}</span>
  by <span class="artist">${artist}</span>
  from <span class="artist">${album}</span>
</%text>
</script>
