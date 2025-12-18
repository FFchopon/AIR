"""Computer Use Agent Implementation

This module defines an agent that can operate a computer (mouse, keyboard,
scrolling, etc.) using the OpenAI Agents SDK built-in Computer Use tool.

It is similar in structure to the existing code_agent and embodied_agent
case studies, but uses the hosted Computer Use tool instead of local tools.

NOTE: To use this agent you must:
  - Have an OpenAI API key configured in your environment
  - Be running in an environment where the OpenAI Computer Use tool is
    supported (see OpenAI Agents SDK documentation).
"""

from __future__ import annotations

import asyncio
from typing import Any, Literal, Union

from playwright.async_api import Browser, Page, Playwright, async_playwright

from agents import (
    Agent,
    AsyncComputer,
    Button,
    ComputerTool,
    Environment,
    ModelSettings,
)


# Key mapping used by the example LocalPlaywrightComputer from the
# official Agents SDK computer_use example.
CUA_KEY_TO_PLAYWRIGHT_KEY = {
    "/": "Divide",
    "\\": "Backslash",
    "alt": "Alt",
    "arrowdown": "ArrowDown",
    "arrowleft": "ArrowLeft",
    "arrowright": "ArrowRight",
    "arrowup": "ArrowUp",
    "backspace": "Backspace",
    "capslock": "CapsLock",
    "cmd": "Meta",
    "ctrl": "Control",
    "delete": "Delete",
    "end": "End",
    "enter": "Enter",
    "esc": "Escape",
    "home": "Home",
    "insert": "Insert",
    "option": "Alt",
    "pagedown": "PageDown",
    "pageup": "PageUp",
    "shift": "Shift",
    "space": " ",
    "super": "Meta",
    "tab": "Tab",
    "win": "Meta",
}


class LocalPlaywrightComputer(AsyncComputer):
    """A computer implemented using a local Playwright browser.

    This is adapted from the official OpenAI Agents SDK example
    (examples/tools/computer_use.py).
    """

    def __init__(self) -> None:
        self._playwright: Union[Playwright, None] = None
        self._browser: Union[Browser, None] = None
        self._page: Union[Page, None] = None

    async def _get_browser_and_page(self) -> tuple[Browser, Page]:
        width, height = self.dimensions
        launch_args = [f"--window-size={width},{height}"]
        browser = await self.playwright.chromium.launch(
            headless=False,
            args=launch_args,
        )
        page = await browser.new_page()
        await page.set_viewport_size({"width": width, "height": height})
        await page.goto("https://www.bing.com")
        return browser, page

    async def __aenter__(self) -> "LocalPlaywrightComputer":
        self._playwright = await async_playwright().start()
        self._browser, self._page = await self._get_browser_and_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[override]
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def open(self) -> "LocalPlaywrightComputer":
        """Open resources without using a context manager."""
        await self.__aenter__()
        return self

    async def close(self) -> None:
        """Close resources without using a context manager."""
        await self.__aexit__(None, None, None)

    async def _ensure_open(self) -> None:
        """Ensure that Playwright, browser and page are initialized.

        Some versions of the Agents SDK call computer methods directly on the
        AsyncComputer instance without first entering it as an async context or
        calling an explicit open() helper. To keep this implementation
        compatible, we lazily initialize the browser/page on first use.
        """

        if self._page is not None and self._browser is not None and self._playwright is not None:
            return

        # Delegate to the same initialization logic used by the context manager.
        await self.__aenter__()

    @property
    def playwright(self) -> Playwright:
        assert self._playwright is not None
        return self._playwright

    @property
    def browser(self) -> Browser:
        assert self._browser is not None
        return self._browser

    @property
    def page(self) -> Page:
        assert self._page is not None
        return self._page

    @property
    def environment(self) -> Environment:
        return "browser"

    @property
    def dimensions(self) -> tuple[int, int]:
        return (1024, 768)

    async def screenshot(self) -> str:
        await self._ensure_open()
        png_bytes = await self.page.screenshot(full_page=False)
        import base64

        return base64.b64encode(png_bytes).decode("utf-8")

    async def click(self, x: int, y: int, button: Button = "left") -> None:
        await self._ensure_open()
        playwright_button: Literal["left", "middle", "right"] = "left"
        if button in ("left", "right", "middle"):
            playwright_button = button  # type: ignore[assignment]
        await self.page.mouse.click(x, y, button=playwright_button)

    async def double_click(self, x: int, y: int) -> None:
        await self._ensure_open()
        await self.page.mouse.dblclick(x, y)

    async def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        await self._ensure_open()
        await self.page.mouse.move(x, y)
        await self.page.evaluate(f"window.scrollBy({scroll_x}, {scroll_y})")

    async def type(self, text: str) -> None:
        await self._ensure_open()
        await self.page.keyboard.type(text)

    async def wait(self) -> None:
        await asyncio.sleep(1)

    async def move(self, x: int, y: int) -> None:
        await self._ensure_open()
        await self.page.mouse.move(x, y)

    async def keypress(self, keys: list[str]) -> None:
        await self._ensure_open()
        mapped_keys = [CUA_KEY_TO_PLAYWRIGHT_KEY.get(key.lower(), key) for key in keys]
        for key in mapped_keys:
            await self.page.keyboard.down(key)
        for key in reversed(mapped_keys):
            await self.page.keyboard.up(key)

    async def drag(self, path: list[tuple[int, int]]) -> None:
        if not path:
            return
        await self._ensure_open()
        await self.page.mouse.move(path[0][0], path[0][1])
        await self.page.mouse.down()
        for px, py in path[1:]:
            await self.page.mouse.move(px, py)
        await self.page.mouse.up()


def create_computer_use_agent(
    agent_name: str = "Computer Use Agent",
    model: str = "computer-use-preview",
    instructions: str | None = None,
) -> Agent:
    """Create an agent configured with the built-in Computer Use tool.

    The agent is configured to:
    - Use OpenAI's hosted Computer Use tool
    - Follow high-level instructions for safe computer interaction

    Args:
        agent_name: Human-readable name for the agent
        model: Model ID to use with the Agent SDK
        instructions: Optional custom system instructions. If not provided,
            a default set of instructions focused on careful, explainable
            computer interactions is used.

    Returns:
        Configured :class:`Agent` instance.
    """

    if instructions is None:
        instructions = (
            "You are a computer use assistant. "
            "You control the user's computer using the Computer Use tool. "
            "Always explain what you are about to do before you do it, and "
            "prefer small, incremental steps over large, irreversible ones. "
            "Avoid risky operations such as deleting files, changing system "
            "settings, or installing software unless the user explicitly "
            "requests it and the intent is unambiguous. "
            "Once the user's request has clearly been fulfilled and the "
            "result is visible on screen, stop using the Computer Use tool "
            "and return a concise natural-language answer. Avoid taking "
            "excessive screenshots or waiting once the goal has been "
            "achieved."
        )

    # Create an Agent with the hosted Computer Use tool configured.
    # According to the Agents SDK docs, ComputerTool expects a "computer"
    # configuration, which can be either a concrete AsyncComputer instance
    # or a ComputerProvider that creates one per run. To keep this example
    # compatible with older SDK versions that may not export ComputerProvider,
    # we pass a LocalPlaywrightComputer AsyncComputer instance directly.
    computer = LocalPlaywrightComputer()
    agent = Agent(
        name=agent_name,
        model=model,
        instructions=instructions,
        tools=[ComputerTool(computer=computer)],
        # The computer-use-preview model requires truncation="auto".
        model_settings=ModelSettings(truncation="auto"),
    )

    return agent
