from __future__ import annotations

import asyncio
import hashlib
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from revisionproof.assets import DEMO_ASSET_ID, demo_asset_path
from revisionproof.contracts import ExecutionMode
from revisionproof.evidence.live import (
    McpClickHouseReader,
    VertexGeminiInterpreter,
    build_segment_search_query,
    normalize_clickhouse_fixed_string,
)
from revisionproof.settings import Settings

_PROJECT_ID_RE = re.compile(r"^revisionproof-[a-z0-9-]{6,16}$")
_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
VIEW_DEFINER_USER = "revisionproof_view_definer_user"
VIEW_DEFINER_ROLE = "revisionproof_view_definer"
_CLICKHOUSE_CLOUD_HOST_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.clickhouse\.cloud$")


@dataclass(frozen=True, slots=True)
class SeedSegment:
    segment_id: str
    start_seconds: float
    end_seconds: float
    transcript: str
    visual_summary: str
    embedding_text: str


SEED_SEGMENTS = (
    SeedSegment(
        segment_id="01J00000000000000000000001",
        start_seconds=0,
        end_seconds=8,
        transcript="A producer introduces the delivery risk before the product reveal.",
        visual_summary="A dark editing interface establishes the review workflow.",
        embedding_text="video revision approval workflow introduction",
    ),
    SeedSegment(
        segment_id="01J00000000000000000000002",
        start_seconds=8,
        end_seconds=14,
        transcript='The presenter says "RevisionProof" and reveals the approval firewall.',
        visual_summary="The RevisionProof wordmark and proof trace fill the center frame.",
        embedding_text="RevisionProof",
    ),
    SeedSegment(
        segment_id="01J00000000000000000000003",
        start_seconds=24,
        end_seconds=29,
        transcript="The end card asks the viewer to approve the verified delivery.",
        visual_summary="A bottom-right publish call to action remains visible.",
        embedding_text="verified delivery call to action end card",
    ),
)

APPEND_ONLY_TABLE_LAYOUTS = {
    "revision_specs": ("MergeTree", "run_id, spec_hash, approved_at"),
    "version_features": (
        "MergeTree",
        "run_id, version_label, feature_name, time_start, extracted_at",
    ),
    "version_checks": (
        "MergeTree",
        "run_id, version_label, check_id, checked_at",
    ),
}

CLICKHOUSE_CLOUD_ENGINE_ALIASES = {
    "SharedMergeTree": "MergeTree",
    "SharedReplacingMergeTree": "ReplacingMergeTree",
}


def normalize_clickhouse_engine(engine: str) -> str:
    """Return the logical MergeTree engine name reported outside ClickHouse Cloud."""
    return CLICKHOUSE_CLOUD_ENGINE_ALIASES.get(engine, engine)


def split_sql_statements(sql: str) -> list[str]:
    return [statement.strip() for statement in sql.split(";") if statement.strip()]


def validate_live_bootstrap_settings(settings: Settings) -> None:
    if settings.mode is not ExecutionMode.LIVE:
        raise ValueError("LIVE bootstrap requires REVISIONPROOF_MODE=LIVE")
    if not settings.google_cloud_project or not _PROJECT_ID_RE.fullmatch(
        settings.google_cloud_project
    ):
        raise ValueError("Google Cloud project must be a dedicated revisionproof-* project")
    if settings.gcs_bucket != f"{settings.google_cloud_project}-media":
        raise ValueError("GCS bucket must match the dedicated project id")
    if settings.google_cloud_location != "global":
        raise ValueError("Vertex location must be global for the verified model pair")
    if settings.gemini_model != "gemini-3.5-flash-lite":
        raise ValueError("Gemini model must match the credential-verified deployment model")
    if (
        not settings.clickhouse_host
        or not _CLICKHOUSE_CLOUD_HOST_RE.fullmatch(settings.clickhouse_host)
        or settings.clickhouse_port != 8443
        or not settings.clickhouse_secure
        or not settings.clickhouse_verify
        or settings.clickhouse_database != "revisionproof"
    ):
        raise ValueError("ClickHouse must use the locked TLS Cloud service contract")
    if settings.live_missing_settings:
        raise ValueError("Missing LIVE settings: " + ", ".join(settings.live_missing_settings))
    locked_identifiers = {
        "clickhouse_writer_username": (
            settings.clickhouse_writer_username,
            "revisionproof_writer_user",
        ),
        "clickhouse_writer_role": (settings.clickhouse_writer_role, "revisionproof_writer"),
        "clickhouse_mcp_username": (
            settings.clickhouse_mcp_username,
            "revisionproof_mcp_user",
        ),
        "clickhouse_mcp_role": (settings.clickhouse_mcp_role, "revisionproof_mcp_reader"),
    }
    for name, (actual, expected) in locked_identifiers.items():
        if actual != expected or not _IDENTIFIER_RE.fullmatch(actual):
            raise ValueError(f"{name} must be the locked RevisionProof identifier {expected}")


def user_provisioning_commands(settings: Settings) -> list[tuple[str, dict[str, str]]]:
    return [
        (
            "CREATE USER IF NOT EXISTS "
            f"{settings.clickhouse_writer_username} "
            "IDENTIFIED WITH sha256_password BY {password:String}",
            {"password": str(settings.clickhouse_writer_password)},
        ),
        (
            f"ALTER USER {settings.clickhouse_writer_username} "
            "IDENTIFIED WITH sha256_password BY {password:String}",
            {"password": str(settings.clickhouse_writer_password)},
        ),
        (f"REVOKE ALL ON *.* FROM {settings.clickhouse_writer_username}", {}),
        (
            "CREATE USER IF NOT EXISTS "
            f"{settings.clickhouse_mcp_username} "
            "IDENTIFIED WITH sha256_password BY {password:String}",
            {"password": str(settings.clickhouse_mcp_password)},
        ),
        (
            f"ALTER USER {settings.clickhouse_mcp_username} "
            "IDENTIFIED WITH sha256_password BY {password:String}",
            {"password": str(settings.clickhouse_mcp_password)},
        ),
        (f"REVOKE ALL ON *.* FROM {settings.clickhouse_mcp_username}", {}),
        (
            f"ALTER USER {settings.clickhouse_mcp_username} SETTINGS "
            "readonly = 2, max_execution_time = 5, max_result_rows = 2000",
            {},
        ),
        (
            f"GRANT {settings.clickhouse_writer_role} TO {settings.clickhouse_writer_username}",
            {},
        ),
        (
            f"SET DEFAULT ROLE {settings.clickhouse_writer_role} "
            f"TO {settings.clickhouse_writer_username}",
            {},
        ),
        (
            f"GRANT {settings.clickhouse_mcp_role} TO {settings.clickhouse_mcp_username}",
            {},
        ),
        (
            f"SET DEFAULT ROLE {settings.clickhouse_mcp_role} "
            f"TO {settings.clickhouse_mcp_username}",
            {},
        ),
    ]


def _apply_sql_files(admin: Any, repo_root: Path) -> None:
    for relative_path in ("infra/clickhouse/schema.sql", "infra/clickhouse/roles.sql"):
        sql = (repo_root / relative_path).read_text(encoding="utf-8")
        for statement in split_sql_statements(sql):
            admin.command(statement)


def verify_append_only_layouts(admin: Any) -> None:
    rows = admin.query(
        "SELECT name, engine, sorting_key FROM system.tables "
        "WHERE database = 'revisionproof' AND name IN "
        "('revision_specs', 'version_features', 'version_checks')"
    ).result_rows
    actual = {
        str(name): (normalize_clickhouse_engine(str(engine)), str(sorting_key))
        for name, engine, sorting_key in rows
    }
    if actual != APPEND_ONLY_TABLE_LAYOUTS:
        raise RuntimeError(
            "ClickHouse append-only schema drift detected; run the guarded migration first; "
            f"actual={actual!r}"
        )


def ensure_deployment_metadata(admin: Any, settings: Settings) -> None:
    expected = (str(settings.google_cloud_project), str(settings.clickhouse_host))
    rows = admin.query(
        "SELECT project_id, clickhouse_host FROM revisionproof.deployment_metadata"
    ).result_rows
    if not rows:
        admin.insert(
            "revisionproof.deployment_metadata",
            [[expected[0], expected[1], datetime.now(UTC)]],
            column_names=["project_id", "clickhouse_host", "created_at"],
        )
        rows = admin.query(
            "SELECT project_id, clickhouse_host FROM revisionproof.deployment_metadata"
        ).result_rows
    actual = [(str(project_id), str(host)) for project_id, host in rows]
    if actual != [expected]:
        raise RuntimeError(
            "ClickHouse deployment metadata does not exactly match this RevisionProof project"
        )


def _provision_users(admin: Any, settings: Settings) -> None:
    for query, parameters in user_provisioning_commands(settings):
        admin.command(query, parameters=parameters or None)
    expected_memberships = {
        VIEW_DEFINER_USER: VIEW_DEFINER_ROLE,
        settings.clickhouse_writer_username: settings.clickhouse_writer_role,
        settings.clickhouse_mcp_username: settings.clickhouse_mcp_role,
    }
    for grantee, expected_role in expected_memberships.items():
        rows = admin.query(
            "SELECT granted_role_name FROM system.role_grants WHERE user_name = {grantee:String}",
            parameters={"grantee": grantee},
        ).result_rows
        for row in rows:
            granted_role = str(row[0])
            if granted_role != expected_role:
                if not _IDENTIFIER_RE.fullmatch(granted_role):
                    raise RuntimeError("refusing an invalid inherited ClickHouse role")
                admin.command(f"REVOKE {granted_role} FROM {grantee}")
    for role in (
        VIEW_DEFINER_ROLE,
        settings.clickhouse_writer_role,
        settings.clickhouse_mcp_role,
    ):
        rows = admin.query(
            "SELECT granted_role_name FROM system.role_grants WHERE role_name = {role:String}",
            parameters={"role": role},
        ).result_rows
        for row in rows:
            inherited_role = str(row[0])
            if not _IDENTIFIER_RE.fullmatch(inherited_role):
                raise RuntimeError("refusing an invalid inherited ClickHouse role")
            admin.command(f"REVOKE {inherited_role} FROM {role}")


def verify_view_security(admin: Any) -> None:
    rows = admin.query(
        "SELECT name, definer, create_table_query FROM system.tables "
        "WHERE database = 'revisionproof' "
        "AND name IN ('search_segments', 'version_feature_diff')"
    ).result_rows
    definitions = {str(name): (str(definer), str(query)) for name, definer, query in rows}
    if set(definitions) != {"search_segments", "version_feature_diff"}:
        raise RuntimeError("RevisionProof security views are missing")
    for name, (definer, query) in definitions.items():
        if (
            definer != VIEW_DEFINER_USER
            or VIEW_DEFINER_USER not in query
            or "SQL SECURITY DEFINER" not in query
        ):
            raise RuntimeError(f"RevisionProof view {name} has an unsafe definer")

    user_rows = admin.query(f"SHOW CREATE USER {VIEW_DEFINER_USER}").result_rows
    if len(user_rows) != 1 or "HOST NONE" not in str(user_rows[0][0]):
        raise RuntimeError("RevisionProof view definer must be unable to log in")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _upload_source_asset(settings: Settings, source: Path) -> tuple[str, bool]:
    try:
        from google.api_core.exceptions import PreconditionFailed
        from google.cloud import storage
    except ImportError as exc:
        raise RuntimeError("install the backend 'live' extra to bootstrap GCS") from exc

    object_name = f"assets/{DEMO_ASSET_ID}/revisionproof_v1.mp4"
    gcs_uri = f"gs://{settings.gcs_bucket}/{object_name}"
    digest = _sha256(source)
    client = storage.Client(project=settings.google_cloud_project)
    try:
        blob = client.bucket(str(settings.gcs_bucket)).blob(object_name)
        if blob.exists(client=client):
            blob.reload(client=client)
            metadata = blob.metadata or {}
            if metadata.get("sha256") != digest or blob.size != source.stat().st_size:
                raise RuntimeError(f"refusing to overwrite drifted source object {gcs_uri}")
            return gcs_uri, False
        blob.metadata = {
            "app": "revisionproof",
            "asset_id": DEMO_ASSET_ID,
            "sha256": digest,
        }
        try:
            blob.upload_from_filename(
                str(source),
                content_type="video/mp4",
                if_generation_match=0,
            )
        except PreconditionFailed as exc:
            raise RuntimeError(f"source object appeared concurrently at {gcs_uri}") from exc
        return gcs_uri, True
    finally:
        client.close()


def _seed_clickhouse(
    admin: Any,
    settings: Settings,
    interpreter: VertexGeminiInterpreter,
    gcs_uri: str,
) -> int:
    created_at = datetime.now(UTC)
    asset_rows = admin.query(
        "SELECT title, gcs_uri, duration_seconds FROM revisionproof.assets "
        "WHERE asset_id = {asset_id:String}",
        parameters={"asset_id": DEMO_ASSET_ID},
    ).result_rows
    if not asset_rows:
        admin.insert(
            "revisionproof.assets",
            [[DEMO_ASSET_ID, "RevisionProof — Product Reveal", gcs_uri, 30.0, created_at]],
            column_names=[
                "asset_id",
                "title",
                "gcs_uri",
                "duration_seconds",
                "created_at",
            ],
        )
    elif len(asset_rows) != 1 or (
        str(asset_rows[0][0]) != "RevisionProof — Product Reveal"
        or str(asset_rows[0][1]) != gcs_uri
        or abs(float(asset_rows[0][2]) - 30.0) > 0.001
    ):
        raise RuntimeError("refusing to continue with a drifted ClickHouse demo asset")

    existing_rows = admin.query(
        "SELECT segment_id, start_seconds, end_seconds, transcript, visual_summary, "
        "length(embedding) FROM revisionproof.segments "
        "WHERE asset_id = {asset_id:String}",
        parameters={"asset_id": DEMO_ASSET_ID},
    ).result_rows
    existing: dict[str, tuple[Any, ...]] = {}
    for row in existing_rows:
        segment_id = normalize_clickhouse_fixed_string(row[0])
        if segment_id in existing:
            raise RuntimeError(f"duplicate seeded segment {segment_id}")
        existing[segment_id] = row
    for expected in SEED_SEGMENTS:
        row = existing.get(expected.segment_id)
        if row is None:
            continue
        if (
            abs(float(row[1]) - expected.start_seconds) > 0.001
            or abs(float(row[2]) - expected.end_seconds) > 0.001
            or str(row[3]) != expected.transcript
            or str(row[4]) != expected.visual_summary
            or int(row[5]) != 768
        ):
            raise RuntimeError(f"refusing to reuse drifted segment {expected.segment_id}")
    missing = [segment for segment in SEED_SEGMENTS if segment.segment_id not in existing]
    rows: list[list[Any]] = []
    for segment in missing:
        embedding = interpreter.embed(segment.embedding_text)
        if len(embedding) != 768:
            raise RuntimeError("Vertex seed embedding did not contain 768 dimensions")
        rows.append(
            [
                segment.segment_id,
                DEMO_ASSET_ID,
                segment.start_seconds,
                segment.end_seconds,
                segment.transcript,
                segment.visual_summary,
                embedding,
                created_at,
            ]
        )
    if rows:
        admin.insert(
            "revisionproof.segments",
            rows,
            column_names=[
                "segment_id",
                "asset_id",
                "start_seconds",
                "end_seconds",
                "transcript",
                "visual_summary",
                "embedding",
                "created_at",
            ],
        )
    return len(rows)


def bootstrap_live(
    settings: Settings,
    *,
    clickhouse_admin_username: str,
    clickhouse_admin_password: str,
    repo_root: Path,
) -> dict[str, Any]:
    validate_live_bootstrap_settings(settings)
    if not clickhouse_admin_username or not clickhouse_admin_password:
        raise ValueError("ClickHouse admin credentials are required")
    source = demo_asset_path(settings.runtime_dir)
    if not source.is_file():
        raise FileNotFoundError("demo source is missing; run scripts/generate_demo_assets.py")
    try:
        import clickhouse_connect
    except ImportError as exc:
        raise RuntimeError("install the backend 'live' extra to bootstrap ClickHouse") from exc

    admin = clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=clickhouse_admin_username,
        password=clickhouse_admin_password,
        database="default",
        secure=settings.clickhouse_secure,
        verify=settings.clickhouse_verify,
    )
    try:
        _apply_sql_files(admin, repo_root)
        ensure_deployment_metadata(admin, settings)
        verify_append_only_layouts(admin)
        _provision_users(admin, settings)
        verify_view_security(admin)
        gcs_uri, source_uploaded = _upload_source_asset(settings, source)
        interpreter = VertexGeminiInterpreter(settings)
        inserted_segments = _seed_clickhouse(admin, settings, interpreter, gcs_uri)
    finally:
        admin.close()

    target_embedding = interpreter.embed("RevisionProof")
    rows = asyncio.run(
        McpClickHouseReader(settings).run_query(
            build_segment_search_query(DEMO_ASSET_ID, target_embedding, 5)
        )
    )
    returned_anchors = [
        (
            normalize_clickhouse_fixed_string(row.get("segment_id")),
            float(row.get("score", 0.0)),
        )
        for row in rows
    ]
    if not returned_anchors or returned_anchors[0][0] != SEED_SEGMENTS[1].segment_id:
        raise RuntimeError(
            "official mcp-clickhouse did not return the expected evidence segment; "
            f"returned={returned_anchors!r}"
        )
    if float(rows[0]["score"]) < 0.82:
        raise RuntimeError("seeded evidence score is below the automatic-preview threshold")

    return {
        "status": "PASS",
        "project": settings.google_cloud_project,
        "vertex_location": settings.google_cloud_location,
        "gemini_model": settings.gemini_model,
        "embedding_model": settings.embedding_model,
        "gcs_uri": gcs_uri,
        "source_uploaded": source_uploaded,
        "segments_inserted": inserted_segments,
        "mcp_tool": "run_query",
        "top_anchor": {
            **asdict(SEED_SEGMENTS[1]),
            "score": float(rows[0]["score"]),
        },
    }
