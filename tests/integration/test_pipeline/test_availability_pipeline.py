from player_availability.pipeline.availability_pipeline import AvailabilityPipeline


class TestAvailabilityPipeline:
    def test_empty_pipeline(self, repository):
        pipeline = AvailabilityPipeline(
            collectors=[],
            parsers=[],
            normalizers=[],
            repository=repository,
        )
        result = pipeline.run()
        assert result.raw_count == 0
        assert result.parsed_count == 0
        assert result.normalized_count == 0
        assert result.stored_count == 0
        assert result.errors == []
