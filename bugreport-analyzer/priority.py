from typing import Dict, List
from enum import Enum


class Severity(Enum):
    CRITICAL = 1.0
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4


class Frequency(Enum):
    ALWAYS = 1.0
    OFTEN = 0.7
    SOMETIMES = 0.4
    RARE = 0.2


class FixComplexity(Enum):
    SIMPLE = 0.2
    MODERATE = 0.5
    COMPLEX = 0.8
    DIFFICULT = 1.0


class PriorityCalculator:

    WEIGHTS = {
        'confidence': 0.40,
        'severity': 0.25,
        'frequency': 0.20,
        'fix_complexity': 0.15
    }

    @classmethod
    def calculate(
        cls,
        confidence: float,
        severity: str,
        frequency: str,
        fix_complexity: str
    ) -> float:
        severity_score = Severity[severity.upper()].value if severity.upper() in Severity.__members__ else 0.5
        frequency_score = Frequency[frequency.upper()].value if frequency.upper() in Frequency.__members__ else 0.5
        complexity_score = FixComplexity[fix_complexity.upper()].value if fix_complexity.upper() in FixComplexity.__members__ else 0.5

        score = (
            confidence * cls.WEIGHTS['confidence'] +
            severity_score * cls.WEIGHTS['severity'] +
            frequency_score * cls.WEIGHTS['frequency'] +
            (1 - complexity_score) * cls.WEIGHTS['fix_complexity']
        )

        return round(score, 2)

    @classmethod
    def rank_causes(cls, causes: List[Dict]) -> List[Dict]:
        for cause in causes:
            cause['priority_score'] = cls.calculate(
                cause.get('confidence', 0.5),
                cause.get('severity', 'MEDIUM'),
                cause.get('frequency', 'SOMETIMES'),
                cause.get('fix_complexity', 'MODERATE')
            )

        sorted_causes = sorted(causes, key=lambda x: x['priority_score'], reverse=True)

        for i, cause in enumerate(sorted_causes, 1):
            cause['rank'] = i

        return sorted_causes
