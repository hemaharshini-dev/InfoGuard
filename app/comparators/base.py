from abc import ABC, abstractmethod
from app.schemas.models import ComparisonInput, ComparatorResult


class BaseComparator(ABC):
    @abstractmethod
    def compare(self, input: ComparisonInput) -> ComparatorResult:
        """Compare transcript vs summary and return structured issues."""
        ...
