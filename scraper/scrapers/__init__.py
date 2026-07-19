"""Registry of all available scrapers."""

from scraper.scrapers.huntington import HuntingtonScraper
from scraper.scrapers.lyric_stage import LyricStageScraper
from scraper.scrapers.boston_theatre_scene import BostonTheatreSceneScraper
from scraper.scrapers.emerson import EmersonScraper
from scraper.scrapers.central_square import CentralSquareScraper
from scraper.scrapers.speakeasy import SpeakeasyScraper
from scraper.scrapers.boston_playwrights import BostonPlaywrightsScraper
from scraper.scrapers.art import ARTScraper
from scraper.scrapers.apollinaire import ApollinaireScraper
from scraper.scrapers.wheelock import WheelockScraper
from scraper.scrapers.footlight import FootlightScraper

ALL_SCRAPERS = [
    HuntingtonScraper,
    LyricStageScraper,
    BostonTheatreSceneScraper,
    EmersonScraper,
    CentralSquareScraper,
    SpeakeasyScraper,
    BostonPlaywrightsScraper,
    ARTScraper,
    ApollinaireScraper,
    WheelockScraper,
    FootlightScraper,
]
