import os

import pytest

from seed_data import initialize_database


@pytest.fixture(scope="session", autouse=True)
def seed_test_database():
    db_path = os.path.join(os.getcwd(), "data", "controller_office.duckdb")
    initialize_database(db_path)
