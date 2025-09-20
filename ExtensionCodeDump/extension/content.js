(async () => {
  pdfjsLib.GlobalWorkerOptions.workerSrc = chrome.runtime.getURL("pdf.worker.js");

  // Create overlay
  const overlay = document.createElement("div");
  overlay.style.position = "fixed";
  overlay.style.top = "10px";
  overlay.style.left = "10px";
  overlay.style.padding = "10px";
  overlay.style.backgroundColor = "#fff";
  overlay.style.border = "1px solid #ccc";
  overlay.style.zIndex = 9999;
  overlay.style.boxShadow = "0 0 10px rgba(0,0,0,0.3)";
  overlay.innerHTML = `
    <div id="status">PDF Text Extractor: Initializing...</div>
    <input type="file" id="fileInput" accept=".pdf">
    <button id="closeBtn">✖ Close</button>
  `;
  document.body.appendChild(overlay);

  const statusEl = overlay.querySelector("#status");
  const fileInput = overlay.querySelector("#fileInput");
  const closeBtn = overlay.querySelector("#closeBtn");

  // Allow user to close the popup manually
  closeBtn.addEventListener("click", () => overlay.remove());

  try {
    let pdfData;

    if (window.location.href.startsWith("http")) {
      // ✅ Online PDF
      const resp = await fetch(window.location.href);
      pdfData = await resp.arrayBuffer();
      await extractPDF(pdfData);

    } else {
      // ⚠️ Local PDF: wait for user to select file
      statusEl.textContent = "Select a local PDF to extract text (optional)";
      fileInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        statusEl.textContent = "🔍 Extracting PDF...";
        pdfData = await file.arrayBuffer();
        await extractPDF(pdfData);
      });
    }

  } catch (err) {
    console.error("❌ PDF extraction failed", err);
    statusEl.textContent = "PDF extraction failed: " + err.message;
  }

  async function extractPDF(data) {
    const pdf = await pdfjsLib.getDocument({ data }).promise;
    let text = "";
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      text += content.items.map(item => item.str).join(" ") + "\n";
    }

    statusEl.textContent = "✅ Extraction complete! Closing in 3s...";

    // Send to backend
    chrome.runtime.sendMessage({ action: "sendText", text }, (response) => {
      if (response?.error) {
        console.error("❌ Backend error:", response.error);
      } else {
        console.log("✅ Backend snippet:", response.snippet);
      }
    });

    // Auto-close overlay after 3 seconds
    setTimeout(() => overlay.remove(), 3000);
  }
})();
