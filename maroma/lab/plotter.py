import matplotlib.pyplot as plt


class Plotter(object):

    def __init__(self, width=10, height=5):
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['grid.linestyle'] = "--"
        plt.rcParams['figure.figsize'] = width, height
        pass

    def plot_car(self, car, std_err, num_events, look_back, look_forward, show=True, pdf_filename=None ):

        #plotting
        li_time = list(range(-look_back, look_forward + 1))
        # print(li_time)

        # Plotting the chart
        plt.clf()
        plt.grid()
        plt.axhline(y=1.0, xmin=-look_back, xmax=look_forward, color='k')
        plt.errorbar(li_time[look_back:], car[look_back:],
                    yerr=std_err[look_back:], ecolor='#AAAAFF',
                    alpha=0.7)
        plt.plot(li_time, car, linewidth=1, label='mean', color='b')
        plt.xlim(-look_back - 1, look_forward + 1)
        plt.title('Market Relative CAR of ' + str(num_events) + ' events')
        plt.xlabel('Days')
        plt.ylabel('Cumulative Abnormal Returns')
        if pdf_filename is not None:
            plt.savefig(pdf_filename, format='pdf')
        if show:
            plt.show()


