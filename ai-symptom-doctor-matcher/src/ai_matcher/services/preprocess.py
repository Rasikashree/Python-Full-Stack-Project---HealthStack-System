// AI Symptom Checker Implementation
(function(){
  const aiFaceBtn = document.getElementById('ai-face-btn');
  const chatbotModal = document.getElementById('ai-chatbot-modal');
  const chatMessages = document.getElementById('chat-messages');
  const chatOptions = document.getElementById('chat-options');

  if(aiFaceBtn){
    aiFaceBtn.addEventListener('click', () => {
      chatbotModal.style.display = 'block';
      appendMessage('bot', "Hello! I'm your HealthStack assistant. How can I help?");
      showOptions(['Symptom Checker', 'Book Appointment', 'View Doctor List']);
    });
  }

  function appendMessage(sender, text) {
    const div = document.createElement('div');
    div.className = `chat-message ${sender}`;
    div.innerHTML = `<div class="message-bubble ${sender}"><div class="message-content">${escapeHtml(text)}</div></div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function showOptions(options) {
    chatOptions.innerHTML = options.map(option => 
      `<button class="chat-option-btn" data-action="option" data-value="${escapeHtml(option)}">${escapeHtml(option)}</button>`
    ).join('');
  }

  chatOptions.addEventListener('click', e => {
    const btn = e.target.closest('.chat-option-btn');
    if (!btn) return;

    const value = btn.dataset.value.toLowerCase();
    if (value === 'symptom checker') {
      startSymptomChecker();
    }
  });

  function startSymptomChecker() {
    appendMessage('bot', 'Select a category:');
    const SYMPTOM_CATEGORIES = [
      { id: 'general', name: 'General', symptoms: ['fever', 'fatigue', 'headache', 'nausea'] },
      { id: 'resp', name: 'Respiratory', symptoms: ['cough', 'shortness of breath', 'chest pain'] },
      { id: 'neuro', name: 'Neurological', symptoms: ['dizziness', 'memory issues'] },
      { id: 'derm', name: 'Dermatology', symptoms: ['rash', 'itching'] }
    ];

    chatOptions.innerHTML = SYMPTOM_CATEGORIES.map(category => 
      `<button class="chat-option-btn" data-action="symptom-category" data-cat-id="${category.id}">${category.name}</button>`
    ).join('');
  }

  chatOptions.addEventListener('click', e => {
    const btn = e.target.closest('.chat-option-btn');
    if (!btn) return;

    const action = btn.dataset.action;
    if (action === 'symptom-category') {
      const categoryId = btn.dataset.catId;
      loadCategorySymptoms(categoryId);
    }
  });

  function loadCategorySymptoms(catId) {
    const symptoms = {
      general: ['fever', 'fatigue', 'headache', 'nausea'],
      resp: ['cough', 'shortness of breath', 'chest pain'],
      neuro: ['dizziness', 'memory issues'],
      derm: ['rash', 'itching']
    };

    appendMessage('bot', 'Select symptoms (toggle) then Complete.');
    chatOptions.innerHTML = symptoms[catId].map(symptom => 
      `<button class="chat-option-btn" data-action="symptom-add" data-symptom="${symptom}">${symptom}</button>`
    ).join('') + 
    `<button class="chat-option-btn" data-action="symptom-complete">Complete</button>`;
  }

  chatOptions.addEventListener('click', e => {
    const btn = e.target.closest('.chat-option-btn');
    if (!btn) return;

    const action = btn.dataset.action;
    if (action === 'symptom-add') {
      toggleSymptom(btn.dataset.symptom, btn);
    } else if (action === 'symptom-complete') {
      finalizeSymptoms();
    }
  });

  let selectedSymptoms = [];

  function toggleSymptom(symptom, btn) {
    const index = selectedSymptoms.indexOf(symptom);
    if (index === -1) {
      selectedSymptoms.push(symptom);
      btn.style.opacity = '0.5';
    } else {
      selectedSymptoms.splice(index, 1);
      btn.style.opacity = '1';
    }
  }

  function finalizeSymptoms() {
    if (selectedSymptoms.length === 0) {
      appendMessage('bot', 'Please select at least one symptom.');
      return;
    }

    appendMessage('bot', 'Selected symptoms: ' + selectedSymptoms.join(', '));
    fetchDoctorRecommendations(selectedSymptoms);
  }

  function fetchDoctorRecommendations(symptoms) {
    appendMessage('bot', 'Finding doctors for your symptoms...');
    const csrftoken = getCookie('csrftoken');

    fetch('/ai/doctor-matching/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({ symptoms })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        renderDoctorButtons(data.doctors);
      } else {
        appendMessage('bot', 'No doctors found for your symptoms.');
      }
    })
    .catch(error => {
      appendMessage('bot', 'Error fetching doctors: ' + error.message);
    });
  }

  function renderDoctorButtons(doctors) {
    appendMessage('bot', 'Recommended doctors:');
    chatOptions.innerHTML = doctors.map(doctor => 
      `<button class="chat-option-btn" data-action="select-doctor" data-doctor-id="${doctor.id}">${doctor.name}</button>`
    ).join('');
  }

  chatOptions.addEventListener('click', e => {
    const btn = e.target.closest('.chat-option-btn');
    if (!btn) return;

    if (btn.dataset.action === 'select-doctor') {
      const doctorId = btn.dataset.doctorId;
      bookAppointment(doctorId);
    }
  });

  function bookAppointment(doctorId) {
    appendMessage('bot', 'Booking appointment with doctor ID: ' + doctorId);
    // Implement the booking logic here
  }

  function escapeHtml(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function getCookie(name) {
    let value = `; ${document.cookie}`;
    let parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }
})();