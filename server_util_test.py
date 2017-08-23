import unittest

import json

from server_util import getGlobalReqId, splitGlobalReqId, extractUDPPair, extractTCPPair, prepare

class TestServerUtil(unittest.TestCase):
    def setUp(self):
        pass

    def test_getGlobalReqId(self):
        self.assertEqual(getGlobalReqId(2, 4), '2_4')

    def test_splitGlobalReqId(self):
        self.assertEqual(splitGlobalReqId('2_4'), (2, 4))

    def test_extractUDPPair(self):
        self.assertEqual(extractUDPPair(('127.0.0.1', 8000, 9000)), ('127.0.0.1', 8000))

    def test_extractTCPPair(self):
        self.assertEqual(extractTCPPair(('127.0.0.1', 8000, 9000)), ('127.0.0.1', 9000))

    def test_prepare(self):
        msg = dict()
        msg['hello'] = 'world'
        result = prepare(msg)
        resultDecoded = result.decode()
        resultDict = json.loads(resultDecoded)

        ref = dict()
        ref['hello'] = 'world'

        self.assertDictEqual(resultDict, ref)

if __name__ == '__main__':
    unittest.main()