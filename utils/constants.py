from enum import Enum
from pathlib import Path

ROOT_PATH = Path(__file__).parents[1]

FRONTEND_PATH = ROOT_PATH / "frontend"
BACKEND_PATH = ROOT_PATH / "backend"


class StationIds(Enum):
    MALMO = 740000003
    GOTEBORG = 740000002
    UMEA = 740000190
