import nationstates

from ns_endotarter import exceptions


CHAMBER = 'ga'
NS_LIST_DELIMITER = ';'


class NS_API():
    """NationSates API adapter. All results returned as set.

    Args:
        ns_api (nationstates.Nationstates): NationStates API object
        my_nation (str): My nation's name
    """

    def __init__(self, ns_api, my_nation):
        self.api = ns_api
        self.my_nation = my_nation

    def login(self, password):
        """Send ping to the nation and return X-Pin.

        Args:
            my_nation (str): My nation's name

        Returns:
            str: X-Pin
        """

        my_nation = self.api.nation(self.my_nation, password)

        try:
            resp = my_nation.get_shards('ping', full_response=True)
        except nationstates.exceptions.Forbidden:
            raise exceptions.AuthError('Could not log into your nation!')

        return resp['headers']['X-Pin']

    def get_wa_members(self):
        """Get all WA members in the game.

        Returns:
            Set: Set of WA members
        """
        wa = self.api.wa(CHAMBER)
        members = wa.members

        result = set(members.split(NS_LIST_DELIMITER))
        return result

    def get_region_members(self):
        """Get all nations of current region.

        Returns:
            Set: Set of all regional nations
        """

        my_nation = self.api.nation(self.my_nation)
        nations = my_nation.region.nations

        result = {nation.nation_name for nation in nations}
        return result
