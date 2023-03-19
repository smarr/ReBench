class TestPersistence(object):
    __test__ = False  # This is not a test class

    def __init__(self):
        self._data_points = []

    def use_on(self, runs):
        for run in runs:
            run.add_persistence(self)

    def get_data_points(self, run_id=None):
        if run_id:
            return [dp for dp in self._data_points if dp.run_id is run_id]
        return self._data_points

    def persist_data_point(self, data_point):
        self._data_points.append(data_point)

    def close(self):
        pass

    def run_completed(self):
        pass
