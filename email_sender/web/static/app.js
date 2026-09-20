const form = document.getElementById("compose");
const previewBtn = document.getElementById("preview-btn");
const sendBtn = document.getElementById("send-btn");
const previewMeta = document.getElementById("preview-meta");
const previewSubject = document.getElementById("preview-subject");
const previewHtml = document.getElementById("preview-html");
const previewText = document.getElementById("preview-text");
const resultSummary = document.getElementById("result-summary");
const resultList = document.getElementById("result-list");
const smtpStatus = document.getElementById("smtp-status");

let activeBody = "text";

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((other) => other.classList.remove("is-active"));
    tab.classList.add("is-active");
    activeBody = tab.dataset.target === "html-body" ? "html" : "text";
    document.getElementById("text-body").classList.toggle("is-hidden", activeBody !== "text");
    document.getElementById("html-body").classList.toggle("is-hidden", activeBody !== "html");
    renderPreviewPane();
  });
});

let lastPreview = null;

function renderPreviewPane() {
  if (!lastPreview) return;
  const showHtml = activeBody === "html" && lastPreview.html;
  previewHtml.classList.toggle("is-hidden", !showHtml);
  previewText.classList.toggle("is-hidden", showHtml);
  if (showHtml) {
    previewHtml.srcdoc = lastPreview.html;
  } else {
    previewText.textContent = lastPreview.text;
  }
}

async function post(url) {
  const response = await fetch(url, { method: "POST", body: new FormData(form) });
  const payload = await response.json().catch(() => ({ error: "Unexpected server response." }));
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
  return payload;
}

function busy(isBusy) {
  previewBtn.disabled = isBusy;
  sendBtn.disabled = isBusy;
}

previewBtn.addEventListener("click", async () => {
  busy(true);
  try {
    lastPreview = await post("/api/preview");
    previewMeta.textContent = `${lastPreview.recipients.length} recipient(s) — showing ${lastPreview.preview_for}`;
    previewSubject.textContent = lastPreview.subject;
    renderPreviewPane();
  } catch (error) {
    lastPreview = null;
    previewMeta.textContent = error.message;
    previewSubject.textContent = "";
    previewHtml.srcdoc = "";
    previewText.textContent = "";
  } finally {
    busy(false);
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  busy(true);
  resultList.innerHTML = "";
  resultSummary.textContent = "Sending…";
  try {
    const data = await post("/api/send");
    const verb = data.dry_run ? "would send" : "sent";
    resultSummary.textContent = `${verb} ${data.sent}/${data.total} message(s)`;
    data.results.forEach((result) => {
      const item = document.createElement("li");
      const status = document.createElement("span");
      status.className = result.sent ? "status-ok" : "status-err";
      status.textContent = result.sent ? "✓" : "✗";
      item.append(status, document.createTextNode(result.recipient));
      if (result.error) {
        const detail = document.createElement("span");
        detail.className = "muted";
        detail.textContent = result.error;
        item.append(detail);
      }
      resultList.append(item);
    });
  } catch (error) {
    resultSummary.textContent = error.message;
  } finally {
    busy(false);
  }
});

fetch("/api/config")
  .then((response) => response.json())
  .then((data) => {
    if (data.configured) {
      smtpStatus.className = "badge badge-ok";
      smtpStatus.textContent = `SMTP ${data.host}:${data.port} as ${data.from}`;
    } else {
      smtpStatus.className = "badge badge-err";
      smtpStatus.textContent = "SMTP not configured — dry run only";
    }
  })
  .catch(() => {
    smtpStatus.className = "badge badge-err";
    smtpStatus.textContent = "SMTP status unavailable";
  });
