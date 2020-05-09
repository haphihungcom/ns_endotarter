import datetime
import os
import json
import io
import gzip
from unittest import mock

import freezegun
import pytest
import xmltodict

from ns_endotarter import data


@pytest.fixture
def mock_dump():
    nations = {'NATION': [{'NAME': 'Nation 1', 'REGION': 'My Region',
                           'ENDORSEMENTS': 'my_nation,nation_2'},
                          {'NAME': 'Nation 2', 'REGION': 'My Region',
                           'ENDORSEMENTS': 'my_nation'},
                          {'NAME': 'Nation 3', 'REGION': 'My Region',
                           'ENDORSEMENTS': ''},
                          {'NAME': 'My Nation', 'REGION': 'My Region',
                           'ENDORSEMENTS': 'nation_1,nation_2'},
                          {'NAME': 'Nation 4', 'REGION': 'Other Region',
                           'ENDORSEMENTS': 'nation_5,nation_6'}]}
    xml = xmltodict.unparse({'NATIONS': nations})
    dump = io.StringIO(xml)
    return dump


class TestData():
    def test_get_endorsed_from_dump(self, mock_dump):
        # my_nation and my_region expects canonicalized input
        obj = data.Data(mock.Mock(), mock.Mock(), '',
                        'my_region', 'my_nation')

        obj.get_endorsed_from_dump(mock_dump)

        assert obj.endorsed == {'nation_1', 'nation_2'}

    def test_gen_endorseable(self):
        get_wa_members = mock.Mock(return_value={'nation1', 'nation2', 'nation3', 'nation4'})
        get_region_members = mock.Mock(return_value={'nation1', 'nation2', 'nation3', 'nation5'})
        mock_api = mock.Mock(get_wa_members=get_wa_members,
                             get_region_members=get_region_members)
        obj = data.Data(mock_api, mock.Mock(), '', '', '')
        obj.endorsed = {'nation1'}

        obj.gen_endorseable()

        assert all(nation in ['nation2', 'nation3'] for nation in obj.endorseable)

    def test_endorseable_iterator(self):
        obj = data.Data(mock.Mock(), mock.Mock(), '', '', '')
        obj.endorseable = ['nation_1', 'nation_2', 'nation_3']
        iterator = obj.get_endorseable_iter()

        first_result = next(iterator)
        next(iterator)

        assert first_result == 'nation_1'
        assert obj.endorseable == ['nation_2', 'nation_3']
        assert 'nation_1' in obj.endorsed

    def test_endorseable_iterator_empty_endoresable(self):
        obj = data.Data(mock.Mock(), mock.Mock(), '', '', '')
        obj.endorseable = []
        iterator = obj.get_endorseable_iter()

        with pytest.raises(StopIteration):
            next(iterator)


class TestCache():
    @pytest.fixture
    def setup_cache_file(self):
        json_dict = {'created_time': 1, 'key1': ['data1', 'data2']}
        with open('cache.json', 'w') as f:
            json.dump(json_dict, f)

    @pytest.fixture
    def remove_cache_file(self):
        yield
        os.remove('cache.json')

    def test_load(self, setup_cache_file, remove_cache_file):
        obj = data.Cache('cache.json', '00:00:00')

        is_exist = obj.load()

        assert obj == {'key1': ['data1', 'data2']}
        assert is_exist

    @freezegun.freeze_time('1970-01-01 00:00:01')
    def test_save(self, remove_cache_file):
        obj = data.Cache('cache.json', '00:00:00')
        obj['key1'] = ['data1', 'data2']

        obj.save()

        with open('cache.json') as f:
            result = json.load(f)

        assert result == {'created_time': 1, 'key1': ['data1', 'data2']}

    @freezegun.freeze_time('1970-01-02 11:00:00')
    def test_is_update(self):
        obj = data.Cache('', '12:00:00')
        obj.created_day = datetime.date.fromisoformat('1970-01-01')

        assert obj.is_updated


class TestDataandCache():
    @pytest.fixture
    def mock_dump_file(self, mock_dump):
        with gzip.open('dump.xml.gz', 'wb') as f:
            f.write(mock_dump.getvalue().encode())

        yield

        os.remove('dump.xml.gz')

    @pytest.fixture
    def setup_mock_cache(self):
        json_dict = {'created_time': 1, 'endorsed': ['nation_3', 'nation_4']}
        with open('cache.json', 'w') as f:
            json.dump(json_dict, f)

    @pytest.fixture
    def remove_mock_cache(self):
        yield
        os.remove('cache.json')

    def test_get_endorsed_nations_not_yet_exist_cache(self, mock_dump_file, remove_mock_cache):
        cache = data.Cache('cache.json', '13:00:00')
        obj = data.Data(mock.Mock(), cache, 'dump.xml.gz',
                        'my_region', 'my_nation')

        obj.get_endorsed_nations()

        assert obj.endorsed == {'nation_1', 'nation_2'}
        assert os.path.exists('cache.json')

    @freezegun.freeze_time('1970-01-02 14:00:00')
    def test_get_endorsed_nations_outdated_cache(self, mock_dump_file, setup_mock_cache,
                                                 remove_mock_cache):
        cache = data.Cache('cache.json', '12:00:00')
        obj = data.Data(mock.Mock(), cache, 'dump.xml.gz',
                        'my_region', 'my_nation')

        obj.get_endorsed_nations()

        assert obj.endorsed == {'nation_1', 'nation_2'}

    @freezegun.freeze_time('1970-01-01 14:00:00')
    def test_get_endorsed_nations_up_to_date_cache(self, mock_dump_file, setup_mock_cache,
                                                 remove_mock_cache):
        cache = data.Cache('cache.json', '12:00:00')
        obj = data.Data(mock.Mock(), cache, 'dump.xml.gz',
                        'my_region', 'my_nation')

        obj.get_endorsed_nations()

        assert obj.endorsed == {'nation_3', 'nation_4'}
