# class JGFPerformance(Performance):
#     """JGFPerformance is used to read the output of the JGF barrier benchmarks.
#     """
#     re_barrierSec1 = re.compile(r"^(?:.*:.*:)(.*)(?:\s+)([0-9\.E]+)(?:\s+)\(barriers/s\)") # for the barrier benchmarks in sec 1 of the JGF benchmarks
#     re_sec2 = re.compile(r"^(?:Section2:.*:)(.*)(?::.*)(?:\s+)([0-9]+)(?:\s+)\(ms\)")            # for the benchmarks from sec 2
#     re_sec3 = re.compile(r"^(?:Section3:.*:)(.*)(?::Run:.*)(?:\s+)([0-9]+)(?:\s+)\(ms\)")        # for the benchmarks from sec 3, the time of 'Run' is used
#
#     re_invalid = re.compile("Validation failed")
#
#     def __init__(self):
#         self._otherErrorDefinitions = [JGFPerformance.re_invalid]
#
#     def parse_data(self, data, run_id):
#         data_points = []
#         current = DataPoint(run_id)
#
#         for line in data.split("\n"):
#             if self.check_for_error(line):
#                 raise ResultsIndicatedAsInvalid("Output of bench program indicated error.")
#
#             m = self.re_barrierSec1.match(line)
#             if not m:
#                 m = self.re_sec2.match(line)
#                 if not m:
#                     m = self.re_sec3.match(line)
#
#             if m:
#                 time = float(m.group(2))
#                 val = Measurement(time, None)
#                 result.append(val)
#                 #print "DEBUG OUT:" + time
#
#         if time is None:
#             raise OutputNotParseable(data)
#
#         return (time, result)
