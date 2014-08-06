# class EPCCPerformance(Performance):
#     """EPCCPerformance is used to read the output of the EPCC barrier benchmarks.
#     """
#     barrier_time  = re.compile(r"^BARRIER time =\s+([0-9\.E]+) microseconds(?:.+)")
#     barrier_time2 = re.compile(r"\s*Total time without initialization\s+:?\s+([0-9]+)")
#     barnes = re.compile(r"COMPUTETIME\s+=\s+([0-9]+)")
#     re_error = re.compile("Error [^t][^o][^l]")
#     barrier_time3 = re.compile(r"^BARRIER overhead =\s+([0-9\.E]+) microseconds(?:.+)")
#
#     def parse_data(self, data):
#         result = []
#         time = None
#
#         for line in data.split("\n"):
#             if self.check_for_error(line):
#                 raise ResultsIndicatedAsInvalid("Output of bench program indicated error.")
#             #import pdb; pdb.set_trace()
#             m = self.barrier_time.match(line)
#             if not m:
#                 m = self.barrier_time2.match(line)
#                 if not m:
#                     m = self.barnes.match(line)
#                     if not m:
#                         m = self.barrier_time3.match(line)
#
#             if m:
#                 time = float(m.group(1))
#                 val = Measurement(time, None)
#                 result.append(val)
#
#         if time is None:
#             raise OutputNotParseable(data)
#
#         return (time, result)