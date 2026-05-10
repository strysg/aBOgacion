// Static client-side search for Bolivian norms
let store = null;
let searchIndex = null;

async function initSearch() {
    const response = await fetch('/assets/docs.json');
    const documents = await response.json();
    
    // Create FlexSearch document index
    searchIndex = new FlexSearch.Document({
        document: {
            id: 'id',
            index: ['title', 'type', 'year', 'content_preview'],
            store: ['title', 'type', 'year', 'url']
        }
    });
    
    // Add all documents
    for (const doc of documents) {
        searchIndex.add(doc);
    }
    
    // Build store for quick filtering
    store = Object.fromEntries(documents.map(doc => [doc.id, doc]));
    
    populateFilters();
    
    // Attach event listeners
    document.getElementById('searchInput').addEventListener('input', search);
    document.getElementById('yearFilter').addEventListener('change', search);
    document.getElementById('typeFilter').addEventListener('change', search);
    
    // Read year from URL and apply filter
    const urlParams = new URLSearchParams(window.location.search);
    const yearParam = urlParams.get('year');
    if (yearParam) {
        const yearSelect = document.getElementById('yearFilter');
        yearSelect.value = yearParam;
    }
    
    search();
}

function populateFilters() {
    const years = new Set();
    const types = new Set();
    for (const id in store) {
        years.add(store[id].year);
        types.add(store[id].type);
    }
    const yearSelect = document.getElementById('yearFilter');
    const typeSelect = document.getElementById('typeFilter');
    
    // Add years (descending order)
    [...years].sort().reverse().forEach(y => {
        const opt = document.createElement('option');
        opt.value = y;
        opt.textContent = y;
        yearSelect.appendChild(opt);
    });
    
    // Add types (alphabetical)
    [...types].sort().forEach(t => {
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        typeSelect.appendChild(opt);
    });
}

async function search() {
    const query = document.getElementById('searchInput').value.trim();
    const year = document.getElementById('yearFilter').value;
    const type = document.getElementById('typeFilter').value;
    
    let results = [];
    if (query.length < 2) {
        if (year.length < 2 && type.length < 2)
            results = [];
        else
            results = Object.values(store);
        
    } else {
        const res = searchIndex.search(query);
        const ids = new Set();
        for (const r of res) {
            r.result.forEach(id => ids.add(id));
        }
        results = Array.from(ids).map(id => store[id]);
    }
    
    // Apply year and type filters
    results = results.filter(r => (!year || r.year === year) && (!type || r.type === type));
    
    const container = document.getElementById('results');
    if (results.length === 0) {
        container.innerHTML = '<div class="result-card">No se encontraron normas.</div>';
        return;
    }
    
    container.innerHTML = results.map(r => `
        <div class="result-card">
            <div class="result-title"><a href="${r.url}">${escapeHtml(r.title)}</a></div>
            <div class="result-meta">
                <span>${escapeHtml(r.type)}</span> · <span>${escapeHtml(r.year)}</span>
            </div>
            <div class="result-preview">${escapeHtml(r.content_preview)}…</div>
        </div>
    `).join('');
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, m => {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

// Start everything once the DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSearch);
} else {
    initSearch();
}
