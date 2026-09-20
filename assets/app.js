// Global State
let activeFormat = 'text'; // 'text' | 'html'
let attachmentsList = [];
let sampleTemplates = [];

// DOM Elements - SMTP & Providers
const smtpHost = document.querySelector('#smtpHost');
const smtpPort = document.querySelector('#smtpPort');
const smtpUsername = document.querySelector('#smtpUsername');
const smtpPassword = document.querySelector('#smtpPassword');
const smtpSender = document.querySelector('#smtpSender');
const smtpSecurity = document.querySelector('#smtpSecurity');
const providerChips = document.querySelectorAll('.provider-chip');
const providerTip = document.querySelector('#providerTip');
const serverConfigNotice = document.querySelector('#serverConfigNotice');
const serverConfigText = document.querySelector('#serverConfigText');
const testConnBtn = document.querySelector('#testConnBtn');
const testConnStatus = document.querySelector('#testConnStatus');

// DOM Elements - Recipients
const importCsvBtn = document.querySelector('#importCsvBtn');
const csvFileInput = document.querySelector('#csvFileInput');
const clearRecipientsBtn = document.querySelector('#clearRecipientsBtn');
const recipientsField = document.querySelector('#recipients');
const recipientCount = document.querySelector('#recipientCount');
const recipientsValidation = document.querySelector('#recipientsValidation');

// DOM Elements - Compose & Format
const subjectField = document.querySelector('#subject');
const selectNormalMailBtn = document.querySelector('#selectNormalMailBtn');
const selectHtmlMailBtn = document.querySelector('#selectHtmlMailBtn');
const templateSelect = document.querySelector('#templateSelect');

// Normal Body
const normalMailBodyBlock = document.querySelector('#normalMailBodyBlock');
const normalBody = document.querySelector('#normalBody');
const normalWordCount = document.querySelector('#normalWordCount');
const insertGreetingBtn = document.querySelector('#insertGreetingBtn');
const insertSignoffBtn = document.querySelector('#insertSignoffBtn');
const clearNormalBodyBtn = document.querySelector('#clearNormalBodyBtn');

// HTML Body
const htmlMailBodyBlock = document.querySelector('#htmlMailBodyBlock');
const htmlBody = document.querySelector('#htmlBody');
const htmlCharCount = document.querySelector('#htmlCharCount');
const textFallback = document.querySelector('#textFallback');
const copyToTextBtn = document.querySelector('#copyToTextBtn');
const insertTagP = document.querySelector('#insertTagP');
const insertTagB = document.querySelector('#insertTagB');
const insertTagH2 = document.querySelector('#insertTagH2');
const insertTagButton = document.querySelector('#insertTagButton');
const insertTagCard = document.querySelector('#insertTagCard');

// Attachments
const addAttachmentBtn = document.querySelector('#addAttachmentBtn');
const attachmentInput = document.querySelector('#attachmentInput');
const attachmentListEl = document.querySelector('#attachmentList');

// Send Actions & Feedback
const sendNormalBtn = document.querySelector('#sendNormalBtn');
const sendHtmlBtn = document.querySelector('#sendHtmlBtn');
const feedback = document.querySelector('#feedback');

// Live Preview & Tabs
const tabPreviewBtn = document.querySelector('#tabPreviewBtn');
const tabHistoryBtn = document.querySelector('#tabHistoryBtn');
const previewTabContent = document.querySelector('#previewTabContent');
const historyTabContent = document.querySelector('#historyTabContent');
const preview = document.querySelector('#preview');
const previewFrom = document.querySelector('#previewFrom');
const previewTo = document.querySelector('#previewTo');
const previewSubject = document.querySelector('#previewSubject');
const previewFormatBadge = document.querySelector('#previewFormatBadge');

// History
const historyList = document.querySelector('#historyList');
const historyCount = document.querySelector('#historyCount');
const refreshHistoryBtn = document.querySelector('#refreshHistoryBtn');

// Header Status
const statusDot = document.querySelector('#statusDot');
const statusText = document.querySelector('#statusText');

const EMAIL_REGEX = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

// ==========================================
// 1. SMTP Provider Presets & Storage
// ==========================================
const PROVIDER_CONFIGS = {
    gmail: {
        host: 'smtp.gmail.com',
        port: '465',
        security: 'ssl',
        tip: '<strong>Gmail Setup:</strong> Enter your Gmail address in <em>Username</em> and <em>From Address</em>. In <em>Password</em>, enter a <strong>Google App Password</strong> (16 characters from Google Account &gt; Security &gt; 2-Step Verification &gt; App Passwords), not your regular Gmail account password.'
    },
    outlook: {
        host: 'smtp.office365.com',
        port: '587',
        security: 'starttls',
        tip: '<strong>Outlook / 365 Setup:</strong> Uses STARTTLS on port 587. Enter your Microsoft email and password/app-password.'
    },
    yahoo: {
        host: 'smtp.mail.yahoo.com',
        port: '465',
        security: 'ssl',
        tip: '<strong>Yahoo Setup:</strong> Uses SSL on port 465. Generate an App Password in your Yahoo Account Security settings.'
    },
    custom: {
        host: '',
        port: '465',
        security: 'ssl',
        tip: '<strong>Custom SMTP:</strong> Enter your mail server host, port, credentials, and select SSL or STARTTLS.'
    }
};

providerChips.forEach(chip => {
    chip.addEventListener('click', () => {
        providerChips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        const pKey = chip.dataset.provider;
        const conf = PROVIDER_CONFIGS[pKey];
        if (!conf) return;

        if (conf.host) smtpHost.value = conf.host;
        smtpPort.value = conf.port;
        smtpSecurity.value = conf.security;
        providerTip.innerHTML = conf.tip;
        saveSettingsToStorage();
    });
});

// Auto-mirror Username into From Address if empty
let lastAutoUser = '';
smtpUsername.addEventListener('input', () => {
    const val = smtpUsername.value.trim();
    if (!smtpSender.value || smtpSender.value === lastAutoUser) {
        smtpSender.value = val;
        lastAutoUser = val;
    }
    updatePreview();
    saveSettingsToStorage();
});

smtpHost.addEventListener('input', saveSettingsToStorage);
smtpPort.addEventListener('input', saveSettingsToStorage);
smtpSender.addEventListener('input', () => {
    updatePreview();
    saveSettingsToStorage();
});
smtpSecurity.addEventListener('change', saveSettingsToStorage);

function saveSettingsToStorage() {
    const settings = {
        host: smtpHost.value.trim(),
        port: smtpPort.value.trim(),
        username: smtpUsername.value.trim(),
        sender: smtpSender.value.trim(),
        security: smtpSecurity.value
    };
    try {
        localStorage.setItem('dispatch_smtp_config', JSON.stringify(settings));
    } catch {}
}

function restoreSettingsFromStorage() {
    try {
        const saved = localStorage.getItem('dispatch_smtp_config');
        if (saved) {
            const conf = JSON.parse(saved);
            if (conf.host) smtpHost.value = conf.host;
            if (conf.port) smtpPort.value = conf.port;
            if (conf.username) smtpUsername.value = conf.username;
            if (conf.sender) smtpSender.value = conf.sender;
            if (conf.security) smtpSecurity.value = conf.security;
        }
    } catch {}
}

// ==========================================
// 2. Email Format Switching Logic
// ==========================================
function setMailFormat(format) {
    activeFormat = format;

    if (format === 'text') {
        selectNormalMailBtn.classList.add('active');
        selectHtmlMailBtn.classList.remove('active');
        normalMailBodyBlock.style.display = 'block';
        htmlMailBodyBlock.style.display = 'none';

        sendNormalBtn.classList.remove('inactive-action');
        sendHtmlBtn.classList.add('inactive-action');

        previewFormatBadge.textContent = 'NORMAL TEXT';
        previewFormatBadge.className = 'format-badge plain';
    } else {
        selectHtmlMailBtn.classList.add('active');
        selectNormalMailBtn.classList.remove('active');
        htmlMailBodyBlock.style.display = 'block';
        normalMailBodyBlock.style.display = 'none';

        sendHtmlBtn.classList.remove('inactive-action');
        sendNormalBtn.classList.add('inactive-action');

        previewFormatBadge.textContent = 'RICH HTML';
        previewFormatBadge.className = 'format-badge';
    }

    updatePreview();
}

selectNormalMailBtn.addEventListener('click', () => setMailFormat('text'));
selectHtmlMailBtn.addEventListener('click', () => setMailFormat('html'));

// ==========================================
// 3. Recipients Parsing & Validation
// ==========================================
function parseEmails(text) {
    const tokens = text.split(/[\r\n,;]+/).map(t => t.trim()).filter(Boolean);
    const valid = [];
    const invalid = [];

    tokens.forEach(token => {
        if (EMAIL_REGEX.test(token)) {
            if (!valid.includes(token)) valid.push(token);
        } else {
            invalid.push(token);
        }
    });
    return { valid, invalid };
}

function updateRecipientsDisplay() {
    const { valid, invalid } = parseEmails(recipientsField.value);
    const count = valid.length;
    recipientCount.textContent = `${count} recipient${count === 1 ? '' : 's'}`;

    if (invalid.length > 0) {
        recipientsValidation.textContent = `${invalid.length} invalid address${invalid.length === 1 ? '' : 'es'}`;
        recipientsValidation.className = 'validation-pill invalid';
    } else {
        recipientsValidation.textContent = count > 0 ? '✓ Ready to send' : '';
        recipientsValidation.className = 'validation-pill';
    }

    if (count === 0) {
        previewTo.textContent = 'No recipients specified';
    } else if (count === 1) {
        previewTo.textContent = valid[0];
    } else {
        previewTo.textContent = `${valid[0]} and ${count - 1} other${count > 2 ? 's' : ''}`;
    }
}

importCsvBtn.addEventListener('click', () => csvFileInput.click());

csvFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
        const { valid } = parseEmails(event.target.result);
        if (valid.length === 0) {
            alert('No valid email addresses found in the selected file.');
            return;
        }
        const existing = parseEmails(recipientsField.value).valid;
        const merged = Array.from(new Set([...existing, ...valid]));
        recipientsField.value = merged.join('\n');
        updateRecipientsDisplay();
    };
    reader.readAsText(file);
    csvFileInput.value = '';
});

clearRecipientsBtn.addEventListener('click', () => {
    recipientsField.value = '';
    updateRecipientsDisplay();
});

recipientsField.addEventListener('input', updateRecipientsDisplay);

// ==========================================
// 4. Body Block Tools & Stats
// ==========================================
function updateNormalStats() {
    const text = normalBody.value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    const chars = normalBody.value.length;
    normalWordCount.textContent = `${words} word${words === 1 ? '' : 's'} • ${chars} character${chars === 1 ? '' : 's'}`;
    updatePreview();
}

function updateHtmlStats() {
    const chars = htmlBody.value.length;
    htmlCharCount.textContent = `${chars} character${chars === 1 ? '' : 's'}`;
    updatePreview();
}

normalBody.addEventListener('input', updateNormalStats);
htmlBody.addEventListener('input', updateHtmlStats);
subjectField.addEventListener('input', updatePreview);
smtpSender.addEventListener('input', updatePreview);

insertGreetingBtn.addEventListener('click', () => {
    if (!normalBody.value.startsWith('Hello') && !normalBody.value.startsWith('Hi')) {
        normalBody.value = `Hi there,\n\n${normalBody.value}`;
        updateNormalStats();
    }
});

insertSignoffBtn.addEventListener('click', () => {
    normalBody.value = `${normalBody.value.trim()}\n\nBest regards,\nYour Name`;
    updateNormalStats();
});

clearNormalBodyBtn.addEventListener('click', () => {
    normalBody.value = '';
    updateNormalStats();
});

function insertSnippetAtCursor(textarea, before, after = '') {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    const selected = text.substring(start, end);
    const replacement = before + selected + after;
    textarea.value = text.substring(0, start) + replacement + text.substring(end);
    textarea.focus();
    textarea.selectionStart = start + before.length;
    textarea.selectionEnd = start + replacement.length - after.length;
    updateHtmlStats();
}

insertTagP.addEventListener('click', () => insertSnippetAtCursor(htmlBody, '<p>', '</p>'));
insertTagB.addEventListener('click', () => insertSnippetAtCursor(htmlBody, '<b>', '</b>'));
insertTagH2.addEventListener('click', () => insertSnippetAtCursor(htmlBody, '<h2 style="color: #14201e; margin-bottom: 8px;">', '</h2>'));
insertTagButton.addEventListener('click', () => {
    insertSnippetAtCursor(htmlBody, '<a href="#" style="display: inline-block; background: #14201e; color: #ffffff; padding: 12px 22px; text-decoration: none; border-radius: 4px; font-weight: 700; margin: 14px 0;">', 'Button Label</a>');
});
insertTagCard.addEventListener('click', () => {
    insertSnippetAtCursor(htmlBody, '<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 18px; margin: 16px 0;">\n  ', '\n</div>');
});

copyToTextBtn.addEventListener('click', () => {
    const rawHtml = htmlBody.value;
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = rawHtml;
    textFallback.value = tempDiv.innerText || tempDiv.textContent || '';
    alert('Plain-text fallback generated from HTML!');
});

// ==========================================
// 5. Live Preview
// ==========================================
function updatePreview() {
    previewSubject.textContent = subjectField.value.trim() || 'Your subject line';
    const sender = smtpSender.value.trim() || smtpUsername.value.trim() || 'you@example.com';
    previewFrom.textContent = sender;

    if (activeFormat === 'text') {
        const textVal = normalBody.value.trim();
        if (!textVal) {
            preview.srcdoc = `<!DOCTYPE html><html><body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 13.5px; color: #94a3b8; padding: 24px; margin: 0;"><em>Your plain-text message will appear here as you type...</em></body></html>`;
        } else {
            const escaped = textVal
                .replaceAll('&', '&amp;')
                .replaceAll('<', '&lt;')
                .replaceAll('>', '&gt;');
            preview.srcdoc = `<!DOCTYPE html><html><head><meta charset="utf-8"></head><body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 14px; line-height: 1.65; color: #1e293b; padding: 24px; margin: 0; white-space: pre-wrap; word-break: break-word;">${escaped}</body></html>`;
        }
    } else {
        const htmlVal = htmlBody.value.trim();
        if (!htmlVal) {
            preview.srcdoc = `<!DOCTYPE html><html><body style="font-family: sans-serif; font-size: 13.5px; color: #94a3b8; padding: 24px; margin: 0;"><em>Your rich HTML email template will render here in real time...</em></body></html>`;
        } else {
            preview.srcdoc = htmlVal;
        }
    }
}

// ==========================================
// 6. Template Presets
// ==========================================
async function loadPresets() {
    try {
        const res = await fetch('/api/templates');
        if (!res.ok) return;
        const data = await res.json();
        sampleTemplates = data.templates || [];

        templateSelect.innerHTML = '<option value="">-- Choose a ready template --</option>';
        sampleTemplates.forEach((t) => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = t.name;
            templateSelect.appendChild(opt);
        });
    } catch {}
}

templateSelect.addEventListener('change', () => {
    const selId = templateSelect.value;
    if (!selId) return;
    const tmpl = sampleTemplates.find(t => t.id === selId);
    if (!tmpl) return;

    subjectField.value = tmpl.subject || '';
    if (tmpl.format === 'html') {
        setMailFormat('html');
        htmlBody.value = tmpl.html || '';
        textFallback.value = tmpl.text || '';
        updateHtmlStats();
    } else {
        setMailFormat('text');
        normalBody.value = tmpl.text || '';
        updateNormalStats();
    }
});

// ==========================================
// 7. File Attachments
// ==========================================
addAttachmentBtn.addEventListener('click', () => attachmentInput.click());

attachmentInput.addEventListener('change', async (event) => {
    const files = Array.from(event.target.files);
    for (const file of files) {
        if (file.size > 20 * 1024 * 1024) {
            alert(`File "${file.name}" exceeds the 20MB limit.`);
            continue;
        }
        const base64Data = await readFileAsBase64(file);
        attachmentsList.push({
            filename: file.name,
            type: file.type || 'application/octet-stream',
            size: file.size,
            content: base64Data,
        });
    }
    renderAttachmentChips();
    attachmentInput.value = '';
});

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const dataUrl = reader.result;
            const base64Index = dataUrl.indexOf(',') + 1;
            resolve(dataUrl.substring(base64Index));
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function renderAttachmentChips() {
    attachmentListEl.innerHTML = '';
    attachmentsList.forEach((att, index) => {
        const chip = document.createElement('span');
        chip.className = 'attachment-chip';
        const kbSize = (att.size / 1024).toFixed(1);
        chip.innerHTML = `<span>&#128206; ${escapeHtml(att.filename)} (${kbSize} KB)</span><span class="chip-remove" title="Remove">&times;</span>`;
        chip.querySelector('.chip-remove').addEventListener('click', () => {
            attachmentsList.splice(index, 1);
            renderAttachmentChips();
        });
        attachmentListEl.appendChild(chip);
    });
}

// ==========================================
// 8. Test SMTP Connection
// ==========================================
testConnBtn.addEventListener('click', async () => {
    testConnStatus.textContent = 'Connecting to SMTP server...';
    testConnStatus.className = 'test-status loading';
    testConnBtn.disabled = true;

    try {
        const res = await fetch('/api/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                smtp: {
                    host: smtpHost.value.trim(),
                    port: smtpPort.value.trim(),
                    username: smtpUsername.value.trim(),
                    password: smtpPassword.value,
                    security: smtpSecurity.value,
                }
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Connection failed');
        testConnStatus.textContent = '✓ SMTP Connected & Authenticated!';
        testConnStatus.className = 'test-status success';
    } catch (err) {
        testConnStatus.textContent = `✗ ${err.message}`;
        testConnStatus.className = 'test-status error';
    } finally {
        testConnBtn.disabled = false;
    }
});

// ==========================================
// 9. Real Email Delivery
// ==========================================
async function executeSend(targetFormat) {
    feedback.className = 'feedback show info';
    feedback.textContent = `Connecting to SMTP server and delivering ${targetFormat === 'text' ? 'Normal Mail' : 'HTML Mail'}...`;
    sendNormalBtn.disabled = true;
    sendHtmlBtn.disabled = true;

    try {
        const { valid, invalid } = parseEmails(recipientsField.value);
        if (valid.length === 0) {
            throw new Error('Please enter at least one valid recipient email address.');
        }
        if (invalid.length > 0) {
            throw new Error(`Invalid email address: "${invalid[0]}". Please check the format.`);
        }

        const subjectVal = subjectField.value.trim();
        if (!subjectVal) {
            throw new Error('Please enter an email subject line.');
        }

        let bodyPayload = {};
        if (targetFormat === 'text') {
            const bodyVal = normalBody.value.trim();
            if (!bodyVal) {
                throw new Error('Please enter message text in the Message Body block.');
            }
            bodyPayload = {
                format: 'text',
                text: bodyVal,
                html: '',
            };
        } else {
            const htmlVal = htmlBody.value.trim();
            if (!htmlVal) {
                throw new Error('Please enter HTML markup in the HTML Mail Body block.');
            }
            bodyPayload = {
                format: 'html',
                html: htmlVal,
                text: textFallback.value.trim(),
            };
        }

        // Validate SMTP fields
        if (!smtpHost.value.trim()) throw new Error('Please specify the SMTP Host (e.g. smtp.gmail.com)');
        if (!smtpUsername.value.trim()) throw new Error('Please enter your email username in Step 01');
        if (!smtpPassword.value) throw new Error('Please enter your email/app password in Step 01');
        if (!smtpSender.value.trim()) throw new Error('Please enter your From Address in Step 01');

        const payload = {
            smtp: {
                host: smtpHost.value.trim(),
                port: smtpPort.value.trim(),
                username: smtpUsername.value.trim(),
                password: smtpPassword.value,
                sender: smtpSender.value.trim(),
                security: smtpSecurity.value,
            },
            recipients: valid,
            subject: subjectVal,
            attachments: attachmentsList.map(a => ({
                filename: a.filename,
                type: a.type,
                content: a.content,
            })),
            ...bodyPayload,
        };

        const response = await fetch('/api/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Server rejected transmission');
        }

        feedback.className = 'feedback show';
        feedback.textContent = `✓ ${result.message}`;
        fetchHistory();
    } catch (error) {
        feedback.className = 'feedback show error';
        feedback.textContent = `✗ ${error.message}`;
    } finally {
        sendNormalBtn.disabled = false;
        sendHtmlBtn.disabled = false;
    }
}

sendNormalBtn.addEventListener('click', () => {
    setMailFormat('text');
    executeSend('text');
});

sendHtmlBtn.addEventListener('click', () => {
    setMailFormat('html');
    executeSend('html');
});

// ==========================================
// 10. Tabs & History
// ==========================================
tabPreviewBtn.addEventListener('click', () => {
    tabPreviewBtn.classList.add('active');
    tabHistoryBtn.classList.remove('active');
    previewTabContent.classList.add('active');
    historyTabContent.classList.remove('active');
});

tabHistoryBtn.addEventListener('click', () => {
    tabHistoryBtn.classList.add('active');
    tabPreviewBtn.classList.remove('active');
    historyTabContent.classList.add('active');
    previewTabContent.classList.remove('active');
    fetchHistory();
});

refreshHistoryBtn.addEventListener('click', fetchHistory);

async function fetchHistory() {
    try {
        const res = await fetch('/api/history');
        if (!res.ok) return;
        const data = await res.json();
        renderHistory(data.history || []);
    } catch {}
}

function renderHistory(items) {
    historyCount.textContent = items.length;
    if (items.length === 0) {
        historyList.innerHTML = '<div class="history-empty">No emails delivered in this session yet.</div>';
        return;
    }

    historyList.innerHTML = items.map(item => {
        const isSuccess = item.failed_count === 0;
        const pillClass = isSuccess ? 'sent' : 'failed';
        const pillText = isSuccess ? 'DELIVERED' : `${item.sent_count} sent / ${item.failed_count} failed`;
        const fmtLabel = item.mail_format === 'html' ? '⚡ HTML' : '✉ Normal';
        const attSummary = item.attachments && item.attachments.length > 0 ? ` &bull; ${item.attachments.length} attachment(s)` : '';

        return `
            <div class="history-card">
                <div class="history-card-header">
                    <div>
                        <div class="history-card-title">${escapeHtml(item.subject || '(No Subject)')}</div>
                        <div class="history-card-time">${item.timestamp} &bull; ${fmtLabel}</div>
                    </div>
                    <span class="history-pill ${pillClass}">${pillText}</span>
                </div>
                <div class="history-card-details">
                    <div>To: ${item.recipients_count} recipient(s) &bull; From: ${escapeHtml(item.sender || 'Sender')}${attSummary}</div>
                </div>
            </div>
        `;
    }).join('');
}

function escapeHtml(str) {
    return str.replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[m]);
}

// ==========================================
// 11. Health Check & Init
// ==========================================
async function init() {
    restoreSettingsFromStorage();

    try {
        const response = await fetch('/api/health');
        if (!response.ok) throw new Error();
        const data = await response.json();

        statusDot.className = 'status-dot online';
        statusText.textContent = 'Server Online';

        if (data.smtp_configured && data.default_smtp) {
            serverConfigNotice.style.display = 'flex';
            serverConfigText.textContent = `Server SMTP detected (${data.default_smtp.host} / ${data.default_smtp.sender})`;
            if (!smtpHost.value) smtpHost.value = data.default_smtp.host;
            if (!smtpPort.value) smtpPort.value = data.default_smtp.port;
            if (!smtpSender.value) smtpSender.value = data.default_smtp.sender;
            if (data.default_smtp.security) smtpSecurity.value = data.default_smtp.security;
        }
    } catch {
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Server Offline';
    }

    setMailFormat('text');
    updateNormalStats();
    updateRecipientsDisplay();
    loadPresets();
    fetchHistory();
}

init();
