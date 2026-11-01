from fastapi import HTTPException, UploadFile
from sqlmodel import Session, select

from typing import Any
import yaml
import zipfile
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from backend.core.constants import (
    BUNDLED_PLUGIN_DIR,
    FRONTEND_PLUGIN_DIR,
    USER_PLUGIN_DIR,
)
from backend.core.database.models import Plugin
from backend.core.logging_config import get_logger
from backend.plugin_manager import normalise_uid

logger = get_logger(__name__)

# Installed plugins go to USER_PLUGIN_DIR (backend/config/plugins), not
# BUNDLED_PLUGIN_DIR (backend/plugins). Both are searched by the loader via
# PLUGIN_DIRS, but only USER_PLUGIN_DIR is inside the mounted config volume -
# anything written to BUNDLED_PLUGIN_DIR is destroyed when the container is
# recreated, while its frontend half survives in its own volume and then blocks
# reinstallation. BUNDLED_PLUGIN_DIR is treated as read-only here.

REQUIRED_MANIFEST_FIELDS = [
    "name",
    "version",
    "author",
    "description",
    "entry_point",
]


def _read_manifest(plugin_root: Path) -> dict[str, Any]:
    """Load and validate manifest.yaml from an extracted .lna."""
    manifest_path = plugin_root / "manifest.yaml"
    if not manifest_path.exists():
        raise HTTPException(
            status_code=400, detail="manifest.yaml not found in .lna file"
        )

    try:
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to read manifest.yaml"
        ) from e

    if not isinstance(manifest, dict):
        raise HTTPException(
            status_code=400, detail="manifest.yaml must contain a mapping"
        )

    missing_fields = [f for f in REQUIRED_MANIFEST_FIELDS if f not in manifest]
    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Manifest missing required fields: {', '.join(missing_fields)}",
        )
    # `uid` is deliberately not required: .lna files built before it existed must stay
    # installable, matching startup reconciliation, which also tolerates its absence.
    # The packager rejects newly built plugins that omit it.
    return manifest


def _record_plugin(
    manifest: dict[str, Any],
    session: Session,
    *,
    source_repo_id: UUID | None,
) -> None:
    """Create or adopt the Plugin row for a freshly installed plugin.

    Startup reconciliation also writes rows, and it is the only writer for plugins that
    appear on disk by other means. Writing the row here too is what makes provenance
    possible at all: `source_repo_id` is known only at install time and could not be
    recovered later, because two repositories may offer the same plugin. Reconciliation
    matches this row by uid on the next boot and updates the descriptive fields without
    touching the origin.
    """
    name = manifest["name"]
    uid = normalise_uid(manifest.get("uid"), plugin_name=name)

    # Adopt an existing row rather than inserting beside it. A row can outlive its files
    # (a directory removed by hand, a restore of a database without its plugins), and
    # `uid` is unique, so a blind insert would fail on the constraint instead.
    plugin = None
    if uid:
        plugin = session.exec(select(Plugin).where(Plugin.uid == uid)).first()
    if plugin is None:
        plugin = session.exec(select(Plugin).where(Plugin.name == name)).first()

    if plugin is None:
        plugin = Plugin(
            uid=uid,
            name=name,
            version=manifest["version"],
            author=manifest.get("author", ""),
            description=manifest.get("description", ""),
            enabled=True,
            source_repo_id=source_repo_id,
        )
    else:
        if uid:
            plugin.uid = uid
        plugin.name = name
        plugin.version = manifest["version"]
        plugin.author = manifest.get("author", "")
        plugin.description = manifest.get("description", "")
        plugin.source_repo_id = source_repo_id

    session.add(plugin)
    session.commit()


def _install_from_lna_path(
    lna_path: Path,
    session: Session,
    *,
    source_repo_id: UUID | None = None,
    expected_uid: str | None = None,
) -> dict[str, Any]:
    """Install the plugin packaged in the .lna at `lna_path`.

    Shared by every install route: the file may have been uploaded by the user or
    downloaded from a repository, and by this point the two are indistinguishable - a
    repository download has already been checksum-verified by the caller.

    `source_repo_id` records which repository the artifact came from, or None for a
    manual upload. `expected_uid` is set for a repository install and makes the manifest
    prove it is the plugin the catalog advertised.
    """
    with TemporaryDirectory() as temp_dir:
        # Extract into its own directory rather than alongside the archive: the caller
        # owns `lna_path`'s directory and may have put other things in it.
        extract_dir = Path(temp_dir)

        try:
            with zipfile.ZipFile(lna_path, "r") as zip_ref:
                # extractall already drops absolute paths and ".." components, so no
                # additional zip-slip guard is needed here.
                zip_ref.extractall(extract_dir)
        except zipfile.BadZipFile as e:
            raise HTTPException(
                status_code=400, detail="Invalid .lna file format"
            ) from e

        manifest = _read_manifest(extract_dir)
        plugin_name = manifest["name"]

        if expected_uid is not None:
            manifest_uid = normalise_uid(manifest.get("uid"), plugin_name=plugin_name)
            if manifest_uid != expected_uid:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"The downloaded artifact declares uid {manifest_uid or 'none'} "
                        f"but the catalog offered {expected_uid}. Refusing to install a "
                        "plugin that is not the one advertised."
                    ),
                )

        plugin_backend_dest = USER_PLUGIN_DIR / plugin_name
        plugin_frontend_dest = FRONTEND_PLUGIN_DIR / plugin_name

        # A bundled plugin of the same name would be shadowed by this install and
        # cannot be uninstalled to make room, so refuse rather than create a
        # duplicate the loader would pick up twice.
        if (BUNDLED_PLUGIN_DIR / plugin_name).exists():
            raise HTTPException(
                status_code=409,
                detail=f"'{plugin_name}' is a bundled plugin and cannot be replaced by an install.",
            )

        if plugin_backend_dest.exists() or plugin_frontend_dest.exists():
            raise HTTPException(
                status_code=409,
                detail=f"Plugin '{plugin_name}' already exists. Please uninstall it first.",
            )

        USER_PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        FRONTEND_PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

        backend_src = extract_dir / "backend"
        if backend_src.exists() and backend_src.is_dir():
            try:
                shutil.copytree(backend_src, plugin_backend_dest)
                shutil.copy2(
                    extract_dir / "manifest.yaml", plugin_backend_dest / "manifest.yaml"
                )
            except Exception as e:
                if plugin_backend_dest.exists():
                    shutil.rmtree(plugin_backend_dest)
                raise HTTPException(
                    status_code=500, detail=f"Failed to install backend: {str(e)}"
                )

        frontend_src = extract_dir / "frontend"
        if frontend_src.exists() and frontend_src.is_dir():
            frontend_manifest = frontend_src / "manifest.tsx"
            if not frontend_manifest.exists():
                # Cleanup backend if frontend manifest is missing
                if plugin_backend_dest.exists():
                    shutil.rmtree(plugin_backend_dest)
                raise HTTPException(
                    status_code=400,
                    detail="Frontend manifest.tsx not found in frontend directory",
                )

            try:
                shutil.copytree(frontend_src, plugin_frontend_dest)
            except Exception as e:
                # Cleanup on failure
                if plugin_backend_dest.exists():
                    shutil.rmtree(plugin_backend_dest)
                if plugin_frontend_dest.exists():
                    shutil.rmtree(plugin_frontend_dest)
                raise HTTPException(
                    status_code=500, detail=f"Failed to install frontend: {str(e)}"
                )

        # Last, so a failure to write the row cannot leave a half-installed plugin: the
        # files are rolled back and the install reports as failed.
        try:
            _record_plugin(manifest, session, source_repo_id=source_repo_id)
        except Exception as e:
            session.rollback()
            if plugin_backend_dest.exists():
                shutil.rmtree(plugin_backend_dest)
            if plugin_frontend_dest.exists():
                shutil.rmtree(plugin_frontend_dest)
            raise HTTPException(
                status_code=500, detail=f"Failed to register plugin: {str(e)}"
            ) from e

    logger.info(
        f"Installed plugin '{plugin_name}' version {manifest['version']}"
        + (f" from repository {source_repo_id}" if source_repo_id else "")
    )

    # No "success" field: every failure path above raises HTTPException, so a 2xx
    # response is itself the success signal and the flag could only ever be true.
    return {
        "message": f"Plugin '{plugin_name}' version {manifest['version']} installed successfully."
    }


async def _install_plugin_util(file: UploadFile, session: Session) -> dict[str, Any]:
    """Install a plugin from a user-uploaded .lna file."""
    if not file.filename or not file.filename.endswith(".lna"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Must be .lna file"
        )

    with TemporaryDirectory() as temp_dir:
        # Only the basename: a filename carrying path components would otherwise decide
        # where the upload gets written.
        lna_path = Path(temp_dir) / Path(file.filename).name

        try:
            content = await file.read()
            lna_path.write_bytes(content)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail="Failed to save uploaded file"
            ) from e

        return _install_from_lna_path(lna_path, session)


async def _uninstall_plugin_util(plugin_id: UUID, session: Session) -> dict[str, Any]:
    plugin = None

    plugin = session.get(Plugin, plugin_id)

    if not plugin:
        raise HTTPException(
            status_code=404, detail=f"Plugin with ID {plugin_id} not found"
        )

    plugin_name = plugin.name

    # Never delete out of BUNDLED_PLUGIN_DIR. It is image/source content, not user
    # data: in a source checkout those directories are the only copy of plugins that
    # are deliberately gitignored, so an rmtree here is unrecoverable. Disabling is
    # the supported way to turn a bundled plugin off.
    if (BUNDLED_PLUGIN_DIR / plugin_name).exists():
        raise HTTPException(
            status_code=409,
            detail=(
                f"'{plugin_name}' is a bundled plugin and cannot be uninstalled. "
                "Disable it instead. (If it was installed by an older version that "
                "wrote to the bundled directory, remove that directory manually.)"
            ),
        )

    plugin_backend_path = USER_PLUGIN_DIR / plugin_name
    plugin_frontend_path = FRONTEND_PLUGIN_DIR / plugin_name

    # Remove backend directory
    if plugin_backend_path.exists():
        try:
            shutil.rmtree(plugin_backend_path)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to remove backend plugin files: {str(e)}",
            )

    # Remove frontend directory if it exists
    if plugin_frontend_path.exists():
        try:
            shutil.rmtree(plugin_frontend_path)
        except Exception as e:
            # Attempt to restore backend if frontend deletion fails
            raise HTTPException(
                status_code=500,
                detail=f"Failed to remove frontend plugin files: {str(e)}",
            )

    # Remove plugin from database
    try:
        session.delete(plugin)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to remove plugin from database: {str(e)}"
        )

    return {"message": f"Plugin '{plugin_name}' uninstalled successfully."}
