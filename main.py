import random
import socket
import subprocess
import asyncio
import requests
from ping3 import ping
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from itertools import islice
from proxyscrape import create_collector
from fp.fp import FreeProxy
from proxybroker import Broker
from tqdm import tqdm
import time
from free_proxy_list_net import get_proxy_list
import random
import tls_client

host = "127.0.0.1"
port = 9050
TOR_EXE_PATH = "./tor/tor/tor.exe"
TOR_RC_PATH = "./tor/tor/torrc"
SELECTED_PROXY = ""
TOR_PROCESS = None
PROXY_URL = "https://httpbin.org/ip"

# -----------------------------
# Check if a SOCKS proxy is running
# -----------------------------
def is_proxy_running(host,port):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        s.connect((host, port))
        return True
    except:
        return False

# -----------------------------
# Check if a HTTP proxy is running
# -----------------------------

def boot():

    global SELECTED_PROXY,TOR_PROCESS,PROXY_URL

    print("Proxy check")
    proxies = get_proxy_list(http_mode="https")

    try:
        print(proxies)
    except Exception as e:
        print("Failed to fetch proxy list:", e)
        return []
    for proxy in proxies:
        if(proxy[5] == 'yes' and proxy[6] == 'yes' ):
            fullprox = proxy[0] + ":" + proxy[1]
            try:
                r = requests.get(PROXY_URL, proxies={"http": fullprox, "https": fullprox}, timeout=8)
                print("OK:", r.json()["origin"])
                break
            except Exception:
                print("Failed")
    SELECTED_PROXY = fullprox
    with open(TOR_RC_PATH, "w") as f:
        f.write(f"HTTPProxy {SELECTED_PROXY}\n")
        f.write("SocksPort 9050\n")
        f.write("ControlPort 9051\n")
        f.write("Log notice stdout\n") # debugging
    SELECTED_PROXY = f"http://{SELECTED_PROXY}"
    TOR_PROCESS = start_tor()
    print(f"Using Tor → {SELECTED_PROXY}")

# -----------------------------
# Helper: Start Tor process
# -----------------------------
def start_tor():
    if is_proxy_running(host,port):
        print("Tor is already running ✅")
        return None  # Tor already running

    TOR_PROCESS = subprocess.Popen(
        [TOR_EXE_PATH, "-f", TOR_RC_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print("Starting Tor and waiting for bootstrap...")
    while True:
        line = TOR_PROCESS.stdout.readline()
        if not line:
            break
        print(line.strip())
        if "Bootstrapped 100%" in line:
            break
    return TOR_PROCESS

# -----------------------------
# Helper: Stop Tor process
# -----------------------------
def stop_tor():
    print("Stopping Tor")
    global TOR_PROCESS
    if TOR_PROCESS is not None:
        TOR_PROCESS.terminate()
        TOR_PROCESS = None
        print("Tor stopped.")
    else:
        print("Tor never started.")

# -----------------------------
# Helper: Reset Tor process
# -----------------------------



# -----------------------------
# Request via Tor (HTTP round-trip)
# -----------------------------

session = tls_client.Session(
    client_identifier="chrome_120",  # available: chrome_120, chrome_112, firefox_110, safari_17_0, etc.
    random_tls_extension_order=True  # makes fingerprint less detectable
)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br"
}

def search_request(url: str):
    global SELECTED_PROXY

    try:
        r = requests.get(PROXY_URL, proxies={"http": SELECTED_PROXY, "https": SELECTED_PROXY}, timeout=8)
        print("Operational:", r.json()["origin"])
    except Exception:
        print("Failed. Restarting")
        boot()
    try:

        #https://bot.sannysoft.com/
        #https://httpbin.org/headers

        resp = session.get(
            url,
            headers=headers,
            proxy=SELECTED_PROXY,
        )

        return resp

    except Exception as e:
        print(f"Error connection", e)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    #1.Boot
    boot()
    #2.Search
    search_request("https://bot.sannysoft.com/")
    #3.Stop
    stop_tor()
