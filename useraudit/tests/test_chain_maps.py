from django.test import TestCase

from .utils import chain_maps


class ChainMapsTest(TestCase):
    def test_empty_dict_for_no_args(self):
        self.assertEquals(chain_maps(), {})

    def test_same_dict_returned_for_single_arg(self):
        d = {'a': 1}
        d2 = chain_maps(d)
        self.assertEquals(d2, d)

    def test_copy_of_dict_returned_for_single_arg(self):
        d = {'a': 1}
        d2 = chain_maps(d)
        d2['a'] = 2
        self.assertEquals(d['a'], 1)
        self.assertEquals(d2['a'], 2)

    def test_first_dict_value_overwrites_second_dict_value(self):
        d = {'a': 1}
        d2 = {'a': 2}
        self.assertEquals(chain_maps(d2, d)['a'], 2)
        self.assertEquals(chain_maps(d, d2)['a'], 1)

    def test_parent_dict_is_used_when_key_not_in_first_dict(self):
        d = {'a': 1}
        d2 = {'b': 2}
        self.assertEquals(chain_maps(d2, d)['a'], 1)
        self.assertEquals(chain_maps(d2, d)['b'], 2)

    def test_multiple_parents(self):
        d = {'a': 1}
        d2 = {'b': 2}
        d3 = {'c': 3}
        chain = chain_maps(d3, d2, d)
        self.assertEquals(chain['a'], 1)
        self.assertEquals(chain['b'], 2)
        self.assertEquals(chain['c'], 3)
