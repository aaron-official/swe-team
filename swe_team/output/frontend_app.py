#!/usr/bin/env python3
"""
Frontend scaffolder & static server for Task Tracker

This script creates a complete vanilla-JS frontend in output/public/ based on the
architecture document and serves it on http://localhost:3000. The frontend
integrates with the backend API (default: http://localhost:8080/api/tasks).

Run this script to write the static files and start a simple local server.

Author: AI Engineering Crew
Generated: 2025-12-12
"""
import os
import sys
import textwrap
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
import threading
import webbrowser

# Configuration
PUBLIC_DIR = Path(__file__).resolve().parent / "public"
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8081/api/tasks")
HOST = os.environ.get("FRONTEND_HOST", "localhost")
PORT = int(os.environ.get("FRONTEND_PORT", "3000"))

INDEX_HTML = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Task Tracker</title>
  <link rel="stylesheet" href="/styles.css" />
  <meta name="api-base-url" content="{API_BASE_URL}" />
</head>
<body>
  <header id="header" class="header">
    <div class="header-left">
      <h1 id="site-title">Task Tracker</h1>
      <span class="subtitle">Manage tasks quickly</span>
    </div>
    <div class="header-right">
      <button id="btn-new-task" class="btn primary" aria-label="Create new task">New Task</button>
    </div>
  </header>
  <main id="main" class="container">
    <section id="toolbar" class="toolbar" aria-label="Toolbar">
      <label class="sr-only" for="filter-status">Filter by status</label>
      <select id="filter-status" aria-label="Filter by status">
        <option value="">All statuses</option>
        <option value="pending">Pending</option>
        <option value="in-progress">In-Progress</option>
        <option value="completed">Completed</option>
      </select>

      <label class="sr-only" for="sort-by">Sort by</label>
      <select id="sort-by" aria-label="Sort by">
        <option value="createdAt">Created</option>
        <option value="priority">Priority</option>
      </select>

      <button id="sort-order" class="btn" aria-pressed="false">Desc</button>

      <label class="sr-only" for="search-box">Search tasks</label>
      <input id="search-box" placeholder="Search title or description..." aria-label="Search tasks" />

      <button id="btn-export" class="btn" title="Export tasks">Export</button>
    </section>

    <section id="task-list" class="task-list" aria-live="polite"></section>
  </main>

  <!-- Modals & Toasts -->
  <div id="modal-root" aria-hidden="true"></div>
  <div id="toast-root" aria-live="polite" aria-atomic="true"></div>

  <script src="/app.js"></script>
</body>
</html>
"""

STYLES_CSS = """:root{
  --bg-primary:#1a1a2e;
  --bg-secondary:#16213e;
  --accent:#00A3FF;
  --text-primary:#E6EEF8;
  --text-muted:#A9B6C6;
  --priority-high:#FF6B6B;
  --priority-medium:#FFD166;
  --priority-low:#4EE1A0;
}
*{box-sizing:border-box}
html,body{height:100%}
body{
  margin:0;
  font-family:Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
  background:linear-gradient(180deg,var(--bg-primary),#0f1724);
  color:var(--text-primary);
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
}
.header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:16px 24px;
  background:linear-gradient(90deg, rgba(255,255,255,0.02), transparent);
  border-bottom:1px solid rgba(255,255,255,0.03);
  position:sticky;top:0;z-index:10;
}
.header-left h1{margin:0;font-size:20px}
.header-left .subtitle{display:block;color:var(--text-muted);font-size:12px}
.container{padding:20px;max-width:1100px;margin:0 auto}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:16px}
.toolbar select, .toolbar input{background:var(--bg-secondary);color:var(--text-primary);border:1px solid rgba(255,255,255,0.04);padding:8px 10px;border-radius:6px}
.toolbar .btn{background:transparent;color:var(--text-primary);border:1px solid rgba(255,255,255,0.04);padding:8px 12px;border-radius:6px;cursor:pointer}
.btn.primary{background:linear-gradient(90deg,var(--accent),#66d9ff);color:#071428;border:none}
.task-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.task-card{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));padding:12px;border-radius:8px;border:1px solid rgba(255,255,255,0.03);display:flex;flex-direction:column;gap:8px}
.task-header{display:flex;justify-content:space-between;align-items:center}
.task-header h3{margin:0;font-size:16px}
.priority{padding:4px 8px;border-radius:999px;font-size:12px;color:#071428;font-weight:600}
.desc{margin:0;color:var(--text-muted);font-size:13px}
.meta{display:flex;gap:8px;font-size:12px;color:var(--text-muted);align-items:center}
.actions{display:flex;gap:8px;margin-top:8px}
.actions button{background:transparent;border:1px solid rgba(255,255,255,0.04);color:var(--text-primary);padding:6px 8px;border-radius:6px;cursor:pointer}
.toast{position:fixed;top:20px;right:20px;padding:12px 16px;border-radius:8px;color:#071428;background:#bfe9ff;box-shadow:0 6px 18px rgba(0,0,0,0.4);z-index:999}
.toast.error{background:#ffb3b3;color:#300000}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
/* Modal */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:1000}
.modal{background:var(--bg-primary);padding:16px;border-radius:8px;max-width:600px;width:100%;border:1px solid rgba(255,255,255,0.04)}
.form-row{display:flex;flex-direction:column;gap:6px;margin-bottom:10px}
.form-row input, .form-row textarea, .form-row select{background:var(--bg-secondary);color:var(--text-primary);border:1px solid rgba(255,255,255,0.04);padding:8px;border-radius:6px}
.form-actions{display:flex;gap:8px;justify-content:flex-end}
.loading{display:inline-block;width:18px;height:18px;border:3px solid rgba(255,255,255,0.12);border-top-color:var(--accent);border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@media (max-width:640px){.toolbar{gap:6px}.task-list{grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}}
"""

APP_JS = """// Vanilla JS frontend for Task Tracker
// Reads API base URL from <meta name="api-base-url"> in index.html
const API_BASE = document.querySelector('meta[name="api-base-url"]').getAttribute('content') || '/api/tasks';

// Helper: show toast
function showToast(message, type='success'){
  const root = document.getElementById('toast-root');
  const el = document.createElement('div');
  el.className = 'toast' + (type==='error' ? ' error' : '');
  el.textContent = message;
  root.appendChild(el);
  setTimeout(()=>{el.classList.add('fade');try{el.remove()}catch(e){}},4000);
}

// Helper: show loading spinner in a button
function setButtonLoading(btn, loading=true){
  if(loading){
    btn.disabled = true;
    const s = document.createElement('span');
    s.className = 'loading';
    s.setAttribute('aria-hidden', 'true');
    s.style.marginLeft = '8px';
    s.dataset.loader = '1';
    btn.appendChild(s);
  } else {
    btn.disabled = false;
    const loader = btn.querySelector('[data-loader]');
    if(loader) loader.remove();
  }
}

// API wrapper
async function apiFetch(url, opts = {}){
  try{
    const res = await fetch(url, opts);
    const ct = res.headers.get('content-type') || '';
    let body = null;
    if(ct.includes('application/json')) body = await res.json(); else body = await res.text();
    if(!res.ok){
      throw {status: res.status, body};
    }
    return body;
  }catch(e){
    throw e;
  }
}

async function fetchTasks(filters = {}){
  const params = new URLSearchParams();
  if(filters.status) params.set('status', filters.status);
  if(filters.sortBy) params.set('sortBy', filters.sortBy);
  if(filters.sortOrder) params.set('sortOrder', filters.sortOrder);
  if(filters.search) params.set('search', filters.search);
  const url = API_BASE + '?' + params.toString();
  return await apiFetch(url);
}

async function getTask(id){
  return await apiFetch(API_BASE + '/' + id);
}

async function createTask(payload){
  return await apiFetch(API_BASE, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
}

async function updateTask(id,payload){
  return await apiFetch(API_BASE + '/' + id, {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
}

async function deleteTask(id){
  const res = await fetch(API_BASE + '/' + id, {method:'DELETE'});
  if(res.status === 204) return null;
  const body = await res.json();
  if(!res.ok) throw {status: res.status, body};
}

async function exportTasks(){
  const url = API_BASE.replace(/\\/api\\/tasks\\/?$/, '') + '/api/tasks/export';
  // If API_BASE is full path e.g. http://host:port/api/tasks, this will work
  try{
    const res = await fetch(url);
    if(!res.ok){
      const body = await res.json(); throw {status:res.status, body};
    }
    const blob = await res.blob();
    const urlBlob = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = urlBlob;
    a.download = 'tasks-export.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(urlBlob);
    showToast('Export started');
  }catch(err){
    console.error(err);
    showToast('Export failed','error');
  }
}

// UI rendering
function priorityColor(priority){
  switch(priority){
    case 'high': return getComputedStyle(document.documentElement).getPropertyValue('--priority-high') || '#FF6B6B';
    case 'medium': return getComputedStyle(document.documentElement).getPropertyValue('--priority-medium') || '#FFD166';
    case 'low': return getComputedStyle(document.documentElement).getPropertyValue('--priority-low') || '#4EE1A0';
    default: return '#A9B6C6';
  }
}

function truncate(s, n=140){ if(!s) return ''; return s.length>n? s.slice(0,n-1)+'…':s; }

function renderTaskList(tasks){
  const root = document.getElementById('task-list');
  root.innerHTML = '';
  if(!tasks || tasks.length===0){
    const emp = document.createElement('div'); emp.className='empty'; emp.textContent='No tasks found'; emp.style.color='var(--text-muted)'; root.appendChild(emp); return;
  }
  const ul = document.createElement('div'); ul.className='task-grid';
  tasks.forEach(t => {
    const card = document.createElement('article'); card.className='task-card'; card.setAttribute('role','article');
    const header = document.createElement('div'); header.className='task-header';
    const h3 = document.createElement('h3'); h3.textContent = t.title;
    const pri = document.createElement('span'); pri.className='priority'; pri.textContent = t.priority;
    pri.style.background = priorityColor(t.priority);
    header.appendChild(h3); header.appendChild(pri);

    const p = document.createElement('p'); p.className='desc'; p.textContent = truncate(t.description || '', 200);

    const meta = document.createElement('div'); meta.className='meta';
    const status = document.createElement('span'); status.className='status'; status.textContent = t.status;
    const created = document.createElement('span'); created.className='created'; created.textContent = new Date(t.createdAt).toLocaleString();
    meta.appendChild(status); meta.appendChild(created);

    const actions = document.createElement('div'); actions.className='actions';
    const btnEdit = document.createElement('button'); btnEdit.textContent='Edit'; btnEdit.onclick = ()=> openTaskModal(t);
    const btnDelete = document.createElement('button'); btnDelete.textContent='Delete'; btnDelete.onclick = ()=> openDeleteConfirm(t);
    actions.appendChild(btnEdit); actions.appendChild(btnDelete);

    card.appendChild(header); card.appendChild(p); card.appendChild(meta); card.appendChild(actions);
    ul.appendChild(card);
  });
  root.appendChild(ul);
}

// Modal system
function openTaskModal(task=null){
  const root = document.getElementById('modal-root'); root.innerHTML = '';
  const overlay = document.createElement('div'); overlay.className='modal-overlay'; overlay.setAttribute('role','dialog'); overlay.setAttribute('aria-modal','true');
  const modal = document.createElement('div'); modal.className='modal';
  const title = document.createElement('h2'); title.textContent = task? 'Edit Task' : 'New Task';

  const form = document.createElement('form'); form.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const fd = new FormData(form);
    const payload = { title: fd.get('title'), description: fd.get('description'), status: fd.get('status'), priority: fd.get('priority') };
    try{
      submitBtn = form.querySelector('button[type=submit]');
      setButtonLoading(submitBtn, true);
      if(task){
        await updateTask(task.id, payload);
        showToast('Task updated');
      } else {
        await createTask(payload);
        showToast('Task created');
      }
      overlay.remove(); await refreshTasks();
    }catch(err){
      console.error(err); showToast(err.body?.error || 'Save failed','error');
    }finally{ setButtonLoading(form.querySelector('button[type=submit]'), false); }
  });

  const row1 = document.createElement('div'); row1.className='form-row';
  const label1 = document.createElement('label'); label1.textContent='Title'; label1.htmlFor='title';
  const inputTitle = document.createElement('input'); inputTitle.name='title'; inputTitle.id='title'; inputTitle.required=true; inputTitle.maxLength=100; inputTitle.value = task? task.title: '';
  row1.appendChild(label1); row1.appendChild(inputTitle);

  const row2 = document.createElement('div'); row2.className='form-row';
  const label2 = document.createElement('label'); label2.textContent='Description'; label2.htmlFor='description';
  const textarea = document.createElement('textarea'); textarea.name='description'; textarea.id='description'; textarea.rows=4; textarea.maxLength=500; textarea.value = task? (task.description||'') : '';
  row2.appendChild(label2); row2.appendChild(textarea);

  const row3 = document.createElement('div'); row3.className='form-row';
  const label3 = document.createElement('label'); label3.textContent='Status'; label3.htmlFor='status';
  const selectStatus = document.createElement('select'); selectStatus.name='status'; selectStatus.id='status'; ['pending','in-progress','completed'].forEach(s=>{ const o=document.createElement('option'); o.value=s; o.textContent=s; if(task && task.status===s) o.selected=true; selectStatus.appendChild(o); });
  row3.appendChild(label3); row3.appendChild(selectStatus);

  const row4 = document.createElement('div'); row4.className='form-row';
  const label4 = document.createElement('label'); label4.textContent='Priority'; label4.htmlFor='priority';
  const selectPri = document.createElement('select'); selectPri.name='priority'; selectPri.id='priority'; ['low','medium','high'].forEach(p=>{ const o=document.createElement('option'); o.value=p; o.textContent=p; if(task && task.priority===p) o.selected=true; selectPri.appendChild(o); });
  row4.appendChild(label4); row4.appendChild(selectPri);

  const actions = document.createElement('div'); actions.className='form-actions';
  const btnCancel = document.createElement('button'); btnCancel.type='button'; btnCancel.textContent='Cancel'; btnCancel.onclick = ()=> overlay.remove();
  const btnSubmit = document.createElement('button'); btnSubmit.type='submit'; btnSubmit.className='btn primary'; btnSubmit.textContent = task? 'Save' : 'Create';
  actions.appendChild(btnCancel); actions.appendChild(btnSubmit);

  form.appendChild(row1); form.appendChild(row2); form.appendChild(row3); form.appendChild(row4); form.appendChild(actions);
  modal.appendChild(title); modal.appendChild(form); overlay.appendChild(modal); root.appendChild(overlay);
  inputTitle.focus();
}

function openDeleteConfirm(task){
  const root = document.getElementById('modal-root'); root.innerHTML = '';
  const overlay = document.createElement('div'); overlay.className='modal-overlay'; overlay.setAttribute('role','dialog'); overlay.setAttribute('aria-modal','true');
  const modal = document.createElement('div'); modal.className='modal';
  const h2 = document.createElement('h2'); h2.textContent='Delete Task';
  const p = document.createElement('p'); p.textContent = `Are you sure you want to delete "${task.title}"? This action cannot be undone.`;
  const actions = document.createElement('div'); actions.className='form-actions';
  const btnCancel = document.createElement('button'); btnCancel.type='button'; btnCancel.textContent='Cancel'; btnCancel.onclick = ()=> overlay.remove();
  const btnDelete = document.createElement('button'); btnDelete.type='button'; btnDelete.className='btn'; btnDelete.textContent='Delete'; btnDelete.style.background='#ff6b6b'; btnDelete.onclick = async ()=>{
    try{ setButtonLoading(btnDelete,true); await deleteTask(task.id); showToast('Task deleted'); overlay.remove(); await refreshTasks(); }catch(err){ console.error(err); showToast(err.body?.error || 'Delete failed','error'); }finally{ setButtonLoading(btnDelete,false); }
  };
  actions.appendChild(btnCancel); actions.appendChild(btnDelete);
  modal.appendChild(h2); modal.appendChild(p); modal.appendChild(actions); overlay.appendChild(modal); root.appendChild(overlay);
}

// App state & refresh
let currentFilters = { status: '', sortBy: 'createdAt', sortOrder: 'desc', search: '' };

async function refreshTasks(){
  const root = document.getElementById('task-list');
  root.innerHTML = '<div style="padding:20px"><span class="loading" aria-hidden="true"></span> Loading tasks...</div>';
  try{
    const tasks = await fetchTasks(currentFilters);
    renderTaskList(tasks);
  }catch(err){
    console.error(err);
    const msg = err?.body?.error || 'Failed to load tasks';
    showToast(msg,'error');
    root.innerHTML = '<div style="padding:20px;color:var(--text-muted)">Unable to load tasks</div>';
  }
}

// Wiring
document.addEventListener('DOMContentLoaded', ()=>{
  const btnNew = document.getElementById('btn-new-task');
  const filterStatus = document.getElementById('filter-status');
  const sortBy = document.getElementById('sort-by');
  const sortOrder = document.getElementById('sort-order');
  const searchBox = document.getElementById('search-box');
  const btnExport = document.getElementById('btn-export');

  btnNew.addEventListener('click', ()=> openTaskModal(null));
  filterStatus.addEventListener('change', async (e)=>{ currentFilters.status = e.target.value; await refreshTasks(); });
  sortBy.addEventListener('change', async (e)=>{ currentFilters.sortBy = e.target.value; await refreshTasks(); });
  sortOrder.addEventListener('click', async (e)=>{ currentFilters.sortOrder = currentFilters.sortOrder==='desc' ? 'asc' : 'desc'; sortOrder.textContent = currentFilters.sortOrder==='desc'?'Desc':'Asc'; await refreshTasks(); });
  let searchTimer = null;
  searchBox.addEventListener('input', (e)=>{ clearTimeout(searchTimer); searchTimer = setTimeout(async ()=>{ currentFilters.search = e.target.value; await refreshTasks(); }, 500); });
  btnExport.addEventListener('click', exportTasks);
  // initial load
  refreshTasks();
});
"""

# Ensure public directory exists and write files
def ensure_public_files():
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    (PUBLIC_DIR / 'index.html').write_text(INDEX_HTML, encoding='utf-8')
    (PUBLIC_DIR / 'styles.css').write_text(STYLES_CSS, encoding='utf-8')
    (PUBLIC_DIR / 'app.js').write_text(APP_JS, encoding='utf-8')
    print(f"Wrote static assets to: {PUBLIC_DIR}")

class QuietHandler(SimpleHTTPRequestHandler):
    # Serve files from PUBLIC_DIR and reduce console spam
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)
    def log_message(self, format, *args):
        pass

def run_server(host=HOST, port=PORT):
    os.chdir(str(PUBLIC_DIR))
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, QuietHandler)
    print(f"Serving frontend at http://{host}:{port} (API base: {API_BASE_URL})")
    print("Press Ctrl+C to stop. Opening in browser...")
    threading.Timer(0.5, lambda: webbrowser.open(f'http://{host}:{port}')).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down server...')
        httpd.server_close()

def main():
    ensure_public_files()
    # Inform about CORS: backend_app.py default CORS was http://localhost:3000 — matching this server
    print('\nIMPORTANT: Ensure the backend is running and allows CORS from this origin (http://localhost:3000).')
    print(f'Backend API base (used in generated frontend): {API_BASE_URL}')
    run_server()

if __name__ == '__main__':
    main()