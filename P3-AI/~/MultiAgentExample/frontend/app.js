const byId = (id) => document.getElementById(id);
const state = { employees: [], departments: [], editingId: null, toastTimer: null, history: [], busy: false };
const employeeRows = byId('employee-rows');
const dialog = byId('employee-dialog');
const form = byId('employee-form');

function escapeHtml(value = '') {
  return String(value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[character]);
}
function initials(name) { return name.trim().split(/\s+/).slice(0, 2).map((part) => part[0] || '').join('').toUpperCase(); }
function money(value) { return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0, notation: 'compact' }).format(value || 0); }
function dateLabel(value) { return value ? new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) : '—'; }
function showToast(message) {
  const toast = byId('toast'); toast.textContent = message; toast.classList.add('visible');
  clearTimeout(state.toastTimer); state.toastTimer = setTimeout(() => toast.classList.remove('visible'), 3000);
}
async function api(url, options = {}) {
  const response = await fetch(url, { ...options, headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...options.headers } });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.error || 'Something went wrong. Please try again.');
  return data;
}
async function refreshDirectory() {
  byId('loading-state').hidden = false;
  try {
    const parameters = new URLSearchParams();
    const search = byId('search-input').value.trim();
    const department = byId('department-filter').value;
    const status = byId('status-filter').value;
    if (search) parameters.set('search', search);
    if (department) parameters.set('department', department);
    if (status) parameters.set('status', status);
    const [directory, summary] = await Promise.all([api(`/api/employees?${parameters}`), api('/api/summary')]);
    state.employees = directory.employees; state.departments = directory.departments;
    renderDirectory(); renderSummary(summary); renderDepartmentFilter();
  } catch (error) { showToast(error.message); }
  finally { byId('loading-state').hidden = true; }
}
function renderSummary(summary) {
  byId('metric-headcount').textContent = summary.headcount;
  byId('metric-active').textContent = summary.active;
  byId('metric-departments').textContent = summary.departments;
  byId('metric-payroll').textContent = money(summary.payroll);
  byId('nav-count').textContent = summary.headcount;
}
function renderDepartmentFilter() {
  const select = byId('department-filter'); const selected = select.value;
  select.innerHTML = '<option value="">All departments</option>' + state.departments.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join('');
  if (state.departments.includes(selected)) select.value = selected;
}
function renderDirectory() {
  const hasFilters = byId('search-input').value.trim() || byId('department-filter').value || byId('status-filter').value;
  const empty = state.employees.length === 0;
  byId('empty-state').hidden = !empty || Boolean(hasFilters);
  byId('no-results-state').hidden = !empty || !hasFilters;
  byId('result-count').textContent = `${state.employees.length} ${state.employees.length === 1 ? 'person' : 'people'}`;
  byId('table-footer-label').textContent = `Showing ${state.employees.length} ${state.employees.length === 1 ? 'employee' : 'employees'}`;
  employeeRows.innerHTML = state.employees.map((employee) => {
    const tone = employee.status.toLowerCase().replaceAll(' ', '-');
    return `<tr><td><div class="employee-cell"><span class="avatar" aria-hidden="true">${escapeHtml(initials(employee.name))}</span><span class="employee-info"><strong>${escapeHtml(employee.name)}</strong><small>${escapeHtml(employee.email)}</small></span></div></td><td>${escapeHtml(employee.department)}</td><td class="role-cell">${escapeHtml(employee.title)}</td><td>${dateLabel(employee.start_date)}</td><td><span class="status-badge status-${tone}">${escapeHtml(employee.status)}</span></td><td><span class="row-actions"><button class="row-action" type="button" data-edit="${employee.id}" title="Edit ${escapeHtml(employee.name)}" aria-label="Edit ${escapeHtml(employee.name)}">✎</button><button class="row-action delete" type="button" data-delete="${employee.id}" title="Delete ${escapeHtml(employee.name)}" aria-label="Delete ${escapeHtml(employee.name)}">×</button></span></td></tr>`;
  }).join('');
}
function openDialog(employee = null) {
  state.editingId = employee?.id ?? null; form.reset();
  byId('dialog-title').textContent = employee ? 'Edit employee' : 'Add employee';
  byId('save-button').textContent = employee ? 'Save changes' : 'Save employee';
  if (employee) {
    for (const [key, value] of Object.entries(employee)) {
      if (form.elements.namedItem(key)) form.elements.namedItem(key).value = value;
    }
  } else {
    form.elements.namedItem('status').value = 'Active';
  }
  dialog.showModal(); form.elements.namedItem('name').focus();
}
async function saveEmployee(event) {
  event.preventDefault(); const button = byId('save-button'); button.disabled = true;
  const values = Object.fromEntries(new FormData(form)); values.salary = Number(values.salary);
  try {
    await api(state.editingId ? `/api/employees/${state.editingId}` : '/api/employees', { method: state.editingId ? 'PUT' : 'POST', body: JSON.stringify(values) });
    dialog.close(); showToast(state.editingId ? 'Employee updated.' : 'Employee added.'); await refreshDirectory();
  } catch (error) { showToast(error.message); }
  finally { button.disabled = false; }
}
async function deleteEmployee(id) {
  const employee = state.employees.find((person) => person.id === Number(id));
  if (!employee || !window.confirm(`Remove ${employee.name} from the directory? This cannot be undone.`)) return;
  try { await api(`/api/employees/${id}`, { method: 'DELETE' }); showToast('Employee removed.'); await refreshDirectory(); }
  catch (error) { showToast(error.message); }
}
function exportCsv() {
  if (!state.employees.length) return showToast('There are no employees to export.');
  const columns = ['name', 'email', 'phone', 'department', 'title', 'start_date', 'salary', 'status'];
  const cell = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`;
  const csv = [columns.join(','), ...state.employees.map((person) => columns.map((key) => cell(person[key])).join(','))].join('\r\n');
  const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  link.download = `employee-directory-${new Date().toISOString().slice(0, 10)}.csv`; link.click(); URL.revokeObjectURL(link.href);
}
function appendMessage(text, kind = '') {
  const bubble = document.createElement('div'); bubble.className = `chat-message ${kind}`.trim(); bubble.textContent = text;
  byId('chat-messages').append(bubble); bubble.scrollIntoView({ block: 'nearest' }); return bubble;
}
async function sendMessage(text) {
  if (!text || state.busy) return;
  state.busy = true; byId('chat-send').disabled = true; byId('suggestions').hidden = true;
  appendMessage(text, 'user'); const pending = appendMessage('Routing to the right agent…');
  try {
    const data = await api('/api/assistant', { method: 'POST', body: JSON.stringify({ message: text, history: state.history }) });
    pending.textContent = data.answer; pending.dataset.agent = `${data.agent} agent`;
    state.history.push({ role: 'user', content: text }, { role: 'model', content: data.answer.slice(0, 3000) }); state.history = state.history.slice(-12);
  } catch (error) { pending.textContent = error.message; pending.classList.add('error'); }
  finally { state.busy = false; byId('chat-send').disabled = false; byId('chat-input').focus(); }
}
byId('today-label').textContent = new Intl.DateTimeFormat(undefined, { weekday: 'short', month: 'short', day: 'numeric' }).format(new Date());
let searchTimer;
byId('search-input').addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(refreshDirectory, 180); });
byId('department-filter').addEventListener('change', refreshDirectory);
byId('status-filter').addEventListener('change', refreshDirectory);
byId('refresh-button').addEventListener('click', refreshDirectory);
byId('add-button').addEventListener('click', () => openDialog());
byId('empty-add-button').addEventListener('click', () => openDialog());
byId('export-button').addEventListener('click', exportCsv);
byId('clear-filters-button').addEventListener('click', () => { byId('search-input').value = ''; byId('department-filter').value = ''; byId('status-filter').value = ''; refreshDirectory(); });
byId('employee-form').addEventListener('submit', saveEmployee);
byId('employee-rows').addEventListener('click', (event) => {
  const edit = event.target.closest('[data-edit]'); const remove = event.target.closest('[data-delete]');
  if (edit) openDialog(state.employees.find((person) => person.id === Number(edit.dataset.edit)));
  if (remove) deleteEmployee(remove.dataset.delete);
});
document.querySelectorAll('.dialog-close, .dialog-cancel').forEach((button) => button.addEventListener('click', () => dialog.close()));
dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
byId('chat-form').addEventListener('submit', (event) => { event.preventDefault(); const input = byId('chat-input'); const text = input.value.trim(); input.value = ''; sendMessage(text); });
byId('chat-input').addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); byId('chat-form').requestSubmit(); } });
document.querySelectorAll('[data-prompt]').forEach((button) => button.addEventListener('click', () => sendMessage(button.dataset.prompt)));
document.addEventListener('keydown', (event) => { if (event.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) { event.preventDefault(); byId('search-input').focus(); } });
refreshDirectory();
