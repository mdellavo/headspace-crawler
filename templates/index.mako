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

  <div class="span-8">
    <audio id="player" controls="controls" 
           autoplay="autoplay" preload="auto" src=""></audio>
    <a href="#skip-backward"  id="skip-backward">
      <img src="/static/img/skip-backward.png"/>
    </a>
    <a href="#skip-foreward"  id="skip-foreward">
      <img src="/static/img/skip-forward.png" id="skip-foreward"/>
    </a>
    <div id="playlist"></div>
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
  Now Playing: <span class="artist">${data.title}</span>
  by <span class="artist">${data.artist}</span>
  from <span class="artist">${data.album}</span>
</%text>
</script>

<script id="playlist-item-template" type="text/x-jquery-tmpl">
<%text>
<div class="item">
  <a class="play" href="/source/${uid}">${data.artist} - ${data.title}</a>
</div>
</%text>
</script>
