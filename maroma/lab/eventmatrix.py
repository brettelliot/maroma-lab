import pandas as pd
import numpy as np

class EventMatrix(object):

    def __init__(self, datetimes, symbols):
        '''
        :param datetimes:
        :param symbols:
        Constructs A pandas dataframe indexed by datetimes and with columns for each symbol.
        The constructor fills this with all NANs and an abstract base method exists to be customized.
        '''

        # Build an empty event matrix with an index of all the datetimes and columns for each symbol.
        # Fill with NANs
        self.event_matrix = pd.DataFrame({'Date': datetimes})
        self.event_matrix = self.event_matrix.set_index('Date')
        self.event_matrix.tz_localize(tz='America/New_York')
        self.symbols = symbols
        for symbol in self.symbols:
            self.event_matrix[symbol] = np.nan

    def build_event_matrix(self, start_date, end_date):
        '''
        Implement this method a derived class.
        :param start_date:
        :param end_date:
        :return: FIll up the event matrix with 1's in the row/column for which there was an event.
        '''
        raise NotImplementedError("Please Implement this method in a base class")

