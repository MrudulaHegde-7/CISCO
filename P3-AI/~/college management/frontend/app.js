const state = {
  departments: [],
  authUser: null,
  chatHistory: [],
  chatDocuments: [],
  chatBusy: false,
  studentSearchTimer: null,
  departmentSearchTimer: null,
  toastTimer: null,
};

const $ = (selector) => document.querySelector(selector);

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  if (response.status === 204) return null;

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const fieldErrors = Array.isArray(data.errors)
      ? data.errors.map((error) => `${error.field}: ${error.message}`).join("; ")
      : "";
    const detail = Array.isArray(data.detail) ? "Invalid request data" : data.detail;
    throw new Error(fieldErrors || detail || "The request could not be completed.");
  }
  return data;
}

function showToast(message, isError = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.hidden = false;
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => { toast.hidden = true; }, 3500);
}

function showError(selector, message) {
  const notice = $(selector);
  notice.textContent = message;
  notice.hidden = false;
}

function clearError(selector) {
  $(selector).hidden = true;
}

function setAuthMode(mode) {
  const isSignup = mode === "signup";
  $("#login-tab").setAttribute("aria-selected", String(!isSignup));
  $("#signup-tab").setAttribute("aria-selected", String(isSignup));
  $("#login-form").hidden = isSignup;
  $("#signup-form").hidden = !isSignup;
  $("#auth-title").textContent = isSignup ? "Create your account" : "Welcome back";
  $("#auth-subtitle").textContent = isSignup
    ? "Set up an account to manage your college directory."
    : "Sign in to continue to your directory.";
  clearError("#auth-error");
}

function showAuth(mode = "login", errorMessage = "") {
  $("#app-shell").hidden = true;
  $("#auth-screen").hidden = false;
  setAuthMode(mode);
  if (errorMessage) showError("#auth-error", errorMessage);
}

function showAuthenticatedApp(user) {
  state.authUser = user;
  $("#account-name").textContent = user.full_name;
  $("#auth-screen").hidden = true;
  $("#app-shell").hidden = false;
  Promise.all([loadDashboard(), loadDepartments(), loadStudents(), loadChatDocuments()]);
}

async function submitAuthForm(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const isSignup = form.id === "signup-form";
  try {
    const result = await apiRequest(isSignup ? "/api/auth/signup" : "/api/auth/login", {
      method: "POST",
      body: JSON.stringify(formValues(form)),
    });
    form.reset();
    showAuthenticatedApp(result.user);
  } catch (error) {
    showError("#auth-error", error.message);
  }
}

async function signOut() {
  try {
    await apiRequest("/api/auth/logout", { method: "POST" });
  } catch (error) {
    showToast(error.message, true);
  }
  state.authUser = null;
  state.chatHistory = [];
  state.chatDocuments = [];
  state.chatBusy = false;
  $("#chat-messages").replaceChildren();
  appendChatMessage("Hello. Ask about college records or information in your uploaded files.");
  renderChatDocuments();
  setChatOpen(false);
  showAuth("login");
}

function setChatOpen(open) {
  $("#chat-panel").hidden = !open;
  $("#chat-launcher").setAttribute("aria-expanded", String(open));
  if (open) $("#chat-question").focus();
}

function appendChatMessage(text, role = "assistant-message") {
  const message = document.createElement("p");
  message.className = `chat-message ${role}`;
  message.textContent = text;
  $("#chat-messages").append(message);
  $("#chat-messages").scrollTop = $("#chat-messages").scrollHeight;
  return message;
}

function renderChatDocuments() {
  const list = $("#chat-documents");
  list.replaceChildren();
  if (!state.chatDocuments.length) {
    const empty = document.createElement("li");
    empty.className = "chat-documents-empty";
    empty.textContent = "No files uploaded";
    list.append(empty);
    return;
  }

  state.chatDocuments.forEach((file) => {
    const item = document.createElement("li");
    item.className = "chat-document";
    const name = document.createElement("span");
    name.textContent = file.file_name;
    name.title = file.file_name;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "chat-document-remove";
    remove.dataset.documentId = file.id;
    remove.setAttribute("aria-label", `Remove ${file.file_name}`);
    remove.title = `Remove ${file.file_name}`;
    remove.textContent = "×";
    item.append(name, remove);
    list.append(item);
  });
}

async function loadChatDocuments() {
  try {
    const data = await apiRequest("/api/chat/documents");
    state.chatDocuments = data.documents;
    renderChatDocuments();
  } catch (error) {
    $("#chat-file-status").textContent = error.message;
  }
}

async function uploadChatDocument(event) {
  const input = event.currentTarget;
  const file = input.files?.[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);
  input.disabled = true;
  $("#chat-file-status").textContent = `Uploading ${file.name}…`;
  try {
    const result = await apiRequest("/api/chat/documents", {
      method: "POST",
      body: formData,
    });
    state.chatDocuments.unshift(result.document);
    renderChatDocuments();
    $("#chat-file-status").textContent = `${file.name} is ready for questions.`;
    appendChatMessage(`I’ve added ${file.name}. What would you like to know about it?`);
    $("#chat-question").focus();
  } catch (error) {
    $("#chat-file-status").textContent = error.message;
    const message = appendChatMessage(`I couldn’t add ${file.name}: ${error.message}`);
    message.classList.add("chat-error");
  } finally {
    input.value = "";
    input.disabled = false;
  }
}

async function removeChatDocument(documentId, button) {
  button.disabled = true;
  try {
    await apiRequest(`/api/chat/documents/${documentId}`, { method: "DELETE" });
    state.chatDocuments = state.chatDocuments.filter((file) => String(file.id) !== documentId);
    renderChatDocuments();
    $("#chat-file-status").textContent = "File removed.";
  } catch (error) {
    button.disabled = false;
    $("#chat-file-status").textContent = error.message;
  }
}

async function submitChatMessage(event) {
  event.preventDefault();
  const input = $("#chat-question");
  const question = input.value.trim();
  if (!question || state.chatBusy) return;

  state.chatBusy = true;
  $("#chat-send").disabled = true;
  input.value = "";
  appendChatMessage(question, "user-message");
  const pendingMessage = appendChatMessage("Thinking…");

  try {
    const result = await apiRequest("/api/chat", {
      method: "POST",
      body: JSON.stringify({ question, history: state.chatHistory }),
    });
    pendingMessage.textContent = result.answer;
    state.chatHistory.push(
      { role: "user", content: question },
      { role: "model", content: result.answer.slice(0, 1500) },
    );
    state.chatHistory = state.chatHistory.slice(-12);
  } catch (error) {
    pendingMessage.textContent = error.message;
    pendingMessage.classList.add("chat-error");
    input.value = question;
  } finally {
    state.chatBusy = false;
    $("#chat-send").disabled = false;
    $("#chat-messages").scrollTop = $("#chat-messages").scrollHeight;
    if (!$("#chat-panel").hidden) input.focus();
  }
}

async function loadDashboard() {
  try {
    const data = await apiRequest("/api/dashboard");
    $("#student-total").textContent = data.student_count;
    $("#department-total").textContent = data.department_count;
    $("#student-tab-count").textContent = data.student_count;
    $("#department-tab-count").textContent = data.department_count;

    const largest = data.departments[0];
    $("#largest-department").textContent = largest?.name ?? "—";
    $("#largest-count").textContent = largest
      ? `${largest.student_count} students`
      : "Student enrollment";
  } catch (error) {
    showError("#student-error", error.message);
  }
}

function renderDepartments() {
  const query = $("#department-search").value.trim().toLowerCase();
  const departments = state.departments.filter((department) =>
    [department.name, department.code, department.head]
      .some((value) => String(value ?? "").toLowerCase().includes(query))
  );

  $("#department-rows").innerHTML = departments.length
    ? departments.map((department) => `
      <tr>
        <td><span class="name">${escapeHtml(department.name)}</span><span class="subtext">${escapeHtml(department.code)}</span></td>
        <td>${escapeHtml(department.building || "—")}</td>
        <td>${escapeHtml(department.head || "—")}</td>
        <td>${department.student_count}</td>
        <td><div class="actions">
          <button class="button secondary small" data-edit-department="${department.id}" aria-label="Edit ${escapeHtml(department.name)}">Edit</button>
          <button class="button danger small" data-delete-department="${department.id}" aria-label="Delete ${escapeHtml(department.name)}">Delete</button>
        </div></td>
      </tr>`).join("")
    : `<tr><td class="empty" colspan="5"><strong>No departments found</strong>Add a department or adjust your search.</td></tr>`;
}

async function loadDepartments() {
  clearError("#department-error");
  try {
    state.departments = await apiRequest("/api/departments");
    const options = state.departments.map((department) =>
      `<option value="${department.id}">${escapeHtml(department.code)} · ${escapeHtml(department.name)}</option>`
    ).join("");

    $("#department-filter").innerHTML = '<option value="">All departments</option>' + options;
    $("#student-department").innerHTML = state.departments.length
      ? '<option value="">Select a department</option>' + options
      : '<option value="" selected disabled>No departments available</option>';
    $("#department-empty-help").hidden = state.departments.length > 0;
    $("#department-tab-count").textContent = state.departments.length;
    renderDepartments();
  } catch (error) {
    $("#student-department").innerHTML = '<option value="" selected disabled>Departments could not be loaded</option>';
    $("#department-empty-help").hidden = true;
    showError("#department-error", error.message);
  }
}

async function loadStudents() {
  clearError("#student-error");
  const params = new URLSearchParams();
  const search = $("#student-search").value.trim();
  const departmentId = $("#department-filter").value;
  if (search) params.set("search", search);
  if (departmentId) params.set("department_id", departmentId);

  try {
    const students = await apiRequest(`/api/students?${params}`);
    $("#student-rows").innerHTML = students.length
      ? students.map((student) => `
        <tr>
          <td><span class="name">${escapeHtml(student.full_name)}</span><span class="subtext">Student #${student.id}</span></td>
          <td>${escapeHtml(student.email)}<span class="subtext">${escapeHtml(student.phone || "No phone provided")}</span></td>
          <td><span class="tag">${escapeHtml(student.department_code)}</span><span class="subtext">${escapeHtml(student.department_name)}</span></td>
          <td>${student.enrollment_year}</td>
          <td><div class="actions">
            <button class="button secondary small" data-edit-student="${student.id}" aria-label="Edit ${escapeHtml(student.full_name)}">Edit</button>
            <button class="button danger small" data-delete-student="${student.id}" aria-label="Delete ${escapeHtml(student.full_name)}">Delete</button>
          </div></td>
        </tr>`).join("")
      : `<tr><td class="empty" colspan="5"><strong>No students found</strong>Add a student or adjust your search.</td></tr>`;
  } catch (error) {
    showError("#student-error", error.message);
  }
}

function openModal(selector) {
  const modal = $(selector);
  modal.hidden = false;
  modal.querySelector("input:not([type=hidden]), select").focus();
}

function closeModal(selector) {
  $(selector).hidden = true;
}

function resetStudentForm() {
  const form = $("#student-form");
  form.reset();
  form.elements.id.value = "";
  form.elements.enrollment_year.value = new Date().getFullYear();
  updatePhoneValidity();
  $("#student-dialog-title").textContent = "Add student";
}

function resetDepartmentForm() {
  const form = $("#department-form");
  form.reset();
  form.elements.id.value = "";
  $("#department-dialog-title").textContent = "Add department";
}

function setTab(activeTab) {
  const showStudents = activeTab === "students";
  $("#students-tab").setAttribute("aria-selected", String(showStudents));
  $("#departments-tab").setAttribute("aria-selected", String(!showStudents));
  $("#students-view").hidden = !showStudents;
  $("#departments-view").hidden = showStudents;
}

function formValues(form) {
  return Object.fromEntries(new FormData(form));
}

function fillForm(form, record) {
  for (const [key, value] of Object.entries(record)) {
    if (form.elements[key]) form.elements[key].value = value ?? "";
  }
}

function updatePhoneValidity() {
  const phoneInput = $("#student-phone");
  const phone = phoneInput.value.trim();
  const digitCount = phone.replace(/\D/g, "").length;
  const validFormat = /^\+?(?:\([0-9]{1,5}\)|[0-9])[0-9\s().-]*$/.test(phone);

  if (!phone) {
    phoneInput.setCustomValidity("");
  } else if (!validFormat) {
    phoneInput.setCustomValidity("Use only digits, spaces, parentheses, periods, +, or hyphens.");
  } else if (digitCount !== 10) {
    phoneInput.setCustomValidity("Phone number must contain exactly 10 digits.");
  } else {
    phoneInput.setCustomValidity("");
  }
}

async function saveStudent(event) {
  event.preventDefault();
  const form = event.currentTarget;
  updatePhoneValidity();
  if (!form.reportValidity()) return;

  const id = form.elements.id.value;
  const payload = formValues(form);
  payload.department_id = Number(payload.department_id);
  payload.enrollment_year = Number(payload.enrollment_year);

  try {
    await apiRequest(id ? `/api/students/${id}` : "/api/students", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    closeModal("#student-modal");
    showToast(id ? "Student record updated." : "Student added.");
    await Promise.all([loadStudents(), loadDepartments(), loadDashboard()]);
  } catch (error) {
    showToast(error.message, true);
  }
}

async function saveDepartment(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const id = form.elements.id.value;

  try {
    await apiRequest(id ? `/api/departments/${id}` : "/api/departments", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(formValues(form)),
    });
    closeModal("#department-modal");
    showToast(id ? "Department updated." : "Department added.");
    await Promise.all([loadDepartments(), loadStudents(), loadDashboard()]);
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleStudentAction(event) {
  const editButton = event.target.closest("[data-edit-student]");
  const deleteButton = event.target.closest("[data-delete-student]");

  if (editButton) {
    try {
      const student = await apiRequest(`/api/students/${editButton.dataset.editStudent}`);
      resetStudentForm();
      fillForm($("#student-form"), student);
      updatePhoneValidity();
      $("#student-dialog-title").textContent = "Edit student";
      openModal("#student-modal");
    } catch (error) {
      showToast(error.message, true);
    }
  }

  if (deleteButton && confirm("Delete this student record?")) {
    try {
      await apiRequest(`/api/students/${deleteButton.dataset.deleteStudent}`, { method: "DELETE" });
      showToast("Student deleted.");
      await Promise.all([loadStudents(), loadDepartments(), loadDashboard()]);
    } catch (error) {
      showToast(error.message, true);
    }
  }
}

async function handleDepartmentAction(event) {
  const editButton = event.target.closest("[data-edit-department]");
  const deleteButton = event.target.closest("[data-delete-department]");

  if (editButton) {
    try {
      const department = await apiRequest(`/api/departments/${editButton.dataset.editDepartment}`);
      resetDepartmentForm();
      fillForm($("#department-form"), department);
      $("#department-dialog-title").textContent = "Edit department";
      openModal("#department-modal");
    } catch (error) {
      showToast(error.message, true);
    }
  }

  if (deleteButton && confirm("Delete this department? Departments with students cannot be deleted.")) {
    try {
      await apiRequest(`/api/departments/${deleteButton.dataset.deleteDepartment}`, { method: "DELETE" });
      showToast("Department deleted.");
      await Promise.all([loadDepartments(), loadStudents(), loadDashboard()]);
    } catch (error) {
      showToast(error.message, true);
    }
  }
}

function bindEvents() {
  $("#login-tab").addEventListener("click", () => setAuthMode("login"));
  $("#signup-tab").addEventListener("click", () => setAuthMode("signup"));
  $("#login-form").addEventListener("submit", submitAuthForm);
  $("#signup-form").addEventListener("submit", submitAuthForm);
  $("#logout").addEventListener("click", signOut);
  $("#chat-launcher").addEventListener("click", () => setChatOpen(true));
  $("#chat-close").addEventListener("click", () => setChatOpen(false));
  $("#chat-form").addEventListener("submit", submitChatMessage);
  $("#chat-file").addEventListener("change", uploadChatDocument);
  $("#chat-documents").addEventListener("click", (event) => {
    const button = event.target.closest("[data-document-id]");
    if (button) removeChatDocument(button.dataset.documentId, button);
  });
  $("#students-tab").addEventListener("click", () => setTab("students"));
  $("#departments-tab").addEventListener("click", () => setTab("departments"));
  $("#student-search").addEventListener("input", () => {
    clearTimeout(state.studentSearchTimer);
    state.studentSearchTimer = setTimeout(loadStudents, 180);
  });
  $("#department-filter").addEventListener("change", loadStudents);
  $("#department-search").addEventListener("input", () => {
    clearTimeout(state.departmentSearchTimer);
    state.departmentSearchTimer = setTimeout(renderDepartments, 180);
  });
  $("#add-student").addEventListener("click", () => {
    resetStudentForm();
    openModal("#student-modal");
  });
  $("#add-department").addEventListener("click", () => {
    resetDepartmentForm();
    openModal("#department-modal");
  });
  $("#create-department-from-student").addEventListener("click", () => {
    closeModal("#student-modal");
    setTab("departments");
    resetDepartmentForm();
    openModal("#department-modal");
  });
  $("#student-form").addEventListener("submit", saveStudent);
  $("#student-phone").addEventListener("input", updatePhoneValidity);
  $("#department-form").addEventListener("submit", saveDepartment);
  $("#student-rows").addEventListener("click", handleStudentAction);
  $("#department-rows").addEventListener("click", handleDepartmentAction);

  document.querySelectorAll("[data-close]").forEach((button) => {
    button.addEventListener("click", () => {
      closeModal("#student-modal");
      closeModal("#department-modal");
    });
  });
  document.querySelectorAll(".overlay").forEach((overlay) => {
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) closeModal(`#${overlay.id}`);
    });
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeModal("#student-modal");
      closeModal("#department-modal");
    }
  });
}

function initializePage() {
  $("#today").textContent = new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "long",
  }).format(new Date());
  $("#student-year").value = new Date().getFullYear();
  bindEvents();
  apiRequest("/api/auth/me")
    .then(({ user }) => showAuthenticatedApp(user))
    .catch(() => showAuth("login"));
}

document.addEventListener("DOMContentLoaded", initializePage);
