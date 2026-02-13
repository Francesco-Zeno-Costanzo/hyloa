# This file is part of HYLOA - HYsteresis LOop Analyzer.
# Copyright (C) 2024 Francesco Zeno Costanzo

# HYLOA is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# HYLOA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with HYLOA. If not, see <https://www.gnu.org/licenses/>.

"""
Code to handle worksheet dataframes to ensure comunication
between different worksheets
"""

class WsData:
    '''
    Run-time storage of dataframes for each worksheet, to ensure communication between different worksheets
    and allow to create a plot with columns from different worksheets.
    '''
    
    def __init__(self):
        '''
        Initialization of dataframe storage
        '''
        # {worksheet_name : pandas.DataFrame}
        self._datasets = {}

    def add(self, name, df):
        '''
        Frunction to add or update a dataframe

        Parameters
        ----------
        name : str
            Name of the worksheet
        df : pandas.DataFrame
            data stored in the worksheet
        '''

        self._datasets[name] = df
    
    def remove(self, name):
        '''
        Frunction to remove a .

        Parameters
        ----------
        name : str
            Name of the worksheet
        ''' 

        if name in self._datasets:
            del self._datasets[name]
    
    def get(self, name):
        '''
        Get dataframe by worksheet name.

        Parameters
        ----------
        name : str
            Name of the worksheet
        
        Return
        ------
        pandas.DataFrame in name worksheet
        '''

        return self._datasets.get(name)
    
    def get_all(self):
        '''
        Get all dataframe.

        Return
        ------
        dict, all dataframes in all worksheet
        '''

        return self._datasets
    
    def get_all_columns(self):
        '''
        Return flattened structure:
        {
            "ws1::colA": (ws1, colA),
            "ws2::colB": (ws2, colB)
        }
        '''
        flat = {}
        for ws_name, df in self._datasets.items():
            for col in df.columns:
                flat[f"{ws_name}::{col}"] = (ws_name, col)
        return flat

