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
    .then(response => response.ok ? response.json() : Promise.reject(response))
    .then(data => {
        if (Array.isArray(data) && data.length) {
            renderDoctorButtons(data);
        } else {
            appendMessage('bot', 'No matching doctors found. Please try again.');
            showOptions(['Book Appointment', 'Symptom Checker', 'Main Menu']);
        }
    })
    .catch(error => {
        appendMessage('bot', 'Error fetching doctors: ' + error.message);
        showOptions(['Book Appointment', 'Symptom Checker', 'Main Menu']);
    });
}

// Function to render doctor buttons
function renderDoctorButtons(doctors) {
    appendMessage('bot', 'Recommended doctors:');
    chatOptions.innerHTML = doctors.map(doctor => {
        return `<button class="chat-option-btn" data-action="select-doctor" data-doctor-id="${doctor.id}" data-doctor-name="${escapeHtml(doctor.name)}">
                    ${escapeHtml(doctor.name)}<br/><small>${escapeHtml(doctor.department_name)}</small>
                </button>`;
    }).join('') + `<button class="chat-option-btn" data-action="option" data-value="Main Menu">Main Menu</button>`;
}

// Function to start the symptom checker
function startSymptomChecker() {
    state.symptomsChosen = [];
    state.symptomCategory = null;
    appendMessage('bot', 'Select a category:');
    chatOptions.innerHTML = SYMPTOM_CATEGORIES.map(category =>
        `<button class="chat-option-btn" data-action="symptom-category" data-cat-id="${escapeHtml(category.id)}">${escapeHtml(category.name)}</button>`
    ).join('') + `<button class="chat-option-btn" data-action="option" data-value="Main Menu">Main Menu</button>`;
}

// Function to load symptoms based on selected category
function loadCategorySymptoms(catId) {
    const category = SYMPTOM_CATEGORIES.find(c => c.id === catId);
    if (!category) {
        appendMessage('bot', 'Category not found.');
        startSymptomChecker();
        return;
    }
    appendMessage('bot', 'Select symptoms (toggle) then Complete.');
    chatOptions.innerHTML = category.symptoms.map(symptom =>
        `<button class="chat-option-btn" data-action="symptom-add" data-symptom="${escapeHtml(symptom.code)}">${escapeHtml(symptom.name)}</button>`
    ).join('') +
    `<button class="chat-option-btn" data-action="symptom-complete" style="background:#00cc66;">Complete</button>` +
    `<button class="chat-option-btn" data-action="option" data-value="Main Menu">Main Menu</button>`;
}

// Function to finalize symptoms and fetch recommendations
function finalizeSymptomsDynamic() {
    if (state.symptomsChosen.length === 0) {
        appendMessage('bot', 'Select at least one symptom.');
        return;
    }
    appendMessage('bot', 'Selected: ' + state.symptomsChosen.join(', '));
    fetchDoctorRecommendations(state.symptomsChosen);
}