CREATE ROLE IF NOT EXISTS revisionproof_writer;
GRANT INSERT ON revisionproof.* TO revisionproof_writer;

CREATE ROLE IF NOT EXISTS revisionproof_mcp_reader;
GRANT SELECT ON revisionproof.search_segments TO revisionproof_mcp_reader;
GRANT SELECT ON revisionproof.version_feature_diff TO revisionproof_mcp_reader;
