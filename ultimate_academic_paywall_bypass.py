#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paywall Bypass Helper - Open Access Article Finder
Finds legally accessible versions of academic papers using open-access APIs and sources.

⚠️ ETHICAL USE ONLY: This tool searches for legally available open-access versions.
   Always respect publisher terms, robots.txt, and copyright law.
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import validators
from urllib.parse import quote, unquote
import sys
import time
import re
import logging
import random
import os
from colorama import init, Fore, Style

# =========================
# CONFIG
# =========================

# ✅ Use environment variables for credentials (more secure)
USER_EMAIL = os.getenv("UNPAYWALL_EMAIL", "your_email@example.com")
CORE_API_KEY = os.getenv("CORE_API_KEY", "")
ENABLE_SELENIUM = True  # Set False if you don't want Selenium-based sources

# Rate limiting settings (be respectful to servers)
REQUEST_DELAY = (1, 3)  # Random delay between requests in seconds
MAX_RETRIES = 5
REQUEST_TIMEOUT = 15

# =========================
# INIT
# =========================

init(autoreset=True)

logging.basicConfig(
    filename="paywall_bypass.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# =========================
# UTILS
# =========================

def validate_url(url: str) -> bool:
    """Validate if the URL is syntactically valid and HTTP(S)."""
    if not url or not isinstance(url, str):
        return False
    if not validators.url(url):
        logging.warning(f"Invalid URL format: {url[:100]}")
        return False
    if not (url.startswith("https://") or url.startswith("http://")):
        logging.warning(f"Non-HTTP(S) URL rejected: {url[:100]}")
        return False
    return True


def extract_doi(doi_input: str) -> str | None:
    """Extract DOI identifier from a full DOI URL or plain DOI."""
    if not doi_input:
        return None
    # Pattern matches DOI format: 10.xxxx/...
    doi_pattern = r"(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)"
    match = re.search(doi_pattern, doi_input.strip(), re.I)
    if match:
        return match.group(1)
    return None


def retry_request(url, headers=None, retries=MAX_RETRIES, timeout=REQUEST_TIMEOUT):
    """Retry HTTP requests with capped exponential backoff and User-Agent rotation."""
    if not headers:
        headers = {
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
            ]),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }
    
    for i in range(retries):
        try:
            # Add random jitter to avoid hammering servers
            if i > 0:
                delay = min(2 ** i, 30) + random.uniform(0, 2)
                time.sleep(delay)
            
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout for {url} (attempt {i+1}/{retries})")
            print(f"{Fore.YELLOW}⏱️ Timeout for {url} (attempt {i+1}/{retries})")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "unknown"
            logging.warning(f"HTTP {status} for {url} (attempt {i+1}/{retries})")
            if status in [404, 410]:  # Don't retry permanent errors
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {url}: {e}")
            print(f"{Fore.RED}🔴 Request failed for {url}: {type(e).__name__}")
        
        if i == retries - 1:
            return None
            
    return None


def init_selenium_driver():
    """Initialize a headless Chrome driver with anti-detection options."""
    if not ENABLE_SELENIUM:
        return None
        
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Optional: Add proxy if needed (uncomment and configure)
    # options.add_argument("--proxy-server=http://127.0.0.1:9050")
    
    try:
        driver = webdriver.Chrome(options=options)
        # Hide webdriver property to avoid detection
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(60)
        return driver
    except Exception as e:
        logging.error(f"Selenium initialization error: {e}")
        print(f"{Fore.RED}🔴 Selenium error: {e}\n💡 Ensure ChromeDriver is installed and matches your Chrome version")
        return None


def safe_sleep(min_sec=1, max_sec=3):
    """Sleep for a random duration to avoid rate limiting."""
    time.sleep(random.uniform(min_sec, max_sec))

# =========================
# SOURCES
# =========================

def query_unpaywall(doi: str):
    """Query Unpaywall API for open-access versions."""
    print(f"{Fore.CYAN}🕵️‍♂️ Querying Unpaywall for DOI: {doi}")
    logging.info(f"Querying Unpaywall for DOI: {doi}")
    
    # ✅ FIXED: Removed extra spaces in URL
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
    except Exception as e:
        logging.error(f"Unpaywall unexpected error: {e}")
        
    print(f"{Fore.YELLOW}⚠️ No Unpaywall OA URL found")
    return None


def search_google_scholar(doi: str):
    """Search Google Scholar for alternative article versions."""
    print(f"{Fore.CYAN}🕵️‍♂️ Searching Google Scholar for DOI: {doi}")
    logging.info(f"Searching Google Scholar for DOI: {doi}")
    
    # ✅ FIXED: Removed extra spaces
    query = f"https://scholar.google.com/scholar?q={quote(doi)}"
    
    response = retry_request(query)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No Google Scholar results")
        return None
        
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            
            # ✅ FIXED: Properly parse Google Scholar redirect URLs
            if href.startswith("/url?q="):
                raw_url = href.split("/url?q=")[1].split("&")[0]
                decoded_url = unquote(raw_url)
                
                if decoded_url.lower().endswith(".pdf") and validate_url(decoded_url):
                    logging.info(f"Found PDF on Google Scholar: {decoded_url}")
                    print(f"{Fore.GREEN}✅ Found Google Scholar PDF: {decoded_url}")
                    return decoded_url
            elif href.lower().endswith(".pdf") and validate_url(href):
                logging.info(f"Found direct PDF on Google Scholar: {href}")
                print(f"{Fore.GREEN}✅ Found Google Scholar PDF: {href}")
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
    
    # ✅ FIXED: Removed extra spaces
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
    except Exception as e:
        logging.error(f"Wayback Machine unexpected error: {e}")
        
    print(f"{Fore.YELLOW}⚠️ No Wayback Machine archive found")
    return None


def query_biorxiv(doi: str):
    """Query bioRxiv for article by DOI."""
    print(f"{Fore.CYAN}🕵️‍♂️ Querying bioRxiv for DOI: {doi}")
    logging.info(f"Querying bioRxiv for DOI: {doi}")
    
    # ✅ FIXED: Removed extra spaces
    api_url = f"https://api.biorxiv.org/details/biorxiv/{quote(doi)}"
    
    response = retry_request(api_url)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No bioRxiv results")
        return None
        
    try:
        data = response.json()
        collection = data.get("collection", [])
        if collection and isinstance(collection, list) and len(collection) > 0:
            pdf_url = collection[0].get("pdf_url")
            if pdf_url and validate_url(pdf_url):
                logging.info(f"Found bioRxiv PDF: {pdf_url}")
                print(f"{Fore.GREEN}✅ Found bioRxiv PDF: {pdf_url}")
                return pdf_url
    except ValueError as e:
        logging.error(f"bioRxiv JSON parsing error: {e}")
        print(f"{Fore.RED}🔴 bioRxiv JSON parsing error: {e}")
    except Exception as e:
        logging.error(f"bioRxiv unexpected error: {e}")
        
    print(f"{Fore.YELLOW}⚠️ No bioRxiv PDF found")
    return None


def query_core(doi: str):
    """Query CORE API for open-access articles."""
    if not CORE_API_KEY:
        logging.debug("CORE API key not set, skipping")
        return None
        
    print(f"{Fore.CYAN}🕵️‍♂️ Querying CORE for DOI: {doi}")
    logging.info(f"Querying CORE for DOI: {doi}")
    
    headers = {
        "Authorization": f"Bearer {CORE_API_KEY}",
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
        ])
    }
    
    # ✅ FIXED: Removed extra spaces
    api_url = f"https://api.core.ac.uk/v3/search/works/?q=doi:{quote(doi)}"
    
    response = retry_request(api_url, headers=headers)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No CORE results")
        return None
        
    try:
        data = response.json()
        for result in data.get("results", []):
            download = result.get("downloadUrl") or result.get("sourceUrl")
            if download and validate_url(download):
                logging.info(f"Found CORE PDF: {download}")
                print(f"{Fore.GREEN}✅ Found CORE PDF: {download}")
                return download
    except ValueError as e:
        logging.error(f"CORE JSON parsing error: {e}")
        print(f"{Fore.RED}🔴 CORE JSON parsing error: {e}")
    except Exception as e:
        logging.error(f"CORE unexpected error: {e}")
        
    print(f"{Fore.YELLOW}⚠️ No CORE PDF found")
    return None


def query_zenodo(doi: str):
    """Query Zenodo for article by DOI."""
    print(f"{Fore.CYAN}🕵️‍♂️ Querying Zenodo for DOI: {doi}")
    logging.info(f"Querying Zenodo for DOI: {doi}")
    
    # ✅ FIXED: Removed extra spaces
    api_url = f"https://zenodo.org/api/records?q=doi:{quote(doi)}"
    
    response = retry_request(api_url)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No Zenodo results")
        return None
        
    try:
        data = response.json()
        # ✅ FIXED: Handle both old and new Zenodo API response formats
        hits = data.get("hits", [])
        if not hits and "results" in data:
            hits = data.get("results", [])
            
        for record in hits:
            files = record.get("files", [])
            # Handle dict vs list format for files
            if isinstance(files, dict):
                files = list(files.values())
                
            for file in files:
                # Try multiple possible URL fields
                link = (file.get("links", {}).get("self") or 
                       file.get("url") or 
                       file.get("download_url"))
                if link and validate_url(link):
                    logging.info(f"Found Zenodo file: {link}")
                    print(f"{Fore.GREEN}✅ Found Zenodo file: {link}")
                    return link
    except ValueError as e:
        logging.error(f"Zenodo JSON parsing error: {e}")
        print(f"{Fore.RED}🔴 Zenodo JSON parsing error: {e}")
    except Exception as e:
        logging.error(f"Zenodo unexpected error: {e}")
        
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
        # ✅ FIXED: Removed extra spaces
        query = f"https://www.researchgate.net/search/publication?q={quote(doi)}"
        driver.get(query)
        safe_sleep(2, 4)
        
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(("tag name", "body")))
        safe_sleep(1, 2)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Look for publication links
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "publication" in href and href.startswith("https://www.researchgate.net/publication/"):
                driver.get(href)
                safe_sleep(2, 4)
                WebDriverWait(driver, 15).until(EC.presence_of_element_located(("tag name", "body")))
                
                inner_soup = BeautifulSoup(driver.page_source, "html.parser")
                
                # ✅ IMPROVED: More specific regex pattern for PDF links
                pdf_link = inner_soup.find(
                    "a", 
                    href=True, 
                    string=re.compile(r"\b(PDF|Download\s+PDF|Full[\s-]?text|View\s+PDF)\b", re.I)
                )
                
                if pdf_link and validate_url(pdf_link["href"]):
                    pdf_url = pdf_link["href"]
                    # Handle relative URLs
                    if pdf_url.startswith("/"):
                        pdf_url = f"https://www.researchgate.net{pdf_url}"
                    if validate_url(pdf_url):
                        logging.info(f"Found ResearchGate PDF: {pdf_url}")
                        print(f"{Fore.GREEN}✅ Found ResearchGate PDF: {pdf_url}")
                        return pdf_url
                        
        print(f"{Fore.YELLOW}⚠️ No ResearchGate PDF found")
        return None
        
    except TimeoutException:
        logging.warning("ResearchGate: Page load timeout")
        print(f"{Fore.YELLOW}⏱️ ResearchGate timeout")
        return None
    except Exception as e:
        logging.error(f"ResearchGate scraping error: {e}")
        print(f"{Fore.RED}🔴 ResearchGate error: {type(e).__name__}")
        return None
    finally:
        try:
            driver.quit()
        except:
            pass


def scrape_acs(doi: str):
    """Scrape ACS Publications for open-access or supporting information."""
    if not ENABLE_SELENIUM:
        return None
        
    print(f"{Fore.CYAN}🕵️‍♂️ Scraping ACS Publications for DOI: {doi}")
    logging.info(f"Scraping ACS Publications for DOI: {doi}")
    
    driver = init_selenium_driver()
    if not driver:
        return None
        
    # ✅ FIXED: Removed extra spaces
    acs_url = f"https://pubs.acs.org/doi/{doi}"
    
    try:
        driver.get(acs_url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(("tag name", "body")))
        safe_sleep(2, 4)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Look for PDF/Full Text links
        pdf_link = soup.find(
            "a",
            href=True,
            string=re.compile(r"\b(PDF|Download|Full\s*Text|Open\s*Access|Supporting\s*Information)\b", re.I)
        )
        
        if pdf_link:
            href = pdf_link["href"]
            # ✅ FIXED: Properly construct absolute URL without extra space
            if not href.startswith("http"):
                href = f"https://pubs.acs.org{href}"
            if validate_url(href):
                logging.info(f"Found ACS link: {href}")
                print(f"{Fore.GREEN}✅ Found ACS link: {href}")
                return href
                
        print(f"{Fore.YELLOW}⚠️ No ACS PDF found")
        return None
        
    except TimeoutException:
        logging.warning("ACS: Page load timeout")
        print(f"{Fore.YELLOW}⏱️ ACS timeout")
        return None
    except Exception as e:
        logging.error(f"ACS scraping error: {e}")
        print(f"{Fore.RED}🔴 ACS error: {type(e).__name__}")
        return None
    finally:
        try:
            driver.quit()
        except:
            pass


def search_author_profiles(doi: str):
    """Search for author-uploaded versions via Google (public PDFs)."""
    print(f"{Fore.CYAN}🕵️‍♂️ Searching author profiles for DOI: {doi}")
    logging.info(f"Searching author profiles for DOI: {doi}")
    
    query = f"site:*.edu OR site:researchgate.net OR site:academia.edu \"{doi}\" filetype:pdf"
    
    # ✅ FIXED: Removed extra spaces
    search_url = f"https://www.google.com/search?q={quote(query)}"
    
    response = retry_request(search_url)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No author profile results")
        return None
        
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            
            # Parse Google redirect URL
            if href.startswith("/url?q="):
                raw_url = href.split("/url?q=")[1].split("&")[0]
                href = unquote(raw_url)  # ✅ FIXED: Added URL decoding
                
            if href.lower().endswith(".pdf") and validate_url(href):
                # Filter out known non-PDF domains
                if any(blocked in href.lower() for blocked in ["google", "doubleclick", "adservice"]):
                    continue
                logging.info(f"Found author-uploaded PDF: {href}")
                print(f"{Fore.GREEN}✅ Found author-uploaded PDF: {href}")
                return href
                
    except Exception as e:
        logging.error(f"Author profile search error: {e}")
        print(f"{Fore.RED}🔴 Author profile search error: {type(e).__name__}")
        
    print(f"{Fore.YELLOW}⚠️ No author-uploaded PDF found")
    return None


# =========================
# MAIN SEARCH PIPELINE
# =========================

def find_article(doi: str):
    """Main function to find article using open-access oriented techniques."""
    logging.info(f"🔍 Starting search for DOI: {doi}")
    print(f"{Fore.BLUE}🔍 Searching for article with DOI: {doi}\n")

    # Order sources by reliability and speed (fastest/most reliable first)
    steps = [
        ("Unpaywall", query_unpaywall),
        ("bioRxiv", query_biorxiv),
        ("Zenodo", query_zenodo),
        ("CORE", query_core),
        ("Wayback Machine", check_wayback_machine),
        ("Google Scholar", search_google_scholar),
        ("Author Profiles", search_author_profiles),
    ]
    
    # Add Selenium-based sources only if enabled
    if ENABLE_SELENIUM:
        steps.extend([
            ("ResearchGate", scrape_researchgate),
            ("ACS Publications", scrape_acs),
        ])

    for name, step in steps:
        try:
            print(f"\n{Fore.CYAN}→ Checking {name}...")
            safe_sleep(*REQUEST_DELAY)  # Be respectful
            url = step(doi)
            if url:
                return url
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️ Search interrupted by user")
            logging.warning("Search interrupted by user")
            return None
        except Exception as e:
            logging.error(f"Error in step {name}: {e}")
            print(f"{Fore.RED}🔴 Error in {name}: {type(e).__name__}")
            continue  # Continue with next source

    print(f"\n{Fore.RED}❌ No accessible version found.")
    print(f"{Fore.YELLOW}💡 Suggestions:")
    print(f"   • Contact the corresponding author directly")
    print(f"   • Check your institution's library access")
    print(f"   • Try the publisher's open access options")
    print(f"   • Search the author's institutional repository")
    
    logging.info(f"❌ No accessible version found for DOI: {doi}")
    return None


# =========================
# CLI ENTRY
# =========================

def print_banner():
    """Print application banner."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f"  🔓 Open Access Article Finder")
    print(f"  Finds legally accessible versions of academic papers")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}⚠️  ETHICAL USE ONLY: Respect copyright and publisher terms")
    print(f"{Fore.YELLOW}   This tool searches for OPEN ACCESS versions only.\n")


def main():
    print_banner()
    
    print(f"{Fore.BLUE}📝 Enter DOI or DOI URL:")
    print(f"   Examples: 10.1038/nature12345")
    print(f"            https://doi.org/10.1038/nature12345\n")
    
    doi_input = input(f"{Fore.WHITE}➤  ").strip()
    
    if not doi_input:
        print(f"{Fore.RED}❌ No input provided.")
        return
        
    doi = extract_doi(doi_input)
    if not doi:
        print(f"{Fore.RED}❌ Invalid DOI format.")
        print(f"{Fore.YELLOW}💡 Valid examples:")
        print(f"   • 10.1000/xyz123")
        print(f"   • https://doi.org/10.1000/xyz123")
        logging.error(f"Invalid DOI input: {doi_input}")
        return

    print(f"\n{Fore.CYAN}🔎 Extracted DOI: {doi}\n")
    result = find_article(doi)
    
    print(f"\n{Fore.CYAN}{'='*60}")
    if result:
        print(f"{Fore.GREEN}🎉 Success! Access the article at:")
        print(f"{Fore.WHITE}{Style.BRIGHT}{result}")
        print(f"{Fore.CYAN}{'='*60}\n")
        logging.info(f"✅ Found article at: {result}")
        
        # Optional: Copy to clipboard (requires pyperclip)
        try:
            import pyperclip
            pyperclip.copy(result)
            print(f"{Fore.GREEN}📋 URL copied to clipboard!\n")
        except ImportError:
            pass
    else:
        print(f"{Fore.RED}❌ Failed to find an accessible version.")
        print(f"{Fore.CYAN}{'='*60}\n")
        logging.info("❌ Failed to find an accessible version.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Exiting...")
        logging.info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}💥 Unexpected error: {e}")
        logging.exception("Unhandled exception")
        sys.exit(1)
