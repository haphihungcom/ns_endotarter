from ns_endotarter import utils


class TestUtils():
    def test_canonical(self):
        result = utils.canonical('Test_Nation')

        assert result == 'test_nation'
