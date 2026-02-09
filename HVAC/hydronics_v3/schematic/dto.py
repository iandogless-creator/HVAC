@dataclass(frozen=True, slots=True)
class SchematicNodeDTO:
    id: str
    x: float
    y: float
    role: NodeRole

    hover: NodeHoverDTO | None = None
