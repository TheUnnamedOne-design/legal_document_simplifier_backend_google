chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url) {
      const isLikelyPDF = (
        tab.url.startsWith("file://") ||
        tab.url.toLowerCase().includes(".pdf") ||
        tab.url.toLowerCase().includes("/pdf/") ||
        tab.url.toLowerCase().endsWith("/pdf")
      );
      if (isLikelyPDF) {
        // Proceed with current extraction logic


      
      if (tab.url.startsWith("http")) {
        // Handle online PDFs by fetching and uploading the blob
        fetch(tab.url)
          .then(res => res.blob())
          .then(blob => {
            let fd = new FormData();
            fd.append("file", blob, "document.pdf");
            return fetch("http://localhost:5000/api/upload_pdf", {
              method: "POST",
              body: fd
            });
          })
          .then(r => r.json())
          .then(json => {
            console.log("[BG] Got summary:", json);
            chrome.tabs.sendMessage(tabId, {
              action: "showSummary",
              summary: json.summary,
              docId: json.doc_id
            });
          })
          .catch(err => console.error("[BG] Error uploading online PDF:", err));
      } 
      else if (tab.url.startsWith("file://")) {
        // For local PDFs: wait 2 seconds before extraction to allow DOM to fully render
        console.log("[BG] Local PDF detected. Waiting 2 seconds before extraction...");
        setTimeout(() => {
          chrome.scripting.executeScript({
            target: { tabId: tabId },
            func: extractPDFText
          }, (results) => {
            if (chrome.runtime.lastError) {
              console.error("[BG] Script injection failed:", chrome.runtime.lastError.message || chrome.runtime.lastError);
              return;
            }

            
            if (results && results[0] && results[0].result) {
              const extractedText = results[0].result;
              console.log(`[BG] Full extracted text (${extractedText.length} chars):`);
              console.log("------BEGIN Text------");
              console.log(extractedText);
              console.log("-------END Text-------");
              
              fetch("http://localhost:5000/api/upload_text", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json"
                },
                body: JSON.stringify({
                  text: extractedText,
                  filename: tab.url.split("/").pop() || "local_document.pdf"
                })
              })
              .then(r => r.json())
              .then(json => {
                console.log("[BG] Got local PDF summary:", json);
                chrome.tabs.sendMessage(tabId, {
                  action: "showSummary",
                  summary: json.summary,
                  docId: json.doc_id
                });
              })
              .catch(err => console.error("[BG] Error sending extracted text to backend:", err));
            } else {
              console.warn("[BG] No text extracted from PDF.");
            }
          });
        }, 2000); // 2 seconds delay
      }
    }
  }
});

function extractPDFText() {
  try {
    const textLayer = document.querySelector('.textLayer');
    if (textLayer) {
      const textContent = textLayer.innerText || textLayer.textContent;
      console.log(`[Content] .textLayer length: ${textContent.length}`);
      if (textContent.trim().length > 0) {
        return textContent;
      }
    }
    console.warn("[Content] .textLayer not found or empty");
    return "";
  } catch (error) {
    console.error("[Content] Extraction error:", error);
    return "";
  }
}


// Handle "Advanced" button
chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.action === "openAdvanced") {
    chrome.tabs.create({
      url: "http://localhost:5000/dashboard?doc_id=test123"
    });
  }
});
