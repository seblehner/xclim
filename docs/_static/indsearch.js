let indicators = [];
let miniSearch = new MiniSearch({
  fields: ['title', 'abstract', 'variables'], // fields to index for full-text search
  storeFields: ['title', 'abstract', 'vars', 'realm', 'name'], // fields to return with search results
  searchOptions: {
    boost: {'title': 3, 'variables': 2},
    fuzzy: 0.1,
    prefix: true,
  },
  extractField: (doc, field) => {
    if (field === 'variables') {
      return Object.keys(doc['vars']).join(' ');
    }
    return MiniSearch.getDefault('extractField')(doc, field);
  }
});

// populate list
fetch('indicators.json')
  .then(data => data.json())
  .then(data => {
    indicators = Object.entries(data).map(([k, v]) => {
      return {id: k.toLowerCase(), ...v}
    });
    miniSearch.addAll(indicators);
    indFilter();
  });

function indTemplate(ind) {
  const varlist = Object.entries(ind.vars).map((kv) => `<code class="indVarname">${kv[0]}</code>`).join('');
  return `
    <div class="indElem" id="${ind.id}">
      <div class="indHeader">
        <b class="indTitle">${ind.title}</b>
        <a class="reference_internal indName" href="api.html#xclim.indicators.${ind.realm}.${ind.name}" title="${ind.name}">
          <code>${ind.realm}.${ind.name}</code>
        </a>
      </div>
      <div class="indVars">Uses: ${varlist}</div>
      <div class="indDesc"><p>${ind.abstract}</p></div>
      <div class="indID">Yaml ID: <code>${ind.id}</code></div>
    </div>
  `;
}

function indFilter() {
  const input = document.getElementById("queryInput").value;
  let inds = [];
  if (input === "") {
    inds = indicators;
  } else {
    inds = miniSearch.search(input);
  }

  const newTable = inds.map(indTemplate).join('');
  const tableElem = document.getElementById("indTable");
  tableElem.innerHTML = newTable;
  return newTable;
}
