# Copyright (c) 2009 Stefan Marr
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

from __future__ import with_statement
from contextpy import layer, proceed, activelayer, activelayers, after, around, before, base, globalActivateLayer

benchmark = layer("benchmark")
profile = layer("profile")

class Reporter:
    
    def __init__(self, config, output_file = None):
        self.config = config
        self.benchmark_results = None
        self.benchmark_data = None
        self.profile_data = None
        self.output_file = output_file
    
    def set_data(self, data):
        (result, benchmark_data) = data
        self.benchmark_results = result
        self.benchmark_data = benchmark_data

    def compile_report(self):
        pass

    @after(profile)
    def compile_report(self, __result__):
        memory_lines = []
        opcode_lines = []
        library_lines = []
        
        dict = profile_data[0].get_memory_usage()
        line = "ObjectSize:" + "\t".join(dict.keys())
        memory_lines.append(line)
        
        dict = profile_data[0].get_library_usage()
        line = "Library:" + "\t".join(dict.keys())
        library_lines.append(line)
        
        dict = profile_data[0].get_opcode_usage()
        line = "Opcodes:" + "\t".join(dict.keys())
        opcode_lines.append(line)
        
        for profile in profile_data:
            vm, bench = profile.get_vm_and_benchmark()
            head = "%s:%s"%(vm, bench)
            memory_lines.append(head + "\t".join(profile.get_memory_usage().values()))
            opcode_lines.append(head + "\t".join(profile.get_opcode_usage().values()))
            library_lines.append(head + "\t".join(profile.get_library_usage().values()))
            
        report = "\n".join(memory_lines)
        report = report + "\n"
        report = "\n".join(opcode_lines)
        report = report + "\n"
        report = "\n".join(library_lines)
        
        return report
            
    def normalize_data(self, profile_data):
        for profileA in profile_data:
            for profileB in profile_data:
                if profileA != profileB:
                    profileA.normalize(profileB)
                    
    def report_profile_results(self, verbose):
        profile_data = self.normalize_data(self.profile_data)
        report = self.compile_report(verbose)
        return report
    
    def report(self, verbose):
        profile = ""
        if self.profile_data is not None:
            profile = self.report_profile_results(verbose)
            print profile
        
        benchmark = self.report_benchmark_results(verbose)
        print benchmark
        
        if self.output_file is not None:
            if not verbose:
                if self.profile_data is not None:
                    profile = self.report_profile_results(True)
                benchmark = self.report_benchmark_results(True)
        
            f = open(self.output_file, 'w+')
            try:
                f.write(profile)
                f.write(benchmark)
            finally:
                f.close()
                
    
    def report_benchmark_results(self, verbose):
        report = "VM\tBenchmark\tMean\tStdDev\tInterv_low\tInterv_high\tError\n"
        lines = []
        for (vm, benchmarks) in self.benchmark_results.items():
            for (benchmark, results) in benchmarks.items():
                (mean, sdev, ((i_low, i_high), error),
                             interval_t) = results
                lines.append("\t".join([vm, benchmark, str(mean), str(sdev), str(i_low), str(i_high), str(error)]))
        
        report += "\n".join(lines)
        return report
