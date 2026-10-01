from scripts import file_processor


def test_local_data_businesses_are_initialized_from_real_folders():
    businesses = file_processor.list_all_businesses()
    ids = {b["id"] for b in businesses}

    assert "air_traffic" in ids
    assert "bank" in ids
    assert "hydro_power" in ids

    local_businesses = [b for b in businesses if b["id"] in {"air_traffic", "bank", "hydro_power"}]
    assert len(local_businesses) == 3
    for business in local_businesses:
        assert business["db_exists"] is True
        assert business["table_count"] > 0
