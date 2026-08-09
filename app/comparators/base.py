"""Abstract base class that all comparators must implement."""
from abc import ABC, abstractmethod
from app.schemas.models import ComparisonInput, ComparatorResult


class BaseComparator(ABC):
    """Every comparator must implement compare() and return a ComparatorResult."""
    @abstractmethod
    def compare(self, input: ComparisonInput) -> ComparatorResult:
        """Compare transcript vs summary and return structured issues."""
        ...
