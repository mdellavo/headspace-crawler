<table>
  <thead>
    <th></th>
    <th>Title</th>
    <th>Artist</th>
    <th>Album</th>
  </thead>
  <tbody>
    %for i, source in enumerate(sources[:10]):
    <tr>
      <td class="controls">
        <span style="display:none">
          <a class="play" href="/source/${source.uid}">Play</a>
        </span>
      </td>
      <td>${source.data.get('title', '')}</td>
      <td>${source.data.get('artist', '')}</td>
      <td>${source.data.get('album', '')}</td>
    </tr>
    %endfor
  </tbody>
</table>

<p>
  ${sources.count()} Matches 
  <a href="/search?offset=">
    More
  </a>
</p>
