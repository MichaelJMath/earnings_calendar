"""Get any necessary data for given symbols"""

import os

import numpy as np
import pycharts


class CompanyClient(pycharts.CompanyClient):
    """Child Class of pycharts Company Client that adds additional methods
    to make it more convenient to get data from the YCharts API"""
    def __init__(self, ycharts_api_key, symbol_list):
        super(CompanyClient, self).__init__(ycharts_api_key)
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


if __name__ == '__main__':
    YCHARTS_API_KEY = os.environ['YCHARTS_API_KEY']
    symbol_list = ['AAPL', 'xyz']
    field_list = ['price', 'average_volume_30']
    cc = CompanyClient(YCHARTS_API_KEY, 'aapl')

    from pprint import pprint
    pprint(cc.fetch_data(field_list))
    # pprint(cc.get_points(cc.symbol_list, field_list))
