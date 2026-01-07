from .collector import Collector
from .deduplicator import Deduplicator
from .summarizer import Summarizer
from .translator import Translator
from .pipeline import NewsPipeline

__all__ = [
    "Collector",
    "Deduplicator",
    "Summarizer",
    "Translator",
    "NewsPipeline",
]
