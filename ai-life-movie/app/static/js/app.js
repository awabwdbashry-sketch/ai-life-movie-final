// Shared front-end logic: upload with progress, media grid, settings persistence.

async function loadMedia(projectId) {
    const res = await fetch(`/api/projects/${projectId}/media`);
    if (!res.ok) return;
    const items = await res.json();
    renderMediaGrid(projectId, items);
}

function renderMediaGrid(projectId, items) {
    const grid = document.getElementById('mediaGrid');
    if (!grid) return;
    grid.innerHTML = '';
    items.forEach(item => {
        const el = document.createElement('div');
        el.className = 'media-item';
        const thumbUrl = item.thumbnail_url || '';
        el.innerHTML = `
            ${thumbUrl ? `<img src="${thumbUrl}" onerror="this.style.display='none'">` : ''}
            <span class="type-badge">${item.media_type === 'image' ? '📸' : '🎥'}</span>
            <button class="remove-btn" onclick="removeMedia('${projectId}', '${item.id}')">✕</button>
        `;
        grid.appendChild(el);
    });
}

async function uploadFiles(projectId, fileList) {
    if (!fileList || !fileList.length) return;
    const formData = new FormData();
    for (const file of fileList) formData.append('files', file);

    const progressWrap = document.getElementById('uploadProgress');
    const barFill = document.getElementById('uploadBarFill');
    const statusEl = document.getElementById('uploadStatus');
    progressWrap.style.display = 'block';
    statusEl.textContent = `Uploading ${fileList.length} file(s)...`;
    barFill.style.width = '10%';

    try {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `/api/projects/${projectId}/media`);
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const pct = Math.round((e.loaded / e.total) * 100);
                barFill.style.width = pct + '%';
            }
        };
        xhr.onload = () => {
            statusEl.textContent = xhr.status < 300 ? 'Upload complete.' : 'Some files failed to upload.';
            barFill.style.width = '100%';
            loadMedia(projectId);
            setTimeout(() => { progressWrap.style.display = 'none'; barFill.style.width = '0%'; }, 1500);
        };
        xhr.onerror = () => { statusEl.textContent = 'Upload failed.'; };
        xhr.send(formData);
    } catch (err) {
        statusEl.textContent = 'Upload failed: ' + err.message;
    }
}

async function removeMedia(projectId, mediaId) {
    await fetch(`/api/media/${mediaId}`, {method: 'DELETE'});
    loadMedia(projectId);
}

async function saveSettings(projectId) {
    const form = document.getElementById('settingsForm');
    if (!form) return;
    const payload = {
        style: form.style.value,
        target_duration_seconds: parseInt(form.target_duration_seconds.value, 10),
        aspect_ratio: form.aspect_ratio.value,
        language: form.language.value,
        narration_enabled: form.narration_enabled.checked,
        subtitles_enabled: form.subtitles_enabled.checked,
        music_track: form.music_track.value,
    };
    await fetch(`/api/projects/${projectId}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
    });
}
