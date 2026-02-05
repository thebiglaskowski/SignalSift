"""Tests for base source module."""

from datetime import datetime

import pytest

from signalsift.sources.base import BaseSource, ContentItem


class TestContentItem:
    """Tests for ContentItem dataclass."""

    def test_content_item_creation(self):
        """Test creating a ContentItem."""
        now = datetime.now()
        item = ContentItem(
            id="test123",
            source_type="reddit",
            source_id="SEO",
            title="Test Title",
            content="Test content",
            url="https://example.com",
            created_at=now,
            metadata={"score": 100},
        )

        assert item.id == "test123"
        assert item.source_type == "reddit"
        assert item.source_id == "SEO"
        assert item.title == "Test Title"
        assert item.content == "Test content"
        assert item.url == "https://example.com"
        assert item.created_at == now
        assert item.metadata == {"score": 100}

    def test_content_item_with_empty_metadata(self):
        """Test creating ContentItem with empty metadata."""
        item = ContentItem(
            id="test",
            source_type="youtube",
            source_id="UC123",
            title="Title",
            content="Content",
            url="https://youtube.com",
            created_at=datetime.now(),
            metadata={},
        )

        assert item.metadata == {}

    def test_content_item_youtube_type(self):
        """Test ContentItem for YouTube source."""
        item = ContentItem(
            id="video123",
            source_type="youtube",
            source_id="UCabcd",
            title="SEO Tutorial",
            content="Video transcript here",
            url="https://youtube.com/watch?v=123",
            created_at=datetime.now(),
            metadata={"views": 10000, "likes": 500},
        )

        assert item.source_type == "youtube"
        assert item.metadata["views"] == 10000


class TestBaseSource:
    """Tests for BaseSource abstract class."""

    def test_cannot_instantiate_directly(self):
        """Test that BaseSource cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseSource()

    def test_concrete_implementation(self):
        """Test that a concrete implementation can be created."""

        class ConcreteSource(BaseSource):
            def fetch(self, since=None, limit=None):
                return []

            def get_source_type(self):
                return "test"

            def test_connection(self):
                return True

        source = ConcreteSource()
        assert source.get_source_type() == "test"
        assert source.test_connection() is True
        assert source.fetch() == []

    def test_fetch_with_parameters(self):
        """Test fetch method with parameters."""
        test_items = [
            ContentItem(
                id="1",
                source_type="test",
                source_id="test_source",
                title="Test",
                content="Content",
                url="https://test.com",
                created_at=datetime.now(),
                metadata={},
            )
        ]

        class ConcreteSource(BaseSource):
            def fetch(self, since=None, limit=None):
                items = test_items[:]
                if limit:
                    items = items[:limit]
                return items

            def get_source_type(self):
                return "test"

            def test_connection(self):
                return True

        source = ConcreteSource()
        result = source.fetch(limit=1)
        assert len(result) == 1
        assert result[0].id == "1"

    def test_test_connection_failure(self):
        """Test that test_connection can return False."""

        class FailingSource(BaseSource):
            def fetch(self, since=None, limit=None):
                return []

            def get_source_type(self):
                return "failing"

            def test_connection(self):
                return False

        source = FailingSource()
        assert source.test_connection() is False

    def test_abstract_methods_required(self):
        """Test that all abstract methods must be implemented."""

        # Missing fetch
        class MissingFetch(BaseSource):
            def get_source_type(self):
                return "test"

            def test_connection(self):
                return True

        with pytest.raises(TypeError):
            MissingFetch()

        # Missing get_source_type
        class MissingSourceType(BaseSource):
            def fetch(self, since=None, limit=None):
                return []

            def test_connection(self):
                return True

        with pytest.raises(TypeError):
            MissingSourceType()

        # Missing test_connection
        class MissingTestConnection(BaseSource):
            def fetch(self, since=None, limit=None):
                return []

            def get_source_type(self):
                return "test"

        with pytest.raises(TypeError):
            MissingTestConnection()
