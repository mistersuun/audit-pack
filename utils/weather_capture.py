"""
Utility to automatically capture weather screenshot from MétéoMédia for Laval.
"""

from playwright.sync_api import sync_playwright
import io
from PIL import Image

def capture_weather_laval():
    """
    Captures a screenshot of the weather for Laval from MétéoMédia.
    Returns: PIL Image object
    """
    try:
        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1400, 'height': 1000})

            # Go to MétéoMédia Laval page
            page.goto('https://www.meteomedia.com/ca/meteo/quebec/laval', timeout=30000)

            # Wait for the page to load
            page.wait_for_load_state('networkidle')

            # Wait for weather content to load
            page.wait_for_timeout(3000)

            # Try to capture the center/main content
            try:
                # Look for the main weather content container
                element = page.locator('.center').first
                screenshot_bytes = element.screenshot()
            except:
                # Fallback to full viewport screenshot
                screenshot_bytes = page.screenshot(full_page=False)

            browser.close()

            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(screenshot_bytes))

            return image

    except Exception as e:
        print(f"Error capturing weather from MétéoMédia: {e}")
        return None


def capture_weather_environnement_canada():
    """
    Alternative: Captures weather from Environment Canada (more reliable).
    Returns: PIL Image object
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1400, 'height': 1000})

            # Go to Environment Canada Laval page with coordinates
            page.goto('https://www.meteo.gc.ca/fr/location/index.html?coords=45.585,-73.751', timeout=30000)

            # Wait for the page to load
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(3000)

            # Try to capture the main content area
            try:
                # Look for the center content area
                element = page.locator('.center').first
                screenshot_bytes = element.screenshot()
            except:
                # Fallback to full viewport screenshot
                screenshot_bytes = page.screenshot(full_page=False)

            browser.close()

            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(screenshot_bytes))

            return image

    except Exception as e:
        print(f"Error capturing weather from Environment Canada: {e}")
        return None


# Use MétéoMédia as default (more reliable URL structure)
def get_weather_screenshot():
    """
    Gets weather screenshot. Tries MétéoMédia first, falls back to Environment Canada.
    Returns: PIL Image object or None
    """
    # Try MétéoMédia first
    image = capture_weather_laval()

    if image is None:
        # Fallback to Environment Canada
        print("Trying Environment Canada as fallback...")
        image = capture_weather_environnement_canada()

    return image
