from io import BytesIO
from collections import defaultdict
import numpy as np
import re
from types import SimpleNamespace
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

def show_available_elections():
    for election in elections:
        print(f"{election}: {elections[election]["name"]:45s}", end="")
        http = urllib3.PoolManager()
        response = http.request("HEAD", elections[election]["file"])
        if response.status == 200:
            print("    (file found)")
        else:
            print("    (file NOT found)")


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
    
    election_file = elections[election]["file"]
    
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
    response = http.request('GET', "https://www.bpb.de/system/files/datei/Wahl-O-Mat_Bundestagswahl_2025_Datensatz_v1.02.zip")
    zip_file = zipfile.ZipFile(BytesIO(response.data))
    for f in zip_file.filelist:
        if f.filename.endswith(".txt"):
            file = f
    with zip_file.open(file, "r") as f:
        data.note = f.read().decode("unicode-escape")
    
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
                if int(m[-1])==1 and int(m[-2])==0:
                    parties.append(s[0])
                    
        # Statements
        if l.startswith("WOMT_aThesen["):
            m = re.findall(pat, l)
            if len(m) >= 3:
                s = re.findall(pat_s, l)
                if int(m[1])==0:
                    if int(m[2])==0:
                        statements.append(s[0])
                    elif int(m[2])==1:
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

elections = {

    # Europa
    "2024-06-09_eu": {
        "name": "Europawahl 2024",
        "file": "https://www.wahl-o-mat.de/europawahl2024/wahlomat.zip",
    },
    "2014-05-25_eu": {
        "name": "Europawahl 2014",
        "file": "https://archiv.wahl-o-mat.de/europawahl2014/wahlomat.zip",
    },
    "2009-06-07_eu": {
        "name": "Europawahl 2009",
        "file": "https://www.bpb.de/system/files/datei/wahlomat-eu2009.zip?download=1",
    },
    "2004-06-13_eu": {
        "name": "Europawahl 2009",
        "file": "http://www.wahl-o-mat.de/europa2004/wahlomat.zip",
    },

    # Bundestag
    "2025-02-23_de": {
        "name": "Bundestagswahl 2025",
        "file": "https://www.wahl-o-mat.de/bundestagswahl2025/wahlomat.zip",
    },
    "2021-09-26_de": {
        "name": "Bundestagswahl 2021",
        "file": "https://archiv.wahl-o-mat.de/bundestagswahl2021/wahlomat.zip",
    },
    "2017-09-24_de": {
        "name": "Bundestagswahl 2017",
        "file": "https://archiv.wahl-o-mat.de/bundestagswahl2017/wahlomat.zip",
    },
    "2013-09-22_de": {
        "name": "Bundestagswahl 2013",
        "file": "https://archiv.wahl-o-mat.de/bundestagswahl2013/wahlomat.zip",
    },
    "2009-09-27_de": {
        "name": "Bundestagswahl 2009",
        "file": "http://www.wahl-o-mat.de/bundestagswahl2009/wahlomat.zip",
    },
    "2005-09-18_de": {
        "name": "Bundestagswahl 2005",
        "file": "http://www.wahl-o-mat.de/bundestagswahl2005/wahlomat.zip",
    },

    # Baden-Württemberg
    "2026-03-08_bw": {
        "name": "Landtagswahl in Baden-Württemberg 2026",
        "file": "https://www.wahl-o-mat.de/bw2026/wahlomat.zip",
    },
    "2021-03-14_bw": {
        "name": "Landtagswahl in Baden-Württemberg 2021",
        "file": "https://archiv.wahl-o-mat.de/bw2021/wahlomat.zip",
    },
    "2016-03-13_bw": {
        "name": "Landtagswahl in Baden-Württemberg 2016",
        "file": "https://archiv.wahl-o-mat.de/bw2016/wahlomat.zip",
    },
    "2011-03-27_bw": {
        "name": "Landtagswahl in Baden-Württemberg 2011",
        "file": "https://www.bpb.de/system/files/datei/wahlomat-bw11.zip?download=1",
    },
    "2006-03-26_bw": {
        "name": "Landtagswahl in Baden-Württemberg 2006",
        "file": "http://www.wahl-o-mat.de/bw2006/wahlomat.zip",
    },

    # Bayern
    "2023-10-08_by": {
        "name": "Landtagswahl in Bayern 2023",
        "file": "https://archiv.wahl-o-mat.de/bayern2023/wahlomat.zip",
    },
    "2018-10-14_by": {
        "name": "Landtagswahl in Bayern 2018",
        "file": "https://archiv.wahl-o-mat.de/bayern2018/wahlomat.zip",
    },
    "2013-09-15_by": {
        "name": "Landtagswahl in Bayern 2013",
        "file": "https://archiv.wahl-o-mat.de/bayern2013/wahlomat.zip",
    },
    "2003-09-21_by": {
        "name": "Landtagswahl in Bayern 2003",
        "file": "http://www.wahl-o-mat.de/bayern2003/wahlomat.zip",
    },

    # Berlin
    "2023-02-12_be": {
        "name": "Wahl zum Abgeordnetenhaus von Berlin 2023",
        "file": "https://archiv.wahl-o-mat.de/berlin2023/wahlomat.zip",
    },
    "2021-09-26_be": {
        "name": "Wahl zum Abgeordnetenhaus von Berlin 2021",
        "file": "https://archiv.wahl-o-mat.de/berlin2021/wahlomat.zip",
    },
    "2016-09-18_be": {
        "name": "Wahl zum Abgeordnetenhaus von Berlin 2016",
        "file": "https://archiv.wahl-o-mat.de/berlin2016/wahlomat.zip",
    },
    "2011-09-18_be": {
        "name": "Wahl zum Abgeordnetenhaus von Berlin 2011",
        "file": "https://archiv.wahl-o-mat.de/berlin2011/wahlomat.zip",
    },
    "2006-09-17_be": {
        "name": "Wahl zum Abgeordnetenhaus von Berlin 2006",
        "file": "https://archiv.wahl-o-mat.de/berlin2006/wahlomat.zip",
    },

    # Brandenburg
    "2024-09-22_bb": {
        "name": "Landtagswahl in Brandenburg 2024",
        "file": "https://archiv.wahl-o-mat.de/brandenburg2024/wahlomat.zip",
    },
    "2019-09-01_bb": {
        "name": "Landtagswahl in Brandenburg 2019",
        "file": "https://archiv.wahl-o-mat.de/brandenburg2019/wahlomat.zip",
    },
    "2014-09-14_bb": {
        "name": "Landtagswahl in Brandenburg 2014",
        "file": "https://archiv.wahl-o-mat.de/brandenburg2014/wahlomat.zip",
    },

    # Bremen
    "2023-05-14_hb": {
        "name": "Bürgerschaftswahl in Bremen 2023",
        "file": "https://www.wahl-o-mat.de/bremen2023/wahlomat.zip",
    },
    "2019-05-26_hb": {
        "name": "Bürgerschaftswahl in Bremen 2019",
        "file": "https://www.wahl-o-mat.de/bremen2019/wahlomat.zip",
    },
    "2015-05-10_hb": {
        "name": "Bürgerschaftswahl in Bremen 2015",
        "file": "https://www.wahl-o-mat.de/bremen2015/wahlomat.zip",
    },
    "2011-05-22_hb": {
        "name": "Bürgerschaftswahl in Bremen 2011",
        "file": "https://www.wahl-o-mat.de/bremen2011/wahlomat.zip",
    },
    "2007-05-13_hb": {
        "name": "Bürgerschaftswahl in Bremen 2007",
        "file": "https://www.wahl-o-mat.de/bremen2007/wahlomat.zip",
    },

    # Hamburg
    "2025-03-02_hh": {
        "name": "Bürgerschaftswahl in Hamburg 2025",
        "file": "https://www.wahl-o-mat.de/hamburg2025/wahlomat.zip",
    },
    "2020-02-23_hh": {
        "name": "Bürgerschaftswahl in Hamburg 2020",
        "file": "https://www.wahl-o-mat.de/hamburg2020/wahlomat.zip",
    },
    "2015-02-15_hh": {
        "name": "Bürgerschaftswahl in Hamburg 2015",
        "file": "https://www.wahl-o-mat.de/hamburg2015/wahlomat.zip",
    },
    "2011-02-20_hh": {
        "name": "Bürgerschaftswahl in Hamburg 2011",
        "file": "https://www.bpb.de/system/files/datei/wahlomat_0.zip?download=1",
    },
    "2008-02-24_hh": {
        "name": "Bürgerschaftswahl in Hamburg 2008",
        "file": "https://www.wahl-o-mat.de/hamburg2008/wahlomat.zip",
    },

    # Hessen
    "2023-10-08_he": {
        "name": "Landtagswahl in Hessen 2023",
        "file": "https://archiv.wahl-o-mat.de/hessen2023/wahlomat.zip",
    },
    "2018-10-28_he": {
        "name": "Landtagswahl in Hessen 2018",
        "file": "https://www.wahl-o-mat.de/hessen2018/wahlomat.zip",
    },
    
    # Mecklenburg-Vorpommern
    "2021-09-26_mv": {
        "name": "Landtagswahl in Mecklenburg-Vorpommern 2021",
        "file": "https://archiv.wahl-o-mat.de/mecklenburgvorpommern2021/wahlomat.zip",
    },

    # Niedersachsen
    "2022-10-09_ni": {
        "name": "Landtagswahl in Niedersachsen 2022",
        "file": "https://archiv.wahl-o-mat.de/niedersachsen2022/wahlomat.zip",
    },
    "2013-01-20_ni": {
        "name": "Landtagswahl in Niedersachsen 2013",
        "file": "http://www.wahl-o-mat.de/niedersachsen2013/wahlomat.zip",
    },
    "2008-01-27_ni": {
        "name": "Landtagswahl in Niedersachsen 2008",
        "file": "http://www.wahl-o-mat.de/niedersachsen2008/wahlomat.zip",
    },

    # Nordrhein-Westfalen
    "2022-05-15_nw": {
        "name": "Landtagswahl in Nordrhein-Westfalen 2022",
        "file": "https://archiv.wahl-o-mat.de/nordrheinwestfalen2022/wahlomat.zip",
    },
    "2017-05-14_nw": {
        "name": "Landtagswahl in Nordrhein-Westfalen 2017",
        "file": "https://archiv.wahl-o-mat.de/nrw2017/wahlomat.zip",
    },
    "2012-05-13_nw": {
        "name": "Landtagswahl in Nordrhein-Westfalen 2012",
        "file": "https://www.bpb.de/system/files/datei/wahlomat-nordrheinwestfalen-2012.zip?download=1",
    },
    "2010-05-09_nw": {
        "name": "Landtagswahl in Nordrhein-Westfalen 2010",
        "file": "http://www.wahl-o-mat.de/nrw2010/wahlomat.zip",
    },
    "2005-05-22_nw": {
        "name": "Landtagswahl in Nordrhein-Westfalen 2005",
        "file": "http://www.wahl-o-mat.de/nrw2005/wahlomat.zip",
    },

    # Rheinland-Pfalz
    "2021-03-14_rp": {
        "name": "Landtagswahl ion Rheinland-Pfalz 2021",
        "file": "http://www.wahl-o-mat.de/rlp2021/wahlomat.zip",
    },
    "2016-03-13_rp": {
        "name": "Landtagswahl ion Rheinland-Pfalz 2016",
        "file": "https://archiv.wahl-o-mat.de/rlp2016/wahlomat.zip",
    },
    "2011-03-27_rp": {
        "name": "Landtagswahl ion Rheinland-Pfalz 2011",
        "file": "https://www.bpb.de/system/files/datei/wahlomat-rlp11.zip?download=1",
    },
    "2006-03-26_rp": {
        "name": "Landtagswahl ion Rheinland-Pfalz 2006",
        "file": "http://www.wahl-o-mat.de/rlp2006/wahlomat.zip",
    },

    # Saarland
    "2022-03-27_sl": {
        "name": "Landtagswahl im Saarland 2022",
        "file": "https://archiv.wahl-o-mat.de/saarland2022/wahlomat.zip",
    },
    "2017-03-26_sl": {
        "name": "Landtagswahl im Saarland 2017",
        "file": "https://archiv.wahl-o-mat.de/saarland2017/wahlomat.zip",
    },
    "2012-03-25_sl": {
        "name": "Landtagswahl im Saarland 2012",
        "file": "https://www.bpb.de/system/files/datei/wahlomat-saarland-2012.zip?download=1",
    },
    "2004-09-05_sl": {
        "name": "Landtagswahl im Saarland 2004",
        "file": "http://www.wahl-o-mat.de/saarland2004/wahlomat.zip",
    },
    
    # Sachsen
    "2024-09-01_sn": {
        "name": "Landtagswahl in Sachsen 2024",
        "file": "https://www.wahl-o-mat.de/sachsen2024/wahlomat.zip",
    },
    "2019-09-01_sn": {
        "name": "Landtagswahl in Sachsen 2019",
        "file": "https://www.wahl-o-mat.de/sachsen2019/wahlomat.zip",
    },
    "2014-08-31_sn": {
        "name": "Landtagswahl in Sachsen 2014",
        "file": "https://archiv.wahl-o-mat.de/sachsen2014/wahlomat.zip",
    },
    "2004-09-19_sn": {
        "name": "Landtagswahl in Sachsen 2004",
        "file": "http://www.wahl-o-mat.de/sachsen2004/wahlomat.zip",
    },

    # Sachsen-Anhalt
    "2021-06-06_st": {
        "name": "Landtagswahl in Sachsen-Anhalt 2021",
        "file": "https://archiv.wahl-o-mat.de/sachsenanhalt2021/wahlomat.zip",
    },
    "2016-03-13_st": {
        "name": "Landtagswahl in Sachsen-Anhalt 2016",
        "file": "https://archiv.wahl-o-mat.de/sachsenanhalt2016/wahlomat.zip",
    },
    "2006-03-23_st": {
        "name": "Landtagswahl in Sachsen-Anhalt 2006",
        "file": "http://www.wahl-o-mat.de/sachsenanhalt2006/wahlomat.zip",
    },

    # Schleswig-Holstein
    "2022-05-08_sh": {
        "name": "Landtagswahl in Schlweswig-Holstein 2022",
        "file": "https://archiv.wahl-o-mat.de/schleswigholstein2022/wahlomat.zip",
    },
    "2017-05-07_sh": {
        "name": "Landtagswahl in Schleswig-Holstein 2017",
        "file": "https://archiv.wahl-o-mat.de/schleswigholstein2017/wahlomat.zip",
    },
    "2012-05-06_sh": {
        "name": "Landtagswahl in Schleswig-Holstein 2012",
        "file": "https://www.bpb.de/system/files/datei/wahlomat-schleswigholstein-2012.zip?download=1",
    },
    "2005-02-21_sh": {
        "name": "Landtagswahl in Schleswig-Holstein 2005",
        "file": "http://www.wahl-o-mat.de/schleswigholstein2005/wahlomat.zip",
    },
    
    # Thüringen
    "2024-09-01_th": {
        "name": "Landtagswahl in Thüringen 2024",
        "file": "https://www.wahl-o-mat.de/thueringen2024/wahlomat.zip",
    },
    "2019-10-27_th": {
        "name": "Landtagswahl in Thüringen 2019",
        "file": "https://archiv.wahl-o-mat.de/thueringen2019/wahlomat.zip",
    },
    "2014-09-14_th": {
        "name": "Landtagswahl in Thüringen 2014",
        "file": "https://archiv.wahl-o-mat.de/thueringen2014/wahlomat.zip",
    },

}

_colors = {
    "III. Weg": "#1d542c",
    "50Plus": "#0A6DAB",
    "ABG": "#7F2982",
    "AfD": "#009ee0",
    "ALFA": "#0066ff",
    "Allianz Deutscher Demokraten": "#1e5ea5",
    "AD-Demokraten": "#1e5ea5",
    "AD-Demokraten NRW": "#1e5ea5",
    "ADM": "#285FBD",
    "ADPM": "#3B9FE2",
    "APPD": "#33302B",
    "AUF": "#B4EEB4",
    "AUFBRUCH C": "#1B779C",
    "B": "#019889",
    "B*": "#019889",
    "dieBasis": "#4d4c4d",
    "BGD": "#EDB800",
    "BGE": "#0C8AA8",
    "BIG": "#ed8045",
    "Bildet Berlin!": "#ffe800",
    "BIW": "#005ab0",
    "Blaue *raute*TeamPetry": "#25378f",
    "Blaue *raute*TeamPetry Thüringen": "#25378f",
    "BP": "#7FFFFF",
    "BSW": "#7d254f",
    "bunt.saar": "#f49800",
    "BÜNDNIS21": "#e81972",
    "Bündnis 21/RRP": "#ff6a1a",
    "Bündnis C": "#0872ba",
    "BÜNDNIS DEUTSCHLAND": "#a2bbf3",
    "BÜRGERBEWEGUNG": "#f07e18",
    "Bü-Mi": "#008800",
    "BüSo": "#1f4569",
    "CDU": "#000000",
    "CDU/CSU": "#000000",
    "CDU / CSU": "#000000",
    "CSU": "#000000",
    "CM": "#029de7",
    "DAVA": "#068E91",
    "DAVA-Hamburg": "#068E91",
    "DBD": "#FF5706",
    "ddp": "#FFA614",
    "Deutsche Konservative": "#006DA8",
    "DiB": "#854d68",
    "DIE DIREKTE!": "#ffc000",
    "DKP": "#ed1c24",
    "DLW": "#227172",
    "DM": "#284f8d",
    "DSP": "#a1b45a",
    "DSU": "#00B2EE",
    "DVU": "#AA4422",
    "Eine für Alle - Partei": "#00858C",
    "EDE": "#7CC03A",
    "DIE EINHEIT": "#f8a501",
    "FAMILIE": "#ff6600",
    "FBI": "#63B8FF",
    "FBI/FWG": "#63B8FF",
    "FBI Freie Wähler": "#63B8FF",
    "FBI/Freie Wähler": "#63B8FF",
    "FBM": "#ff9b30",
    "FDP": "#ffff00",
    "FPA": "#8AE5CC",
    "DIE FRANKEN": "#9c2020",
    "DIE FRAUEN": "#FF83FA",
    "FRAUENLISTE": "#f22179",
    "FREiER HORIZONT": "#0080BB",
    "Freie Union": "#EEA500",
    "FWD": "#FF8000",
    "FW FREIE WÄHLER": "#FF8000",
    "FREIE WÄHLER": "#FF8000",
    "Freie W&auml;hler Bayern": "#FF8000",
    "FREIE WÄHLER BREMEN": "#FF8000",
    "BVB / FREIE WÄHLER": "#FF8000",
    "FREIE SACHSEN": "#20B2AA",
    "DIE FREIHEIT": "#2564AD",
    "DIE FREIHEIT Niedersachsen": "#2564AD",
    "Gesundheitsforschung": "#6A9683",
    "GFA": "#339900",
    "Die Grauen": "#9e9e9e",
    "Graue Panther": "#6b6b6b",
    "GRÜNE": "#46962b",
    "GRÜNE/B 90": "#46962b",
    "GRÜNE/GAL": "#46962b",
    "Bündnis 90/Die Grünen": "#46962b",
    "BÜNDNIS 90/DIE GRÜNEN": "#46962b",
    "B&uuml;ndnis 90/Die Gr&uuml;nen": "#46962b",
    "Die Grünen": "#46962b",
    "HEIMAT": "#d79e2a",
    "PdH": "#2191BD",
    "Die Humanisten": "#2191BD",
    "Die Humanisten Niedersachsen": "#2191BD",
    "JED": "#CD0000",
    "KLIMALISTE": "#5cc14c",
    "Klimaliste Berlin": "#5cc14c",
    "KlimalisteBW": "#5cc14c",
    "Klimaliste RLP e. V.": "#5cc14c",
    "Klimaliste ST": "#5cc14c",
    "KLIMALISTE WÄHLERLISTE": "#5cc14c",
    "KPD": "#8B0000",
    "LETZTE GENERATION": "#FF4C00",
    "LfK": "#d2175e",
    "Liberale": "#00758C",
    "LIEBE": "#db3028",
    "Die Linke": "#BE3075",
    "DIE LINKE": "#BE3075",
    "DIE LINKE.": "#BE3075",
    "DIE LINKE.PDS": "#8B1C62",
    "LKR": "#f39200",
    "REFORMER": "#f39200",
    "MENSCHLICHE WELT": "#f26f22",
    "MERA25": "#f15a32",
    "MIETERPARTEI": "#002b83",
    "MLPD": "#ed1c24",
    "MUD": "#1D85C4",
    "mut": "#00CCCC",
    "neo": "#a5d839",
    "Die neuen Demokraten": "#0aa9ab",
    "Neue Demokraten": "#0aa9ab",
    "DIE NEUE MITTE": "#F6A424",
    "Partei der Nichtwähler": "#ea6a09",
    "NPD": "#8b4726",
    "ödp": "#ff6400",
    "ÖDP": "#ff6400",
    "ÖDP / Familie ..": "#ff6400",
    "Die PARTEI": "#b5152b",
    "Die PARTEI ": "#b5152b",
    "PBC": "#d2b829",
    "PdF": "#f5a612",
    "PDS": "#8B1C62",
    "PDV": "#002366",
    "PARTEI DER VERNUNFT": "#002366",
    "Partei der Vernunft": "#002366",
    "PIRATEN": "#ff820a",
    "PIRATEN ": "#ff820a",
    "Plus": "#792D8F",
    "pro Deutschland": "#096594",
    "PRO NRW": "#005ea8",
    "pro NRW": "#005ea8",
    "PSG": "#B70E0C",
    "DIE RECHTE": "#80512f",
    "RENTNER": "#fe6500",
    "REP": "#0075BE",
    "RRP": "#FF6A1A",
    "Schöner Leben": "#57FFD1",
    "SGP": "#B70E0C",
    "SGV": "#292d77",
    "SPD": "#E3000F",
    "SSW": "#003c8f",
    "TIERSCHUTZ hier!": "#45ad4c",
    "TIERSCHUTZ hier! Hamburg": "#45ad4c",
    "TIERSCHUTZliste": "#45ad4c",
    "Tierschutzallianz": "#3d449a",
    "Die Tierschutzpartei": "#006D77",
    "Tierschutzpartei": "#006D77",
    "Team Todenhöfer": "#20274d",
    "Die Gerechtigkeitspartei - Team Todenhöfer": "#20274d",
    "UNABHÄNGIGE": "#ff9900",
    "du.": "#ff9700",
    "Die Urbane.": "#ff9700",
    "V-Partei³": "#a1bf14",
    "Verfüngungsforschung": "#6A9683",
    "Verjüngungsforschung": "#6A9683",
    "Partei für schulmedizinische Verjüngungsforschung": "#6A9683",
    "DIE VIOLETTEN": "#621c75",
    "Volksabstimmung": "#757575",
    "Volt": "#562883",
    "Volt ": "#562883",
    "Volt Hamburg": "#562883",
    "WASG": "#DE2922",
    "WerteUnion": "#0A3C5B",
    "WIR": "#496164",
    "W2020": "#496164",
    "DieWahl - WFG": "#9C4A85",
    "WiR2020": "#496164",
    "WU": "#0A3C5B",
    "Z.": "#005a62",
    "Z.SH": "#16748F",
    "ZENTRUM": "#0000CD",
}
color_dict = defaultdict(lambda: "#777777", _colors)