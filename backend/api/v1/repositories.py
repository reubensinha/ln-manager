"""Plugin repository management and the merged installable-plugin catalog.

These live under /api/v1 rather than /api/plugins: they are core endpoints the app owns,
not routes contributed by a plugin.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, col, select

from backend.core.database.database import get_session
from backend.core.database.models import (
    Plugin,
    PluginRepository,
    PluginRepositoryCreate,
    PluginRepositoryPublic,
    PluginRepositoryUpdate,
)
from backend.core.logging_config import get_logger
from backend.core.plugins.repository import (
    RepositoryError,
    fetch_catalog,
    merge_catalogs,
    validate_repository_url,
)

logger = get_logger(__name__)

router = APIRouter()


def _to_public(session: Session, repo: PluginRepository) -> PluginRepositoryPublic:
    """Shape a repository row for the API, excluding its cached catalog."""
    installed = session.exec(
        select(Plugin).where(Plugin.source_repo_id == repo.id)
    ).all()
    return PluginRepositoryPublic(
        **repo.model_dump(exclude={"catalog"}),
        plugin_count=len(installed),
    )


@router.get("/plugin-repositories", response_model=list[PluginRepositoryPublic])
async def list_repositories(*, session: Session = Depends(get_session)):
    """Every configured repository, newest first."""
    repos = session.exec(
        select(PluginRepository).order_by(col(PluginRepository.created_at).desc())
    ).all()
    return [_to_public(session, r) for r in repos]


@router.post("/plugin-repositories", response_model=PluginRepositoryPublic)
async def add_repository(
    *, payload: PluginRepositoryCreate, session: Session = Depends(get_session)
):
    """Add a repository and fetch its catalog immediately.

    The fetch is part of adding rather than a later step: a URL that cannot be read is
    not a repository, and failing now is far clearer than storing a row that silently
    offers nothing.
    """
    try:
        url = validate_repository_url(payload.url)
    except RepositoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if session.exec(
        select(PluginRepository).where(PluginRepository.url == url)
    ).first():
        raise HTTPException(
            status_code=409, detail=f"Repository '{url}' has already been added."
        )

    try:
        catalog = await fetch_catalog(url)
    except RepositoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repo = PluginRepository(
        name=payload.name or catalog.get("name") or url,
        url=url,
        catalog=catalog,
        last_refreshed_at=datetime.utcnow(),
    )
    session.add(repo)
    session.commit()
    session.refresh(repo)
    logger.info(
        f"Added plugin repository '{repo.name}' ({url}) "
        f"offering {len(catalog.get('plugins') or [])} plugin(s)"
    )
    return _to_public(session, repo)


@router.patch(
    "/plugin-repositories/{repository_id}", response_model=PluginRepositoryPublic
)
async def update_repository(
    *,
    repository_id: UUID,
    payload: PluginRepositoryUpdate,
    session: Session = Depends(get_session),
):
    """Rename a repository or enable/disable it. A disabled repository is skipped when
    building the catalog but keeps its installed plugins and its provenance."""
    repo = session.get(PluginRepository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(repo, key, value)
    session.add(repo)
    session.commit()
    session.refresh(repo)
    return _to_public(session, repo)


@router.delete("/plugin-repositories/{repository_id}")
async def remove_repository(
    *, repository_id: UUID, session: Session = Depends(get_session)
) -> dict[str, str]:
    """Remove a repository. Plugins installed from it stay installed - the FK is
    ON DELETE SET NULL, so they simply lose their recorded origin."""
    repo = session.get(PluginRepository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    name = repo.name
    orphaned = session.exec(
        select(Plugin).where(Plugin.source_repo_id == repo.id)
    ).all()
    for plugin in orphaned:
        plugin.source_repo_id = None
        session.add(plugin)

    session.delete(repo)
    session.commit()
    logger.info(
        f"Removed plugin repository '{name}'; {len(orphaned)} installed plugin(s) kept"
    )
    return {"message": f"Repository '{name}' removed."}


@router.post(
    "/plugin-repositories/{repository_id}/refresh",
    response_model=PluginRepositoryPublic,
)
async def refresh_repository(
    *, repository_id: UUID, session: Session = Depends(get_session)
):
    """Re-fetch one repository's index.

    A failure is recorded on the row and returned as 502 rather than raised past it, so
    the UI can show which repository is unreachable while the rest keep working.
    """
    repo = session.get(PluginRepository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        catalog = await fetch_catalog(repo.url)
    except RepositoryError as exc:
        repo.last_error = str(exc)
        repo.last_refreshed_at = datetime.utcnow()
        session.add(repo)
        session.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    repo.catalog = catalog
    repo.last_error = None
    repo.last_refreshed_at = datetime.utcnow()
    session.add(repo)
    session.commit()
    session.refresh(repo)
    return _to_public(session, repo)


@router.get("/plugin-catalog")
async def get_catalog(*, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Every plugin on offer across enabled repositories, deduplicated by uid.

    Served from each repository's cached catalog, so this never hits the network; call
    the refresh endpoint to update it. Entries are annotated with whether that uid is
    already installed, which is the whole reason a stable uid exists.
    """
    repos = session.exec(
        select(PluginRepository).where(PluginRepository.enabled == True)
    ).all()

    entries = merge_catalogs(
        [(str(r.id), r.name, r.catalog or {}) for r in repos]
    )

    installed = {
        p.uid: p for p in session.exec(select(Plugin)).all() if p.uid
    }

    plugins: list[dict[str, Any]] = []
    for entry in entries:
        data = entry.to_dict()
        existing = installed.get(entry.uid)
        data["installed"] = existing is not None
        data["installed_version"] = existing.version if existing else None
        plugins.append(data)

    return {
        "plugins": plugins,
        "repository_count": len(repos),
        "stale": [
            {"id": str(r.id), "name": r.name, "error": r.last_error}
            for r in repos
            if r.last_error
        ],
    }
