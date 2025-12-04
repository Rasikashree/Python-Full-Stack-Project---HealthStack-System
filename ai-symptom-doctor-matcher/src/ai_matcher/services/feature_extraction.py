// Symptom categories and their respective symptoms
const SYMPTOM_CATEGORIES = [
  { id: 'general', name: 'General', symptoms: [
    { code: 'fever', name: 'Fever' },
    { code: 'fatigue', name: 'Fatigue' },
    { code: 'headache', name: 'Headache' },
    { code: 'nausea', name: 'Nausea' }
  ]},
  { id: 'resp', name: 'Respiratory', symptoms: [
    { code: 'cough', name: 'Cough' },
    { code: 'shortness of breath', name: 'Shortness of Breath' },
    { code: 'chest pain', name: 'Chest Pain' }
  ]},
  { id: 'neuro', name: 'Neurological', symptoms: [
    { code: 'dizziness', name: 'Dizziness' },
    { code: 'memory issues', name: 'Memory Issues' }
  ]},
  { id: 'derm', name: 'Dermatology', symptoms: [
    { code: 'rash', name: 'Rash' },
    { code: 'itching', name: 'Itching' }
  ]}
];

// State to keep track of selected symptoms
let state = {
  symptomsChosen: []
};

// Function to start the symptom checker
function startSymptomChecker() {
  state.symptomsChosen = [];
  appendMessage('bot', 'Select a category:');
  chatOptions.innerHTML = SYMPTOM_CATEGORIES.map(c =>
    `<button class="chat-option-btn" data-action="symptom-category" data-cat-id="${escapeHtml(c.id)}">${escapeHtml(c.name)}</button>`
  ).join('') + `<button class="chat-option-btn" data-action="option" data-value="Main Menu">Main Menu</button>`;
}

// Function to load symptoms for the selected category
function loadCategorySymptoms(catId) {
  const cat = SYMPTOM_CATEGORIES.find(c => c.id === catId);
  if (!cat) {
    appendMessage('bot', 'Category not found.');
    startSymptomChecker();
    return;
  }
  appendMessage('bot', 'Select symptoms (toggle) then Complete.');
  chatOptions.innerHTML = cat.symptoms.map(s =>
    `<button class="chat-option-btn" data-action="symptom-add" data-symptom="${escapeHtml(s.code)}">${escapeHtml(s.name)}</button>`
  ).join('') +
  `<button class="chat-option-btn" data-action="symptom-complete" style="background:#00cc66;">Complete</button>` +
  `<button class="chat-option-btn" data-action="option" data-value="Main Menu">Main Menu</button>`;
}

// Function to toggle symptoms selection
function toggleSymptom(code, btn) {
  const i = state.symptomsChosen.indexOf(code);
  if (i === -1) {
    state.symptomsChosen.push(code);
    btn.style.opacity = '.55';
  } else {
    state.symptomsChosen.splice(i, 1);
    btn.style.opacity = '1';
  }
}

// Function to finalize symptoms and fetch doctor recommendations
function finalizeSymptomsDynamic() {
  if (state.symptomsChosen.length === 0) {
    appendMessage('bot', 'Select at least one symptom.');
    return;
  }
  appendMessage('bot', 'Selected: ' + state.symptomsChosen.join(', '));
  fetchDoctorRecommendations(state.symptomsChosen);
}

// Function to fetch doctor recommendations based on symptoms
function fetchDoctorRecommendations(symptoms) {
  appendMessage('bot', 'Matching doctors...');
  const csrftoken = getCookie('csrftoken');
  fetch('/ai/doctor-matching/', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
    body: JSON.stringify({ symptoms })
  })
  .then(r => r.ok ? r.json() : r.json().then(j => Promise.reject(j)))
  .then(list => {
    if (Array.isArray(list) && list.length) {
      renderDoctorButtons(list);
    } else {
      appendMessage('bot', 'No direct matches from AI. You can still book a general checkup.');
      showOptions(['Book Appointment', 'Symptom Checker', 'Main Menu']);
    }
  })
  .catch(() => {
    appendMessage('bot', 'AI endpoint failed. You can still book a general checkup.');
    showOptions(['Book Appointment', 'Symptom Checker', 'Main Menu']);
  });
}

// Function to render doctor buttons based on recommendations
function renderDoctorButtons(list) {
  appendMessage('bot', 'Recommended doctors:');
  chatOptions.innerHTML = list.map(d => {
    const id = d.id || d.doctor_id;
    const name = d.name || 'Doctor';
    const dept = d.department_name || '';
    return `<button class="chat-option-btn" data-action="select-doctor" data-doctor-id="${id}" data-doctor-name="${escapeHtml(name)}">${escapeHtml(name)}<br/><small>${escapeHtml(dept)}</small></button>`;
  }).join('') + `<button class="chat-option-btn" data-action="option" data-value="Main Menu">Main Menu</button>`;
}