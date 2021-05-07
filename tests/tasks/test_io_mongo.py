"""Test io_mongo."""
from dataplaybook.tasks import io_mongo


def test_db_schema_post_validator():
    """Test read."""
    dbm = io_mongo.MongoURI.new_from_string("db://localhost:27027/d1/c1/s1")

    assert dbm.netloc == "localhost:27027"
    assert dbm.set_id == "s1"
    assert dbm.database == "d1"
    assert dbm.collection == "c1"

    clean = ("localhost:27027", "mongodb://localhost:27027/", "db://localhost:27027/")

    for test in clean:
        dbm = io_mongo.MongoURI(netloc=test, database="", collection="")
        assert dbm.netloc == clean[0]
