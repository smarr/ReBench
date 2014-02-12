class DataPoint(object):
    def __init__(self, run_id):
        self._run_id = run_id
        self._measurements = []
        self._total = None
    
    def number_of_measurements(self):
        return len(self._measurements)
    
    def add_measurement(self, measurement):
        self._measurements.append(measurement)
        if measurement.is_total():
            if self._total is not None:
                raise ValueError("A data point should only include one 'total' measurement.")
            self._total = measurement
    
    def get_measurements(self):
        return self._measurements

    def get_total_value(self):
        return self._total.value if self._total else None