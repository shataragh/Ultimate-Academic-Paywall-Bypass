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
This tool does **not** break paywalls. It automates what researchers already do manually — but faster, smarter, and more reliably.

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
- Unpaywall API  
- Google Scholar (public results)  
- Wayback Machine  
- bioRxiv  
- CORE API (optional)  
- Zenodo  
- Author‑uploaded PDFs (via Google search)  
- ResearchGate (public pages, Selenium optional)  
- ACS Publications (open‑access links, Selenium optional)

### 🔁 Smart Retry Logic
- Capped exponential backoff  
- Randomized user‑agents  
- Graceful handling of timeouts and failures  

### 📝 Logging
All activity is logged to `paywall_bypass.log`.

### ⚙️ Optional Selenium Support
For platforms that require dynamic rendering (ResearchGate, ACS).

---

## 🛠️ Installation
Clone the repository:
git clone https://github.com/shataragh/ultimate-academic-paywall-bypass.git  
cd ultimate-academic-paywall-bypass

Install dependencies:
pip install -r requirements.txt

### ✔ Updated `requirements.txt`
requests>=2.31.0  
beautifulsoup4>=4.12.2  
selenium>=4.15.2  
validators>=0.22.0  
colorama>=0.4.6  
Optional (for faster HTML parsing):  
lxml>=4.9.3

---

## ▶️ Usage
Run the script:
python ultimate_academic_paywall_bypass.py

Enter a DOI or DOI URL:
10.1038/s41586-020-2649-2

The tool will automatically:
1. Validate the DOI  
2. Query multiple open‑access sources  
3. Return the first accessible version found  

---

## ⚠️ Disclaimer
This tool:
- Does **not** break paywalls  
- Does **not** bypass authentication  
- Does **not** access restricted content  
- Only retrieves **publicly available** open‑access versions of academic articles  

Use responsibly and in accordance with your local laws.

---

## ❤️ Purpose
This project was created to support researchers — especially those in regions affected by sanctions, limited institutional access, or financial barriers — ensuring that scientific knowledge remains accessible to everyone.

---

## 📄 License
This project is licensed under the **MIT License**.
