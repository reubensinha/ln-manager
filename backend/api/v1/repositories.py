"""Plugin repository management and the merged installable-plugin catalog.

These live under /api/v1 rather than /api/plugins: they are core endpoints the app owns,
not routes contributed by a plugin.
"""

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, SQLModel, col, select

from backend.api.v1.utils import _install_from_lna_path
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
    CatalogVersion,
    RepositoryError,
    download_artifact,
    fetch_catalog,
    merge_catalogs,
    validate_repository_url,
)
from backend.plugin_manager import normalise_uid

logger = get_logger(__name__)

router = APIRouter()


class CatalogInstallRequest(SQLModel):
    """Which catalog plugin to install.

    `version` defaults to the newest on offer and `repository_id` to whichever
    repository provides it, which is unambiguous unless repositories disagree about the
    artifact for that version - see the conflict check in the endpoint.
    """

    uid: str
    version: str | None = None
    repository_id: UUID | None = None


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


async def _refresh_catalog(session: Session, repo: PluginRepository) -> None:
    """Re-fetch `repo`'s index into its cached catalog, recording the outcome on the row.

    Raises `RepositoryError` on failure, but only after persisting it: the endpoint turns
    that into a 502 while startup just logs it, and both have to leave the same record
    behind so an unreachable repository reads the same in the UI either way.
    """
    try:
        catalog = await fetch_catalog(repo.url)
    except RepositoryError as exc:
        repo.last_error = str(exc)
        repo.last_refreshed_at = datetime.utcnow()
        session.add(repo)
        session.commit()
        raise

    repo.catalog = catalog
    repo.last_error = None
    repo.last_refreshed_at = datetime.utcnow()
    session.add(repo)
    session.commit()


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
        await _refresh_catalog(session, repo)
    except RepositoryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    session.refresh(repo)
    return _to_public(session, repo)


async def hydrate_repository_catalogs(session: Session) -> None:
    """Fetch the index for every enabled repository that has never been refreshed.

    This exists for the repository seeded by migration 0006, which is written without a
    catalog because a migration must not do network I/O. Only rows with no catalog at
    all are fetched - a repository that already has one keeps it, so startup does not
    become a refresh-everything pass that re-fetches on every restart. A row whose first
    fetch failed is retried on the next boot, which is the behaviour a transient outage
    during a first boot wants.

    Nothing here is fatal: an unreachable repository must not stop the app from starting.
    """
    pending = session.exec(
        select(PluginRepository).where(
            col(PluginRepository.catalog).is_(None),
            PluginRepository.enabled == True,
        )
    ).all()

    for repo in pending:
        try:
            await _refresh_catalog(session, repo)
        except RepositoryError as exc:
            logger.warning(f"Could not fetch the index for '{repo.name}': {exc}")
        else:
            offered = len((repo.catalog or {}).get("plugins") or [])
            logger.info(
                f"Fetched the index for '{repo.name}', offering {offered} plugin(s)"
            )


def _enabled_repositories(session: Session) -> list[PluginRepository]:
    return list(
        session.exec(
            select(PluginRepository).where(PluginRepository.enabled == True)
        ).all()
    )


@router.get("/plugin-catalog")
async def get_catalog(*, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Every plugin on offer across enabled repositories, deduplicated by uid.

    Served from each repository's cached catalog, so this never hits the network; call
    the refresh endpoint to update it. Entries are annotated with whether that uid is
    already installed, which is the whole reason a stable uid exists.
    """
    repos = _enabled_repositories(session)
    entries = merge_catalogs([(str(r.id), r.name, r.catalog or {}) for r in repos])

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


def _select_version(
    entry_name: str,
    versions: list[CatalogVersion],
    payload: CatalogInstallRequest,
) -> CatalogVersion:
    """Pick the version to install, narrowing by whatever the request specified."""
    candidates = versions
    if payload.repository_id is not None:
        candidates = [v for v in candidates if v.repo_id == str(payload.repository_id)]
        if not candidates:
            raise HTTPException(
                status_code=404,
                detail=f"That repository does not offer '{entry_name}'.",
            )
    if payload.version is not None:
        candidates = [v for v in candidates if v.version == payload.version]
        if not candidates:
            raise HTTPException(
                status_code=404,
                detail=f"Version '{payload.version}' of '{entry_name}' is not on offer.",
            )
    if not candidates:
        raise HTTPException(
            status_code=404,
            detail=f"'{entry_name}' has no installable versions.",
        )
    # merge_catalogs sorts versions newest-first, so the default is the newest release.
    return candidates[0]


@router.post("/plugin-catalog/install")
async def install_from_catalog(
    *, payload: CatalogInstallRequest, session: Session = Depends(get_session)
) -> dict[str, str]:
    """Download a plugin from a repository and install it.

    The artifact is verified against the catalog's sha256 before anything is unpacked,
    and the resulting plugin row records which repository it came from. As with a manual
    upload, the plugin is on disk but not loaded until the server restarts.
    """
    uid = normalise_uid(payload.uid)
    if not uid:
        raise HTTPException(status_code=400, detail="A valid plugin uid is required.")

    repos = _enabled_repositories(session)
    entries = merge_catalogs([(str(r.id), r.name, r.catalog or {}) for r in repos])
    entry = next((e for e in entries if e.uid == uid), None)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"No enabled repository offers a plugin with uid {uid}.",
        )

    if session.exec(select(Plugin).where(Plugin.uid == uid)).first():
        raise HTTPException(
            status_code=409,
            detail=f"'{entry.name}' is already installed. Uninstall it first.",
        )

    chosen = _select_version(entry.name, entry.versions, payload)

    # Repositories disagreeing about what this version's bytes are is the one case the
    # catalog cannot resolve on the user's behalf: picking either silently would install
    # code the user did not choose. Naming a repository is the way to say which.
    if payload.repository_id is None and any(
        c["version"] == chosen.version for c in entry.conflicts
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Repositories disagree about version {chosen.version} of "
                f"'{entry.name}' - they offer different files under the same version. "
                "Choose which repository to install from."
            ),
        )

    with TemporaryDirectory() as temp_dir:
        # A fixed name: the catalog's plugin name is remote input and has no business
        # deciding a path, even a temporary one.
        lna_path = Path(temp_dir) / "artifact.lna"
        try:
            await download_artifact(chosen.url, lna_path, chosen.sha256)
        except RepositoryError as exc:
            # 502, not 400: the request was fine, the repository's response was not.
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        result = _install_from_lna_path(
            lna_path,
            session,
            source_repo_id=UUID(chosen.repo_id) if chosen.repo_id else None,
            expected_uid=uid,
        )

    logger.info(
        f"Installed '{entry.name}' {chosen.version} from repository "
        f"'{chosen.repo_name}' ({chosen.url})"
    )
    return result
