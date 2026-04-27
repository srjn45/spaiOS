"""Chrome control agent via Chrome DevTools Protocol (CDP).

Chrome must be running with --remote-debugging-port=9222.
Use scripts/launch-chrome.sh to start it.
"""

import subprocess
import time
from pathlib import Path
from typing import Optional

import pychrome

_CDP_URL = "http://localhost:9222"
_LAUNCH_SCRIPT = Path(__file__).parents[4] / "scripts" / "launch-chrome.sh"
_CHROME_LAUNCH_WAIT = 2.0


class ChromeNotAvailable(Exception):
    """Raised when Chrome CDP endpoint is unreachable."""


class ChromeAgent:
    def __init__(self) -> None:
        self._browser: Optional[pychrome.Browser] = None
        self._tab: Optional[pychrome.Tab] = None

    def is_available(self) -> bool:
        try:
            import urllib.request

            urllib.request.urlopen(f"{_CDP_URL}/json/version", timeout=1)
            return True
        except Exception:
            return False

    def _ensure_connected(self) -> None:
        if self._browser is not None and self._tab is not None:
            return
        if not self.is_available():
            raise ChromeNotAvailable(
                "Chrome is not running with --remote-debugging-port=9222. "
                "Run scripts/launch-chrome.sh to start it."
            )
        self._browser = pychrome.Browser(url=_CDP_URL)
        tabs = self._browser.list_tab()
        if not tabs:
            self._tab = self._browser.new_tab()
        else:
            self._tab = tabs[0]
        self._tab.start()
        self._tab.Page.enable()

    def _launch_and_connect(self) -> None:
        if not _LAUNCH_SCRIPT.exists():
            raise ChromeNotAvailable(
                f"Launch script not found: {_LAUNCH_SCRIPT}. "
                "Chrome must be started manually with --remote-debugging-port=9222."
            )
        subprocess.Popen(
            ["bash", str(_LAUNCH_SCRIPT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(_CHROME_LAUNCH_WAIT)
        if not self.is_available():
            raise ChromeNotAvailable("Chrome launched but CDP port is not yet reachable.")
        self._browser = None
        self._tab = None
        self._ensure_connected()

    def open_url(self, url: str) -> str:
        """Navigate the active Chrome tab to url. Launches Chrome if not running."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        if not self.is_available():
            self._launch_and_connect()
        else:
            self._ensure_connected()
        self._tab.Page.navigate(url=url)
        time.sleep(0.5)
        return f"Navigated to {url}"

    def get_current_url(self) -> str:
        """Return the URL of the current active tab."""
        self._ensure_connected()
        result = self._tab.Runtime.evaluate(expression="window.location.href")
        return result.get("result", {}).get("value", "(unknown)")

    def get_page_content(self) -> str:
        """Return visible page text (body.innerText) truncated to 4000 chars."""
        self._ensure_connected()
        result = self._tab.Runtime.evaluate(
            expression="document.body ? document.body.innerText : ''"
        )
        text = result.get("result", {}).get("value", "")
        if len(text) > 4000:
            text = text[:4000] + "\n…(truncated)"
        return text or "(empty page)"

    def search_web(self, query: str) -> str:
        """Navigate Chrome to a Google search for query."""
        import urllib.parse

        url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
        return self.open_url(url)

    def click_element(self, selector: str) -> str:
        """Click the first element matching CSS selector."""
        self._ensure_connected()
        result = self._tab.Runtime.evaluate(expression=f"""
(function() {{
  var el = document.querySelector({repr(selector)});
  if (!el) return 'not_found';
  el.click();
  return 'clicked';
}})()
""")
        value = result.get("result", {}).get("value", "error")
        if value == "not_found":
            return f"No element found for selector: {selector}"
        return f"Clicked element: {selector}"

    def close(self) -> None:
        if self._tab is not None:
            try:
                self._tab.stop()
            except Exception:
                pass
        self._tab = None
        self._browser = None
