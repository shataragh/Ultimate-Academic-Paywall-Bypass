# 🧠 Ultimate Academic Paywall Bypass
![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Open Access](https://img.shields.io/badge/Open%20Science-Supported-orange)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
> 🚀 A powerful open‑access discovery tool that helps researchers locate publicly available versions of academic papers using ethical, legal, multi‑source search techniques.
---
## 📚 Overview
Access to scientific knowledge should never depend on geography, sanctions, or financial barriers.  
**Ultimate Academic Paywall Bypass** is a Python‑based tool that automatically searches across open‑access APIs, preprint servers, author‑uploaded PDFs, and archival mirrors to find accessible versions of academic articles.
This tool does **not** break paywalls.  
It automates what researchers already do manually — but faster, smarter, and more reliably.
---
## 📸 Screenshot
<p align="center">
  <img src="https://i.postimg.cc/VsHJP9kY/Untitled.png" alt="Screenshot of the program" width="600">
</p>
---
## ✨ Features
### 🔍 DOI Extraction & Validation  
Accepts raw DOIs or DOI URLs and automatically extracts the correct identifier.
### 🌐 Multi‑Source Open‑Access Search  
The tool checks a wide range of legal, public sources:
- **Unpaywall API**
- **Google Scholar (public results)**
- **Wayback Machine**
- **bioRxiv**
- **CORE API** (optional)
- **Zenodo**
- **Author‑uploaded PDFs** (via Google search)
- **ResearchGate** (public pages, Selenium optional)
- **ACS Publications** (open‑access links, Selenium optional)
### 🔁 Smart Retry Logic  
- Capped exponential backoff  
- Randomized user‑agents  
- Graceful handling of timeouts and failures  
### 📝 Logging  
All activity is logged to:
