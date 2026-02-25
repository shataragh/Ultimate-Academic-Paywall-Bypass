## 🛠️ Installation

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
### 3. Install ChromeDriver (for Selenium features)
⚠️ Required only if ENABLE_SELENIUM = True (for ResearchGate/ACS scraping)
#### Option A: Manual Install
1. Check your Chrome version by visiting chrome://version/ in your browser
2. Download the matching ChromeDriver: https://chromedriver.chromium.org/downloads
3. Extract and add to your system PATH, or place the executable in your project root
##### Option B: Use webdriver-manager (Recommended ✅)
```bash
pip install webdriver-manager
```
Then update the init_selenium_driver() function in the script:
```bash
from webdriver_manager.chrome import ChromeDriverManager

def init_selenium_driver():
    # ... existing options setup ...
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    # ... rest of function ...
```
##### Verify Installation
```bash
# Test ChromeDriver is accessible
chromedriver --version

# Or test via Python
python -c "from selenium import webdriver; print('✅ Selenium ready')"
```
### Configure Environment Variables (Recommended)
🔐 Keeps credentials out of source code and version control
#### Linux / macOS
```bash
# Add to ~/.bashrc, ~/.zshrc, or current session:
export UNPAYWALL_EMAIL="your_registered_email@example.com"
export CORE_API_KEY="your_core_api_key"  # Optional - get from https://core.ac.uk/services/api

# Reload shell config (if added to rc file):
source ~/.bashrc  # or source ~/.zshrc
```
#### Windows (Command Prompt)
```bash
set UNPAYWALL_EMAIL=your_registered_email@example.com
set CORE_API_KEY=your_core_api_key
```
#### Windows (PowerShell)
```bash
$env:UNPAYWALL_EMAIL="your_registered_email@example.com"
$env:CORE_API_KEY="your_core_api_key"
```
#### Permanent Setup (.env file + python-dotenv)
1. Install dotenv support:
```bash
pip install python-dotenv
```
2. Create a .env file in project root:
```bash
UNPAYWALL_EMAIL=your_registered_email@example.com
CORE_API_KEY=your_core_api_key
```
3. Add to .gitignore to avoid committing secrets:
```bash
# Credentials
.env
*.log
__pycache__/
```
4. Load in script (add near top of ultimate_academic_paywall_bypass.py):
```bash
from dotenv import load_dotenv
load_dotenv()  # Loads variables from .env into os.environ
```
🔑 Register your email at Unpaywall for higher rate limits (100k requests/day) and proper attribution.
