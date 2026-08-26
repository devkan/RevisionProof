CREATE ROLE IF NOT EXISTS revisionproof_writer;
REVOKE ALL ON *.* FROM revisionproof_writer;
GRANT INSERT ON revisionproof.revision_specs TO revisionproof_writer;
GRANT INSERT ON revisionproof.version_features TO revisionproof_writer;
GRANT INSERT ON revisionproof.version_checks TO revisionproof_writer;

CREATE ROLE IF NOT EXISTS revisionproof_mcp_reader;
REVOKE ALL ON *.* FROM revisionproof_mcp_reader;
GRANT SELECT ON revisionproof.search_segments TO revisionproof_mcp_reader;
GRANT SELECT ON revisionproof.version_feature_diff TO revisionproof_mcp_reader;
