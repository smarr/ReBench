class ProfileData(object):
    def __init__(self, run_id, processed_data, num_iterations, invocation):
        self.run_id = run_id
        self.processed_data = processed_data
        self.num_iterations = num_iterations
        self.invocation = invocation

    def as_dict(self):
        return {
            'd': self.processed_data,
            'nit': self.num_iterations,
            'in': self.invocation
        }
