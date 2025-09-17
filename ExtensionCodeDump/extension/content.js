(async () => {
  pdfjsLib.GlobalWorkerOptions.workerSrc = chrome.runtime.getURL("pdf.worker.js");

  try {
    const response = await fetch(window.location.href);
    const pdfData = await response.arrayBuffer();

    const loadingTask = pdfjsLib.getDocument({ data: pdfData });
    const pdf = await loadingTask.promise;

    let text = "";
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      text += content.items.map(item => item.str).join(" ") + "\n";
    }

    // Send full text to background instead of server directly
    chrome.runtime.sendMessage(
      { action: "sendText", text },
      (response) => {
        if (response?.error) {
          console.error("❌ Server error:", response.error);
        } else {
          console.log("Snippet from server:", response.snippet);
        }
      }
    );

  } catch (err) {
    console.error("❌ PDF extraction failed", err);
  }
})();
