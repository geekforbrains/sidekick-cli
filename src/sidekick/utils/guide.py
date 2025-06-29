from pathlib import Path

from ..session import Session


def load_guide(session: Session):
    guide_path = Path.cwd() / "SIDEKICK.md"
    if guide_path.exists():
        session.project_guide = guide_path.read_text(encoding="utf-8").strip()
    else:
        session.project_guide = None
    return session.project_guide


def get_guide(session: Session):
    return session.project_guide
