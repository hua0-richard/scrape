#!/usr/bin/env python3
import undetected_chromedriver as uc
import argparse
import json
import os


def load_browser_config(profile_path=None):
    """
    Set up browser configuration with optional profile
    """
    options = uc.ChromeOptions()

    # Basic stealth settings
    options.add_argument('--no-first-run')
    options.add_argument('--no-service-autorun')
    options.add_argument('--password-store=basic')

    # Use existing profile if specified
    if profile_path and os.path.exists(profile_path):
        options.add_argument(f'--user-data-dir={profile_path}')

    return options


def launch_browser(headless=False, profile=None, proxy=None, port=None):
    """
    Launch undetected Chrome with specified options
    """
    options = load_browser_config(profile)

    if headless:
        options.add_argument('--headless')

    if proxy:
        options.add_argument(f'--proxy-server={proxy}')

    if port:
        driver = uc.Chrome(
            options=options,
            driver_executable_path=None,
            browser_executable_path=None,
            port=port
        )
    else:
        driver = uc.Chrome(options=options)

    return driver


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Launch undetected Chrome browser')

    parser.add_argument('--headless', action='store_true',
                        help='Run in headless mode')

    parser.add_argument('--profile', type=str,
                        help='Path to Chrome profile directory')

    parser.add_argument('--proxy', type=str,
                        help='Proxy server address (e.g., socks5://127.0.0.1:9050)')

    parser.add_argument('--port', type=int,
                        help='Remote debugging port')

    args = parser.parse_args()

    try:
        driver = launch_browser(
            headless=args.headless,
            profile=args.profile,
            proxy=args.proxy,
            port=args.port
        )

        print("Browser launched successfully!")
        print("Press Ctrl+C to quit")

        # Keep browser open
        while True:
            pass

    except KeyboardInterrupt:
        print("\nClosing browser...")
        driver.quit()
    except Exception as e:
        print(f"Error: {e}")