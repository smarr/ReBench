# Copyright (c) 2009 Stefan Marr <http://www.stefan-marr.de/>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import re
from DataAggregator import DataPoint

class Performance:
    """Performance provides a common interface and some helper functionality
       to evaluate the output of benchmarks and to determine measured performance
       values.
    """
    
    # definition of some regular expression to identify erroneous runs
    re_error    = re.compile("Error")
    re_segfault = re.compile("Segmentation fault")
    re_buserror = re.compile("Bus error")
    
    def __init__(self):
        self._otherErrorDefinitions = None
    
    def acquire_command(self, command):
        return command
    
    def parse_data(self, data):
        raise NotImplementedError()
    
    def check_for_error(self, line):
        """Check whether the output line contains one of the common error
           messages. If its an erroneous run, the result has to be discarded.
        """
        if self.re_error.search(line):
            return True
        if self.re_segfault.search(line):
            return True
        if self.re_buserror.search(line):
            return True
        
        if self._otherErrorDefinitions:
            for regEx in self._otherErrorDefinitions:
                if regEx.search(line):
                    return True
        
        return False

class LogPerformance(Performance):
    """LogPerformance is the standard log parser of ReBench.
       It reads a simple log format, which includes the number of iterations of
       a benchmark and its runtime in microseconds.
    """
    re_logline = re.compile(r"^(?:.*: )?(\w+)( \w+)?: iterations=([0-9]+) runtime: ([0-9]+)([mu])s")
    
    
    re_NPB_partial_invalid = re.compile(r".*Failed.*verification")
    re_NPB_invalid = re.compile(r".*Benchmark done.*verification failed")
    
    def __init__(self):
        self._otherErrorDefinitions = [self.re_NPB_partial_invalid, 
                                       self.re_NPB_invalid]

    def parse_data(self, data):
        result = []
        total = None
         
        for line in data.split("\n"):
            if self.check_for_error(line):
                raise RuntimeError("Output of bench program indicated error.")
            
            m = self.re_logline.match(line)
            if m:
                time = float(m.group(4))
                if m.group(5) == "u":
                    time = time / 1000
                criterion = (m.group(2) or 'total').strip()
                
                val = DataPoint(time, criterion)
                result.append(val)

                if criterion == 'total':
                    assert total == None, "benchmark run returned more than one 'total' value"
                    total = time
        
        if total is None:
            print "Failed parsing: ###" + data + "###"
            raise RuntimeError("Output of bench program did not contain a total value")
            
        return (total, result)

class StatsPerformance(Performance):
    """StatsPerformance is similar to LogPerformance but starts parsing
       only between certain markers
    """
    start = "Stats{"
    stop = "}Stats"
    re_statline= re.compile(r"^([BNC]|T[smu]?):(\w+):\s*(\d*\.?\d+)?")

    def parse_data(self, data):
        from DataAggregator import NonTimeDataPoint
        result = []
        total = None
        go = False
        benchName = None
        iterations = None

        for line in data.split("\n"):
            if self.check_for_error(line):
                raise RuntimeError("Output of bench program indicated error.")

            if self.start == line:
                go = True
                continue
            elif self.stop == line:
                go = False
                continue

            if not go:
                continue

            m = self.re_statline.match(line)
            if m:
                mult = 1
                dp = NonTimeDataPoint
                data = None
                name = m.group(2).strip()
                typ = m.group(1)
                if typ[0] == "T":
                    dp = DataPoint
                    data = float(m.group(3).strip())
                    if len(typ) == 2:
                        if typ[1] == "s":
                            mult = 1.0 / 1000
                        elif typ[1] == "m":
                            mult = 1
                        elif typ[1] == "u":
                            mult = 1000
                        assert iterations is not None, \
                            "iterations must be given before timed values"
                        if mult > iterations:
                            mult = float(mult) / iterations
                        else:
                            mult = mult / iterations
                elif typ[0] == "C":
                    data = int(m.group(3).strip())
                    mult = 1
                elif typ[0] == "N": #the iteration count
                    iterations = int(m.group(3).strip())
                elif typ[0] == "B": #the Benchmark name, breaks DataAggregator
                    pass
                    # benchName = name
                    # if len(result) > 0:
                    #     for dp in results:
                    #         dp.benchName = benchName
                else:
                    print "Failed parsing: ###" + line + "###"
                    raise RuntimeError("Unknown Stat entry")

                if data:
                    val = dp(data * mult, benchName, name)
                    if val.isTotal():
                        assert total is None, "there was more than one 'total'"
                        total = val.time
                        result.append(DataPoint(total, criterion='total'))
                    else:
                        result.append(val)

        if total is None:
            print "Failed parsing: ###" + data + "###"
            raise RuntimeError("Output of bench did not contain a total value")
        return (total, result)



class JGFPerformance(Performance):
    """JGFPerformance is used to read the output of the JGF barrier benchmarks.
    """
    re_barrierSec1 = re.compile(r"^(?:.*:.*:)(.*)(?:\s+)([0-9\.E]+)(?:\s+)\(barriers/s\)") # for the barrier benchmarks in sec 1 of the JGF benchmarks
    re_sec2 = re.compile(r"^(?:Section2:.*:)(.*)(?::.*)(?:\s+)([0-9]+)(?:\s+)\(ms\)")            # for the benchmarks from sec 2
    re_sec3 = re.compile(r"^(?:Section3:.*:)(.*)(?::Run:.*)(?:\s+)([0-9]+)(?:\s+)\(ms\)")        # for the benchmarks from sec 3, the time of 'Run' is used

    re_invalid = re.compile("Validation failed")

    def __init__(self):
        self._otherErrorDefinitions = [JGFPerformance.re_invalid]

    def parse_data(self, data):
        result = []
        time = None
    
        for line in data.split("\n"):
            if self.check_for_error(line):
                raise RuntimeError("Output of bench program indicated error.")
    
            m = self.re_barrierSec1.match(line)
            if not m:
                m = self.re_sec2.match(line)
                if not m:
                    m = self.re_sec3.match(line)

            if m:
                time = float(m.group(2))
                val = DataPoint(time, None)
                result.append(val)
                #print "DEBUG OUT:" + time

        if time is None:
            print "Failed parsing: " + data
            raise RuntimeError("Output of bench program did not contain a total value")

        return (time, result)

class EPCCPerformance(Performance):
    """EPCCPerformance is used to read the output of the EPCC barrier benchmarks.
    """
    barrier_time  = re.compile(r"^BARRIER time =\s+([0-9\.E]+) microseconds(?:.+)")
    barrier_time2 = re.compile(r"\s*Total time without initialization\s+:?\s+([0-9]+)")
    barnes = re.compile(r"COMPUTETIME\s+=\s+([0-9]+)") 
    re_error = re.compile("Error [^t][^o][^l]") 
    barrier_time3 = re.compile(r"^BARRIER overhead =\s+([0-9\.E]+) microseconds(?:.+)")
    
    def parse_data(self, data):
        result = []
        time = None
    
        for line in data.split("\n"):
            if self.check_for_error(line):
                raise RuntimeError("Output of bench program indicated error.")
            #import pdb; pdb.set_trace() 
            m = self.barrier_time.match(line)
            if not m:
                m = self.barrier_time2.match(line)
                if not m:
                    m = self.barnes.match(line)
                    if not m:
                        m = self.barrier_time3.match(line)

            if m:
                time = float(m.group(1))
                val = DataPoint(time, None)
                result.append(val)

        if time is None:
            print "Failed parsing: " + data
            raise RuntimeError("Output of bench program did not contain a total value")

        return (time, result)


class TimePerformance(Performance):
    """TimePerformance uses the systems time utility to allow measurement of
       unmodified programs or aspects which need to cover the whole program
       execution time.
    """
    re_time = re.compile(r"^(\w+)\s*(\d+)m(\d+\.\d+)s")
    re_time2 = re.compile(r"^(\w+)(\s*)(\d+\.\d+)")
    
    def acquire_command(self, command):
        return "/usr/bin/time -p %s"%(command)
    
    def parse_data(self, data):
        result = []
        total = None
        
        for line in data.split("\n"):
            if self.check_for_error(line):
                return None
          
            m1 = self.re_time.match(line)
            m2 = self.re_time2.match(line)
            if m1 or m2:
                m = m1 or m2
                criterion = 'total' if m.group(1) == 'real' else m.group(1)
                time = (float(m.group(2).strip() or 0) * 60 + float(m.group(3))) * 1000
                val = DataPoint(time, criterion)
                result.append(val)
          
                if criterion == 'total':
                    assert total == None, "benchmark run returned more than one 'total' value"
                    total = time
      
        return (total, result)


class TimeManualPerformance(TimePerformance):
    """TimeManualPerformance works like TimePerformance but does expect the
       user to use the /usr/bin/time manually.
       This is useful for runs on remote machines like the Tilera or ARM boards.
    """
    def acquire_command(self, command):
        return command


class TestVMPerformance(Performance):
    """Perfromance reader for the test case and the definitions
       in test/test.conf
    """
    
    re_time = re.compile(r"RESULT-(\w+):\s*(\d+\.\d+)")
    
    def __init__(self):
        self._otherErrorDefinitions = [re.compile("FAILED")]
    
    def parse_data(self, data):
        results = []
        total = None
        
        
        for line in data.split("\n"):
            if self.check_for_error(line):
                raise RuntimeError("Output of bench program indicated error.")
            
            m = TestVMPerformance.re_time.match(line)
            if m:
                val = DataPoint(float(m.group(2)), None, m.group(1))
                if val.isTotal():
                    assert total is None
                    total = val.time
                results.append(val)
        
        if total is None:
            raise RuntimeError("Output of bench program did not contain a total value")
        
        return (total, results)



class TestPerformance(Performance):
    
    test_data = [45872, 45871, 45868, 45869, 45873,
                 45865, 45869, 45874, 45863, 45873,
                 45872, 45873, 45867, 45872, 45876,
                 45871, 45870, 45870, 45868, 45869,
                 45872, 45873, 45867, 45866, 45869,
                 45875, 45871, 45869, 45870, 45874]
    index = 0
    
    def parse_data(self, data):
        result = self.test_data[self.index]
        self.index = (self.index + 1) % len(self.test_data)
        return result


class CaliperPerformance(Performance):
    """CaliperPerformance parses the output of Caliper with
       the ReBenchConsoleResultProcessor.
    """
    re_logline = re.compile(r"Measurement \(runtime\) for (.*?) in (.*?): (.*?)ns")
    
    def check_for_error(self, line):
        ## for the moment we will simply not check fir errors, because
        ## there are to many simple Error strings referring to class names
        ## TODO: find better solution
        pass
    
    def parse_data(self, data):
        results = []        
        total_time = 0
        total_bench = None # the benchmark we use to represent the total
         
        for line in data.split("\n"):
            if self.check_for_error(line):
                raise RuntimeError("Output of bench program indicates errors.")
            
            m = self.re_logline.match(line)
            if m:
                time = float(m.group(3)) / 1000000
                results.append(DataPoint(time, criterion = m.group(1))) #m.group(2),
                
                if total_bench is None:
                    total_bench = m.group(1)
                    
                # is used to determine when benchmark is completed, is currently 
                # problematic with sources that produced multiple results
                if total_bench == m.group(1):
                    # well, so the overall total is going to be the last one
                    total_time = time
                    # this is the fake result, to determine whether to stop benchmarking
                    results.append(DataPoint(time, criterion = 'total'))  # m.group(2),
        
        if total_time == 0:
            print "Failed parsing: ###" + data + "###"
            raise RuntimeError("Output of bench program did not contain a total value")
            
        return (total_time, results)

