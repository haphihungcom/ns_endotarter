import requests
import bs4

from ns_endotarter import exceptions


ACTION_URL = "https://www.nationstates.net/{}"
LOCALID_URL = "https://www.nationstates.net/template-overall=none/page=settings"
ENDORSE_ACTION = "cgi-bin/endorse.cgi"


def check_errors(resp):
    """Check respond for HTTP or NationStates errors.

    Args:
        resp (requests.Respond): Respond.

    Raises:
        exceptions.NSSiteError: Contains error message.
    """

    if resp.status_code != 200:
        raise exceptions.NSSiteError("""A HTTP error occured when connecting to NationStates website.
                                   HTTP status code: {}""".format(resp.status_code))

    soup = bs4.BeautifulSoup(resp.text, 'html.parser')
    error_elem = soup.find(name='p', attrs={'class': 'error'})

    if error_elem is None:
        return
    else:
        error = error_elem.string
        raise exceptions.NSSiteError("NationStates site error: {}".format(error))


class NSSite():
    """API to send POST requests to NationStates main site.

    Args:
        user_agent (str): User agent
    """

    def __init__(self, user_agent):
        self.session = requests.Session()
        self.session.headers['user-agent'] = user_agent

        self.local_id = None

    def set_local_id(self, pin):
        """Set local id acquired from a page that contains it.
        Args:
            pin (str): PIN number for login. Get by private API call
        """

        self.session.cookies['pin'] = pin

        resp = self.session.get(LOCALID_URL)
        check_errors(resp)

        soup = bs4.BeautifulSoup(resp.text, 'html.parser')
        local_id = soup.find(name='input', attrs={'name': 'localid'})['value']

        self.local_id = local_id


    def execute(self, action, params):
        """Send a POST request.

        Args:
            action (str): URL
            params (dict): Parameters.

        Returns:
            str: Respond's HTML content
        """

        params['localid'] = self.local_id
        url = ACTION_URL.format(action)

        resp = self.session.post(url, data=params)

        check_errors(resp)

        return resp.text


class EndorseExecutor():
    """Execute endorse actions.

    Args:
        ns_api (ns_endotarter.NS_API): NS API adapter
        ns_site (ns_endotarter.NSSite): NS main site interface
        password (str): Password
    """

    def __init__(self, ns_api, ns_site):
        self.ns_api = ns_api
        self.ns_site = ns_site

    def setup_session(self, password):
        """Setup a logged in NS session.
        """

        pin = self.ns_api.login(password)
        self.ns_site.set_local_id(pin)

    def endorse(self, nation):
        """Endorse a nation

        Args:
            nation (str): Nation's name

        Raises:
            exceptions.EndotarterError: Raises if failed to endorse a nation
        """

        params = {'nation': nation,
                  'action': 'endorse'}

        html = self.ns_site.execute(action=ENDORSE_ACTION, params=params)

        soup = bs4.BeautifulSoup(html, 'html.parser')

        if soup.find(name='input', attrs={'name': 'action', 'value': 'unendorse'}):
            raise exceptions.EndotarterError('Could not endorse {}'.format(nation))
