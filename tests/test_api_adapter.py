from unittest import mock

import nationstates
import pytest

from ns_endotarter import api_adapter
from ns_endotarter import exceptions


class TestNS_API():
    def test_login(self):
        mock_nation =  mock.Mock(get_shards=mock.Mock(return_value={'headers': {'X-Pin': '12345678'}}))
        mock_api = mock.Mock(nation=mock.Mock(return_value=mock_nation))
        ns_api = api_adapter.NS_API(mock_api, 'my_nation')

        assert ns_api.login('hunterprime123') == '12345678'
        assert mock_nation.get_shards.called_with('my_nation', 'hunterprime123')

    def test_login_forbidden_exception(self):
        mock_nation =  mock.Mock(get_shards=mock.Mock(side_effect=nationstates.exceptions.Forbidden))
        mock_api = mock.Mock(nation=mock.Mock(return_value=mock_nation))
        ns_api = api_adapter.NS_API(mock_api, 'my_nation')

        with pytest.raises(exceptions.AuthError):
            ns_api.login('hunterprime123') == '12345678'

    def test_get_wa_members(self):
        mock_wa = mock.Mock(members='testnation1;testnation2')
        mock_api = mock.Mock(wa=mock.Mock(return_value=mock_wa))
        ns_api = api_adapter.NS_API(mock_api, '')

        assert ns_api.get_wa_members() == {'testnation1', 'testnation2'}

    def test_get_region_members(self):
        mock_nations = [mock.Mock(nation_name='testnation1'),
                        mock.Mock(nation_name='testnation2')]
        mock_region = mock.Mock(nations=mock_nations)
        mock_nation = mock.Mock(region=mock_region)
        mock_api = mock.Mock(nation=mock.Mock(return_value=mock_nation))
        ns_api = api_adapter.NS_API(mock_api, 'my_nation')

        assert ns_api.get_region_members() == {'testnation1', 'testnation2'}
        assert mock_api.nation.called_with('my_nation')

