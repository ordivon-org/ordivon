const state = { catalog: null, works: [], filtered: [] };
const $ = (id) => document.getElementById(id);
const els = {
  search: $('search'), owner: $('owner'), room: $('room'), medium: $('medium'),
  grid: $('grid'), count: $('result-count'), clear: $('clear'), stats: $('stats'),
  standing: $('standing'), detail: $('detail'), detailBody: $('detail-body'), close: $('close'),
  template: $('card-template')
};

const rawUrl = (work, carrier) => `/raw/${encodeURIComponent(work.workId)}/${carrier.relativePath.split('/').map(encodeURIComponent).join('/')}`;
const esc = (s='') => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const humanSize = n => n == null ? '' : n < 1024 ? `${n} B` : n < 1048576 ? `${(n/1024).toFixed(1)} KB` : `${(n/1048576).toFixed(1)} MB`;

function options(el, values) {
  for (const value of [...new Set(values.filter(Boolean))].sort((a,b)=>a.localeCompare(b))) {
    const o = document.createElement('option'); o.value = value; o.textContent = value; el.append(o);
  }
}
function stat(value, label) { return `<div class="stat"><strong>${esc(value)}</strong><span>${esc(label)}</span></div>`; }
function renderStats() {
  const c = state.catalog;
  els.stats.innerHTML = stat(c.works.length, 'recovered works') + stat(c.summary.carrierCount, 'exact carriers') + stat(c.summary.directPreviewWorks, 'direct-preview works') + stat(c.summary.relationCount, 'lineage relations');
  els.standing.textContent = `${c.archiveStanding} · ${c.catalogDigest.slice(0, 23)}…`;
}
function card(work) {
  const node = els.template.content.firstElementChild.cloneNode(true);
  node.querySelector('.owner').textContent = work.owner;
  node.querySelector('.room').textContent = work.room || '—';
  node.querySelector('h3').textContent = work.title;
  node.querySelector('.work-id').textContent = work.workId;
  const chips = node.querySelector('.chips');
  for (const m of work.modalities.slice(0, 4)) { const c=document.createElement('span'); c.className='chip'; c.textContent=m; chips.append(c); }
  const thumb = node.querySelector('.thumb');
  const hero = work.heroCarrier;
  if (hero && hero.kind === 'image') {
    const img = document.createElement('img'); img.loading='lazy'; img.alt=''; img.src=rawUrl(work, hero); thumb.append(img);
  } else {
    const mark=document.createElement('div'); mark.className='kind-mark'; mark.textContent=(hero?.kind || work.modalities[0] || 'work').slice(0,6); thumb.append(mark);
  }
  const open = () => showDetail(work);
  node.addEventListener('click', open);
  node.addEventListener('keydown', e => { if (e.key==='Enter' || e.key===' ') { e.preventDefault(); open(); }});
  return node;
}
function applyFilters() {
  const q=els.search.value.trim().toLowerCase(), owner=els.owner.value, room=els.room.value, medium=els.medium.value;
  state.filtered = state.works.filter(w => {
    const hay=[w.title,w.workId,w.series,w.sourcePath,w.status,...w.modalities].filter(Boolean).join(' ').toLowerCase();
    return (!q || hay.includes(q)) && (!owner || w.owner===owner) && (!room || w.room===room) && (!medium || w.modalities.includes(medium));
  });
  els.count.textContent=`${state.filtered.length} ${state.filtered.length===1?'work':'works'}`;
  els.grid.replaceChildren(...state.filtered.map(card));
  if (!state.filtered.length) els.grid.innerHTML='<div class="empty">No works match these filters.</div>';
}
function previewHtml(work) {
  const c=work.launchCarrier || work.heroCarrier;
  if (!c) return '<div class="preview"><div class="kind-mark">source</div></div>';
  const u=rawUrl(work,c);
  if (c.kind==='image') return `<div class="preview"><img src="${esc(u)}" alt=""></div>`;
  if (c.kind==='video') return `<div class="preview"><video controls preload="metadata" src="${esc(u)}"></video></div>`;
  if (c.kind==='audio') return `<div class="preview"><audio controls preload="metadata" src="${esc(u)}"></audio></div>`;
  if (c.kind==='html') return `<div class="preview"><iframe sandbox="allow-scripts" referrerpolicy="no-referrer" src="${esc(u)}" title="${esc(work.title)} historical HTML carrier"></iframe></div>`;
  if (c.kind==='pdf') return `<div class="preview"><iframe sandbox src="${esc(u)}" title="${esc(work.title)} PDF"></iframe></div>`;
  if (c.kind==='text' || (c.kind==='source' && /\.(py|js|mjs|cjs|ts|tsx|css|sh|bash|lua)$/i.test(c.relativePath))) return `<div class="preview"><iframe sandbox src="${esc(u)}" title="${esc(work.title)} source text"></iframe></div>`;
  return `<div class="preview"><div class="kind-mark">${esc(c.kind)}</div></div>`;
}
function fact(label, value, code=false) { return `<div class="fact"><span>${esc(label)}</span>${code?`<code>${esc(value||'—')}</code>`:`<strong>${esc(value||'—')}</strong>`}</div>`; }
function showDetail(work) {
  const relations=state.catalog.relations.filter(r => r.child_work_id===work.workId || r.parent_work_id===work.workId);
  const carriers=work.carriers.filter(c => c.kind!=='other').slice(0,80);
  els.detailBody.innerHTML=`<div class="detail-wrap">
    <header class="detail-head"><p class="eyebrow">${esc(work.owner)} · ${esc(work.room||'unroomed')}</p><h2>${esc(work.title)}</h2><p class="detail-id">${esc(work.workId)}</p></header>
    ${previewHtml(work)}
    <div class="fact-grid">
      ${fact('Status',work.status)}${fact('Series',work.series)}${fact('Source revision',work.sourceRevision,true)}${fact('Source path',work.sourcePath,true)}${fact('Physical standing',work.physicalStanding)}${fact('Human standing',work.humanStanding)}
    </div>
    ${relations.length?`<h3 class="section-title">Relations</h3><div class="carriers">${relations.map(r=>`<div class="carrier"><span class="type">${esc(r.relation_type)}</span><code>${esc(r.child_work_id===work.workId?r.parent_work_id:r.child_work_id)}</code><span class="size"></span></div>`).join('')}</div>`:''}
    <h3 class="section-title">Exact carriers · ${work.carrierCount}</h3>
    <div class="carriers">${carriers.map(c=>`<div class="carrier"><span class="type">${esc(c.kind)}</span><a href="${esc(rawUrl(work,c))}" target="_blank" rel="noreferrer"><code>${esc(c.relativePath)}</code></a><span class="size">${esc(humanSize(c.size))}</span></div>`).join('')}</div>
  </div>`;
  els.detail.showModal();
}

async function boot() {
  const res=await fetch('/api/catalog'); if(!res.ok) throw new Error(`catalog ${res.status}`);
  state.catalog=await res.json(); state.works=state.catalog.works;
  options(els.owner,state.works.map(w=>w.owner)); options(els.room,state.works.map(w=>w.room)); options(els.medium,state.works.flatMap(w=>w.modalities));
  renderStats(); applyFilters();
}
for (const el of [els.search,els.owner,els.room,els.medium]) el.addEventListener(el===els.search?'input':'change',applyFilters);
els.clear.addEventListener('click',()=>{els.search.value=''; els.owner.value=''; els.room.value=''; els.medium.value=''; applyFilters();});
els.close.addEventListener('click',()=>els.detail.close());
els.detail.addEventListener('click',e=>{if(e.target===els.detail)els.detail.close();});
boot().catch(err=>{console.error(err); els.grid.innerHTML=`<div class="empty">Creative Library failed to load: ${esc(err.message)}</div>`;});
