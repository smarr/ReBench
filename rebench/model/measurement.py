from datetime import datetime

from rebench.model.run_id import RunId


class Measurement(object):
    def __init__(self, value, unit, run_id, criterion = 'total', timestamp = None):
        self._run_id    = run_id
        self._criterion = criterion
        self._value     = value
        self._unit      = unit
        self._timestamp = timestamp or datetime.now()
        
    def is_total(self):
        return self._criterion == 'total'
    
    @property
    def criterion(self):
        return self._criterion
    
    @property
    def value(self):
        return self._value
    
    @property
    def unit(self):
        return self._unit

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def run_id(self):
        return self._run_id

    TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

    def as_str_list(self):
        return ["[" + self._timestamp.strftime(self.TIME_FORMAT) + "]",
                "%f" % self._value,
                self._unit,
                self._criterion] + self._run_id.as_str_list()

    @classmethod
    def from_str_list(cls, str_list):

        timestamp = datetime.strptime(str_list[0][1:-1], cls.TIME_FORMAT)
        value     = float(str_list[1])
        unit      = str_list[2]
        criterion = str_list[3]
        run_id    = RunId.from_str_list(str_list[4:])

        return Measurement(value, unit, run_id, criterion, timestamp)
