import httpx
from bs4 import BeautifulSoup

try:
    from playwright.async_api import Error as PlaywrightError
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from sidekick.utils import ui


async def _playwright_fetch(url: str, timeout: int) -> str:
    try:
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                try:
                    await page.goto(
                        url,
                        timeout=timeout * 1000,
                        wait_until="networkidle",
                    )
                    return await page.content()
                except PlaywrightTimeoutError:
                    err_msg = f"Playwright timed out after {timeout}s fetching '{url}'."
                    ui.error(err_msg)
                except PlaywrightError as e:
                    err_msg = f"Playwright navigation/content error for '{url}': {e}"
                    ui.error(err_msg)
                finally:
                    await page.close()
                    await browser.close()
            except Exception as e:
                err_msg = f"Playwright browser launch error: {e}"
                ui.error(err_msg)
                ui.warning("Browser binaries may be missing. Try running 'playwright install'")
                # Fall back to httpx
                return await _httpx_fetch(url, timeout)
    except Exception as e:
        err_msg = f"Playwright initialization error: {e}"
        ui.error(err_msg)
        # Fall back to httpx
        return await _httpx_fetch(url, timeout)


async def _httpx_fetch(url: str, timeout: int, headers: dict = None) -> str:
    async with httpx.AsyncClient(
        headers=headers,
        follow_redirects=True,
        timeout=timeout,
        http2=True,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def _extract_text(content: str) -> str:
    soup = BeautifulSoup(content, "html.parser")

    for element in soup(["script", "style", "head", "title", "meta", "link", "noscript"]):
        element.decompose()

    # Get text, use ' ' as a separator for block elements, strip leading/trailing whitespace
    # Using .stripped_strings joins text nodes intelligently
    chunks = [text for text in soup.stripped_strings]
    text_content = " ".join(chunks)
    return text_content


async def fetch(
    url: str, render_js: bool = True, extract_text: bool = True, timeout: int = 30
) -> str:
    """
    Fetch the content of a URL, optionally rendering JavaScript and extracting text.

    Uses Playwright (if available and render_js=True) to render JavaScript,
    otherwise falls back to httpx for a direct request.

    Args:
        url (str): The URL to fetch.
        render_js (bool): Whether to attempt rendering JavaScript using a headless browser.
                          Defaults to True. Requires Playwright to be installed.
        extract_text (bool): Whether to parse the HTML and return only the text content.
                             Defaults to True. If False, returns raw HTML.
        timeout (int): Timeout in seconds for the fetch operation. Defaults to 30.

    Returns:
        str: The fetched content (text or HTML) or an error message.
    """
    use_playwright = render_js and PLAYWRIGHT_AVAILABLE

    ui.status(f"Fetch({url})")
    # ui.status(
    #     f"Fetch(url='{url}', "
    #     f"render_js={render_js}, "
    #     f"extract_text={extract_text}, "
    #     f"timeout={timeout}, "
    #     f"use_playwright={use_playwright})"
    # )

    try:
        if use_playwright:
            res = await _playwright_fetch(url, timeout)
        else:
            res = await _httpx_fetch(url, timeout)

        if extract_text:
            return await _extract_text(res)

        return res
    except Exception as e:
        # Catch any unexpected errors and fall back to a simple message
        err_msg = f"Error fetching {url}: {str(e)}"
        ui.error(err_msg)
        return f"Failed to fetch content from {url}. Error: {str(e)}"
