"""Test io_mongo."""
from unittest.mock import MagicMock, call, patch

from dataplaybook.tasks.io_mongo import MongoURI, mongo_sync_sids


def test_db_schema_post_validator():
    """Test read."""
    dbm = MongoURI.new_from_string("db://localhost:27027/d1/c1/s1")

    assert dbm.netloc == "localhost:27027"
    assert dbm.set_id == "s1"
    assert dbm.database == "d1"
    assert dbm.collection == "c1"

    clean = ("localhost:27027", "mongodb://localhost:27027/", "db://localhost:27027/")

    for test in clean:
        dbm = MongoURI(netloc=test, database="", collection="")
        assert dbm.netloc == clean[0]


@patch("dataplaybook.tasks.io_mongo.read_mongo")
@patch("dataplaybook.tasks.io_mongo.write_mongo")
@patch("dataplaybook.tasks.io_mongo.mongo_delete_sids")
def test_mongo_sync_sids(
    mock_mongo_delete_sids, mock_write_mongo, mock_read_mongo, caplog
):
    """Test mongo_sync_sids."""
    mock_l_db = MagicMock()
    mock_l = MagicMock()
    mock_l.get_collection.return_value = mock_l_db

    mock_r_db = MagicMock()
    mock_r = MagicMock()
    mock_r.get_collection.return_value = mock_r_db

    mock_l_db.aggregate.return_value = [
        {"_id": "sid1", "count": 1},
        {"_id": "sid2", "count": 2},
    ]
    mock_r_db.aggregate.return_value = [
        {"_id": "sid1", "count": 1},
        {"_id": "sid3", "count": 3},
    ]

    mongo_sync_sids(mdb_local=mock_l, mdb_remote=mock_r)
    mock_l_db.aggregate.assert_called_once()
    mock_l_db.aggregate.assert_called_once()
    assert mock_read_mongo.call_args_list == [call(mdb=mock_l)]
    assert mock_write_mongo.call_args_list == [
        call(mdb=mock_r, table=mock_read_mongo(), set_id="sid2")
    ]
    assert "Removing sids" in caplog.text
    assert mock_mongo_delete_sids.call_args_list == [call(mdb=mock_r, sids=["sid3"])]

    # test with ignore_remote parameter
    mock_mongo_delete_sids.reset_mock()
    caplog.clear()
    mongo_sync_sids(mdb_local=mock_l, mdb_remote=mock_r, ignore_remote=["sid3"])
    assert "Removing sids" not in caplog.text
    assert mock_mongo_delete_sids.call_args_list == []

    # Test only_sync parameter
    mock_l_db.aggregate.return_value = [
        {"_id": "sid1", "count": 1},
        {"_id": "sid2", "count": 2},
        {"_id": "sid5", "count": 2},
        {"_id": "sid7", "count": 2},
    ]
    mock_mongo_delete_sids.reset_mock()
    caplog.clear()
    mock_read_mongo.reset_mock()
    mock_write_mongo.reset_mock()
    mongo_sync_sids(mdb_local=mock_l, mdb_remote=mock_r, only_sync_sids=["sid2"])
    assert mock_read_mongo.call_args_list == [call(mdb=mock_l)]
    assert mock_write_mongo.call_args_list == [
        call(mdb=mock_r, table=mock_read_mongo(), set_id="sid2")
    ]
    assert "Removing sids" not in caplog.text
    assert mock_mongo_delete_sids.call_args_list == []
