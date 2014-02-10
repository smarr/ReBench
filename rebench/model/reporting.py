class Reporting(object):
    
    def __init__(self, raw_config):
        self._csv_file   = raw_config.get('csv_file',   None)
        self._csv_locale = raw_config.get('csv_locale', None)
        self._csv_raw    = raw_config.get('csv_raw',    None)
        
        self._confidence_level = raw_config.get('confidence_level', 0.95)
    
    @property
    def csv_file(self):
        return self._csv_file
    
    @property
    def csv_locale(self):
        return self._csv_locale
    
    @property
    def csv_raw(self):
        return self._csv_raw
    
    @property
    def confidence_level(self):
        return self._confidence_level

    def combined(self, raw_config):
        rep = Reporting({})
        rep._csv_file   = raw_config.get('csv_file',   self._csv_file)
        rep._csv_locale = raw_config.get('csv_locale', self._csv_locale)
        rep._csv_raw    = raw_config.get('csv_raw',    self._csv_raw)
        
        rep._confidence_level = raw_config.get('confidence_level', self._confidence_level)

        return rep
