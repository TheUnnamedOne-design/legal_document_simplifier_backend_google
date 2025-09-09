(async () => {
  // Tell pdf.js where the worker file is
  pdfjsLib.GlobalWorkerOptions.workerSrc = chrome.runtime.getURL("pdf.worker.js");

  try {
    // Fetch the PDF bytes from the current page
    const response = await fetch(window.location.href);
    const pdfData = await response.arrayBuffer();

    // Load PDF
    const loadingTask = pdfjsLib.getDocument({ data: pdfData });
    const pdf = await loadingTask.promise;

    let text = "";
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      text += content.items.map(item => item.str).join(" ") + "\n";
    }

    console.log("Extracted PDF text:", text.slice(0, 200) + "..."); // preview first 200 chars

    // Send text to background script
    chrome.runtime.sendMessage({ action: "sendText", text });

  } catch (err) {
    console.error("❌ PDF extraction failed", err);
  }
})();
