from ..profile import LuaProfile
import unittest

class LuaProfileTest(unittest.TestCase):
    
    def test_process_profile_data(self):
        data = """Bytecode:\tMOVE\tLOADK\tLOADBOO
Count:\t3825\t10353\t0

Library:\thandle_luainit\tio_write\tll_module
Count:\t1\t212\t1

ObjectSize:\t0\t12\t16
Count:\t1828\t730\t29
"""
        profiler = LuaProfile('test', 'test-bench')
        profiler.process_data_lines(data.splitlines())
        self.assertEqual({'MOVE':'3825', 'LOADK':'10353', 'LOADBOO':'0'}, profiler.get_opcode_usage())
        self.assertEqual({'handle_luainit':'1', 'io_write':'212', 'll_module':'1'}, profiler.get_library_usage())
        self.assertEqual({'0':'1828', '12':'730', '16':'29'}, profiler.get_memory_usage())

def test_suite():
    return unittest.makeSuite(LuaProfileTest)

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')