# ======================================================================
# HVACgooee — Education Resolver
# Phase: Education v1
# Status: CANONICAL
# ======================================================================

"""
Purpose
-------
Select and return read-only education content for GUI display.

This module:
• Routes education content by domain / topic / mode
• Returns plain text only
• Contains NO GUI logic
• Contains NO ProjectState logic
• Performs NO calculations

Education is explanatory only and never authoritative.
"""

from __future__ import annotations

from typing import Tuple

from HVAC.education.hydronics.concepts import HYDRONICS_CONCEPTS
from HVAC.education.heatloss.concepts import HEATLOSS_CONCEPTS
from HVAC.education.fenestration.concepts import FENESTRATION_CONCEPTS
from HVAC.education.workspace_guidance_v1 import (
    WORKSPACE_GUIDANCE_V1,
)


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def resolve(
    *,
    domain: str,
    topic: str,
    mode: str = "standard",
) -> Tuple[str, str]:
    """
    Resolve education content.

    Parameters
    ----------
    domain:
        Education domain (e.g. "heatloss", "hydronics")
    topic:
        Topic key within the domain (e.g. "overview")
    mode:
        Content mode ("beginner" | "standard" | "classical")

    Returns
    -------
    (title, body_text)
    """

    domain = domain.lower()
    topic = topic.lower()
    mode = mode.lower()

    if domain == "hydronics":
        return _resolve_from(HYDRONICS_CONCEPTS, domain, topic, mode)

    if domain == "heatloss":
        return _resolve_from(HEATLOSS_CONCEPTS, domain, topic, mode)

    if domain == "fenestration":
        return _resolve_from(FENESTRATION_CONCEPTS, domain, topic, mode)

    if domain == "workspace":
        return _resolve_from(WORKSPACE_GUIDANCE_V1, domain, topic, mode)

    return _missing(domain, topic, mode)


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------
def _resolve_from(
    source: dict,
    domain: str,
    topic: str,
    mode: str,
) -> Tuple[str, str]:

    topic_block = source.get(topic)
    if not topic_block:
        return _missing(domain, topic, mode)

    entry = topic_block.get(mode)
    if isinstance(entry, dict):
        title = entry.get("title", "Education")
        body = entry.get("body", "")
        return title, body

    # Compatibility with Education v1's original flat topic dictionaries.
    # Their text remains read-only and is shared across the three levels.
    if "title" in topic_block or "body" in topic_block:
        return (
            topic_block.get("title", "Education"),
            topic_block.get("body", ""),
        )

    return _missing(domain, topic, mode)


def _missing(domain: str, topic: str, mode: str) -> Tuple[str, str]:
    return (
        "Education",
        (
            "No education content is available.\n\n"
            f"Domain: {domain}\n"
            f"Topic: {topic}\n"
            f"Mode: {mode}\n\n"
            "This does not affect calculations."
        ),
    )
