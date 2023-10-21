from typing import Iterator, Union
from pydantic import Field
from llmstack.connections.models import Connection, ConnectionStatus
from llmstack.connections.types import ConnectionTypeInterface
from .web_login import WebLoginBaseConfiguration


class LinkedInLoginConfiguration(WebLoginBaseConfiguration):
    username: str = Field(description='Username')
    password: str = Field(description='Password', widget='password')


class LinkedInLogin(ConnectionTypeInterface[LinkedInLoginConfiguration]):
    @staticmethod
    def name() -> str:
        return 'LinkedIn Login'

    @staticmethod
    def provider_slug() -> str:
        return 'linkedin'

    @staticmethod
    def slug() -> str:
        return 'web_login'

    @staticmethod
    def description() -> str:
        return 'Login to LinkedIn'

    async def activate(self, connection) -> Iterator[Union[Connection, dict]]:
        # Start playwright browser
        from playwright.async_api import async_playwright
        from django.conf import settings

        async with async_playwright() as p:
            browser = await p.chromium.connect(ws_endpoint=settings.PLAYWRIGHT_URL) if hasattr(
                settings, 'PLAYWRIGHT_URL') and settings.PLAYWRIGHT_URL else await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto('https://www.linkedin.com/login')

            # Login
            await page.fill('input[name="session_key"]', connection.configuration['username'])
            await page.fill('input[name="session_password"]',
                            connection.configuration['password'])
            await page.click('button[type="submit"]')

            # Check if we have errors on the page
            error = await page.query_selector('div[role="alert"]')
            if error:
                error_text = await error.inner_text()
                connection.status = ConnectionStatus.FAILED
                await browser.close()
                yield {'error': error_text, 'connection': connection}
                return

            # Wait for login to complete and redirect to /feed/
            await page.wait_for_url('https://www.linkedin.com/feed/')

            # Get storage state
            storage_state = await context.storage_state()

            connection.status = ConnectionStatus.ACTIVE
            connection.configuration['_storage_state'] = storage_state

            # Close browser
            await browser.close()

            yield connection

    # def activate(self, connection) -> Iterator[Union[Connection, str]]:
    #     # Start playwright browser
    #     from playwright.sync_api import sync_playwright
    #     from django.conf import settings

    #     with sync_playwright() as p:
    #         browser = p.chromium.connect(ws_endpoint=settings.PLAYWRIGHT_URL) if hasattr(
    #             settings, 'PLAYWRIGHT_URL') and settings.PLAYWRIGHT_URL else p.chromium.launch(headless=False)
    #         context = browser.new_context()
    #         page = context.new_page()
    #         page.goto('https://www.linkedin.com/login')

    #         # Login
    #         page.fill('input[name="session_key"]',
    #                   connection.configuration['username'])
    #         page.fill('input[name="session_password"]',
    #                   connection.configuration['password'])
    #         page.click('button[type="submit"]')

    #         # Wait for login to complete and redirect to /feed/
    #         page.wait_for_url('https://www.linkedin.com/feed/')

    #         # Get storage state
    #         storage_state = context.storage_state()

    #         connection.status = ConnectionStatus.ACTIVE
    #         connection.configuration['_storage_state'] = storage_state

    #         # Close browser
    #         browser.close()

    #         yield connection
