
  
 // Trailer data
const trailerMap = {
    'Open 24 Hours': {
      id: 'iI7yLprZheA',
      img: 'project-image2.jpg',
      year: '2018',
      director: 'Padraig Reynolds',
      duration: '102 min',
      desc: 'A psychological thriller about a woman who takes a job at a 24-hour convenience store after being released from prison.',
      accolades: `
        Official Selection:<br>
        FrightFest London (2018), SITGES International Film Festival, SPAIN (2018)<br>
        BIFAN Film Festival, SOUTH KOREA (2019), Fantastic Fest, USA (2018)<br>
        Telluride Horror Show Film Festival, USA (2018)<br>
        <strong>WINNER:</strong> Best Special Effects / Make-Up @ Screamfest Horror Film Festival, Los Angeles, USA (2018)
      `
    },
    'Dark Light': {
      id: 'Isls30Tok3E',
      img: 'project-image3.jpg',
      year: '2019',
      director: 'Padraig Reynolds',
      duration: '90 min',
      desc: 'A mother fights to protect her daughter from a terrifying presence she believes is in her house.',
      accolades: `
        Premiered at FrightFest, London
      `
    },
    "Daddy's Girl": {
      id: 'MKVRv3AAOlE',
      img: 'project-image1.jpg',
      year: '2018',
      director: 'Julian Richards',
      duration: '89 min',
      desc: 'A young woman held captive by her father must uncover a dark family secret.',
      accolades: `
        Official Selection:<br>
        RAINDANCE (London, 2018), BIFAN (South Korea, 2019)<br>
        National Film and Television Awards, USA (2019)<br>
        Buffalo Dreams Fantastic Film Festival (2020) – 4 Nominations<br>
        <strong>WINNER:</strong> Best Director @ FANTASPORTO Film Festival, Portugal (2019)
      `
    }
  };
  
  // Render the film cards dynamically
  const filmGrid = document.getElementById('filmGrid');
  
  Object.entries(trailerMap).forEach(([title, film]) => {
    const card = document.createElement('div');
    card.className = 'film-card';
    card.innerHTML = `
      <div class="poster-hover">
        <img src="images/${film.img}" alt="${title}" />
        <div class="hover-overlay">
          <div class="hover-text">
            <h3>${title} (${film.year})</h3>
            <p><strong>Director:</strong> ${film.director}</p>
            <p><strong>Duration:</strong> ${film.duration}</p>
            <p>${film.desc}</p>
<h4>ACCOLADES</h4>
<p>${film.accolades}</p>
          </div>
        </div>
      </div>
  
      <div class="film-info">
        <span class="film-year">${film.year}</span>
        <div class="film-title-row">
          <h3>${title}</h3>
          <span class="inline-play-icon" onclick="openTrailer('${title}')">▶ Play Trailer</span>
        </div>
      </div>
    `;
    filmGrid.appendChild(card);
  });
  document.getElementById("filmTitle").textContent = `${title} (${film.year})`;
document.getElementById("filmDetails").innerHTML = `
  <strong>Director:</strong> ${film.director}<br>
  <strong>Duration:</strong> ${film.duration}<br>
  ${film.desc}<br><br>
  <strong>ACCOLADES:</strong><br>${film.accolades}
`;
