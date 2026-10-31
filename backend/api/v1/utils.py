from fastapi import HTTPException, UploadFile
from sqlmodel import Session

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

# Installed plugins go to USER_PLUGIN_DIR (backend/config/plugins), not
# BUNDLED_PLUGIN_DIR (backend/plugins). Both are searched by the loader via
# PLUGIN_DIRS, but only USER_PLUGIN_DIR is inside the mounted config volume -
# anything written to BUNDLED_PLUGIN_DIR is destroyed when the container is
# recreated, while its frontend half survives in its own volume and then blocks
# reinstallation. BUNDLED_PLUGIN_DIR is treated as read-only here.


async def _install_plugin_util(file: UploadFile, session: Session) -> dict[str, Any]:
    # Validate .lna structure and manifest.yaml
    # Manage dependencies
    # Extract plugin.lna files in appropriate directories
    if not file.filename or not file.filename.endswith(".lna"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Must be .lna file"
        )

    if not file.filename.endswith(".lna"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Must be .lna file"
        )

    with TemporaryDirectory() as temp_dir:
        # Save uploaded file to temp directory
        temp_path = Path(temp_dir)
        lna_path = temp_path / file.filename

        # Save uploaded file
        try:
            content = await file.read()
            with open(lna_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail="Failed to save uploaded file"
            ) from e

        # Extract .lna (zip) file
        try:
            with zipfile.ZipFile(lna_path, "r") as zip_ref:
                zip_ref.extractall(temp_path)
        except zipfile.BadZipFile as e:
            raise HTTPException(
                status_code=400, detail="Invalid .lna file format"
            ) from e

        manifest_path = temp_path / "manifest.yaml"

        if not manifest_path or not manifest_path.exists():
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

        required_fields = [
            "name",
            "version",
            "author",
            "description",
            "entry_point",
        ]
        missing_fields = [field for field in required_fields if field not in manifest]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Manifest missing required fields: {', '.join(missing_fields)}",
            )

        plugin_name = manifest["name"]
        plugin_root = manifest_path.parent

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

        backend_src = plugin_root / "backend"
        if backend_src.exists() and backend_src.is_dir():
            try:
                shutil.copytree(backend_src, plugin_backend_dest)
                shutil.copy2(manifest_path, plugin_backend_dest / "manifest.yaml")
            except Exception as e:
                if plugin_backend_dest.exists():
                    shutil.rmtree(plugin_backend_dest)
                raise HTTPException(
                    status_code=500, detail=f"Failed to install backend: {str(e)}"
                )

        frontend_src = plugin_root / "frontend"
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

    # No "success" field: every failure path above raises HTTPException, so a 2xx
    # response is itself the success signal and the flag could only ever be true.
    return {
        "message": f"Plugin '{plugin_name}' version {manifest['version']} installed successfully."
    }


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
