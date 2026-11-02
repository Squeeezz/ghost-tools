import os

import pytest


@pytest.fixture
def hardlink():
    def create(source, alias):
        try:
            os.link(source, alias)
        except OSError as exc:
            if os.environ.get('CI'):
                raise
            pytest.skip(f'This local environment does not permit hard links: {exc}')
    return create
