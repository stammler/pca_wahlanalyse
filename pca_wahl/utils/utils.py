from io import BytesIO
from collections import defaultdict
import numpy as np
import os
import pandas as pd
import re
from types import SimpleNamespace
from typing import Tuple
import urllib3
import zipfile


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


def load_election_data(election: str) -> SimpleNamespace:
    """
    Function load election data and returns name space.
    
    Parameters
    ----------
    election : str
        Keyword of election or URL to app
        
    Returns
    -------
    data : SimpleNamespace
        Name space with election data
    """
    
    election_file = election_files.get(election, election)
    
    http = urllib3.PoolManager()
    response = http.request('GET', election_file)
    zip_file = zipfile.ZipFile(BytesIO(response.data))
    for f in zip_file.filelist:
        if f.filename.endswith("module_definition.js") or f.filename.endswith("module_definition_v1_01.js"):
            file = f
    datafile = zip_file.open(file)
    data = parse_js(datafile.readlines())
    
    # This is to get the TOS
    http = urllib3.PoolManager()
    response = http.request('GET', "https://www.bpb.de/system/files/datei/Wahl-O-Mat%20Bundestag%202021_Datensatz_v1.02.zip")
    zip_file = zipfile.ZipFile(BytesIO(response.data))
    for f in zip_file.filelist:
        if f.filename.endswith(".xlsx"):
            file = f
    datafile = zip_file.open(file)
    df_note = pd.read_excel(datafile, sheet_name=0, header=None)
    list_note = []
    for s in df_note[0]:
        if type(s) == str:
            list_note.append(s)
        else:
            list_note.append("")
    data.note = "\n".join(list_note)
    
    return data


def parse_js(lines: list) -> SimpleNamespace:
    """
    Function takes a list of line from the relevant javascript file and
    returns name space with data.
    
    Parameters
    ----------
    lines : list
        List of strings with lines from javascript file "module_definition.js"
        
    Returns
    -------
    data : SimpleNamespace
        Name space with parsed data
    """
    
    pat = r"\[(.*?)\]"
    pat_s = r"\'(.*?)\'"
    parties = []
    statements = []
    statements_long = []
    for line in lines:
        
        try:
            l = line.decode(encoding="utf-8")
        except:
            l = line.decode(encoding="iso-8859-1")
        
        # Parties
        if l.startswith("WOMT_aParteien["):
            m = re.findall(pat, l)
            if len(m) == 3:
                s = re.findall(pat_s, l)
                if int(m[-1])==1:
                    parties.append(s[0])
                    
        # Statements
        if l.startswith("WOMT_aThesen["):
            m = re.findall(pat, l)
            if len(m) == 3:
                s = re.findall(pat_s, l)
                if int(m[-1])==0:
                    statements.append(s[0])
                elif int(m[-1])==1:
                    statements_long.append(s[0])
    
    # Positions
    N_p, N_s = len(parties), len(statements)
    X = np.empty((N_p, N_s), dtype=int)
    for line in lines:
        
        try:
            l = line.decode(encoding="utf-8")
        except:
            l = line.decode(encoding="iso-8859-1")
        
        if l.startswith("WOMT_aThesenParteien["):
            m = re.findall(pat, l)
            if len(m) == 2:
                i_the, i_par = int(m[0]), int(m[1])
                s = re.findall(pat_s, l)
                X[i_par, i_the] = int(s[0])
                
    data = SimpleNamespace(
        parties=np.array(parties),
        statements=np.array(statements),
        statements_long=np.array(statements_long),
        X=X
    )
    return data


election_files = {
    "2024-09-22_bb": "https://www.wahl-o-mat.de/brandenburg2024/wahlomat.zip",
    "2024-09-01_sn": "https://www.wahl-o-mat.de/sachsen2024/wahlomat.zip",
    "2024-09-01_th": "https://www.wahl-o-mat.de/thueringen2024/wahlomat.zip",
    "2024-06-09_eu": "https://www.wahl-o-mat.de/europawahl2024/wahlomat.zip",
    "2023-05-14_hb": "https://www.wahl-o-mat.de/bremen2023/wahlomat.zip",
    "2023-02-12_be": "https://archiv.wahl-o-mat.de/berlin2023/wahlomat.zip",
    "2022-10-09_ni": "https://archiv.wahl-o-mat.de/niedersachsen2022/wahlomat.zip",
    "2022-05-15_nw": "https://archiv.wahl-o-mat.de/nordrheinwestfalen2022/wahlomat.zip",
    "2022-03-27_sl": "https://archiv.wahl-o-mat.de/saarland2022/wahlomat.zip",
    "2022-05-08_sh": "https://archiv.wahl-o-mat.de/schleswigholstein2022/wahlomat.zip",
    "2021-09-26_mv": "https://archiv.wahl-o-mat.de/mecklenburgvorpommern2021/wahlomat.zip",
    "2021-09-26_be": "https://archiv.wahl-o-mat.de/berlin2021/wahlomat.zip",
    "2021-09-26_de": "https://archiv.wahl-o-mat.de/bundestagswahl2021/wahlomat.zip",
    "2021-06-06_st": "https://archiv.wahl-o-mat.de/sachsenanhalt2021/wahlomat.zip",
    "2019-10-27_th": "https://archiv.wahl-o-mat.de/thueringen2019/wahlomat.zip",
    "2019-05-26_hb": "https://archiv.wahl-o-mat.de/bremen2019/wahlomat.zip",
    "2017-09-24_de": "https://archiv.wahl-o-mat.de/bundestagswahl2017/wahlomat.zip",
    "2017-05-14_nw": "https://archiv.wahl-o-mat.de/nrw2017/wahlomat.zip",
    # "2017-05-07_sh": "https://archiv.wahl-o-mat.de/schleswigholstein2017/wahlomat.zip", # bilingual, not working atm
    "2017-03-26_sl": "https://archiv.wahl-o-mat.de/saarland2017/wahlomat.zip",
    "2016-09-18_be": "https://archiv.wahl-o-mat.de/berlin2016/wahlomat.zip",
    "2016-03-13_st": "https://archiv.wahl-o-mat.de/sachsenanhalt2016/wahlomat.zip",
    "2016-03-13_bw": "https://archiv.wahl-o-mat.de/bw2016/wahlomat.zip",
    "2016-03-13_rp": "https://archiv.wahl-o-mat.de/rlp2016/wahlomat.zip",
    "2015-02-15_hh": "https://archiv.wahl-o-mat.de/hamburg2015/wahlomat.zip",
    "2014-09-14_bb": "https://archiv.wahl-o-mat.de/brandenburg2014/wahlomat.zip",
    "2014-09-14_th": "https://archiv.wahl-o-mat.de/thueringen2014/wahlomat.zip",
    "2014-08-31_sn": "https://archiv.wahl-o-mat.de/sachsen2014/wahlomat.zip",
    "2014-05-25_eu": "https://archiv.wahl-o-mat.de/europawahl2014/wahlomat.zip",
    "2013-09-22_de": "https://archiv.wahl-o-mat.de/bundestagswahl2013/wahlomat.zip",
    "2013-09-15_by": "https://archiv.wahl-o-mat.de/bayern2013/wahlomat.zip",
}

_colors = {
    "III. Weg": "#1d542c",
    "ABG": "#7F2982",
    "AfD": "#009ee0",
    "ALFA": "#0066ff",
    "Allianz Deutscher Demokraten": "#1e5ea5",
    "AUF": "#B4EEB4",
    "B": "#019889",
    "B*": "#019889",
    "dieBasis": "#4d4c4d",
    "BGE": "#0C8AA8",
    "BIG": "#ed8045",
    "BIW": "#005ab0",
    "Blaue *raute*TeamPetry Thüringen": "#25378f",
    "BP": "#7FFFFF",
    "BSW": "#7d254f",
    "bunt.saar": "#f49800",
    "BÜNDNIS21": "#e81972",
    "Bündnis 21/RRP": "#ff6a1a",
    "Bündnis C": "#0872ba",
    "BÜNDNIS DEUTSCHLAND": "#a2bbf3",
    "BÜRGERBEWEGUNG": "#f07e18",
    "BüSo": "#1f4569",
    "CDU": "#000000",
    "CDU/CSU": "#000000",
    "CDU / CSU": "#000000",
    "CSU": "#000000",
    "CM": "#029de7",
    "DAVA": "#068E91",
    "DiB": "#854d68",
    "DIE DIREKTE!": "#ffc000",
    "DKP": "#ed1c24",
    "DLW": "#227172",
    "DM": "#284f8d",
    "DSP": "#a1b45a",
    "DSU": "#00B2EE",
    "DIE EINHEIT": "#f8a501",
    "FAMILIE": "#ff6600",
    "FBI/FWG": "#63B8FF",
    "FBM": "#ff9b30",
    "FDP": "#ffff00",
    "DIE FRANKEN": "#9c2020",
    "DIE FRAUEN": "#FF83FA",
    "FREIE WÄHLER": "#FF8000",
    "BVB / FREIE WÄHLER": "#FF8000",
    "FREIE SACHSEN": "#20B2AA",
    "Die Grauen": "#9e9e9e",
    "Graue Panther": "#6b6b6b",
    "GRÜNE": "#46962b",
    "GRÜNE/B 90": "#46962b",
    "HEIMAT": "#d79e2a",
    "PdH": "#2191BD",
    "Die Humanisten": "#2191BD",
    "Die Humanisten Niedersachsen": "#2191BD",
    "KLIMALISTE": "#5cc14c",
    "Klimaliste Berlin": "#5cc14c",
    "Klimaliste ST": "#5cc14c",
    "KPD": "#8B0000",
    "LETZTE GENERATION": "#FF4C00",
    "LfK": "#d2175e",
    "LIEBE": "#db3028",
    "DIE LINKE": "#BE3075",
    "DIE LINKE.": "#BE3075",
    "LKR": "#f39200",
    "MENSCHLICHE WELT": "#f26f22",
    "MERA25": "#f15a32",
    "MIETERPARTEI": "#002b83",
    "MLPD": "#ed1c24",
    "neo": "#a5d839",
    "Partei der Nichtwähler": "#ea6a09",
    "NPD": "#8b4726",
    "ÖDP": "#ff6400",
    "ÖDP / Familie ..": "#ff6400",
    "Die PARTEI": "#b5152b",
    "PBC": "#d2b829",
    "PdF": "#f5a612",
    "PDV": "#002366",
    "PARTEI DER VERNUNFT": "#002366",
    "PIRATEN": "#ff820a",
    "Plus": "#792D8F",
    "pro Deutschland": "#096594",
    "PRO NRW": "#005ea8",
    "PSG": "#B70E0C",
    "DIE RECHTE": "#80512f",
    "RENTNER": "#fe6500",
    "REP": "#0075BE",
    "SGP": "#B70E0C",
    "SGV": "#292d77",
    "SPD": "#E3000F",
    "SSW": "#003c8f",
    "TIERSCHUTZ hier!": "#45ad4c",
    "Tierschutzallianz": "#3d449a",
    "Tierschutzpartei": "#006D77",
    "Team Todenhöfer": "#20274d",
    "UNABHÄNGIGE": "#ff9900",
    "du.": "#ff9700",
    "Die Urbane.": "#ff9700",
    "V-Partei³": "#a1bf14",
    "DIE VIOLETTEN": "#621c75",
    "Volksabstimmung": "#757575",
    "Volt": "#562883",
    "WIR": "#496164",
    "WiR2020": "#496164",
    "WU": "#0A3C5B",
    "Z.": "#005a62",
    "ZENTRUM": "#0000CD",
}
color_dict = defaultdict(lambda: "#777777", _colors)