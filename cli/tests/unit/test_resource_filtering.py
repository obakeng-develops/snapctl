from cli.internal.aws.resource_filtering import parse_tag_filter, matches_tag_filter


class TestParseTagFilter:
    """Test tag filter parsing logic."""

    def test_parse_single_tag(self):
        """Single tag should create one OR group with one condition."""
        result = parse_tag_filter("tag:Owner=devops")
        assert result == [[("Owner", "devops")]]

    def test_parse_and_condition(self):
        """AND conditions should be in the same group."""
        result = parse_tag_filter("tag:Owner=devops AND tag:Env=prod")
        assert result == [[("Owner", "devops"), ("Env", "prod")]]

    def test_parse_or_condition(self):
        """OR conditions should create separate groups."""
        result = parse_tag_filter("tag:Owner=devops OR tag:Critical=yes")
        assert result == [[("Owner", "devops")], [("Critical", "yes")]]

    def test_parse_complex_condition(self):
        """Complex AND/OR combinations."""
        result = parse_tag_filter("tag:A=1 AND tag:B=2 OR tag:C=3")
        assert result == [[("A", "1"), ("B", "2")], [("C", "3")]]

    def test_parse_with_whitespace(self):
        """Handle extra whitespace gracefully."""
        result = parse_tag_filter("tag:Owner=devops   AND   tag:Env=prod")
        assert result == [[("Owner", "devops"), ("Env", "prod")]]

    def test_parse_empty_string(self):
        """Empty string should return empty list."""
        result = parse_tag_filter("")
        assert result == []


class TestMatchesTagFilter:
    """Test tag matching logic."""

    def test_matches_single_tag(self):
        """Resource with matching single tag."""
        tags = [{"Key": "Owner", "Value": "devops"}]
        filter_groups = [[("Owner", "devops")]]
        assert matches_tag_filter(tags, filter_groups) is True

    def test_does_not_match_wrong_value(self):
        """Resource with wrong tag value should not match."""
        tags = [{"Key": "Owner", "Value": "devops"}]
        filter_groups = [[("Owner", "finance")]]
        assert matches_tag_filter(tags, filter_groups) is False

    def test_does_not_match_missing_key(self):
        """Resource missing required tag key should not match."""
        tags = [{"Key": "Owner", "Value": "devops"}]
        filter_groups = [[("Environment", "prod")]]
        assert matches_tag_filter(tags, filter_groups) is False

    def test_matches_and_condition_all_present(self):
        """AND condition matches when all tags present."""
        tags = [{"Key": "Owner", "Value": "devops"}, {"Key": "Env", "Value": "prod"}]
        filter_groups = [[("Owner", "devops"), ("Env", "prod")]]
        assert matches_tag_filter(tags, filter_groups) is True

    def test_does_not_match_and_condition_partial(self):
        """AND condition fails when only some tags present."""
        tags = [{"Key": "Owner", "Value": "devops"}]
        filter_groups = [[("Owner", "devops"), ("Env", "prod")]]
        assert matches_tag_filter(tags, filter_groups) is False

    def test_matches_or_condition_first_group(self):
        """OR condition matches when first group satisfied."""
        tags = [{"Key": "Owner", "Value": "devops"}]
        filter_groups = [[("Owner", "devops")], [("Critical", "yes")]]
        assert matches_tag_filter(tags, filter_groups) is True

    def test_matches_or_condition_second_group(self):
        """OR condition matches when second group satisfied."""
        tags = [{"Key": "Critical", "Value": "yes"}]
        filter_groups = [[("Owner", "devops")], [("Critical", "yes")]]
        assert matches_tag_filter(tags, filter_groups) is True

    def test_does_not_match_or_condition_none(self):
        """OR condition fails when no groups match."""
        tags = [{"Key": "Team", "Value": "backend"}]
        filter_groups = [[("Owner", "devops")], [("Critical", "yes")]]
        assert matches_tag_filter(tags, filter_groups) is False

    def test_matches_empty_tags(self):
        """Resource with no tags should not match anything."""
        tags = []
        filter_groups = [[("Owner", "devops")]]
        assert matches_tag_filter(tags, filter_groups) is False

    def test_matches_empty_filter(self):
        """Empty filter should not match anything."""
        tags = [{"Key": "Owner", "Value": "devops"}]
        filter_groups = []
        assert matches_tag_filter(tags, filter_groups) is False
