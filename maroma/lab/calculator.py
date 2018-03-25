import numpy as np

class Calculator(object):

    def __init__(self):
        pass

    def calculate_car_qstk(self, event_matrix, stock_data, market_symbol, look_back, look_forward):
        '''

        :param event_matrix:
        :param stock_data:
        :param market_symbol:
        :param look_back:
        :param look_forward:
        :return car: time series of Cumulative Abnormal Return
        :return std_err: the standard error
        :return num_events: the number of events in the matrix

        Most of the code was from here:
        https://github.com/brettelliot/QuantSoftwareToolkit/blob/master/QSTK/qstkstudy/EventProfiler.py
        '''

        # Copy the stock prices into a new dataframe which will become filled with the returns
        daily_returns = stock_data.copy()

        # Convert prices into daily returns.
        # This is the amount that the specific stock increased or decreased in value for one day.
        daily_returns = daily_returns.pct_change().fillna(0)

        # Subtract the market returns from all of the stock's returns. The result is the abnormal return.
        #beta = get_beta()
        beta = 1.0  # deal with beta later
        abnormal_returns = daily_returns.subtract(beta * daily_returns[market_symbol], axis='index')

        # remove the market symbol from the returns and event matrix. It's no longer needed.
        del daily_returns[market_symbol]
        del abnormal_returns[market_symbol]
        del event_matrix[market_symbol]
        #print("abnormal_returns:")
        #print(abnormal_returns.tail())

        # From QSTK
        #daily_returns = daily_returns.reindex(columns=event_matrix.columns)

        # Removing the starting and the end events
        event_matrix.values[0:look_back, :] = np.NaN
        event_matrix.values[-look_forward:, :] = np.NaN

        # Number of events
        i_no_events = int(np.logical_not(np.isnan(event_matrix.values)).sum())
        assert i_no_events > 0, "Zero events in the event matrix"
        na_event_rets = "False"

        # Looking for the events and pushing them to a matrix
        for i, s_sym in enumerate(event_matrix.columns):
            for j, dt_date in enumerate(event_matrix.index):
                if event_matrix[s_sym][dt_date] == 1:
                    na_ret = abnormal_returns[s_sym][j - look_back:j + 1 + look_forward]
                    if type(na_event_rets) == type(""):
                        na_event_rets = na_ret
                    else:
                        na_event_rets = np.vstack((na_event_rets, na_ret))

        if len(na_event_rets.shape) == 1:
            na_event_rets = np.expand_dims(na_event_rets, axis=0)

        # Computing daily rets and retuns
        na_event_rets = np.cumprod(na_event_rets + 1, axis=1)
        na_event_rets = (na_event_rets.T / na_event_rets[:, look_back]).T

        # Study Params
        na_mean = np.mean(na_event_rets, axis=0)
        # print(na_mean)
        # print(na_mean.shape)
        na_std = np.std(na_event_rets, axis=0)

        return na_mean, na_std, i_no_events
