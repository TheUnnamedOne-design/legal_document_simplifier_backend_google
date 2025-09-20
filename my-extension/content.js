// Inject a floating sidebar into PDF tabs
function createSidebar() {
  let sidebar = document.createElement("div");
  sidebar.id = "legal-summarizer-sidebar";
  sidebar.style.position = "fixed";
  sidebar.style.top = "0";
  sidebar.style.right = "0";
  sidebar.style.width = "300px";
  sidebar.style.height = "100%";
  sidebar.style.background = "white";
  sidebar.style.borderLeft = "2px solid #ccc";
  sidebar.style.zIndex = "999999";
  sidebar.style.overflowY = "auto";
  sidebar.style.fontFamily = "sans-serif";
  sidebar.style.fontSize = "14px";
  sidebar.style.padding = "10px";
  sidebar.innerHTML = "<h3>Summary</h3><p>Waiting for analysis...</p>";
  document.body.appendChild(sidebar);
}

// Update sidebar content
function updateSidebar(summaryObj) {
  let sidebar = document.getElementById("legal-summarizer-sidebar");
  if (!sidebar) return;

  let html = "<h3>Summary</h3>";
  for (const [heading, bullets] of Object.entries(summaryObj)) {
    html += `<h4>${heading}</h4><pre>${bullets}</pre>`;
  }
  html += `<button id="advancedBtn">Advanced Features</button>`;
  sidebar.innerHTML = html;

  // advanced button → open site
  document.getElementById("advancedBtn").onclick = () => {
    chrome.runtime.sendMessage({action: "openAdvanced"});
  };
}

// Listen for messages from background
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === "showSummary") {
    updateSidebar(msg.summary);
  }
});

// Run when page loads
if (document.contentType === "application/pdf") {
  createSidebar();
}
