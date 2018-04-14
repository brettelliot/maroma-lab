import datetime
from maroma.lab.stockdatastore import StockDataStore
from examples.eventstudy.exampleeventmatrix import ExampleEventMatrix
from maroma.lab.calculator import Calculator
from maroma.lab.plotter import Plotter
import logging


def main():

    logging.basicConfig(filename='logfile.log', filemode='w', level=logging.DEBUG, format='%(message)s')
    logger = logging.getLogger()


    file_log_handler = logging.FileHandler('logfile.log')
    logger.addHandler(file_log_handler)

    stderr_log_handler = logging.StreamHandler()
    logger.addHandler(stderr_log_handler)
    logger.setLevel('DEBUG')

    # nice output format
    #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #file_log_handler.setFormatter(formatter)
    #stderr_log_handler.setFormatter(formatter)


    # Define the symbols to study
    symbols = ['S3']

    # Define the market symbol to compare against
    market_symbol = "MKT"

    # Add the market symbol to the symbols list to get it's data too
    symbols.append(market_symbol)
    

    # Define the start and end date of the study
    start_date = datetime.datetime(2009, 1, 1)
    end_date = datetime.datetime(2016, 12, 31)
    value_threshold = 7
    estimation_window = 200
    buffer = 5
    pre_event_window = 5
    post_event_window = 10
    csv_file_name = './data/eventdates.csv'

    logger.info("Collecting historical stock data")
    keys = ['adjusted_close','volume']
    # Get a pandas multi-indexed dataframe indexed by datetime and symbol
    stock_data_store = StockDataStore('./data/')
    
    stock_data = stock_data_store.get_stock_data(symbols, keys)
    #print(stock_data.head())


    logger.info("Building event matrix")
    eem = ExampleEventMatrix(stock_data.index.levels[1], symbols,value_threshold, csv_file_name)
                             

    # Get a dataframe with an index of all trading days, and columns of all symbols.
    event_matrix = eem.build_event_matrix(start_date, end_date)
    
    #print(event_matrix[event_matrix['S1'] == 1])

    logger.info("Number of events: " + str(len(event_matrix[(event_matrix == 1.0).any(axis=1)])))
    #logger.info(event_matrix[(event_matrix == 1.0).any(axis=1)])

    #import pdb; pdb.set_trace()

    calculator = Calculator()
    ccr = calculator.calculate_cars_cavcs(event_matrix, stock_data[['adjusted_close','volume']], market_symbol,
                                          estimation_window, buffer, pre_event_window, post_event_window)
                                          
    # print results to file and Plots
    logger.info('CARS and CAVCS results for the whole group of stocks')
    logger.info('  Number of events  =  ' +str(ccr.num_events))
    logger.info('CARS Results')
    logger.info('  CARS number of stocks +ve = ' +str(ccr.cars_num_stocks_positive))
    logger.info('  CARS number of stocks -ve = '+str(ccr.cars_num_stocks_negative))
    logger.info('  CARS t-test value = '+str(ccr.cars_t_test))
    logger.info('  CARS significant = '+str(ccr.cars_significant))
    logger.info('  CARS +ve = '+str(ccr.cars_positive))
    logger.info('CAVCS Results')
    logger.info('  CAVCS number of stocks +ve = ' +str(ccr.cavcs_num_stocks_positive))
    logger.info('  CAVCS number of stocks -ve = '+str(ccr.cavcs_num_stocks_negative))
    logger.info('  CAVCS full t-test value = '+str(ccr.cavcs_t_test))
    logger.info('  CAVCS significant = '+str(ccr.cavcs_significant))
    logger.info('  CAVCS +ve = '+str(ccr.cavcs_positive))


    
    #******************
    
    #import pdb; pdb.set_trace()

    #plotter = Plotter()
    #import pdb; pdb.set_trace()
    #plotter.plot_car(ccr.num_events,ccr.cars, ccr.cars_std_err, ccr.cavcs,ccr.cavcs_std_err,
    #                 pre_event_window, post_event_window, True,'ccrplot.pdf')


if __name__ == "__main__":
    main()
