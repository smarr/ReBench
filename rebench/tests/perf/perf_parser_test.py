# pylint: disable=line-too-long
import json
from unittest import TestCase

from ...interop.perf_parser import PerfParser


class PerfParserTest(TestCase):

    def setUp(self):
        self.p = None

    def _assert_json_is_serializable(self):
        data = self.p.to_json()
        json_str = json.dumps(data)
        self.assertIsInstance(json_str, str)

    def _parse(self, data):
        self.p = p = PerfParser(None)
        p.parse_lines(data.split("\n"))
        return p.get_elements()

    def test_simple_main_entries(self):
        data = """
     0.37%  som-native-inte  som-native-interp-ast  [.] HeapChunkProvider_resetAlignedHeapChunk_3b0d29e3728eb7a6fc10e5e8f65655e2b0d220ca
     0.37%  som-native-inte  [kernel.kallsyms]      [k] native_irq_return_iret
     0.32%  som-native-inte  [kernel.kallsyms]      [k] clear_page_erms
     0.27%  som-native-inte  [kernel.kallsyms]      [k] sync_regs
"""
        elements = self._parse(data)
        self.assertEqual(len(elements), 4)

        e1 = elements[0]
        e4 = elements[3]

        self.assertIsNone(e1.trace)
        self.assertIsNone(e4.trace)
        self.assertEqual(e1.method, "HeapChunkProvider_resetAlignedHeapChunk")
        self.assertEqual(e4.method, "sync_regs")

        self.assertEqual(e1.percent, 0.37)
        self.assertEqual(e4.percent, 0.27)

        self._assert_json_is_serializable()

    def test_simple_hierarchy(self):
        data = """
     7.20%  som-native-inte  som-native-interp-ast  [.] MessageSendNode$AbstractMessageSendNode_evaluateArguments_bf7729bae6effddecf0ca8938ecdffedaf15af80
            |          
             --6.87%--MessageSendNode$AbstractMessageSendNode_evaluateArguments_bf7729bae6effddecf0ca8938ecdffedaf15af80
                       MessageSendNode$AbstractMessageSendNode_executeGeneric_ce143f167036af2090f6f15e30925550ece327b1
                       IntToDoInlinedLiteralsNode_doIntToDo_54685947c4bcab224870fc73d385c495122b828b
                       |          
                        --6.82%--IntToDoInlinedLiteralsNodeFactory$IntToDoInlinedLiteralsNodeGen_executeGeneric_long_long0_428318a36ea78a9e61e6131f65153ae65cab856e
                                  OptimizedCallTarget_executeRootNode_a43d01f11c960918e3be5d613c7f9397ed47b422
                                  |          
                                   --3.13%--OptimizedCallTarget_profiledPERoot_afb4ccd0d1f43f0bbf82d042837d2118c889aac3
                                             OptimizedDirectCallNode_call_ba221ffaf307f8b4cdcc1da9e0b137c8c24c957a
                                             |          
                                              --3.06%--CachedDispatchNode_executeDispatch_25c10c62eef54a3b9bcd3e8ec866c36ad670747a
                                                        |          
                                                         --1.72%--MessageSendNode$GenericMessageSendNode_doPreEvaluated_b0c6be8786ca7c0b2225a86f9d4ef06280c767d7
                                                                   MessageSendNode$AbstractMessageSendNode_executeGeneric_ce143f167036af2090f6f15e30925550ece327b1
"""
        elements = self._parse(data)
        self.assertEqual(len(elements), 1)
        e = elements[0]

        self.assertIsNotNone(e.trace)
        self.assertEqual(len(e.trace), 1)
        self.assertEqual(e.method, "MessageSendNode$AbstractMessageSendNode_evaluateArguments")
        self.assertEqual(e.percent, 7.20)

        e = e.trace[0]
        self.assertIsNotNone(e.trace)
        self.assertEqual(len(e.trace), 3)
        self.assertEqual(e.method, "MessageSendNode$AbstractMessageSendNode_evaluateArguments")
        self.assertEqual(e.percent, 6.87)

        e = e.trace[2]
        self.assertIsNotNone(e.trace)
        self.assertEqual(len(e.trace), 2)
        self.assertEqual(e.method, "IntToDoInlinedLiteralsNodeFactory$IntToDoInlinedLiteralsNodeGen_executeGeneric_long_long0")
        self.assertEqual(e.percent, 6.82)

        e = e.trace[1]
        self.assertIsNotNone(e.trace)
        self.assertEqual(len(e.trace), 2)
        self.assertEqual(e.method, "OptimizedCallTarget_profiledPERoot")
        self.assertEqual(e.percent, 3.13)

        e = e.trace[1]
        self.assertIsNotNone(e.trace)
        self.assertEqual(len(e.trace), 1)
        self.assertEqual(e.method, "CachedDispatchNode_executeDispatch")
        self.assertEqual(e.percent, 3.06)

        e = e.trace[0]
        self.assertIsNotNone(e.trace)
        self.assertEqual(len(e.trace), 1)
        self.assertEqual(e.method, "MessageSendNode$GenericMessageSendNode_doPreEvaluated")
        self.assertEqual(e.percent, 1.72)

        self._assert_json_is_serializable()

    def test_hierarchy_with_some_nesting(self):
        data = """
     5.99%  som-native-inte  som-native-interp-ast  [.] LocalVariableNodeFactory$LocalVariableReadNodeGen_executeGeneric_b6d282cd7cee40289d20846bdb0b59a0940e00a5
            |          
             --5.78%--LocalVariableNodeFactory$LocalVariableReadNodeGen_executeGeneric_b6d282cd7cee40289d20846bdb0b59a0940e00a5
                       |          
                       |--2.92%--EagerBinaryPrimitiveNode_executeGeneric_bf7fec9ded572fea61a9eb9b0031d6b40ef4bfd5
                       |          ExpressionNode_executeLong_60573f5a2d4614ca6dba4dee6fc4c0360506579e
                       |          IntToDoInlinedLiteralsNode_doIntToDo_54685947c4bcab224870fc73d385c495122b828b
                       |          |          
                       |           --2.89%--IntToDoInlinedLiteralsNodeFactory$IntToDoInlinedLiteralsNodeGen_executeGeneric_long_long0_428318a36ea78a9e61e6131f65153ae65cab856e
                       |          
                        --2.86%--MessageSendNode$AbstractMessageSendNode_evaluateArguments_bf7729bae6effddecf0ca8938ecdffedaf15af80
                                  IntToDoInlinedLiteralsNode_doIntToDo_54685947c4bcab224870fc73d385c495122b828b
                                  |          
                                   --2.83%--IntToDoInlinedLiteralsNodeFactory$IntToDoInlinedLiteralsNodeGen_executeGeneric_long_long0_428318a36ea78a9e61e6131f65153ae65cab856e
"""
        elements = self._parse(data)
        self.assertEqual(len(elements), 1)

        e = elements[0]
        self.assertEqual(e.method, "LocalVariableNodeFactory$LocalVariableReadNodeGen_executeGeneric")
        self.assertEqual(e.percent, 5.99)
        self.assertEqual(len(e.trace), 1)

        e = e.trace[0]
        self.assertEqual(e.method,
                         "LocalVariableNodeFactory$LocalVariableReadNodeGen_executeGeneric")
        self.assertEqual(e.percent, 5.78)
        self.assertEqual(len(e.trace), 2)

        e1 = e.trace[0]
        e2 = e.trace[1]
        self.assertEqual(e1.method,
                         "EagerBinaryPrimitiveNode_executeGeneric")
        self.assertEqual(e2.method,
                         "MessageSendNode$AbstractMessageSendNode_evaluateArguments")

        self._assert_json_is_serializable()

    def test_trace_from_main(self):
        data = """
     4.25%  som-native-inte  som-native-interp-ast  [.] OptimizedCallTarget_profileArguments_e8668a5ca6b9022553c0ee2866178043ad99124a
            |
            ---OptimizedCallTarget_profileArguments_e8668a5ca6b9022553c0ee2866178043ad99124a
               OptimizedDirectCallNode_call_ba221ffaf307f8b4cdcc1da9e0b137c8c24c957a
"""
        elements = self._parse(data)
        self.assertEqual(len(elements), 1)

        e = elements[0]
        self.assertEqual(e.method,
                         "OptimizedCallTarget_profileArguments")
        self.assertEqual(e.percent, 4.25)
        self.assertEqual(len(e.trace), 2)

        e1 = e.trace[0]
        e2 = e.trace[1]
        self.assertEqual(e1, "OptimizedCallTarget_profileArguments")
        self.assertEqual(e2, "OptimizedDirectCallNode_call")

        self._assert_json_is_serializable()

    def test_trace_from_main_and_nested(self):
        data = """
     2.84%  som-native-inte  som-native-interp-ast  [.] FrameWithoutBoxing_getTag_371fb5158808fd7258a82f07cb9b58a2fe4c410c
            |
            ---FrameWithoutBoxing_getTag_371fb5158808fd7258a82f07cb9b58a2fe4c410c
               LocalVariableNodeFactory$LocalVariableReadNodeGen_executeGeneric_b6d282cd7cee40289d20846bdb0b59a0940e00a5
               |          
               |--1.91%--MessageSendNode$AbstractMessageSendNode_evaluateArguments_bf7729bae6effddecf0ca8938ecdffedaf15af80
               |          IntToDoInlinedLiteralsNode_doIntToDo_54685947c4bcab224870fc73d385c495122b828b
               |          |          
               |           --1.89%--IntToDoInlinedLiteralsNodeFactory$IntToDoInlinedLiteralsNodeGen_executeGeneric_long_long0_428318a36ea78a9e61e6131f65153ae65cab856e
               |                     IntToDoInlinedLiteralsNodeFactory$IntToDoInlinedLiteralsNodeGen_executeGeneric_6c504e8fb74533c0c8f482ceba93fbeb804e2309
               |          
                --0.93%--EagerBinaryPrimitiveNode_executeGeneric_bf7fec9ded572fea61a9eb9b0031d6b40ef4bfd5
                          ExpressionNode_executeLong_60573f5a2d4614ca6dba4dee6fc4c0360506579e
     """
        elements = self._parse(data)
        self.assertEqual(len(elements), 1)

        e = elements[0]
        self.assertEqual(e.method,
                         "FrameWithoutBoxing_getTag")
        self.assertEqual(e.percent, 2.84)
        self.assertEqual(len(e.trace), 4)

        self.assertEqual(e.trace[0], "FrameWithoutBoxing_getTag")
        self.assertEqual(e.trace[1], "LocalVariableNodeFactory$LocalVariableReadNodeGen_executeGeneric")

        e3 = e.trace[2]
        e4 = e.trace[3]

        self.assertEqual(e3.method, "MessageSendNode$AbstractMessageSendNode_evaluateArguments")
        self.assertEqual(e4.method, "EagerBinaryPrimitiveNode_executeGeneric")

        self._assert_json_is_serializable()

    def test_main_item_with_space(self):
        data = """
     0.76%  gnal Dispatcher  [kernel.kallsyms]   [k] zap_pte_range.isra.0
            |
            ---zap_pte_range.isra.0
               unmap_page_range
"""
        elements = self._parse(data)
        e = elements[0]

        self.assertEqual(e.percent, 0.76)
        self.assertEqual(e.binary, "gnal Dispatcher")
        self.assertEqual(e.method, "zap_pte_range.isra.0")
        self.assertEqual(e.shared_object, "[kernel.kallsyms]")
