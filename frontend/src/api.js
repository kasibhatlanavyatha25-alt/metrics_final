const API_BASE = 'http://localhost:8000/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function validateRepository(repoUrl) {
  try {
    const res = await fetch(`${API_BASE}/projects/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: repoUrl })
    });
    const data = await res.json();
    return data;
  } catch (err) {
    return {
      valid: false,
      is_valid: false,
      error_code: 'NETWORK_ERROR',
      message: 'Failed to connect to repository validation server.',
      details: err.message,
      suggestion: 'Ensure the backend server is running and reachable on port 8000.'
    };
  }
}


export async function startAnalysis(repoUrl, customWeights = null) {
  const res = await fetch(`${API_BASE}/projects/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl, custom_weights: customWeights })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Analysis initiation failed');
  }
  return res.json();
}

export async function fetchAnalysisStatus(projectId) {
  const res = await fetch(`${API_BASE}/projects/${projectId}/status`);
  if (!res.ok) throw new Error('Status fetch failed');
  return res.json();
}

export async function fetchProjectsList() {
  const res = await fetch(`${API_BASE}/projects`);
  return res.json();
}

export async function fetchProjectDetails(projectId) {
  const res = await fetch(`${API_BASE}/projects/${projectId}`);
  return res.json();
}

export async function fetchProjectDashboard(projectId) {
  const res = await fetch(`${API_BASE}/projects/${projectId}/dashboard`);
  return res.json();
}

export async function fetchProjectVersions(projectId) {
  const res = await fetch(`${API_BASE}/projects/${projectId}/versions`);
  return res.json();
}

export async function fetchProjectMetrics(projectId, versionId = null) {
  const url = versionId 
    ? `${API_BASE}/projects/${projectId}/metrics?version_id=${versionId}` 
    : `${API_BASE}/projects/${projectId}/metrics`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchProjectEvolution(projectId) {
  const res = await fetch(`${API_BASE}/projects/${projectId}/evolution`);
  return res.json();
}

export async function fetchProjectDNA(projectId) {
  const res = await fetch(`${API_BASE}/projects/${projectId}/dna`);
  return res.json();
}

export async function fetchProjectMutations(projectId, severity = null) {
  const url = severity && severity !== 'ALL'
    ? `${API_BASE}/projects/${projectId}/mutations?severity=${severity}`
    : `${API_BASE}/projects/${projectId}/mutations`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchProjectESDI(projectId) {
  const res = await fetch(`${API_BASE}/projects/${projectId}/esdi`);
  return res.json();
}

export async function simulateESDI(projectId, weights) {
  const res = await fetch(`${API_BASE}/projects/${projectId}/esdi/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ weights })
  });
  return res.json();
}

export async function fetchProjectRisks(projectId, priority = null) {
  const url = priority && priority !== 'ALL'
    ? `${API_BASE}/projects/${projectId}/risks?priority=${priority}`
    : `${API_BASE}/projects/${projectId}/risks`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchProjectRecommendations(projectId, priority = null) {
  const url = priority && priority !== 'ALL'
    ? `${API_BASE}/projects/${projectId}/recommendations?priority=${priority}`
    : `${API_BASE}/projects/${projectId}/recommendations`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchProjectPrediction(projectId) {
  const res = await fetch(`${API_BASE}/projects/${projectId}/prediction`);
  return res.json();
}

export async function deleteProject(projectId) {
  const res = await fetch(`${API_BASE}/projects/${projectId}`, {
    method: 'DELETE'
  });
  return res.json();
}

export async function fetchDiagnostics(projectId) {
  const res = await fetch(`${API_BASE}/projects/${projectId}/diagnostics`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to fetch diagnostics');
  }
  return res.json();
}

export async function clearAnalysisCache() {
  const res = await fetch(`${API_BASE}/cache/clear`, {
    method: 'POST'
  });
  return res.json();
}
