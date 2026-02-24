import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import validators
from urllib.parse import quote
import sys
import time
import re
import logging
import random
from colorama import init, Fore, Style

# =========================
# CONFIG
# =========================

USER_EMAIL = "your_email@example.com"  # for Unpaywall
CORE_API_KEY = ""  # optional, if you have one
ENABLE_SELENIUM = True  # set False if you don't want Selenium-based sources

# =========================
# INIT
# =========================

init(autoreset=True)

logging.basicConfig(
    filename="paywall_bypass.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =========================
# UTILS
# =========================

def validate_url(url: str) -> bool:
    """Validate if the URL is syntactically valid and HTTP(S)."""
    if not validators.url(url):
        logging.warning(f"Invalid URL: {url}")
        return False
    if not (url.startswith("https://") or url.startswith("http://")):
        logging.warning(f"Non-HTTP(S) URL rejected: {url}")
        return False
    return True


def extract_doi(doi_input: str) -> str | None:
    """Extract DOI identifier from a full DOI URL or plain DOI."""
    doi_pattern = r"(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)"
    match = re.search(doi_pattern, doi_input, re.I)
    if match:
        return match.group(1)
    return None


def retry_request(url, headers=None, retries=5, timeout=15):
    """Retry HTTP requests with capped exponential backoff and User-Agent rotation."""
    headers = headers or {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ])
    }
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logging.error(f"Request failed for {url}: {e}")
            print(f"{Fore.RED}🔴 Request failed for {url}: {e}")
            if i == retries - 1:
                return None
            delay = min(2 ** i, 30)
            time.sleep(delay)
    return None


def init_selenium_driver():
    """Initialize a headless Chrome driver."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(60)
        return driver
    except Exception as e:
        logging.error(f"Selenium initialization error: {e}")
        print(f"{Fore.RED}🔴 Selenium initialization error: {e}")
        return None

# =========================
# SOURCES
# =========================

def query_unpaywall(doi: str):
    """Query Unpaywall API for open-access versions."""
    print(f"{Fore.CYAN}🕵️‍♂️ Querying Unpaywall for DOI: {doi}")
    logging.info(f"Querying Unpaywall for DOI: {doi}")
    api_url = f"https://api.unpaywall.org/v2/{doi}?email={USER_EMAIL}"
    response = retry_request(api_url)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No Unpaywall response")
        return None
    try:
        data = response.json()
        if data.get("is_oa") and data.get("best_oa_location"):
            url = data["best_oa_location"].get("url")
            if url and validate_url(url):
                logging.info(f"Found Unpaywall OA URL: {url}")
                print(f"{Fore.GREEN}✅ Found Unpaywall OA URL: {url}")
                return url
    except ValueError as e:
        logging.error(f"Unpaywall JSON parsing error: {e}")
        print(f"{Fore.RED}🔴 Unpaywall JSON parsing error: {e}")
    print(f"{Fore.YELLOW}⚠️ No Unpaywall OA URL found")
    return None


def search_google_scholar(doi: str):
    """Search Google Scholar for alternative article versions."""
    print(f"{Fore.CYAN}🕵️‍♂️ Searching Google Scholar for DOI: {doi}")
    logging.info(f"Searching Google Scholar for DOI: {doi}")
    query = f"https://scholar.google.com/scholar?q={quote(doi)}"
    response = retry_request(query)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No Google Scholar results")
        return None
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.endswith(".pdf") and validate_url(href):
                logging.info(f"Found PDF on Google Scholar: {href}")
                print(f"{Fore.GREEN}✅ Found Google Scholar PDF: {href}")
                return href
            if "pdf" in href.lower() and validate_url(href):
                logging.info(f"Found potential PDF on Google Scholar: {href}")
                print(f"{Fore.GREEN}✅ Found potential Google Scholar PDF: {href}")
                return href
    except Exception as e:
        logging.error(f"Google Scholar parsing error: {e}")
        print(f"{Fore.RED}🔴 Google Scholar parsing error: {e}")
    print(f"{Fore.YELLOW}⚠️ No Google Scholar PDF found")
    return None


def check_wayback_machine(doi: str):
    """Check Wayback Machine for cached article versions."""
    print(f"{Fore.CYAN}🕵️‍♂️ Checking Wayback Machine for DOI: {doi}")
    logging.info(f"Checking Wayback Machine for DOI: {doi}")
    doi_url = f"https://doi.org/{doi}"
    wayback_url = f"https://archive.org/wayback/available?url={quote(doi_url)}"
    response = retry_request(wayback_url)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No Wayback Machine results")
        return None
    try:
        data = response.json()
        closest = data.get("archived_snapshots", {}).get("closest", {})
        archived_url = closest.get("url")
        if archived_url and validate_url(archived_url):
            logging.info(f"Found archived version: {archived_url}")
            print(f"{Fore.GREEN}✅ Found archived version: {archived_url}")
            return archived_url
    except ValueError as e:
        logging.error(f"Wayback Machine JSON parsing error: {e}")
        print(f"{Fore.RED}🔴 Wayback Machine JSON parsing error: {e}")
    print(f"{Fore.YELLOW}⚠️ No Wayback Machine archive found")
    return None


def query_biorxiv(doi: str):
    """Query bioRxiv for article by DOI."""
    print(f"{Fore.CYAN}🕵️‍♂️ Querying bioRxiv for DOI: {doi}")
    logging.info(f"Querying bioRxiv for DOI: {doi}")
    api_url = f"https://api.biorxiv.org/details/biorxiv/{quote(doi)}"
    response = retry_request(api_url)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No bioRxiv results")
        return None
    try:
        data = response.json()
        collection = data.get("collection")
        if collection and collection[0].get("pdf_url"):
            pdf_url = collection[0]["pdf_url"]
            if validate_url(pdf_url):
                logging.info(f"Found bioRxiv PDF: {pdf_url}")
                print(f"{Fore.GREEN}✅ Found bioRxiv PDF: {pdf_url}")
                return pdf_url
    except ValueError as e:
        logging.error(f"bioRxiv JSON parsing error: {e}")
        print(f"{Fore.RED}🔴 bioRxiv JSON parsing error: {e}")
    print(f"{Fore.YELLOW}⚠️ No bioRxiv PDF found")
    return None


def query_core(doi: str):
    """Query CORE API for open-access articles."""
    if not CORE_API_KEY:
        return None
    print(f"{Fore.CYAN}🕵️‍♂️ Querying CORE for DOI: {doi}")
    logging.info(f"Querying CORE for DOI: {doi}")
    headers = {"Authorization": f"Bearer {CORE_API_KEY}"}
    api_url = f"https://api.core.ac.uk/v3/search/works/?q=doi:{quote(doi)}"
    response = retry_request(api_url, headers=headers)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No CORE results")
        return None
    try:
        data = response.json()
        for result in data.get("results", []):
            download = result.get("downloadUrl")
            if download and validate_url(download):
                logging.info(f"Found CORE PDF: {download}")
                print(f"{Fore.GREEN}✅ Found CORE PDF: {download}")
                return download
    except ValueError as e:
        logging.error(f"CORE JSON parsing error: {e}")
        print(f"{Fore.RED}🔴 CORE JSON parsing error: {e}")
    print(f"{Fore.YELLOW}⚠️ No CORE PDF found")
    return None


def query_zenodo(doi: str):
    """Query Zenodo for article by DOI."""
    print(f"{Fore.CYAN}🕵️‍♂️ Querying Zenodo for DOI: {doi}")
    logging.info(f"Querying Zenodo for DOI: {doi}")
    api_url = f"https://zenodo.org/api/records?q=doi:{quote(doi)}"
    response = retry_request(api_url)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No Zenodo results")
        return None
    try:
        data = response.json()
        for record in data.get("hits", {}).get("hits", []):
            for file in record.get("files", []):
                link = file.get("links", {}).get("self")
                if link and validate_url(link):
                    logging.info(f"Found Zenodo file: {link}")
                    print(f"{Fore.GREEN}✅ Found Zenodo file: {link}")
                    return link
    except ValueError as e:
        logging.error(f"Zenodo JSON parsing error: {e}")
        print(f"{Fore.RED}🔴 Zenodo JSON parsing error: {e}")
    print(f"{Fore.YELLOW}⚠️ No Zenodo file found")
    return None


def scrape_researchgate(doi: str):
    """Scrape ResearchGate for article using Selenium (public pages only)."""
    if not ENABLE_SELENIUM:
        return None
    print(f"{Fore.CYAN}🕵️‍♂️ Scraping ResearchGate for DOI: {doi}")
    logging.info(f"Scraping ResearchGate for DOI: {doi}")
    driver = init_selenium_driver()
    if not driver:
        return None
    try:
        query = f"https://www.researchgate.net/search/publication?q={quote(doi)}"
        driver.get(query)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(("tag name", "body")))
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "publication" in href and href.startswith("https://"):
                driver.get(href)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located(("tag name", "body")))
                time.sleep(3)
                inner_soup = BeautifulSoup(driver.page_source, "html.parser")
                pdf_link = inner_soup.find("a", href=True, string=re.compile("PDF|Download|Full-text|View", re.I))
                if pdf_link and validate_url(pdf_link["href"]):
                    logging.info(f"Found ResearchGate PDF: {pdf_link['href']}")
                    print(f"{Fore.GREEN}✅ Found ResearchGate PDF: {pdf_link['href']}")
                    return pdf_link["href"]
        print(f"{Fore.YELLOW}⚠️ No ResearchGate PDF found")
        return None
    except Exception as e:
        logging.error(f"ResearchGate scraping error: {e}")
        print(f"{Fore.RED}🔴 ResearchGate scraping error: {e}")
        return None
    finally:
        driver.quit()


def scrape_acs(doi: str):
    """Scrape ACS Publications for open-access or supporting information."""
    if not ENABLE_SELENIUM:
        return None
    print(f"{Fore.CYAN}🕵️‍♂️ Scraping ACS Publications for DOI: {doi}")
    logging.info(f"Scraping ACS Publications for DOI: {doi}")
    driver = init_selenium_driver()
    if not driver:
        return None
    acs_url = f"https://pubs.acs.org/doi/{doi}"
    try:
        driver.get(acs_url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(("tag name", "body")))
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        pdf_link = soup.find(
            "a",
            href=True,
            string=re.compile("PDF|Download|Full Text|Open Access|Supporting Information", re.I)
        )
        if pdf_link:
            href = pdf_link["href"]
            if not href.startswith("http"):
                href = f"https://pubs.acs.org{href}"
            if validate_url(href):
                logging.info(f"Found ACS link: {href}")
                print(f"{Fore.GREEN}✅ Found ACS link: {href}")
                return href
        print(f"{Fore.YELLOW}⚠️ No ACS PDF found")
        return None
    except Exception as e:
        logging.error(f"ACS scraping error: {e}")
        print(f"{Fore.RED}🔴 ACS scraping error: {e}")
        return None
    finally:
        driver.quit()


def search_author_profiles(doi: str):
    """Search for author-uploaded versions via Google (public PDFs)."""
    print(f"{Fore.CYAN}🕵️‍♂️ Searching author profiles for DOI: {doi}")
    logging.info(f"Searching author profiles for DOI: {doi}")
    query = f"site:*.edu OR site:researchgate.net OR site:academia.edu {doi} filetype:pdf"
    search_url = f"https://www.google.com/search?q={quote(query)}"
    response = retry_request(search_url)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No author profile results")
        return None
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("/url?q="):
                href = href.split("/url?q=")[1].split("&")[0]
            if href.endswith(".pdf") and validate_url(href):
                logging.info(f"Found author-uploaded PDF: {href}")
                print(f"{Fore.GREEN}✅ Found author-uploaded PDF: {href}")
                return href
    except Exception as e:
        logging.error(f"Author profile search error: {e}")
        print(f"{Fore.RED}🔴 Author profile search error: {e}")
    print(f"{Fore.YELLOW}⚠️ No author-uploaded PDF found")
    return None

# =========================
# MAIN SEARCH PIPELINE
# =========================

def find_article(doi: str):
    """Main function to find article using open-access oriented techniques."""
    logging.info(f"Starting search for DOI: {doi}")
    print(f"{Fore.BLUE}🔍 Searching for article with DOI: {doi}")

    steps = [
        query_unpaywall,
        search_google_scholar,
        check_wayback_machine,
        query_biorxiv,
        query_core,
        query_zenodo,
        scrape_researchgate,
        scrape_acs,
        search_author_profiles,
    ]

    for step in steps:
        try:
            url = step(doi)
            if url:
                return url
        except Exception as e:
            logging.error(f"Error in step {step.__name__}: {e}")
            print(f"{Fore.RED}🔴 Error in {step.__name__}: {e}")

    print(f"{Fore.RED}❌ No accessible version found. Try contacting the author or using institutional/open-access channels.")
    logging.info(f"No accessible version found for DOI: {doi}")
    return None

# =========================
# CLI ENTRY
# =========================

def main():
    print(f"{Fore.BLUE}📝 Enter the DOI URL or DOI (e.g., https://doi.org/10.1000/xyz123 or 10.1000/xyz123):")
    doi_input = input().strip()
    doi = extract_doi(doi_input)
    if not doi:
        print(f"{Fore.RED}❌ Invalid DOI format. Example: https://doi.org/10.1000/xyz123 or 10.1000/xyz123")
        logging.error(f"Invalid DOI input: {doi_input}")
        return

    result = find_article(doi)
    if result:
        print(f"{Fore.GREEN}🎉 Success! Access the article at: {result}")
        logging.info(f"Success! Found article at: {result}")
    else:
        print(f"{Fore.RED}❌ Failed to find an accessible version.")
        logging.info("Failed to find an accessible version.")

if __name__ == "__main__":
    main()
