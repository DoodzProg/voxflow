"""
AcouZ - Open-source AI voice dictation
Copyright (c) 2025-2026 DoodzProg

Page classes for the AcouZ application.

Each page inherits from :class:`~acouz.ui.pages.base.BasePage` and implements
:meth:`~acouz.ui.pages.base.BasePage.retheme` to update all inline-styled
widgets when the application theme changes.
"""

from acouz.ui.pages.base import BasePage
from acouz.ui.pages.home import HomePage
from acouz.ui.pages.general import GeneralPage
from acouz.ui.pages.api import ApiPage
from acouz.ui.pages.audio import AudioPage
from acouz.ui.pages.about import AboutPage

__all__ = [
    "BasePage",
    "HomePage",
    "GeneralPage",
    "ApiPage",
    "AudioPage",
    "AboutPage",
]
