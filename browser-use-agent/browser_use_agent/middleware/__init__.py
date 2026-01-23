"""Middleware package for browser agent extensions."""

from browser_use_agent.middleware.presented_files import (
    PresentedFilesMiddleware,
    PresentedFilesState,
    _presented_files_reducer,
)

__all__ = [
    "PresentedFilesMiddleware",
    "PresentedFilesState",
    "_presented_files_reducer",
]
