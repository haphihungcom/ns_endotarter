from unittest import mock

import pytest

from ns_endotarter import api_adapter
from ns_endotarter import executor
from ns_endotarter import exceptions


class TestHandleErrors():
    def test_raise_no_exception(self):
        resp = mock.Mock(status_code=200, text='')

        executor.check_errors(resp)

    def test_raise_exception_non_200_http_status_code(self):
        resp = mock.Mock(status_code=404, text='')

        with pytest.raises(exceptions.NSSiteError):
            executor.check_errors(resp)

    def test_raise_exception_site_error(self):
        html = '<p class="error">This request failed a security check. Please try again.</p>'
        resp = mock.Mock(status_code=200, text=html)

        with pytest.raises(exceptions.NSSiteError):
            executor.check_errors(resp)


class TestNSSite():
    @mock.patch('requests.Session.get',
                return_value=mock.Mock(status_code=200,
                                       text='<input type="hidden" name="localid" value="123456">'))
    def test_set_localid_with_html_contains_localid_attr_in_input_tag(self, mock_requests_session_get):
        obj = executor.NSSite('')

        obj.set_local_id('1234567890')

        assert obj.local_id == "123456"

    @mock.patch('requests.Session.post',
                return_value=mock.Mock(status_code=200, text=''))
    def test_execute_send_post_request(self, mock_requests_session_post):
        obj = executor.NSSite('')
        obj.local_id = '12345'

        obj.execute('abc', {'ex_param': 'ex_val'})

        mock_requests_session_post.assert_called_with('https://www.nationstates.net/page=abc',
                                                      data={'ex_param': 'ex_val', 'localid': '12345'})


class TestEndorseExecutor():
    def test_endorse_succeeded(self):
        html = '<input type="hidden" name="action" value="endorse">'
        mock_site = mock.Mock(execute=mock.Mock(return_value=html))
        obj = executor.EndorseExecutor(mock.Mock(), mock_site)

        obj.endorse('nation_1')

        mock_site.execute.assert_called()

    def test_endorse_failed(self):
        html = '<input type="hidden" name="action" value="unendorse">'
        mock_site = mock.Mock(execute=mock.Mock(return_value=html))
        obj = executor.EndorseExecutor(mock.Mock(), mock_site)

        with pytest.raises(exceptions.EndotarterError):
            obj.endorse('nation_1')
