pdfjsLib.GlobalWorkerOptions.workerSrc = chrome.runtime.getURL("pdf.worker.js");

const fileInput = document.getElementById("fileInput");
const statusEl = document.getElementById("status");
const outputEl = document.getElementById("extractedText");

fileInput.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  statusEl.textContent = "🔍 Loading PDF...";

  const arrayBuffer = await file.arrayBuffer();
  try {
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    let text = "";

    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      text += content.items.map(item => item.str).join(" ") + "\n";
    }

    statusEl.textContent = "✅ Extraction complete!";
    outputEl.value = text;

    // Send to backend
    chrome.runtime.sendMessage({ action: "sendText", text }, (response) => {
      if (response?.error) {
        console.error("❌ Backend error:", response.error);
      } else {
        console.log("✅ Backend snippet:", response.snippet);
      }
    });

  } catch (err) {
    console.error("❌ PDF extraction failed", err);
    statusEl.textContent = "❌ Extraction failed";
  }
});
