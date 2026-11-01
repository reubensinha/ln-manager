"""Fetching and merging plugin repository catalogs.

A repository is a URL serving an index that lists installable plugins. Two shapes are
accepted, because they suit different publishers:

- **inline** - the index carries each plugin's versions directly. One request refreshes a
  whole repository, which is what a CI-generated index wants.
- **delegated** - an entry carries a `manifest` URL fetched separately. Costs an extra
  request per plugin, but lets an author publish releases without the repository
  maintainer regenerating anything.

The index is either a bare list of entries or an object with a `plugins` list and an
optional `name`::

    {
      "name": "Example Repo",
      "plugins": [
        {"uid": "...", "name": "Torznab", "author": "...", "description": "...",
         "versions": [{"version": "0.1.0", "url": "https://.../x.lna", "sha256": "ab12..."}]},
        {"uid": "...", "manifest": "https://author.example/torznab.yaml"}
      ]
    }

Entries are parsed with ``yaml.safe_load``, which also accepts JSON, so a delegated
manifest may be written in either.

Nothing here downloads or installs a plugin artifact; this module only resolves what is
on offer. Verifying a ``sha256`` and unpacking is the installer's job.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx
import yaml

from backend.core.logging_config import get_logger
from backend.plugin_manager import normalise_uid

logger = get_logger(__name__)

# A repository is remote code, so the transport has to be authenticated. Plain HTTP is
# allowed only for loopback, which keeps a local fixture repo usable during development
# without weakening anything that faces a network.
ALLOWED_SCHEMES = {"https"}
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}

# Caps on anything fetched from a repository. An index is text; these bound how much of
# it a hostile or broken server can make the app hold.
FETCH_TIMEOUT_SECONDS = 15.0
MAX_INDEX_BYTES = 5 * 1024 * 1024
MAX_DELEGATED_MANIFESTS = 100


class RepositoryError(Exception):
    """A repository could not be fetched or its contents could not be understood."""


def _is_loopback(host: str) -> bool:
    if host in LOOPBACK_HOSTS:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def validate_repository_url(url: str) -> str:
    """Return `url` stripped of a trailing slash, or raise if it is not usable.

    Rejecting non-HTTPS matters more here than for an ordinary API call: whatever this
    URL returns decides which code the app is willing to install, so a plaintext fetch
    would let anyone on the path choose that for the user.
    """
    url = (url or "").strip().rstrip("/")
    if not url:
        raise RepositoryError("Repository URL is required")

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise RepositoryError(f"'{url}' is not a valid absolute URL")

    host = parsed.hostname or ""
    if parsed.scheme not in ALLOWED_SCHEMES and not (
        parsed.scheme == "http" and _is_loopback(host)
    ):
        raise RepositoryError(
            f"Repository URLs must use https (got '{parsed.scheme}'). "
            "Plain http is permitted only for localhost."
        )
    return url


@dataclass
class CatalogVersion:
    """One installable release of a plugin, as offered by one repository."""

    version: str
    url: str
    sha256: str
    min_app_version: str | None = None
    changelog: str | None = None
    repo_id: str | None = None
    repo_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "url": self.url,
            "sha256": self.sha256,
            "min_app_version": self.min_app_version,
            "changelog": self.changelog,
            "repo_id": self.repo_id,
            "repo_name": self.repo_name,
        }


@dataclass
class CatalogEntry:
    """One plugin on offer, merged across every repository that lists it."""

    uid: str
    name: str
    author: str | None = None
    description: str | None = None
    versions: list[CatalogVersion] = field(default_factory=list)
    repos: list[dict[str, str]] = field(default_factory=list)
    # (version, sha256) pairs where repositories disagree about the artifact. Surfaced
    # rather than silently resolved: the same version resolving to different bytes is
    # something the user should see before installing either one.
    conflicts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "name": self.name,
            "author": self.author,
            "description": self.description,
            "versions": [v.to_dict() for v in self.versions],
            "repos": self.repos,
            "conflicts": self.conflicts,
        }


def _parse_versions(raw: Any, *, label: str) -> list[CatalogVersion]:
    if not isinstance(raw, list):
        raise RepositoryError(f"{label}: 'versions' must be a list")

    versions: list[CatalogVersion] = []
    for item in raw:
        if not isinstance(item, dict):
            raise RepositoryError(f"{label}: each version must be a mapping")
        version = str(item.get("version") or "").strip()
        url = str(item.get("url") or "").strip()
        sha256 = str(item.get("sha256") or "").strip().lower()
        if not version or not url:
            logger.warning(f"{label}: skipping a version missing 'version' or 'url'")
            continue
        # A checksum is required, not optional: it is the only thing that makes the
        # downloaded artifact verifiable, and it doubles as the identity used to tell
        # "the same release from two repositories" from "two different releases".
        if len(sha256) != 64 or any(c not in "0123456789abcdef" for c in sha256):
            logger.warning(
                f"{label}: skipping version {version} - 'sha256' must be a 64-character hex digest"
            )
            continue
        try:
            url = validate_repository_url(url)
        except RepositoryError as exc:
            logger.warning(f"{label}: skipping version {version} - {exc}")
            continue
        versions.append(
            CatalogVersion(
                version=version,
                url=url,
                sha256=sha256,
                min_app_version=(
                    str(item["min_app_version"]) if item.get("min_app_version") else None
                ),
                changelog=(str(item["changelog"]) if item.get("changelog") else None),
            )
        )
    return versions


def _parse_entry(raw: Any, *, label: str) -> tuple[CatalogEntry | None, str | None]:
    """Parse one index entry. Returns (entry, delegated_manifest_url)."""
    if not isinstance(raw, dict):
        raise RepositoryError(f"{label}: each plugin entry must be a mapping")

    uid = normalise_uid(raw.get("uid"), plugin_name=str(raw.get("name") or "<unnamed>"))
    if not uid:
        logger.warning(f"{label}: skipping an entry with a missing or malformed 'uid'")
        return None, None

    manifest_url = raw.get("manifest")
    if manifest_url and not raw.get("versions"):
        return (
            CatalogEntry(uid=uid, name=str(raw.get("name") or ""), author=None),
            str(manifest_url),
        )

    name = str(raw.get("name") or "").strip()
    if not name:
        logger.warning(f"{label}: skipping entry {uid} - 'name' is required")
        return None, None

    entry = CatalogEntry(
        uid=uid,
        name=name,
        author=(str(raw["author"]) if raw.get("author") else None),
        description=(str(raw["description"]) if raw.get("description") else None),
        versions=_parse_versions(raw.get("versions") or [], label=f"{label}/{name}"),
    )
    return entry, None


def parse_index(document: Any, *, label: str = "index") -> tuple[str | None, list[tuple[CatalogEntry, str | None]]]:
    """Validate a repository index into (repo_name, [(entry, delegated_url), ...])."""
    if isinstance(document, list):
        repo_name, raw_plugins = None, document
    elif isinstance(document, dict):
        repo_name = str(document["name"]) if document.get("name") else None
        raw_plugins = document.get("plugins")
        if raw_plugins is None:
            raise RepositoryError(
                f"{label}: object form must contain a 'plugins' list"
            )
    else:
        raise RepositoryError(
            f"{label}: expected a list of plugins or an object with a 'plugins' list"
        )

    if not isinstance(raw_plugins, list):
        raise RepositoryError(f"{label}: 'plugins' must be a list")

    parsed: list[tuple[CatalogEntry, str | None]] = []
    for raw in raw_plugins:
        entry, delegated = _parse_entry(raw, label=label)
        if entry is not None:
            parsed.append((entry, delegated))
    return repo_name, parsed


async def _fetch_text(client: httpx.AsyncClient, url: str, *, what: str) -> str:
    """GET `url`, enforcing the size cap and refusing a redirect that downgrades scheme."""
    try:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            # Redirects are followed (GitHub and most static hosts rely on them), but the
            # hop chain could land on plain http, which would defeat the scheme check
            # done on the URL we were given.
            final = str(response.url)
            try:
                validate_repository_url(final)
            except RepositoryError as exc:
                raise RepositoryError(f"{what} redirected to an unusable URL: {exc}") from exc

            chunks: list[bytes] = []
            total = 0
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                if total > MAX_INDEX_BYTES:
                    raise RepositoryError(
                        f"{what} is larger than the {MAX_INDEX_BYTES // (1024 * 1024)}MB limit"
                    )
                chunks.append(chunk)
    except httpx.HTTPStatusError as exc:
        raise RepositoryError(
            f"{what} returned HTTP {exc.response.status_code}"
        ) from exc
    except httpx.HTTPError as exc:
        raise RepositoryError(f"{what} could not be fetched: {exc}") from exc

    return b"".join(chunks).decode("utf-8", errors="replace")


async def fetch_catalog(url: str) -> dict[str, Any]:
    """Fetch a repository index, resolving delegated manifests, as a cacheable dict.

    The return value is what gets stored on ``PluginRepository.catalog`` verbatim, so
    browsing never needs the network.
    """
    url = validate_repository_url(url)

    async with httpx.AsyncClient(
        timeout=FETCH_TIMEOUT_SECONDS, follow_redirects=True
    ) as client:
        body = await _fetch_text(client, url, what="Repository index")
        try:
            document = yaml.safe_load(body)
        except yaml.YAMLError as exc:
            raise RepositoryError(f"Repository index is not valid JSON or YAML: {exc}") from exc

        repo_name, parsed = parse_index(document, label="index")

        delegated = [(e, u) for e, u in parsed if u]
        if len(delegated) > MAX_DELEGATED_MANIFESTS:
            raise RepositoryError(
                f"Repository delegates {len(delegated)} manifests, above the "
                f"{MAX_DELEGATED_MANIFESTS} limit"
            )

        entries: list[CatalogEntry] = [e for e, u in parsed if not u]
        for entry, manifest_url in delegated:
            try:
                manifest_url = validate_repository_url(manifest_url)
                raw = await _fetch_text(
                    client, manifest_url, what=f"Manifest for {entry.name or entry.uid}"
                )
                document = yaml.safe_load(raw)
                resolved, nested = _parse_entry(document, label=manifest_url)
                if resolved is None:
                    continue
                if nested:
                    # One level only. A manifest pointing at another manifest is either a
                    # mistake or a loop, and following it would make refresh unbounded.
                    logger.warning(
                        f"Manifest {manifest_url} delegates again; ignoring the nesting"
                    )
                if resolved.uid != entry.uid:
                    logger.warning(
                        f"Manifest {manifest_url} declares uid {resolved.uid} but the "
                        f"index listed {entry.uid}; trusting the manifest"
                    )
                entries.append(resolved)
            except RepositoryError as exc:
                # One bad manifest must not lose the rest of the repository.
                logger.warning(f"Skipping delegated manifest {manifest_url}: {exc}")

    return {
        "name": repo_name,
        "plugins": [e.to_dict() for e in entries],
    }


def merge_catalogs(sources: list[tuple[str, str, dict[str, Any]]]) -> list[CatalogEntry]:
    """Merge per-repository catalogs into one list, deduplicated by plugin `uid`.

    `sources` is (repo_id, repo_name, catalog) for each enabled repository.

    Two repositories offering the same release of the same plugin are collapsed when
    their artifacts carry the same `sha256` - the checksum proves it is the same file, so
    showing it twice would be noise. The same version with *different* checksums is kept
    as a conflict instead, because that is a real disagreement about what the user would
    be installing.
    """
    merged: dict[str, CatalogEntry] = {}

    for repo_id, repo_name, catalog in sources:
        for raw in (catalog or {}).get("plugins") or []:
            uid = normalise_uid(raw.get("uid"), plugin_name=str(raw.get("name") or ""))
            if not uid:
                continue

            entry = merged.get(uid)
            if entry is None:
                entry = CatalogEntry(
                    uid=uid,
                    name=str(raw.get("name") or ""),
                    author=raw.get("author"),
                    description=raw.get("description"),
                )
                merged[uid] = entry

            if not any(r["id"] == repo_id for r in entry.repos):
                entry.repos.append({"id": repo_id, "name": repo_name})

            for rawv in raw.get("versions") or []:
                incoming = CatalogVersion(
                    version=str(rawv.get("version")),
                    url=str(rawv.get("url")),
                    sha256=str(rawv.get("sha256") or "").lower(),
                    min_app_version=rawv.get("min_app_version"),
                    changelog=rawv.get("changelog"),
                    repo_id=repo_id,
                    repo_name=repo_name,
                )
                existing = next(
                    (v for v in entry.versions if v.version == incoming.version), None
                )
                if existing is None:
                    entry.versions.append(incoming)
                elif existing.sha256 != incoming.sha256:
                    conflict = {
                        "version": incoming.version,
                        "repos": [
                            {"id": existing.repo_id, "name": existing.repo_name,
                             "sha256": existing.sha256},
                            {"id": incoming.repo_id, "name": incoming.repo_name,
                             "sha256": incoming.sha256},
                        ],
                    }
                    if conflict not in entry.conflicts:
                        entry.conflicts.append(conflict)

    for entry in merged.values():
        # Newest-looking first, without pretending to understand arbitrary version
        # strings: a numeric tuple when it parses, otherwise lexical.
        entry.versions.sort(key=_version_sort_key, reverse=True)

    return sorted(merged.values(), key=lambda e: e.name.lower())


def _version_sort_key(v: CatalogVersion) -> tuple[int, tuple[int, ...], str]:
    parts = v.version.replace("-", ".").split(".")
    numeric: list[int] = []
    for part in parts:
        if part.isdigit():
            numeric.append(int(part))
        else:
            break
    # Versions that parse numerically sort above ones that do not, so a release like
    # "0.2.0" is never buried under "nightly".
    return (1 if numeric else 0, tuple(numeric), v.version)
