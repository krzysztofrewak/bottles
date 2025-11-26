from scripts import stats


def test_stats_basic(temp_images, monkeypatch):
    monkeypatch.setattr("scripts.stats.IMAGES_DIR", temp_images)

    total, attr_counts, combos, ext_counts, errors = stats.collect_statistics({})

    assert total == 8
    assert len(errors) == 1  # invalid_name.jpg
    assert combos[("euro", "brown", "filled", "light", "labeled", "open")] == 2
    assert combos[("vichy", "brown", "filled", "dark", "labeled", "open")] == 6
    assert ext_counts["jpg"] == 6
