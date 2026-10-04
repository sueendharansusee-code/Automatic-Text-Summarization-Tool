document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const textInput = document.getElementById('text-input');
    const charCount = document.getElementById('char-count');
    const wordCount = document.getElementById('word-count');
    
    const btnSummarize = document.getElementById('btn-summarize');
    const spinner = btnSummarize.querySelector('.spinner');
    const btnText = btnSummarize.querySelector('.btn-text');
    
    const btnSample = document.getElementById('btn-sample');
    const btnPaste = document.getElementById('btn-paste');
    const btnClear = document.getElementById('btn-clear');
    
    const btnCopy = document.getElementById('btn-copy');
    const btnDownload = document.getElementById('btn-download');
    
    const statOrigWords = document.getElementById('stat-orig-words');
    const statSumWords = document.getElementById('stat-sum-words');
    const statCompression = document.getElementById('stat-compression');
    const statSentences = document.getElementById('stat-sentences');
    
    const shortTextAlert = document.getElementById('short-text-alert');
    const alertMessage = document.getElementById('alert-message');
    
    const outputPlaceholder = document.getElementById('output-placeholder');
    const outputText = document.getElementById('output-text');
    
    const btnToggleHistory = document.getElementById('btn-toggle-history');
    const historyModal = document.getElementById('history-modal');
    const btnCloseHistory = document.getElementById('btn-close-history');
    const btnClearHistory = document.getElementById('btn-clear-history');
    const historyTbody = document.getElementById('history-tbody');
    
    const toastContainer = document.getElementById('toast-container');

    let currentSummary = '';

    // --- Toast Notifications ---
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let icon = 'fa-circle-info';
        if (type === 'success') icon = 'fa-circle-check';
        if (type === 'error') icon = 'fa-circle-xmark';
        
        toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // --- Text Input Counters ---
    function updateCounters() {
        const text = textInput.value;
        const charLength = text.length;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;

        charCount.textContent = `${charLength.toLocaleString()} characters`;
        wordCount.textContent = `${words.toLocaleString()} words`;
    }

    textInput.addEventListener('input', updateCounters);

    // --- Quick Tools ---
    btnSample.addEventListener('click', async () => {
        try {
            const res = await fetch('/api/sample');
            const data = await res.json();
            if (data.success) {
                textInput.value = data.sample_text;
                updateCounters();
                showToast('Sample academic text loaded!', 'success');
            }
        } catch (err) {
            showToast('Failed to load sample text.', 'error');
        }
    });

    btnPaste.addEventListener('click', async () => {
        try {
            if (navigator.clipboard && navigator.clipboard.readText) {
                const text = await navigator.clipboard.readText();
                if (text) {
                    textInput.value = text;
                    updateCounters();
                    showToast('Text pasted from clipboard.', 'success');
                } else {
                    showToast('Clipboard is empty.', 'info');
                }
            } else {
                showToast('Clipboard access not supported in browser.', 'error');
            }
        } catch (err) {
            showToast('Permission denied to read clipboard.', 'error');
        }
    });

    btnClear.addEventListener('click', () => {
        textInput.value = '';
        updateCounters();
        resetOutput();
        showToast('Input cleared.', 'info');
    });

    function resetOutput() {
        currentSummary = '';
        outputText.textContent = '';
        outputText.classList.add('hidden');
        outputPlaceholder.classList.remove('hidden');
        shortTextAlert.classList.add('hidden');
        
        statOrigWords.textContent = '0';
        statSumWords.textContent = '0';
        statCompression.textContent = '0%';
        statSentences.textContent = '0 / 0';
        
        btnCopy.disabled = true;
        btnDownload.disabled = true;
    }

    // --- Summarization Logic ---
    btnSummarize.addEventListener('click', async () => {
        const text = textInput.value.trim();
        if (!text) {
            showToast('Please paste or enter article text to summarize.', 'error');
            return;
        }

        const selectedRadio = document.querySelector('input[name="summary-length"]:checked');
        const lengthLevel = selectedRadio ? selectedRadio.value : 'medium';

        // Set Loading State
        btnSummarize.disabled = true;
        spinner.classList.remove('hidden');
        btnText.classList.add('hidden');

        try {
            const response = await fetch('/api/summarize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, length: lengthLevel })
            });

            const data = await response.json();

            if (!data.success) {
                showToast(data.error || 'Error processing summary.', 'error');
                return;
            }

            // Display Results
            currentSummary = data.summary;
            outputText.textContent = data.summary;
            outputPlaceholder.classList.add('hidden');
            outputText.classList.remove('hidden');

            // Update Metrics
            statOrigWords.textContent = data.original_word_count.toLocaleString();
            statSumWords.textContent = data.summary_word_count.toLocaleString();
            statCompression.textContent = `${data.compression_rate}%`;
            statSentences.textContent = `${data.original_sentence_count} → ${data.summary_sentence_count}`;

            // Handle Short Text Info (#14)
            if (data.is_short_text) {
                alertMessage.textContent = data.message || 'Input text is very short; displaying complete text as summary.';
                shortTextAlert.classList.remove('hidden');
            } else {
                shortTextAlert.classList.add('hidden');
            }

            // Enable Actions
            btnCopy.disabled = false;
            btnDownload.disabled = false;

            showToast('Summary generated successfully!', 'success');

        } catch (err) {
            console.error('Summarize error:', err);
            showToast('Server communication error.', 'error');
        } finally {
            btnSummarize.disabled = false;
            spinner.classList.add('hidden');
            btnText.classList.remove('hidden');
        }
    });

    // --- Export Actions ---
    btnCopy.addEventListener('click', () => {
        if (!currentSummary) return;
        navigator.clipboard.writeText(currentSummary).then(() => {
            showToast('Summary copied to clipboard!', 'success');
        }).catch(() => {
            // Fallback selection
            const range = document.createRange();
            range.selectNodeContents(outputText);
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
            document.execCommand('copy');
            showToast('Summary copied to clipboard!', 'success');
        });
    });

    btnDownload.addEventListener('click', () => {
        if (!currentSummary) return;
        const blob = new Blob([currentSummary], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        a.href = url;
        a.download = `summary_${timestamp}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('Downloaded summary as TXT file.', 'success');
    });

    // --- SQLite History Management ---
    btnToggleHistory.addEventListener('click', () => {
        historyModal.classList.remove('hidden');
        loadHistory();
    });

    btnCloseHistory.addEventListener('click', () => {
        historyModal.classList.add('hidden');
    });

    historyModal.addEventListener('click', (e) => {
        if (e.target === historyModal) {
            historyModal.classList.add('hidden');
        }
    });

    async function loadHistory() {
        historyTbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Fetching history records...</td></tr>`;
        try {
            const res = await fetch('/api/history');
            const data = await res.json();
            
            if (!data.success || !data.history || data.history.length === 0) {
                historyTbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No saved summaries found.</td></tr>`;
                return;
            }

            historyTbody.innerHTML = '';
            data.history.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>#${item.id}</strong></td>
                    <td><small>${item.created_at}</small></td>
                    <td><span class="badge-nlp">${item.length_setting}</span></td>
                    <td>${item.original_word_count} → ${item.summary_word_count} w</td>
                    <td><strong class="text-success">${item.compression_rate}%</strong></td>
                    <td class="summary-preview" title="${escapeHtml(item.summary_text)}">${escapeHtml(item.summary_text)}</td>
                    <td>
                        <div class="quick-tools">
                            <button class="btn-tool btn-load-item" data-id="${item.id}" title="Load into input">
                                <i class="fa-solid fa-arrow-up-right-from-square"></i> Load
                            </button>
                            <button class="btn-tool btn-tool-danger btn-delete-item" data-id="${item.id}" title="Delete record">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                historyTbody.appendChild(tr);
            });

            // Attach row events
            document.querySelectorAll('.btn-load-item').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const id = e.currentTarget.dataset.id;
                    const item = data.history.find(h => h.id == id);
                    if (item) {
                        textInput.value = item.original_text;
                        updateCounters();
                        currentSummary = item.summary_text;
                        outputText.textContent = item.summary_text;
                        outputPlaceholder.classList.add('hidden');
                        outputText.classList.remove('hidden');
                        
                        statOrigWords.textContent = item.original_word_count;
                        statSumWords.textContent = item.summary_word_count;
                        statCompression.textContent = `${item.compression_rate}%`;
                        
                        btnCopy.disabled = false;
                        btnDownload.disabled = false;
                        
                        historyModal.classList.add('hidden');
                        showToast(`Loaded summary #${item.id} from history.`, 'info');
                    }
                });
            });

            document.querySelectorAll('.btn-delete-item').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const id = e.currentTarget.dataset.id;
                    if (confirm(`Delete summary record #${id}?`)) {
                        try {
                            const delRes = await fetch(`/api/history/${id}`, { method: 'DELETE' });
                            const delData = await delRes.json();
                            if (delData.success) {
                                showToast('Record deleted.', 'success');
                                loadHistory();
                            }
                        } catch (err) {
                            showToast('Error deleting record.', 'error');
                        }
                    }
                });
            });

        } catch (err) {
            historyTbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted text-danger">Failed to load history.</td></tr>`;
        }
    }

    btnClearHistory.addEventListener('click', async () => {
        if (confirm('Are you sure you want to delete ALL saved summaries from history?')) {
            try {
                const res = await fetch('/api/history', { method: 'DELETE' });
                const data = await res.json();
                if (data.success) {
                    showToast('History cleared completely.', 'success');
                    loadHistory();
                }
            } catch (err) {
                showToast('Failed to clear history.', 'error');
            }
        }
    });

    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
