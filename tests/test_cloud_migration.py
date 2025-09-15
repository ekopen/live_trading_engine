import cloud_migration

def test_migration_entrypoint_exists():
    assert hasattr(cloud_migration, "migration_to_cloud")
    assert callable(cloud_migration.migration_to_cloud)
