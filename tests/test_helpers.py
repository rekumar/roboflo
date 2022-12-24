from unittest import TestCase
from uuid import UUID
from roboflo.helpers import generate_id

def is_valid_UUID(s):
    try:
        UUID(str(s))
        return True
    except ValueError:
        return False

class TestHelpers(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_isUUID4(self):
        uid = generate_id("")
        self.assertTrue(is_valid_UUID(uid), "Blank name resulted in invalid UUID4")

        name = "testname"
        full_id = generate_id(name)
        uid = full_id[len(name)+1:]
        self.assertTrue(is_valid_UUID(uid), "Name was not properly terminated with a UUID4")
    
    def test_makesUniqueIDs(self):
        uids = [generate_id("") for i in range(3)]
        self.assertEqual(len(uids), len(set(uids)), "Not generating unique id's!")


        uids = [generate_id("testname") for i in range(3)]
        self.assertEqual(len(uids), len(set(uids)), "Not generating unique id's!")

    




        
    