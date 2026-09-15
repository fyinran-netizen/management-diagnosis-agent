from app.tools.ingestion.repositories import FilesystemArtifactRepository


def test_repository_reads_existing_semantic_metadata_artifact():
    records = FilesystemArtifactRepository().load_semantic_metadata()
    assert records
    assert records[0]["source_id"]
