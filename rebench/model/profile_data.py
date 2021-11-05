from ..model.run_id import RunId


class ProfileData(object):
    def __init__(self, run_id, processed_data, num_iterations, invocation):
        self.run_id = run_id
        self.processed_data = processed_data
        self.num_iterations = num_iterations
        self.invocation = invocation

    def get_total_unit(self):
        return None

    def as_dict(self):
        return {
            'd': self.processed_data,
            'nit': self.num_iterations,
            'in': self.invocation
        }

    def as_str_list(self):
        return [str(self.invocation), str(self.num_iterations)] + self.run_id.as_str_list() + [self.processed_data]

    @classmethod
    def from_str_list(cls, data_store, str_list, line_number=None, filename=None):
        invocation = int(str_list[0])
        num_iterations = int(str_list[1])
        run_id = RunId.from_str_list(data_store, str_list[2:-1])
        processed_data = str_list[-1]

        return ProfileData(run_id, processed_data, num_iterations, invocation)
