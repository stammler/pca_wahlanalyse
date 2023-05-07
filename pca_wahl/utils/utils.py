from io import BytesIO
from collections import defaultdict
import numpy as np
import os
import pandas as pd
from types import SimpleNamespace
from typing import Tuple
import urllib3
import zipfile

def load_zipfile(url: str) -> Tuple[pd.DataFrame, str]:
    """
    Function takes an url and return data frame and terms of usage.
    
    Parameters
    ----------
    url : str
        url to data sheet
        
    Returns
    -------
    df : pnadas.DataFrame
        Data frame with parsed data
    note : str
        Terms of usage
    """
    http = urllib3.PoolManager()
    response = http.request('GET', url)
    zip_file = zipfile.ZipFile(BytesIO(response.data))
    for f in zip_file.filelist:
        if f.filename.endswith(".xlsx"):
            file = f
    datafile = zip_file.open(file)
    df = pd.read_excel(datafile, sheet_name=-1)
    df_note = pd.read_excel(datafile, sheet_name=0, header=None)
    list_note = []
    for s in df_note[0]:
        if type(s) == str:
            list_note.append(s)
        else:
            list_note.append("")
    note = "\n".join(list_note)
    return df, note


def convert_dataframe(df: pd.DataFrame) -> SimpleNamespace:
    """
    Function takes data frame and returns parsed name space.
    
    Parameters
    ----------
    df : pandas.DataFrame
    
    Returns
    -------
    data : SimpleNamespace
        Parsed and converted data
    """
    df = df[~df["These: Nr."].isna()]
    df = df.astype({"These: Nr.": "int"})
    df = df.astype({"Partei: Nr.": "int"})
    # Truncating sheet after multiple empty lines (fixes Niedersachsen 2022)
    diff = np.diff(df.index)
    if diff.max()>1:
        df = df.iloc[:diff.argmax()+1]
    parties = df["Partei: Kurzbezeichnung"].unique()
    N_par = parties.shape[0]
    statements = df["These: Titel"].unique()
    N_sta = statements.shape[0]
    statements_long = df["These: These"].unique()
    mapping = {
        "stimme zu": 1,
        "stimme nicht zu": -1,
        "neutral": 0,
    }
    X = np.empty((N_par, N_sta), dtype=int)
    for i in range(N_par):
        for j in range(N_sta):
            X[i, j] = mapping[str.lower(df[(df["Partei: Nr."]==i+1) & (df["These: Nr."]==j+1)]["Position: Position"].iloc[0])]
    data = SimpleNamespace(
        parties=parties,
        statements=statements,
        statements_long=statements_long,
        X=X
    )
    return data


def load_election(election: str) -> SimpleNamespace:
    """
    Function loads entire election data set and converts data to usable format.
    
    Parameters
    ----------
    election : str
        String can either be url to data sheet or key word from dictionary with urls
    
    Returns
    -------
    data : SimpleNamespace
        Namespace with data in usable format
    """
    election_file = election_files.get(election, election)
    df, note = load_zipfile(election_file)
    data = convert_dataframe(df)
    data.note = note
    return data


def remove_party_from_data(data: SimpleNamespace, remove=[]) -> SimpleNamespace:
    """
    Function removes party from data set.
    
    Parameters
    ----------
    data : SimpleNamespace
        Namespace with data
    remove : list, optional, default: []
        List of strings with party names to be removed from data set
    
    Returns
    -------
    new_data : SimpleNamespace
        Namespace with new data
    """
    for party in remove:
        if party not in data.parties:
            continue
        i = np.argmax(data.parties==party)
        data.parties = np.delete(data.parties, i, 0)
        data.X = np.delete(data.X, i, 0)
    return data


election_files = {
    "2021-06-06_st": "https://www.bpb.de/system/files/datei/Wahl-O-Mat%20Sachsen-Anhalt%202021_Datensatz_v1.03_0.zip",
    "2021-09-26_de": "https://www.bpb.de/system/files/datei/Wahl-O-Mat%20Bundestag%202021_Datensatz_v1.02.zip",
    # "2021-09-26_mv": "https://www.bpb.de/system/files/datei/Wahl-O-Mat%20Mecklenburg-Vorpommern%202021_Datensatz.zip", # corrupted file
    # "2022-03-27_sl": "https://www.bpb.de/system/files/datei/Wahl-O-Mat_Saarland_2022_Datensatz_v1.01.zip", # corrupted file
    "2022-05-08_sh": "https://www.bpb.de/system/files/datei/Wahl-O-Mat_Schleswig-Holstein_2022_Datensatz_v1.02.zip", 
    "2022-05-15_nw": "https://www.bpb.de/system/files/datei/Wahl-O-Mat_Nordrhein-Westfalen_2022_Datensatz_v1.02.zip", 
    "2022-10-09_ni": "https://www.bpb.de/system/files/datei/Wahl-O-Mat_Niedersachsen_2022_Datensatz_v1.01.zip", 
    "2023-05-14_hb": "https://www.bpb.de/system/files/datei/Wahl-O-Mat_Bremen_2023_Datensatz_v1.01.zip", 
    "2023-02-12_be": "https://www.bpb.de/system/files/datei/Wahl-O-Mat_Berlin_2023_Datensatz.zip",
}

_colors = {
    "III. Weg": "#1d542c",
    "AfD": "#009ee0",
    "B*": "#019889",
    "dieBasis": "#4d4c4d",
    "BIG": "#ed8045",
    "BIW": "#005ab0",
    "BP": "#7FFFFF",
    "BÜNDNIS21": "#e81972",
    "Bündnis C": "#0872ba",
    "BÜRGERBEWEGUNG": "#f07e18",
    "BüSo": "#1f4569",
    "CDU": "#000000",
    "CDU / CSU": "#000000",
    "CSU": "#000000",
    "DiB": "#854d68",
    "DKP": "#ed1c24",
    "DSP": "#a1b45a",
    "FAMILIE": "#ff6600",
    "FBM": "#ff9b30",
    "FDP": "#ffff00",
    "FREIE WÄHLER": "#FF8000",
    "Die Grauen": "#9e9e9e",
    "Graue Panther": "#6b6b6b",
    "GRÜNE": "#46962b",
    "Die Humanisten": "#2191BD",
    "Die Humanisten Niedersachsen": "#2191BD",
    "Klimaliste Berlin": "#5cc14c",
    "Klimaliste ST": "#5cc14c",
    "LfK": "#d2175e",
    "LIEBE": "#db3028",
    "DIE LINKE": "#BE3075",
    "DIE LINKE.": "#BE3075",
    "LKR": "#f39200",
    "MENSCHLICHE WELT": "#f26f22",
    "MIETERPARTEI": "#002b83",
    "MLPD": "#ed1c24",
    "neo": "#a5d839",
    "NPD": "#8b4726",
    "ÖDP": "#ff6400",
    "Die PARTEI": "#b5152b",
    "PdF": "#f5a612",
    "PIRATEN": "#ff820a",
    "REP": "#0075BE",
    "SGP": "#B70E0C",
    "SPD": "#E3000F",
    "SSW": "#003c8f",
    "Tierschutzpartei": "#006D77",
    "Team Todenhöfer": "#20274d",
    "UNABHÄNGIGE": "#ff9900",
    "du.": "#ff9700",
    "Die Urbane.": "#ff9700",
    "V-Partei³": "#a1bf14",
    "DIE VIOLETTEN": "#621c75",
    "Volt": "#562883",
    "WiR2020": "#496164",
    "Z.": "#005a62",
    "ZENTRUM": "#0000CD",
}
color_dict = defaultdict(lambda: "#777777", _colors)