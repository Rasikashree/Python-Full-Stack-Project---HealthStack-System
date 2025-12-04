<!-- Add this section in the appropriate place in your HTML -->
<div id="symptom-checker" style="display:none;">
  <h3>Symptom Checker</h3>
  <div id="symptom-categories"></div>
  <div id="selected-symptoms"></div>
  <button id="submit-symptoms">Find Doctors</button>
</div>

<script>
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
    // Add more categories as needed
  ];

  let selectedSymptoms = [];

  function renderSymptomCategories() {
    const container = document.getElementById('symptom-categories');
    container.innerHTML = SYMPTOM_CATEGORIES.map(category => `
      <div>
        <h4>${category.name}</h4>
        ${category.symptoms.map(symptom => `
          <button class="symptom-btn" data-symptom="${symptom.code}">${symptom.name}</button>
        `).join('')}
      </div>
    `).join('');
  }

  function toggleSymptom(symptomCode) {
    const index = selectedSymptoms.indexOf(symptomCode);
    if (index === -1) {
      selectedSymptoms.push(symptomCode);
    } else {
      selectedSymptoms.splice(index, 1);
    }
    document.getElementById('selected-symptoms').innerText = `Selected Symptoms: ${selectedSymptoms.join(', ')}`;
  }

  document.getElementById('symptom-categories').addEventListener('click', e => {
    if (e.target.classList.contains('symptom-btn')) {
      toggleSymptom(e.target.dataset.symptom);
    }
  });

  document.getElementById('submit-symptoms').addEventListener('click', () => {
    if (selectedSymptoms.length === 0) {
      alert('Please select at least one symptom.');
      return;
    }
    fetchDoctorRecommendations(selectedSymptoms);
  });

  function fetchDoctorRecommendations(symptoms) {
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
        renderDoctorRecommendations(data.doctors);
      } else {
        alert('No doctors found for the selected symptoms.');
      }
    })
    .catch(error => {
      console.error('Error fetching doctor recommendations:', error);
    });
  }

  function renderDoctorRecommendations(doctors) {
    const recommendationsContainer = document.getElementById('doctor-recommendations');
    recommendationsContainer.innerHTML = doctors.map(doctor => `
      <div>
        <h5>${doctor.name} (${doctor.department_name})</h5>
        <button onclick="bookAppointment('${doctor.id}')">Book Appointment</button>
      </div>
    `).join('');
  }

  function bookAppointment(doctorId) {
    // Implement the booking logic here
  }

  // Initialize the symptom checker
  renderSymptomCategories();
</script>