"""Get any necessary data for given symbols"""

import os

import numpy as np
import pandas as pd
import pycharts


class CompanyClient(pycharts.CompanyClient):
    """Child Class of pycharts Company Client that adds additional methods
    to make it more convenient to get data from the YCharts API"""
    def __init__(self, symbol_list):
        YCHARTS_API_KEY = os.environ['YCHARTS_API_KEY']
        super(CompanyClient, self).__init__(YCHARTS_API_KEY)
        if isinstance(symbol_list, basestring):
            symbol_list = [symbol_list]
        self.symbol_list = map(str.upper, symbol_list)

    def fetch_data(self, fields):
        """Fetch data for given fields

        Parameters
        ----------
        fields: list
            Field(s) for which to fetch data

        Returns
        -------
        data_dict: dictionary
            {symbol_1: {field1: data1, field2: data2},
             symbol_2: {field1: data1, field2: data2}
             }
        """
        response = self.get_points(self.symbol_list, field_list)['response']

        # data_dict keyed by symbol
        data_dict = {}

        for symbol in response:
            if response[symbol]['meta']['status'] == 'ok':
                symbol_data = response[symbol]['results']
                data_dict[symbol] = {}
                for data_point in symbol_data:
                    data_dict[symbol][data_point] = \
                        symbol_data[data_point]['data'][1]
            else:
                data_dict[symbol] = {field:np.nan for field in field_list}
        return data_dict

    def to_dataframe(self, data_dict):
        """Convert data_dict5 from fetch data to a DataFrame"""
        return pd.DataFrame.from_dict(data_dict, orient='index')

if __name__ == '__main__':

    symbol_list = ['AAPL', 'xyz']
    field_list = ['price', 'average_volume_30']
    cc = CompanyClient( symbol_list)

    from pprint import pprint
    data = cc.fetch_data(field_list)
    print cc.to_dataframe(data)

