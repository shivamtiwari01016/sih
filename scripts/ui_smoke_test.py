#!/usr/bin/env python3
"""Headless Chrome end-to-end test for the CivicResolve frontend.

Prerequisites:
  * the backend (http://localhost:8000) and frontend (http://localhost:3000)
    are running;
  * Google Chrome/Chromium is installed;
  * ``requests`` and ``websocket-client`` are available.

The test registers a uniquely named institution and complaint through the UI,
checks that the new complaint immediately produced overlap suggestions, records
a case action and visits every page. It intentionally writes demo rows, so run
``python3 scripts/seed_demo_data.py`` afterwards to reset the data (or delete the
test rows through the API).

Override defaults with FRONTEND_URL, CHROME_BIN or UI_TEST_SCREENSHOTS.
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

import requests
import websocket

FRONTEND = os.environ.get("FRONTEND_URL", "http://localhost:3000")
PORT = 9222
PROFILE = tempfile.mkdtemp(prefix="civicresolve-chrome-")
SHOTS = os.environ.get("UI_TEST_SCREENSHOTS") or tempfile.mkdtemp(
    prefix="civicresolve-ui-shots-"
)
CHROME_BIN = os.environ.get("CHROME_BIN", "google-chrome")

results = []


def check(name, condition, detail=""):
    results.append((bool(condition), name, detail))
    print(("PASS " if condition else "FAIL ") + name + ("" if condition else f" :: {detail}"))
    return condition


def start_chrome():
    shutil.rmtree(PROFILE, ignore_errors=True)
    os.makedirs(PROFILE, exist_ok=True)
    os.makedirs(SHOTS, exist_ok=True)
    process = subprocess.Popen(
        [
            CHROME_BIN,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--remote-allow-origins=*",
            f"--remote-debugging-port={PORT}",
            f"--user-data-dir={PROFILE}",
            "--window-size=1600,1000",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        try:
            response = requests.get(f"http://127.0.0.1:{PORT}/json/version", timeout=1)
            if response.ok:
                return process
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("Chrome did not start")


class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=30)
        self.next_id = 0

    def send(self, method, params=None):
        self.next_id += 1
        message_id = self.next_id
        self.ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == message_id:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})

    def eval(self, expression):
        result = self.send(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
                "userGesture": True,
            },
        )
        if result.get("exceptionDetails"):
            raise RuntimeError(result["exceptionDetails"].get("text") or result["exceptionDetails"])
        return result.get("result", {}).get("value")

    def wait_for(self, expression, timeout=20, label=""):
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            try:
                last = self.eval(expression)
                if last:
                    return last
            except Exception as exc:  # noqa: BLE001
                last = str(exc)
            time.sleep(0.25)
        raise RuntimeError(f"Timed out waiting for {label or expression}. Last={last!r}")

    def navigate(self, path):
        self.send("Page.navigate", {"url": FRONTEND + path})

    def shot(self, name):
        data = self.send("Page.captureScreenshot", {"format": "png"})
        path = os.path.join(SHOTS, name)
        with open(path, "wb") as handle:
            handle.write(base64.b64decode(data["data"]))
        return path


HELPERS = r"""
window.__text = () => document.body ? document.body.innerText : '';
window.__set = (el, value) => {
  if (!el) return false;
  const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype
    : el.tagName === 'SELECT' ? HTMLSelectElement.prototype
    : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value);
  el.dispatchEvent(new Event(el.tagName === 'SELECT' ? 'change' : 'input', {bubbles: true}));
  return true;
};
window.__clickText = (text, selector) => {
  const nodes = [...document.querySelectorAll(selector || 'button,a')];
  const el = nodes.find(node => node.textContent.trim() === text)
    || nodes.find(node => node.textContent.trim().includes(text));
  if (!el) return false;
  el.click();
  return true;
};
window.__setByPlaceholder = (placeholder, value) => {
  const el = document.querySelector('[placeholder="' + placeholder + '"]');
  return window.__set(el, value);
};
window.__selectByLabel = (label, valueContains) => {
  const labels = [...document.querySelectorAll('label')];
  const field = labels.find(l => l.textContent.includes(label));
  if (!field) return false;
  const select = field.querySelector('select');
  if (!select) return false;
  const option = [...select.options].find(o => o.textContent.includes(valueContains));
  if (!option) return false;
  return window.__set(select, option.value);
};
"""


def main():
    try:
        requests.get(FRONTEND, timeout=5).raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"Frontend is not reachable at {FRONTEND}: {exc}", file=sys.stderr)
        print("Start the backend and frontend first (see README).", file=sys.stderr)
        return 2
    chrome = start_chrome()
    try:
        tab = requests.put(f"http://127.0.0.1:{PORT}/json/new?{FRONTEND}/login", timeout=5).json()
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cdp.send("Page.enable")
        cdp.send("Runtime.enable")
        cdp.eval(HELPERS)

        unique = "UI Test Institute " + uuid.uuid4().hex[:6]
        subject = "UI test complaint about laboratory safety " + uuid.uuid4().hex[:4]

        # --- Login page -----------------------------------------------------
        cdp.wait_for("document.body.innerText.includes('Sign in')", label="login page")
        check("login page renders", "DEMO ENVIRONMENT" in cdp.eval("document.body.innerText"))
        check("login page has demo quick-fill", "QUICK-FILL DEMO ACCOUNTS" in cdp.eval("document.body.innerText"))
        cdp.shot("01-login.png")

        cdp.eval("window.__clickText('Sign in', 'button')")
        cdp.wait_for("location.pathname === '/dashboard'", label="dashboard navigation")
        cdp.wait_for("document.body.innerText.includes('TOTAL COMPLAINTS')", label="dashboard KPI")
        text = cdp.eval("document.body.innerText")
        check("dashboard renders live KPIs", "TOTAL COMPLAINTS" in text and "Bureau Workload" in text)
        check("dashboard charts render", cdp.eval("document.querySelectorAll('svg.recharts-surface').length > 0"))
        check("dashboard has no server error", "Internal Server Error" not in text and "Cannot reach the server" not in text)
        cdp.shot("02-dashboard.png")

        # --- Institutions ---------------------------------------------------
        cdp.eval("window.__clickText('Institutions', 'a')")
        cdp.wait_for("location.pathname === '/institutions'", label="institutions route")
        cdp.wait_for("document.body.innerText.includes('Institution Registry')", label="institutions page")
        cdp.wait_for("document.querySelectorAll('tbody tr').length > 0", label="institution rows")
        rows = cdp.eval("document.querySelectorAll('tbody tr').length")
        check("institution list loads", rows >= 50, f"rows={rows}")

        cdp.eval("window.__clickText('Add Institution', 'button')")
        cdp.wait_for("document.body.innerText.includes('Register institution')", label="add institution modal")
        filled = cdp.eval(
            "window.__setByPlaceholder('e.g. Western Valley Institute of Technology', %s)"
            % json.dumps(unique)
        )
        check("institution form accepts input", filled)
        cdp.eval("window.__clickText('Save institution', 'button')")
        cdp.wait_for(
            "document.body.innerText.includes(%s)" % json.dumps(unique),
            label="new institution in list",
        )
        check("institution registered from UI", True)
        cdp.shot("03-institutions.png")

        # --- Complaint registration ----------------------------------------
        cdp.eval("window.__clickText('Complaint Registry', 'a')")
        cdp.wait_for("location.pathname === '/complaints'", label="complaints route")
        cdp.wait_for("document.body.innerText.includes('Complaint Registry')", label="complaints page")
        cdp.wait_for("document.querySelectorAll('tbody tr').length > 0", label="complaint rows")

        cdp.eval("window.__clickText('Register Complaint', 'button')")
        cdp.wait_for("document.body.innerText.includes('Register complaint')", label="register complaint modal")
        selected = cdp.eval("window.__selectByLabel('Institution', %s)" % json.dumps(unique))
        check("institution selectable in complaint form", selected)
        cdp.eval("window.__setByPlaceholder('Short summary of the complaint', %s)" % json.dumps(subject))
        cdp.eval(
            "window.__setByPlaceholder('Describe the complaint in detail…', %s)"
            % json.dumps("Laboratory safety equipment is missing and students are exposed to risk during practical sessions.")
        )
        check("complaint form accepts input", True)
        cdp.eval("window.__clickText('Register complaint', 'button')")
        cdp.wait_for("!document.body.innerText.includes('Register complaint')", label="complaint modal closed")
        cdp.wait_for(
            "document.body.innerText.includes(%s)" % json.dumps(subject),
            label="complaint in table",
        )
        check("complaint registered from UI", True)
        cdp.shot("04-complaints.png")

        # --- Automatic overlap suggestions ----------------------------------
        cdp.navigate("/overlaps")
        cdp.wait_for(
            "document.body.innerText.includes('Overlap Intelligence')",
            label="overlaps page after registration",
        )
        cdp.wait_for(
            "!document.body.innerText.includes('No overlap suggestions')",
            label="auto-generated overlap suggestions",
        )
        overlap_body = cdp.eval("document.body.innerText")
        check(
            "new complaint generated overlap suggestions",
            "Suggested" in overlap_body and "Same complaint category" in overlap_body,
        )
        cdp.shot("04b-overlaps-auto.png")
        cdp.navigate("/complaints")
        cdp.wait_for(
            "document.body.innerText.includes('Complaint Registry')",
            label="complaints page return",
        )
        cdp.eval(HELPERS)

        # --- Complaint detail + action --------------------------------------
        cdp.eval("window.__setByPlaceholder('Search number, subject, institution…', %s)" % json.dumps(subject))
        cdp.wait_for("document.querySelectorAll('tbody tr').length === 1", label="filtered complaint row")
        cdp.eval("window.__clickText('Open', 'button')")
        cdp.wait_for("document.body.innerText.includes('Case history')", label="complaint detail")
        check("complaint detail opens", "Description" in cdp.eval("document.body.innerText"))
        cdp.eval("window.__clickText('Update / Status', 'button')")
        cdp.wait_for("document.body.innerText.includes('ACTION TYPE')", label="action tab")
        cdp.eval(
            "window.__setByPlaceholder('What was done on this case?', %s)"
            % json.dumps("UI test: initial documents reviewed.")
        )
        cdp.eval("window.__clickText('Record action', 'button')")
        cdp.wait_for("document.body.innerText.includes('Action recorded')", label="action toast")
        check("case action recorded from UI", True)
        cdp.eval("document.querySelector('[aria-label=\"Close\"]').click()")
        cdp.wait_for("!document.body.innerText.includes('ACTION TYPE')", label="detail modal closed")

        # --- Remaining pages ------------------------------------------------
        pages = [
            ("/overlaps", "Overlap Intelligence", "AWAITING REVIEW"),
            ("/coordination", "Case Coordination", "Cross-bureau requests"),
            ("/notifications", "Alerts & Notifications", "Mark all read"),
            ("/reports", "Reports & Analytics", "Bureau performance"),
            ("/bureaus", "Bureau Management", "Regulation Bureau"),
            ("/users", "User Management", "Case Officer"),
            ("/audit-logs", "Audit Logs", "Immutable trail"),
            ("/settings", "Settings", "Change password"),
        ]
        for path, heading, marker in pages:
            cdp.navigate(path)
            cdp.wait_for(
                "document.body.innerText.includes(%s)" % json.dumps(heading),
                label=f"{path} heading",
            )
            body = cdp.eval("document.body.innerText")
            check(
                f"{path} renders",
                marker in body and "Internal Server Error" not in body,
                f"marker={marker!r}",
            )
            if path == "/reports":
                cdp.wait_for("document.querySelectorAll('svg.recharts-surface').length > 0", label="report charts")
                check("reports charts render", True)
            if path == "/audit-logs":
                cdp.wait_for("document.querySelectorAll('tbody tr').length > 0", label="audit rows")
                check("audit log entries load", True)
            cdp.shot("page" + path.replace("/", "-") + ".png")

        # --- Read-only senior management ------------------------------------
        cdp.eval("localStorage.removeItem('token'); location.href = '/login'")
        cdp.wait_for("document.body.innerText.includes('Sign in')", label="logout to login")
        cdp.eval(HELPERS)
        cdp.eval("window.__setByPlaceholder('admin@civicresolve.demo', 'mgmt@civicresolve.demo')")
        cdp.eval("window.__clickText('Sign in', 'button')")
        cdp.wait_for("location.pathname === '/dashboard'", label="management login")
        body = cdp.eval("document.body.innerText")
        check("read-only role has no user admin nav", "User Management" not in body)
        cdp.navigate("/institutions")
        cdp.wait_for("document.body.innerText.includes('Institution Registry')", label="management institutions")
        check(
            "read-only role cannot add institutions",
            "Add Institution" not in cdp.eval("document.body.innerText"),
        )
        cdp.shot("05-readonly.png")

        failed = [item for item in results if not item[0]]
        print(f"\n{len(results)} UI checks, {len(failed)} failed")
        if failed:
            for item in failed:
                print("FAILED:", item[1], item[2])
            return 1
        print("Screenshots:", SHOTS)
        return 0
    finally:
        chrome.terminate()
        try:
            chrome.wait(timeout=5)
        except Exception:
            chrome.kill()
        shutil.rmtree(PROFILE, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
