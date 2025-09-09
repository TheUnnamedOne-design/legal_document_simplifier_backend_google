const express = require("express");
const fs = require("fs");
const app = express();

app.use(express.json());

app.post("/pdf-text", (req, res) => {
  console.log("📄 Received PDF text:");
//   console.log(req.body.text);   // full text

  // Optional: also save to file
  fs.writeFileSync("output.txt", req.body.text);

  res.send("OK");
});

app.listen(3000, () => console.log("🚀 Backend running on http://localhost:3000"));
