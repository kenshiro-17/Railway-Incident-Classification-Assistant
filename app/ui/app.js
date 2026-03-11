let sessionId = null;

function listInto(el, items) {
  el.innerHTML = '';
  if (!items || !items.length) {
    const li = document.createElement('li');
    li.textContent = 'None';
    el.appendChild(li);
    return;
  }
  items.forEach((item) => {
    const li = document.createElement('li');
    li.textContent = item;
    el.appendChild(li);
  });
}

async function ensureSession(token) {
  if (sessionId) return sessionId;
  const r = await fetch('/chat/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
    body: JSON.stringify({ locale: 'en' }),
  });
  if (!r.ok) throw new Error('Failed to create session');
  const data = await r.json();
  sessionId = data.session_id;
  return sessionId;
}

async function submitIncident() {
  const token = document.getElementById('token').value.trim();
  const sid = await ensureSession(token);
  const payload = {
    session_id: sid,
    clarification_turn: 0,
    user_message: document.getElementById('message').value,
    incident: {
      timestamp: new Date().toISOString(),
      line_or_route: document.getElementById('route').value,
      train_type: document.getElementById('train').value,
      symptoms: document.getElementById('symptoms').value,
      operator_actions_taken: document.getElementById('actions').value,
      safety_flags: [],
      language: document.getElementById('lang').value,
    },
  };

  const response = await fetch('/chat/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    document.getElementById('trace').textContent = JSON.stringify(data, null, 2);
    return;
  }

  document.getElementById('predicted').textContent = data.predicted_class;
  document.getElementById('confidence').textContent = (data.confidence * 100).toFixed(1) + '%';

  const escalationEl = document.getElementById('escalation');
  if (data.escalation_required) {
    escalationEl.textContent = 'Required';
    escalationEl.className = 'value risk-high';
  } else {
    escalationEl.textContent = 'Not Required';
    escalationEl.className = 'value risk-low';
  }

  listInto(document.getElementById('questions'), data.clarifying_questions);
  listInto(document.getElementById('steps'), data.suggested_next_steps);

  const similar = document.getElementById('similar');
  similar.textContent = (data.similar_incidents || [])
    .map((s) => `${s.incident_id} | ${s.class_label} | sim=${s.similarity} | ${s.summary}`)
    .join('\n') || 'No similar incidents found.';

  document.getElementById('trace').textContent = `trace_id=${data.trace_id}\nreason=${data.escalation_reason || 'none'}`;
}

document.getElementById('send').addEventListener('click', () => {
  submitIncident().catch((err) => {
    document.getElementById('trace').textContent = 'Request failed: ' + err.message;
  });
});

document.getElementById('clear').addEventListener('click', () => {
  sessionId = null;
  document.getElementById('predicted').textContent = '-';
  document.getElementById('confidence').textContent = '-';
  document.getElementById('escalation').textContent = '-';
  document.getElementById('escalation').className = 'value';
  document.getElementById('questions').innerHTML = '';
  document.getElementById('steps').innerHTML = '';
  document.getElementById('similar').textContent = '';
  document.getElementById('trace').textContent = 'No trace yet.';
});
