"""
src/voxflow/ui/pages

Page classes for the Voxflow application.

Each page inherits from :class:`~voxflow.ui.pages.base.BasePage` and implements
:meth:`~voxflow.ui.pages.base.BasePage.retheme` to update all inline-styled
widgets when the user switches between DARK and LIGHT mode.
"""

from voxflow.ui.pages.base import BasePage
from voxflow.ui.pages.home import HomePage
from voxflow.ui.pages.general import GeneralPage
from voxflow.ui.pages.api import ApiPage
from voxflow.ui.pages.audio import AudioPage
from voxflow.ui.pages.about import AboutPage

__all__ = [
    "BasePage",
    "HomePage",
    "GeneralPage",
    "ApiPage",
    "AudioPage",
    "AboutPage",
]
