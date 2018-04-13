import matplotlib.pyplot as plt


class Plotter(object):

    def __init__(self, width=10, height=5):
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['grid.linestyle'] = "--"
        plt.rcParams['figure.figsize'] = width, height
        pass

    def plot_car(self, num_events, car, std_err1, cavcs, std_err2, look_back, look_forward, show=True, pdf_filename=None ):

        #printing some Output
        li_time = list(range(-look_back, look_forward + 1))
        # print(li_time)
        
        

        # Plotting the chart first for cavcs
        plt.clf()
        plt.figure(1)
        plt.subplot(211)
        plt.grid()
        plt.axhline(y=1.0, xmin=-look_back, xmax=look_forward, color='k')
        plt.errorbar(li_time[look_back:], car[look_back:],
                    yerr=std_err1[look_back:], ecolor='#AAAAFF',
                    alpha=0.7)
        plt.plot(li_time, car, linewidth=1, label='mean', color='b')
        plt.xlim(-look_back - 1, look_forward + 1)
        plt.title('Market Relative CAR & CAVCS of ' + str(num_events) + ' events')
        plt.xlabel('Days')
        plt.ylabel('Cumulative Abnormal Returns')
        
        
        #now the cavcs
        
        plt.subplot(212)
        plt.grid()
        plt.axhline(y=1.0, xmin=-look_back, xmax=look_forward, color='k')
        plt.errorbar(li_time[look_back:], car[look_back:],
                     yerr=std_err2[look_back:], ecolor='#AAAAFF',
                     alpha=0.7)
        plt.plot(li_time, cavcs, linewidth=1, label='mean', color='b')
        plt.xlim(-look_back - 1, look_forward + 1)
        plt.xlabel('Days')
        plt.ylabel('Cumulative Abnormal Changes in Volumes')


        # write it our
        if pdf_filename is not None:
            plt.savefig(pdf_filename, format='pdf')
        if show:
            plt.show()


