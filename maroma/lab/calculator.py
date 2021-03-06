import numpy as np
from scipy import stats


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
        
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import datetime as dt

        num_events = len(event_matrix[(event_matrix == 1.0).any(axis=1)])
        
        events = event_matrix[(event_matrix == 1.0).any(axis=1)]

        dates = stock_data.loc['MKT', slice(None)].index
        date1 = events.index[0]
        index1 = dates.tolist().index(date1)
        date11 = dates[index1 - buffer]
        date12 = dates[index1 - (buffer + estimation_window)]

        #import pdb; pdb.set_trace()
        
        closing_prices  = stock_data['adjusted_close']
        volumes  = stock_data['volume']


        stock_ret = closing_prices.copy()
        vlm_changes0 = closing_prices.copy()
        vlm_changes = closing_prices.copy()
        
        symbols = stock_data.index.get_level_values(0).unique().tolist()
        
        mypct = lambda x : x[-1] - np.mean(x[:-1])


        for symbol in symbols:
            stock_ret[symbol] = closing_prices[symbol].pct_change().fillna(0)
            #import pdb; pdb.set_trace()
            vlm_changes[symbol] = volumes[symbol].rolling(5,5).apply(mypct).fillna(0)
            #vlm_changes[symbol] = volumes[symbol].pct_change().fillna(0).apply(lambda x : min(3,x))

        
        # do regeression

        pre_stock_returns = stock_ret[
            (stock_data.index.get_level_values(1) > date12) & (stock_data.index.get_level_values(1) <= date11)]

        pre_stock_vlms = vlm_changes[
            (stock_data.index.get_level_values(1) > date12) & (stock_data.index.get_level_values(1) <= date11)]

        #**************
        #First compute cars ******
        #***************
        
        #import pdb; pdb.set_trace()
        
        
        dates =stock_data.index.get_level_values(1).unique().tolist()
        
    
        
        if(market_symbol in symbols):
            stocks =[ x for x in symbols if x != market_symbol]
        else:
            raise ValueError('calculate_cars_cavcs: market_symbol not found in data')
        
        
        
        ar1 = ['cars','cavs']; ar2 = ['slope','intercept']
        
        from itertools import product
        tuples = [(i,j) for i,j in product(ar1,ar2)]  #         tuples = list(zip(*arrays))

        index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second'])
        
        df_regress = pd.DataFrame(0.0,index=index,columns=symbols)
        
        #import pdb; pdb.set_trace()
        
        for stock in stocks:
            
            #set up data
            
            x1 = pre_stock_returns[market_symbol]

            y1 = pre_stock_returns[stock]
            
            
            slope1,intercept1,cars0 = regress_vals(x1,y1)
            cars = np.cumprod(cars0 + 1, axis=0)
            
            # plot if you need

            plot_regressvals(x1,y1,slope1, intercept1,cars,stock)
            
            # the same for cvals
            
            x2 = pre_stock_vlms[market_symbol]

            y2 = pre_stock_vlms[stock]
            
            #y2.argsort()[::-1][:n]

    
            #import pdb; pdb.set_trace()
            
            slope2,intercept2,cavs0= regress_vals(x2,y2)
            cavs = np.cumsum(cavs0)
            
            plot_regressvals(x2,y2,slope2, intercept2,cavs,stock)
            

            # store the regresion values
            

            df_regress.loc[('cars','slope'),stock] = slope1

            df_regress.loc[('cars','intercept'),stock] = intercept1


            df_regress.loc[('cavs','slope'),stock] = slope2
            
            df_regress.loc[('cavs','intercept'),stock] = intercept2
        
        
            # do the same for volumes
            
            
        #***************
        # now the event cars and cavs computations

        ar11  = stocks
        ar12 = ['cars','cavs']


        tuples2 = [(i,j) for i,j in product(ar11,ar12)]  #         tuples = list(zip(*arrays))
        
        index2 = pd.MultiIndex.from_tuples(tuples2, names=['first', 'second'])
        
        df_results = pd.DataFrame(0.0,index=index2,columns= ['positive','significant'])
        
        ccarray = []
        cvarray = []
        
        # now the big loop

        #import pdb; pdb.set_trace()
            
        for stock in stocks:
            
            slope1 = df_regress.loc[('cars','slope'),stock]
            intercept1 = df_regress.loc[('cars','intercept'),stock]
            
            slope2 = df_regress.loc[('cavs','slope'),stock]
            intercept2 = df_regress.loc[('cavs','intercept'),stock]

            ccr=[]
            cvr = []
            
            for event in events.iterrows():
            
            
                dt1 = event[0]
                idx1 = dates.index(dt1)
                window = dates[idx1-pre_event_window:idx1+post_event_window+1]
                
                event_rets = stock_ret[stock][window]
                event_mkt_ret =  stock_ret[market_symbol][window]
                # calculate excess returns
                event_ex_ret = event_rets - (slope1 * event_mkt_ret + intercept1)
                
                event_cum_rets = np.cumprod(event_rets + 1, axis=0)
                #plot_regressvals(event_mkt_ret,event_rets,slope1, intercept1,event_cum_rets,stock)
                
                ccr.append(event_ex_ret.tolist())

                cars = (event_cum_rets[-1] -1)/len(window)
            
            
                # now for vols
                event_vols =  vlm_changes[stock][window]
                mkt_vols  =  vlm_changes[market_symbol][window]
                event_ex_vols = event_vols - (slope2 * mkt_vols + intercept2)
                event_cum_ex_vols = np.cumsum(event_ex_vols)
                #plot_regressvals(mkt_vols,event_ex_vols,slope2, intercept2,event_cum_ex_vols,stock)
                cvr.append(event_ex_vols.tolist())


            #*********************
            # now do computations for the whole stock

            #import pdb; pdb.set_trace()

            cars_stock   =  np.array(ccr)
            
            ccarray.append(cars_stock)
            #df_results.loc[(slice(None),stock),'cars'].tolist()
        
            cars = np.mean(cars_stock,axis=0)
            
            std1 = np.std(cars)
            
            cars_t_test = np.mean(cars) /std1 * np.sqrt(len(window))

                
            pval1 = 1 - stats.t.cdf(cars_t_test,df=len(cars))
                
            if(pval1 < .05):
                cars_significant = True
            else:
                cars_significant = False


            if np.mean(cars) >= 0 :
                cars_positive = True
            else:
                cars_positive = False

            cars_cum = np.cumprod(cars + 1, axis=0)

            #import pdb; pdb.set_trace()

            #plt.plot(cars_cum); plt.title('Cars'); plt.show()

            # do the same for volumes
            #***************
            
            cavs_stock  = np.array(cvr)
            
            cvarray.append(cavs_stock)

            cavs = np.mean(cavs_stock,axis=0)
            
            std2 = np.std(cavs)
            
            cavs_t_test = np.mean(cavs) /std2 * np.sqrt(len(window))

            pval2 = 1 - stats.t.cdf(cavs_t_test,df=len(cavs))
            
            if(pval2 < .05):
                cavs_significant = True
            else:
                cavs_significant = False
            
            
            if np.mean(cavs) >= 0 :
                cavs_positive = True
            else:
                cavs_positive = False

            cavs_cum = np.cumsum(cavs, axis=0)

            #import pdb; pdb.set_trace()


            #plt.plot(cavs_cum); plt.title('Cavs'); plt.show()


            #  store the results *******

            df_results.loc[(stock,'cars'),'positive'] = cars_positive
                                                             
            df_results.loc[(stock,'cars'),'significant'] = cars_significant
                                                             
            df_results.loc[(stock,'cavs'),'positive'] = cavs_positive
             
            df_results.loc[(stock,'cavs'),'significant'] = cavs_significant



        #import pdb; pdb.set_trace()
        
        # aggregate results for output
        #****************

        positive1 = df_results.loc[(slice(None),'cars'),'positive'].tolist()
                                                             
        significant1 = df_results.loc[(slice(None),'cars'),'significant'].tolist()
        
        cars_num_stocks_positive = sum(positive1)
        cars_num_stocks_negative =  sum(np.logical_not(positive1))
        
        
        cars_num_stocks_significant = sum(significant1)
        
        
        
        positive2 = df_results.loc[(slice(None),'cavs'),'positive'].tolist()
        
        significant2 = df_results.loc[(slice(None),'cavs'),'significant'].tolist()
        
        
        cavcs_num_stocks_positive = sum(positive2)
        cavcs_num_stocks_negative =  sum(np.logical_not(positive2))
        
        
        cavcs_num_stocks_significant = sum(significant2)


        

        # The full calculations *********
        
        #import pdb; pdb.set_trace()
        
        Cars = np.mean(np.array(ccarray),axis=0)
        
        num_events = len(Cars)

        cars_std_err = np.std(Cars,axis=0)

        cars =  np.mean(Cars,axis=0)
        
        cars_cum  = np.cumprod(cars + 1, axis=0)
        
        cars_t_testf  = np.mean(Cars) /np.std(cars) * np.sqrt(len(window))
        
        pval1 = 1 - stats.t.cdf(cars_t_testf,df=len(Cars))
        
        
        if(pval1 < .05):
            cars_significant = True
        else:
            cars_significant = False


        if np.mean(cars) > 0 :
            cars_positive = True
        else:
            cars_positive = False



        #***********
        #Now cavs ******
        #*************

        #import pdb; pdb.set_trace()
        Cavcs = np.mean(np.array(cvarray),axis=0)

        cavcs_std_err = np.std(Cavcs,axis=0)

        cavcs =  np.mean(Cavcs,axis=0)

        cavcs_cum  = np.cumsum(cavcs , axis=0)


        cavcs_t_testf  = np.mean(Cavcs) /np.std(cavcs) * np.sqrt(len(window))


        pval2 = 1 - stats.t.cdf(cavcs_t_testf,df=len(Cavcs))


        if(pval2 < .05):
            cavcs_significant = True
        else:
            cavcs_significant = False


        if np.mean(cavcs) > 0 :
            cavcs_positive = True
        else:
            cavcs_positive = False



        #Final  Results to CarsCavcsResult

        #import pdb; pdb.set_trace()
        ccr = CarsCavcsResult(num_events,
                      cars_cum, cars_std_err, cars_t_testf, cars_significant,
                      cars_positive, cars_num_stocks_positive, cars_num_stocks_negative,
                      cavcs_cum, cavcs_std_err, cavcs_t_testf, cavcs_significant,
                      cavcs_positive, cavcs_num_stocks_positive, cavcs_num_stocks_negative)


        return ccr


def plot_regressvals(x,y,slope, intercept,cars,stock):

    import matplotlib.pyplot as plt
    #import pdb; pdb.set_trace()
    plt.figure(1)
    ax1 = plt.subplot(211)
    plt.title('Regression for stock: '+stock)
    ax1.plot(x, y, 'o', label='Original data', markersize=10)
    ax1.plot(x, slope*x + intercept, 'r', label='Fitted line')
    ax1.legend()

    ax2 = plt.subplot(212)
    ax2.plot(cars,label ='excess return')
    #plt.show()


def regress_vals(x,y):
    
    import numpy as np

    A = np.vstack([x, np.ones(len(x))]).T

    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]

    #print(slope, intercept)
    yhat = slope * x + intercept
    cars0 =  y -yhat
    #cars = np.cumprod(cars0 + 1, axis=0)

    return slope,intercept,cars0

