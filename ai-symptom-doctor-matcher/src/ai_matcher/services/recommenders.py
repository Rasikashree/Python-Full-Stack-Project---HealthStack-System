from collections import Counter
import re

_token = re.compile(r"[A-Za-z]+")

def _tokens(t: str) -> set[str]:
    return set(w.lower() for w in _token.findall(t or ""))

def _dept_score(dept: str, specialties: list[str], weights: Counter) -> float:
    if not dept:
        return 0.0
    d = dept.lower()
    dt = _tokens(d)
    s = 0.0
    for sp in specialties:
        base = float(weights.get(sp, 1))
        if d == sp.lower():
            s += base * 3
        elif sp.lower() in d:
            s += base * 1
        elif dt & _tokens(sp):
            s += base * 0.5
    return s

def recommend_doctors(symptoms: list[str], limit: int = 10) -> list[dict]:
    from ai_matcher.services.inference import predict_symptoms
    try:
        from doctor.models import Doctor  # your existing app model
    except Exception:
        return []

    result = predict_symptoms(symptoms)
    specs = result.get("predicted_specialties") or []
    if not specs:
        return []

    weights = Counter(specs)
    out = []
    for d in Doctor.objects.all():
        dept = getattr(d, "department_name", "") or ""
        score = _dept_score(dept, specs, weights)
        if score > 0:
            out.append({
                "id": d.id,
                "name": getattr(d, "name", getattr(d, "full_name", "Doctor")),
                "department_name": dept,
                "score": float(score),
            })
    out.sort(key=lambda x: (-x["score"], x["name"]))
    return out[:limit]

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
        appendMessage('bot', 'AI endpoint failed. Please try again later.');
        showOptions(['Symptom Checker', 'Main Menu']);
    });
}

function renderDoctorButtons(list) {
    appendMessage('bot', 'Recommended doctors:');
    chatOptions.innerHTML = list.map(d => {
        const id = d.id || d.doctor_id;
        const name = d.name || 'Doctor';
        const dept = d.department_name || '';
        return `<button class="chat-option-btn" data-action="select-doctor" data-doctor-id="${id}" data-doctor-name="${escapeHtml(name)}">${escapeHtml(name)}<br/><small>${escapeHtml(dept)}</small></button>`;
    }).join('') + `<button class="chat-option-btn" data-action="option" data-value="Main Menu">Main Menu</button>`;
}