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
Code to create a robust cross-platform serialization for pandas DataFrames.
"""
from typing import Any, Dict

import numpy as np
import pandas as pd

class DataFrameSerializer:
    '''
    Robust cross-platform serialization for pandas DataFrames.
    
    This class handles serialization with explicit dtype preservation,
    ensuring compatibility across different:
    - Operating systems (Windows, Linux, macOS)
    - NumPy/Pandas versions
    
    The serialization strategy:
    1. Use native Python dtypes (int, float, str, bool) instead of NumPy dtypes
    2. Store column-level dtype info in a standard format
    3. Handle NaN/None values explicitly
    4. Preserve index information
    '''

    # Mapping from Numpy/Pandas dtypes to native Python types
    _dtype_mapping = {
        "int8":           ("int", {}),
        "int16":          ("int", {}),
        "int32":          ("int", {}),
        "int64":          ("int", {}),
        "uint8":          ("int", {}),
        "uint16":         ("int", {}),
        "uint32":         ("int", {}),
        "uint64":         ("int", {}),
        "float16":        ("float", {}),
        "float32":        ("float", {}),
        "float64":        ("float", {}),
        "bool":           ("bool", {}),
        "object":         ("str", {}),
        "string":         ("str", {}),
        "datetime64[ns]": ("datetime", {"format": "iso8601"}),
        "category":       ("str", {"categorical": True}),
    }

    @staticmethod
    def serialize(df: pd.DataFrame) -> Dict[str, Any]:
        '''
        Serialize a Pandas DataFrame into a portable dictionary format.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to serialize.
        
        Returns
        -------
        dict
            Portable representation with keys: 'columns', 'index', 'data', 'dtypes', 'attrs'
        '''

        serialized = []
        dtype_info = {}

        for col in df.columns:
            series    = df[col]
            dtype_str = str(series.dtype)

            #Mapping
            portable_dtype, metadata = DataFrameSerializer._dtype_mapping.get(dtype_str, ("str", {}))

            dtype_info[col] = {
                "type":           portable_dtype,
                "original_dtype": dtype_str,
                "metadata":       metadata
            }

            #Serialize columns data 
            col_data = []
            for val in series:
                if pd.isna(val) or val is None:
                    col_data.append(None)  # Explicit None for missing values
                elif portable_dtype == "float":
                    col_data.append(float(val))
                elif portable_dtype == "int":
                    col_data.append(int(val))
                elif portable_dtype == "bool":
                    col_data.append(bool(val))
                elif portable_dtype == "datetime":
                    # ISO8601 format is cross-platform safe
                    if hasattr(val, 'isoformat'):
                        col_data.append(val.isoformat())
                    else:
                        col_data.append(str(val))
                else:  # str
                    col_data.append(str(val))
            
            serialized.append(col_data)

        return {
            "columns":    list(df.columns),
            "index":      df.index.tolist() if df.index.name or any(i != v for i, v in enumerate(df.index)) else None,
            "index_name": df.index.name,
            "data":       serialized,  # Column-oriented storage
            "dtypes":     dtype_info,
            "shape":      df.shape,  
            "attrs":      dict(df.attrs)  # Preserve custom DataFrame attributes
        }
    
    @staticmethod
    def deserialize(serialized: Dict[str, Any]) -> pd.DataFrame:
        '''
        Deserialize a portable dictionary format back into a Pandas DataFrame.

        Parameters
        ----------
        serialized : dict
            The serialized representation of the DataFrame.
        
        Returns
        -------
        pd.DataFrame
            The reconstructed DataFrame.
        '''

        
        columns    = serialized.get("columns", [])
        data_rows  = serialized.get("data", [])
        dtype_info = serialized.get("dtypes", {})
        index_data = serialized.get("index")
        index_name = serialized.get("index_name")

        # ===== Auto-detect storage format (row vs column oriented) =====
        num_cols       = len(columns)
        num_data_lists = len(data_rows)
        
        if num_data_lists > 0:
            first_list_len = len(data_rows[0])
            
            # Detect format:
            # - v2 (column-oriented): num_data_lists == num_cols
            # - v1 (row-oriented): first_list_len == num_cols
            if num_data_lists != num_cols and first_list_len == num_cols:
                # v1 format detected: transpose from row-oriented to column-oriented
                data_rows = list(zip(*data_rows))

        # Build DataFrame from column-oriented data
        data_dict = {}
        for col_idx, col_name in enumerate(columns):
            col_data = data_rows[col_idx] if col_idx < len(data_rows) else []
            
            # ===== Detect dtype format (v1 vs v2) =====
            dtype_entry = dtype_info.get(col_name, {})
            
            if isinstance(dtype_entry, str):
                # Legacy v1 format: dtype is just a string
                target_dtype = DataFrameSerializer._infer_type_from_string(dtype_entry)
            elif isinstance(dtype_entry, dict):
                # New v2 format: dtype is a dict with "type" key
                target_dtype = dtype_entry.get("type", "str")
            else:
                # Fallback
                target_dtype = "str"
            
            # Convert to correct type
            converted = []
            for val in col_data:
                if val is None:
                    converted.append(np.nan)
                elif target_dtype == "float":
                    converted.append(float(val))
                elif target_dtype == "int":
                    converted.append(int(val))
                elif target_dtype == "bool":
                    converted.append(bool(val))
                elif target_dtype == "datetime":
                    try:
                        converted.append(pd.to_datetime(val))
                    except:
                        converted.append(pd.NaT)
                else:  # str
                    converted.append(str(val))
            
            data_dict[col_name] = converted
        
        # Create DataFrame
        df = pd.DataFrame(data_dict)
        
        # Restore index if provided
        if index_data and len(index_data) == len(df):
            try:
                df.index = index_data
            except Exception as e:
                print(f"[WARNING] Could not restore index: {e}")
                # Keep default index
        if index_name:
            df.index.name = index_name
        
        # Restore attributes
        attrs = serialized.get("attrs", {})
        df.attrs.update(attrs)
        
        return df
    
    @staticmethod
    def _infer_type_from_string(dtype_str: str) -> str:
        '''
        Infer portable type from old-format dtype string (v1).
        
        Parameters
        ----------
        dtype_str : str
            Old format dtype string like "float64", "int32", etc.
        
        Returns
        -------
        str
            Portable type: "float", "int", "str", "bool", "datetime"
        '''
        dtype_str = dtype_str.lower()
        
        if "float" in dtype_str:
            return "float"
        elif "int" in dtype_str:
            return "int"
        elif "bool" in dtype_str:
            return "bool"
        elif "datetime" in dtype_str:
            return "datetime"
        else:
            return "str"