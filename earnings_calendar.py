"""This module fetches the earnings calendar from
 https://www.earningswhispers.com. It pulls the symbols, dates,
 and times for the companies reporting earnings."""

import csv
import datetime as dt
import os
import sys, getopt

from bs4 import BeautifulSoup
import pandas as pd
from pandas.tseries.offsets import BDay
import requests

import data_fetcher

def _get_page(day_num, show_more=False):
    """Gets the earnings calendar html page for the
    day at today plus day_num days

    Parameters:
    -----------
    day_num: int
        The weekday day offset from current day (today=0). Must be
        greater than or equal to 0.
    Return:
    -------
    string
        html page text
    """
    if show_more:
        url = r'https://www.earningswhispers.com/morecalendar'
        params={'sb':'p', 'd':day_num, 'v':'t'}
    else:
        url = r'https://www.earningswhispers.com/calendar'
        params={'sb':'p', 'd':day_num, 't':'all'}
    
    headers={'user_agent':('Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36')}
    r = requests.get(url, params=params, headers=headers)
    return r.text

def _is_BTO_or_ATC(time_string):
    """Based on time, determine if earnings are before, during, or
    after market hours.

    Parameters:
    -----------
    time_string: string
        string of the form "7:30 AM ET"

    Returns:
    --------
    string
        String representing whether company reported before, during, or after
        market.
    """
    try:
        time = dt.datetime.strptime(time_string[:-3], '%I:%M %p')
    except ValueError:
        if time_string=='BMO':
            return 'BTO'
        if time_string=='AMC':
            return 'ATC'
        if time_string=='DMH':
            return 'DMH'
        return "n/a"
    else:
        if time.hour < 10:
            return "BTO"
        elif time.hour >= 16:
            return "ATC"
        elif time.hour >= 10 and time.hour <16:
            return 'DMH'
        else:
            return "n/a"

def _find_symbols_and_times(soup):
    """Return all tickers and earnings times given a soup object
    composed of the earningswhispers.com calendar web page

    Parameters
    ----------
    soup: BeautifulSoup object
        contains html page of earnings calendar

    Returns
    -------
    list of tuples:
        (ticker, is_bto_or_atc, times)
    """
    calendar = soup.find('ul', id="epscalendar")
    tickers = calendar.find_all(class_='ticker')
    times = calendar.find_all(class_='time')
    mapper = lambda x: x.text

    tickers = map(mapper, tickers)
    times = map(mapper, times)

    # Set times to none if times do not align with tickers
    if len(tickers) != len(times):
        times=['n/a']*len(tickers)
        is_bto_or_atc = ['n/a']*len(tickers)
    else:
        is_bto_or_atc = map(_is_BTO_or_ATC, times)

    return zip(tickers, is_bto_or_atc, times )

def fetch_all_earnings_and_times(n_days, start_day=1):
    """Get symbols that have earnings and the time of
    the release for the next n_days.

    Parameters
    ----------
    n_days: int
        number of days to fetch (does not count weekends)
    start_day: int
        The day to begin query (0 is the current day).

    Returns
    -------
    calendar_dict: dict
        {earnings_date: list of earnings calendar data returned
                        from _find_symbols_and_times()}
    """
    calendar_dict = {}
    for day in range(start_day, n_days + start_day):
        soup = BeautifulSoup(_get_page(day), 'html.parser')
        date = dt.datetime.today() + BDay(day)
        calendar_dict[date] = _find_symbols_and_times(soup)

    return calendar_dict

def write_to_file(calendar_dict, file_base_name='earnings_calendar',
                  dest_path='./Earnings Calendar Files'):
    """Write earnings calendar to csv file.

    Parameters
    ----------
    calendar_dict: dict
        {earnings_date: list of earnings calendar data returned
                        from _find_symbols_and_times()}
    file_base_name: string
        name of file (before appending date_time identifier)
    dest_path: string
        path to store the file

    Returns
    --------
    file_path: string
        path of the destination file
    """
    sorted_dates = sorted(calendar_dict.keys())
    start_date_str =  sorted_dates[0].strftime('%Y%m%d')
    end_date_str =  sorted_dates[-1].strftime('%Y%m%d')

    file_name = (file_base_name + '_'+ start_date_str + '-' +
                 end_date_str )
    file_path = os.path.join(dest_path, file_name + '.csv' )

    i = 1
    while os.path.exists(file_path):
        file_path = os.path.join(dest_path,
                                 file_name + '({})'.format(i)+'.csv')
        i+=1

    with open(file_path, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['Date', 'Symbol', 'BTO/ATC','Time'])
        for date in sorted_dates:
            for row in calendar_dict[date]:
                str_date = date.strftime('%a, %m/%d/%Y')
                writer.writerow((str_date,) + row)

    return file_path

def append_data_to_file(file_name, fields=['price', 'average_volume_30']):
    """Read in an Earnings Calendar csv file. Append data fields columns.
    Then, rewrite to file"""

    earnings_cal_df = pd.read_csv(file_name)

    symbols = earnings_cal_df['Symbol'].tolist()
    cc = data_fetcher.CompanyClient(symbols)
    data_df = cc.to_dataframe(cc.fetch_data(fields))

    final_df = earnings_cal_df.merge(data_df, how='left',left_on='Symbol',
                                     right_index=True)

    final_df.to_csv(file_name, index=False)


if __name__=='__main__':
    LONG_OPTS = ('days=', 'help', 'start=')
    SHORT_OPTS = 'd:s:h'
    days_to_fetch = 5
    start_day = 1
    try:
        opts, args = getopt.getopt(sys.argv[1:], SHORT_OPTS, LONG_OPTS)
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)
    else:
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                print (
                 'Usage: earnings_calendar.py [OPTION]...\n\n'
                 'Fetch Earnings Calendar from EarningsWhispers.com and \n'
                 'save to csv file\n\n'

                 'Arguments\n'
                 '  -d --days=INT       Number of days to fetch. Default=5\n'
                 '  -s --start=INT      The first day to start (0=Today). Default=1 \n'
                 '  -h --help           display this help message and exit'
                )
                sys.exit()
            if opt in ('-d', '--days'):
                days_to_fetch = int(arg)
            elif opt in ('-s', '--start'):
                start_day = int(arg)

    earnings_calendar = fetch_all_earnings_and_times(days_to_fetch, start_day)
    file_path = write_to_file(earnings_calendar)

    data_fields = ['price', 'average_volume_30']
    append_data_to_file(file_path, data_fields)

