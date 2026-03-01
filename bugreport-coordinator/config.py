from dataclasses import dataclass


@dataclass
class CoordinatorConfig:
    max_iterations: int = 3
    confidence_threshold: float = 0.8
    enable_iteration: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> 'CoordinatorConfig':
        return cls(
            max_iterations=data.get('max_iterations', 3),
            confidence_threshold=data.get('confidence_threshold', 0.8),
            enable_iteration=data.get('enable_iteration', True)
        )
