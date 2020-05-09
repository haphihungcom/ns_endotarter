import nationstates
import toml

from ns_endotarter import api_adapter
from ns_endotarter import data
from ns_endotarter import executor
from ns_endotarter import exceptions
from ns_endotarter import info
from ns_endotarter import utils


class Endotarter():
    def __init__(self, config):
        conf = config['General']
        my_nation = utils.canonical(conf['my_nation'])
        self.password = conf['password']
        user_agent = conf['user_agent']
        if user_agent == '':
            raise exceptions.UserError('You need to set the user agent!')

        ns_api = nationstates.Nationstates(user_agent=user_agent)
        ns_api = api_adapter.NS_API(ns_api, my_nation)
        ns_site = executor.NSSite(user_agent)
        self.executor = executor.EndorseExecutor(ns_api, ns_site)

        cache_conf = config['Cache']
        cache = data.Cache(info.CACHE_PATH, cache_conf['daily_dump_update_time'])
        self.ns_data = data.Data(ns_api, cache, info.DATA_DUMP_PATH,
                                 conf['my_region'], my_nation,
                                 cache_conf['update_from_dump'])

        self.endorseable_iter = None

    def prepare(self):
        self.executor.setup_session(password=self.password)
        print('Logged in')
        self.ns_data.load()
        self.endorseable_iter = self.ns_data.get_endorseable_iter()
        print('Loaded nation list')

    def endorse(self):
        try:
            nation_to_endorse = next(self.endorseable_iter)
            self.executor.endorse(nation_to_endorse)
        except StopIteration:
            print('YOu have endorsed all nations!')
            self.shutdown()

    def print_remaining_nations(self):
        remaining_nations = ', '.join(self.ns_data.endorseable)
        remaining_num = len(remaining_nations)
        print('{} nations to endorse:\n {}'.format(remaining_num, remaining_nations))

    def shutdown(self):
        self.ns_data.save_cache()
        print('Saved cache')


if __name__ == "__main__":
    print('Endotarter v0.1.1')

    config = utils.load_config(info.CONFIG_PATH)
    endotarter = Endotarter(config)

    endotarter.prepare()






