import collections
import os
import time
import json
import xml.etree.ElementTree as ET
import datetime

from ns_endotarter import utils


class Data():
    """Represents NationStates game data.

    Args:
        api (NS_API): NationStates API adapter
        cache (Cache): File cache object
        dump_path (str): Data dump file path
        my_region (str): My region name
        my_nation (str): My nation name
    """

    def __init__(self, api, cache, dump_path, my_region,
                 my_nation, daily_cache_update=True):
        self.api = api
        self.cache = cache

        self.my_region = my_region
        self.my_nation = my_nation
        self.dump_path = dump_path
        self.daily_cache_update = daily_cache_update

        # Nations you have endorsed
        self.endorsed = set()
        # Nations for you to endorse
        self.endorseable = []

    def get_endorsed_from_dump(self, dump):
        """Parse data dump to get endorsed nations.

        Args:
            dump (file): Dump file handle
        """

        xml = ET.iterparse(dump)
        xml_iter = iter(xml)
        evt, root = xml_iter.__next__()

        is_in_region = False
        for evt, elem in xml_iter:
            if evt == 'end' and elem.tag == 'NATION':
                region = utils.canonical(elem.find('REGION').text)
                if region == self.my_region:
                    is_in_region = True
                    endorsee = elem.find('ENDORSEMENTS').text
                    if endorsee is None:
                        continue

                    nation = utils.canonical(elem.find('NAME').text)
                    if nation == self.my_nation:
                        continue

                    if self.my_nation in utils.canonical(endorsee):
                        self.endorsed.add(nation)

                elif is_in_region == True:
                    break

                root.clear()

    def get_endorsed_nations(self):
        """Get endorsed nations from data dump or from cache.
        """

        is_created = self.cache.load()

        if self.daily_cache_update and (not is_created or not self.cache.is_updated):
            dump = utils.load_dump(self.dump_path)
            self.get_endorsed_from_dump(dump)
            self.cache['endorsed'] = list(self.endorsed)
            self.cache.save()
        else:
            self.endorsed = set(self.cache['endorsed'])

    def gen_endorseable(self):
        """Generate nations to endorse.
        """

        wa_members = self.api.get_wa_members()
        region_members = self.api.get_region_members()
        region_wa_members = wa_members & region_members

        self.endorseable = list(region_wa_members - self.endorsed)

    def load(self):
        """Load all data and return an iterator for endorseable.

        Returns:
            Iterator: Iterator to get endorseable nations.
        """

        self.get_endorsed_nations()
        self.gen_endorseable()

    def get_endorseable_iter(self):
        for endorseable in self.endorseable:
            yield endorseable
            self.endorseable.remove(endorseable)
            self.endorsed.add(endorseable)

    def save_cache(self):
        """Save endorsed nations to cache
        """

        self.cache['endorsed'] = list(self.endorsed)
        self.cache.save()


class Cache(collections.UserDict):
    """Cache various data to avoid using the data dump.
    Use like a normal dictionary.

    Args:
        file_path (str): Cache file path
        dump_update_time (str): Daily data dump update time (ISO format)
    """

    def __init__(self, file_path, daily_dump_update_time):
        super().__init__()

        self.file_path = file_path
        self.created_day = None
        self.daily_dump_update_time = datetime.time.fromisoformat(daily_dump_update_time)

    @property
    def is_updated(self):
        """Is the cache still up-to-date.
        """

        current_time = datetime.datetime.utcnow()
        next_dump_update_day = self.created_day + datetime.timedelta(days=1)
        next_dump_update_time = datetime.datetime.combine(next_dump_update_day, self.daily_dump_update_time)

        if current_time < next_dump_update_time:
            return True
        else:
            return False

    def load(self):
        """Load cache from JSON file and return if it exists.

        Returns:
            bool: True if file exists and loaded, False otherwise.
        """

        if os.path.exists(self.file_path):
            with open(self.file_path) as f:
                json_dict = json.load(f)
                created_time = json_dict.pop('created_time')
                self.created_day = datetime.datetime.utcfromtimestamp(created_time).date()
                self.data = json_dict
                return True
        else:
            return False

    def save(self):
        """Save cache to JSON file
        """

        created_time = int(time.time())
        json_dict = {'created_time': created_time}
        json_dict.update(self.data)
        # Discard cache dict after saving
        self.data = {}
        with open(self.file_path, 'w') as f:
            json.dump(json_dict, f)
