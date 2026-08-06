from __future__ import annotations

from .acquisitions import HeroAcquisitionParser
from .characters import CharactersParser
from .heroes import HeroesParser
from .localization import EnglishLocalizationParser
from .skills import SkillsParser


def cta_parsers():
    """Return CTA parsers in one stable public registration point."""
    return (HeroesParser(), CharactersParser(), SkillsParser(), EnglishLocalizationParser(), HeroAcquisitionParser())
