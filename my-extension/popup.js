document.addEventListener("DOMContentLoaded", () => {
  const summaryDiv = document.getElementById("summary");
  const advancedBtn = document.getElementById("advancedBtn");
  const pdfFileInput = document.getElementById("pdfFile");
  const uploadBtn = document.getElementById("uploadBtn");
  const uploadStatus = document.getElementById("uploadStatus");

  console.log("[Popup] Popup loaded, fetching stored summary...");

  // Load existing summary if available
  chrome.storage.local.get(["pdfSummary", "docId"], (data) => {
    console.log("[Popup] Storage data:", data);
    if (data.pdfSummary) {
      try {
        const summary = JSON.parse(data.pdfSummary);
        displaySummary(summary);
      } catch (e) {
        summaryDiv.innerText = data.pdfSummary;
      }
    }

    if (data.docId) {
      advancedBtn.disabled = false;
      advancedBtn.addEventListener("click", () => {
        console.log("[Popup] Advanced button clicked. Opening site...");
        chrome.tabs.create({
          url: `http://localhost:5000/dashboard?doc_id=${encodeURIComponent(data.docId)}`
        });
      });
    }
  });

  // File input change handler
  pdfFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      uploadBtn.disabled = false;
      uploadStatus.innerText = "";
    } else {
      uploadBtn.disabled = true;
    }
  });

  // Upload button handler
  uploadBtn.addEventListener("click", async () => {
    const file = pdfFileInput.files[0];
    if (!file) return;

    uploadBtn.disabled = true;
    uploadStatus.innerText = "Processing PDF...";

    try {
      // Extract text from PDF using PDF.js
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      let fullText = "";

      for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
        const page = await pdf.getPage(pageNum);
        const textContent = await page.getTextContent();
        
        const pageText = textContent.items
          .map(item => item.str)
          .join(" ");
        
        fullText += pageText + "\n\n";
      }

      if (fullText.trim()) {
        uploadStatus.innerText = "Sending to server...";
        
        // Send to backend
        const response = await fetch("http://localhost:5000/api/upload_text", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            text: fullText,
            filename: file.name
          })
        });
        
        const result = await response.json();
        
        uploadStatus.innerText = "✓ Analysis complete!";
        displaySummary(result.summary);
        
        // Store results
        chrome.storage.local.set({
          pdfSummary: JSON.stringify(result.summary),
          docId: result.doc_id
        });
        
        // Enable advanced button
        advancedBtn.disabled = false;
        
      } else {
        throw new Error("No text could be extracted from the PDF");
      }

    } catch (error) {
      console.error("[Popup] PDF processing error:", error);
      uploadStatus.innerText = "Error: " + error.message;
    }
    
    uploadBtn.disabled = false;
  });

  function displaySummary(summary) {
    if (typeof summary === "object") {
      let html = "";
      Object.keys(summary).forEach(section => {
        html += `${section}:\n${summary[section]}\n\n`;
      });
      summaryDiv.innerText = html;
    } else {
      summaryDiv.innerText = summary;
    }
  }
});
