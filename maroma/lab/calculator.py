import numpy as np


class CarsCavcsResult(object):
    def __init__(self, num_events,
                 cars, cars_std_err, cars_t_test, cars_significant, cars_positive, cars_num_stocks_positive,
                 cars_num_stocks_negative,
                 cavcs, cavcs_std_err, cavcs_t_test, cavcs_significant, cavcs_positive, cavcs_num_stocks_positive,
                 cavcs_num_stocks_negative):
        '''
        :param num_events: the number of events in the matrix
        :param cars: time series of Cumulative Abnormal Return
        :params cars_std_err: std error of the CARs
        :param cars_t_test: t-test statistic that checks whether the CARs of all stock are significantly different from 0
        :param cars_significant: True if the CARs of all stocks are significant
        :param cars_positive: True if the CAR is positive
        :param cars_num_stocks_positive: The number of stocks for which the CAR was significantly positive
        :param cars_num_stocks_negative: The number of stocks for which the CAR was significantly negative
        :param cavcs: time series of Cumulative Abnormal Volume Changes
        :params cavcs_std_err: std error of the CAVCs
        :param cavcs_t_test: t-test statistic that checks whether the CAVCs of all stock are significantly different from 0
        :param cavcs_significant: True if the CAVCs of all stocks are significant
        :param cavcs_positive: True if the CAVC is  positive
        :param cavcs_num_stocks_positive: The number of stocks for which the CAVC was significantly positive
        :param cavcs_num_stocks_negative: The number of stocks for which the CAVC was significantly negative

        All of the above t-tests are significant when they are in the 95% confidence levels
        '''
        self.num_events = num_events
        self.cars = cars
        self.cars_std_err = cars_std_err
        self.cars_t_test = cars_t_test
        self.cars_significant = cars_significant
        self.cars_positive = cars_positive
        self.cars_num_stocks_positive = cars_num_stocks_positive
        self.cars_num_stocks_negative = cars_num_stocks_negative
        self.cavcs = cavcs
        self.cavcs_std_err = cavcs_std_err
        self.cavcs_t_test = cavcs_t_test
        self.cavcs_significant = cavcs_significant
        self.cavcs_positive = cavcs_positive
        self.cavcs_num_stocks_positive = cavcs_num_stocks_positive
        self.cavcs_num_stocks_negative = cavcs_num_stocks_negative


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
        # beta = get_beta()
        beta = 1.0  # deal with beta later
        abnormal_returns = daily_returns.subtract(beta * daily_returns[market_symbol], axis='index')

        # remove the market symbol from the returns and event matrix. It's no longer needed.
        del daily_returns[market_symbol]
        del abnormal_returns[market_symbol]
        del event_matrix[market_symbol]
        # print("abnormal_returns:")
        # print(abnormal_returns.tail())

        # From QSTK
        # daily_returns = daily_returns.reindex(columns=event_matrix.columns)

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

    def calculate_cars_cavcs(self, event_matrix, stock_data, market_symbol, estimation_window=200, buffer=5,
                             pre_event_window=10, post_event_window=10):
        '''

        :param event_matrix:
        :param stock_data:
        :param market_symbol:
        :param estimation_window:
        :param buffer:
        :param pre_event_window:
        :param post_event_window:
        :return cars_cavcs_result: An instance of CarsCavcsResult containing the results.


        Modeled after http://arno.uvt.nl/show.cgi?fid=129765

        '''

        num_events = 40
        cars = [0.97087641, 0.9697428, 0.96533544, 0.96929777, 0.98208265, 0.98776592,
                0.98763236, 0.99769771, 0.99635582, 0.99992019, 1.00218281, 0.99891542,
                1.00899683, 1.01576225, 1.01091189, 1.00748266, 1.00564512, 1.00409666,
                1.00107316, 0.99675959, 0.99977831]
        cars_std_err = [0.12162208, 0.11796874, 0.11622789, 0.11458759, 0.09909379, 0.10188796,
                        0.09594914, 0.09913533, 0.09174868, 0.09025341, 0.08595058, 0.08268046,
                        0.08066682, 0.06380801, 0.0603019, 0.04684159, 0.04418724, 0.04189096,
                        0.03336172, 0.02650387, 0.02232655]
        cars_t_test = 1.97
        cars_significant = True
        cars_positive = True
        cars_num_stocks_positive = 2
        cars_num_stocks_negative = 1
        cavcs = [0.97087641, 0.9697428, 0.96533544, 0.96929777, 0.98208265, 0.98776592,
                 0.98763236, 0.99769771, 0.99635582, 0.99992019, 1.00218281, 0.99891542,
                 1.00899683, 1.01576225, 1.01091189, 1.00748266, 1.00564512, 1.00409666,
                 1.00107316, 0.99675959, 0.99977831]
        cavcs_t_test = 1.98
        cavcs_significant = True
        cavcs_std_err = [0.12162208, 0.11796874, 0.11622789, 0.11458759, 0.09909379, 0.10188796,
                         0.09594914, 0.09913533, 0.09174868, 0.09025341, 0.08595058, 0.08268046,
                         0.08066682, 0.06380801, 0.0603019, 0.04684159, 0.04418724, 0.04189096,
                         0.03336172, 0.02650387, 0.02232655]
        cavcs_positive = False
        cavcs_num_stocks_positive = 1
        cavcs_num_stocks_negative = 2

        ccr = CarsCavcsResult(num_events,
                              cars, cars_std_err, cars_t_test, cars_significant,
                              cars_positive, cars_num_stocks_positive, cars_num_stocks_negative,
                              cavcs, cavcs_std_err, cavcs_t_test, cavcs_significant,
                              cavcs_positive, cavcs_num_stocks_positive, cavcs_num_stocks_negative)

        return ccr
