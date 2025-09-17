const express = require("express");
const fs = require("fs");
const cors = require("cors");

const app = express();

app.use(cors()); // allow all origins (for dev)
app.use(express.json());

app.post("/pdf-text", (req, res) => {
  console.log("📄 Received PDF text");

  const fullText = req.body.text || "";
  fs.writeFileSync("output.txt", fullText);

  // Extract first 100 characters
  const snippet = fullText.slice(0, 100);

  res.json({ snippet });
});

app.listen(3000, () =>
  console.log("🚀 Backend running on http://localhost:3000")
);
