CREATE ROLE IF NOT EXISTS revisionproof_view_definer;
REVOKE ALL ON *.* FROM revisionproof_view_definer;
GRANT SELECT ON revisionproof.segments TO revisionproof_view_definer;
GRANT SELECT ON revisionproof.version_features TO revisionproof_view_definer;

CREATE USER IF NOT EXISTS revisionproof_view_definer_user
IDENTIFIED WITH sha256_hash BY 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
HOST NONE;
ALTER USER revisionproof_view_definer_user
IDENTIFIED WITH sha256_hash BY 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
HOST NONE;
REVOKE ALL ON *.* FROM revisionproof_view_definer_user;
GRANT revisionproof_view_definer TO revisionproof_view_definer_user;
SET DEFAULT ROLE revisionproof_view_definer TO revisionproof_view_definer_user;

CREATE ROLE IF NOT EXISTS revisionproof_writer;
REVOKE ALL ON *.* FROM revisionproof_writer;
GRANT INSERT ON revisionproof.revision_specs TO revisionproof_writer;
GRANT INSERT ON revisionproof.version_features TO revisionproof_writer;
GRANT INSERT ON revisionproof.version_checks TO revisionproof_writer;

CREATE ROLE IF NOT EXISTS revisionproof_mcp_reader;
REVOKE ALL ON *.* FROM revisionproof_mcp_reader;
GRANT SELECT ON revisionproof.search_segments TO revisionproof_mcp_reader;
GRANT SELECT ON revisionproof.version_feature_diff TO revisionproof_mcp_reader;
