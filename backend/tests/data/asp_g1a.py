DEF_AP_C = """
defense_combo(6, 5, "AP", event("GM"), team("COL")).
defense_combo(15, 8, "AP", team("CHI"), team("CHI")).
defense_combo(50, 2, "AP", event("COM"), event("COM")).
defense_combo(51, 2, "AP", team("SEA"), team("EDM")).
defense_combo(52, 2, "AP", team("WPG"), team("CHI")).
defense_combo(53, 2, "AP", team("UTA"), team("VGK")).
defense_combo(54, 2, "AP", team("CBJ"), team("FLA")).
defense_combo(55, 2, "AP", event("XP"), team("DET")).
defense_combo(56, 2, "AP", team("CAR"), team("NJD")).
defense_combo(57, 4, "AP", team("MTL"), team("BOS")).
defense_combo(58, 4, "AP", team("OTT"), team("NY")).
defense_combo(59, 4, "AP", team("SEA"), team("TOR")).
defense_combo(60, 4, "AP", team("MTL"), team("OTT")).
"""

DEF_SAL_C = """
defense_combo(3, 6, "SAL", team("DET"), event("GM")).
defense_combo(13, 10, "SAL", nationality("CZECHIA"), team("VAN")).
defense_combo(14, 6, "SAL", team("CHI"), team("CHI")).
defense_combo(16, 10, "SAL", team("NYR"), team("NYR")).
defense_combo(28, 6, "SAL", team("STL"), team("STL")).
defense_combo(29, 6, "SAL", team("CGY"), team("CGY")).
defense_combo(30, 6, "SAL", team("CAR"), team("CAR")).
defense_combo(31, 10, "SAL", nationality("USA"), nationality("CANADA")).
defense_combo(32, 15, "SAL", event("FANT"), event("FANT")).
defense_combo(33, 5, "SAL", team("NSH"), team("DAL")).
defense_combo(34, 6, "SAL", team("LAK"), team("ANA")).
defense_combo(35, 5, "SAL", team("WSH"), team("PHI")).
defense_combo(36, 5, "SAL", event("FANT"), team("TOR")).
defense_combo(37, 10, "SAL", event("FANT"), team("MTL")).
defense_combo(38, 5, "SAL", event("FANT"), team("DET")).
defense_combo(39, 6, "SAL", event("TOTW"), event("TOTW")).
defense_combo(40, 5, "SAL", team("NYR"), team("NYI")).
defense_combo(41, 6, "SAL", team("TBL"), event("HH")).
defense_combo(42, 5, "SAL", team("TBL"), team("MTL")).
defense_combo(43, 5, "SAL", nationality("CZECHIA"), team("VAN")).
defense_combo(44, 7, "SAL", team("STL"), event("CAP")).
defense_combo(45, 7, "SAL", team("EVT"), event("NG")).
defense_combo(46, 6, "SAL", team("NY"), team("BOS")).
defense_combo(47, 6, "SAL", team("VAN"), team("TOR")).
defense_combo(48, 6, "SAL", team("OTT"), team("MIN")).
defense_combo(49, 6, "SAL", team("MTL"), team("MTL")).
"""

DEF_OVR_C = """
defense_combo(2, 1, "OVR", team("DAL"), event("HH")).
defense_combo(4, 1, "OVR", event("COM"), event("GM")).
defense_combo(5, 2, "OVR", event("GM"), team("DAL")).
defense_combo(7, 1, "OVR", event("ICON"), team("NYR")).
defense_combo(8, 2, "OVR", team("CGY"), event("SOTM")).
defense_combo(9, 1, "OVR", team("CGY"), team("NYR")).
defense_combo(10, 2, "OVR", team("MIN"), event("COM")).
defense_combo(11, 1, "OVR", team("VAN"), event("COM")).
defense_combo(12, 1, "OVR", event("NG"), nationality("CZECHIA")).
defense_combo(17, 1, "OVR", team("CAR"), team("PIT")).
defense_combo(18, 1, "OVR", event("TOTW"), event("SOTM")).
defense_combo(19, 1, "OVR", team("MIN"), team("CGY")).
defense_combo(20, 1, "OVR", team("OTT"), team("BUF")).
defense_combo(21, 1, "OVR", team("BOS"), event("NG")).
defense_combo(22, 1, "OVR", team("VAN"), nationality("FINLAND")).
defense_combo(23, 1, "OVR", event("ROOK"), event("HH")).
defense_combo(24, 1, "OVR", team("COL"), event("ICON")).
defense_combo(25, 1, "OVR", event("CAP"), team("SJS")).
defense_combo(26, 1, "OVR", team("MIN"), team("VAN")).
defense_combo(27, 1, "OVR", team("SEA"), team("MTL")).
defense_combo(61, 1, "OVR", team("STL"), team("STL")).
defense_combo(62, 1, "OVR", team("CGY"), team("CGY")).
defense_combo(63, 1, "OVR", team("MTL"), team("MTL")).
defense_combo(64, 1, "OVR", event("NG"), team("EVT")).
defense_combo(65, 1, "OVR", team("CAR"), event("NG")).
"""

FWD_AP_C = """
forward_combo(2, 5, "AP", team("MTL"), nationality("GERMANY"), team("TOR")).
forward_combo(14, 3, "AP", team("PHI"), team("PHI"), team("PHI")).
forward_combo(15, 3, "AP", team("WPG"), team("WPG"), team("WPG")).
forward_combo(16, 3, "AP", team("COL"), team("COL"), team("COL")).
forward_combo(17, 12, "AP", team("DET"), team("DET"), team("DET")).
forward_combo(33, 3, "AP", team("ANA"), team("ANA"), team("ANA")).
forward_combo(34, 3, "AP", team("BOS"), team("BOS"), team("BOS")).
forward_combo(35, 3, "AP", event("COM"), event("COM"), event("COM")).
forward_combo(36, 3, "AP", event("CAP"), team("UTA"), team("STL")).
forward_combo(37, 3, "AP", event("CAP"), team("TOR"), team("CGY")).
forward_combo(38, 3, "AP", team("UTA"), event("FANT"), team("CHI")).
forward_combo(39, 3, "AP", event("TOTW"), event("SOTM"), event("TOTW")).
forward_combo(40, 3, "AP", event("CAP"), team("OTT"), team("CBJ")).
forward_combo(41, 3, "AP", team("ANA"), event("SOTM"), team("LAK")).
forward_combo(42, 3, "AP", event("GB"), team("PIT"), team("CAR")).
forward_combo(43, 3, "AP", event("COM"), team("SJS"), nationality("CZECHIA")).
forward_combo(44, 3, "AP", team("DET"), team("MTL"), nationality("DENMARK")).
forward_combo(45, 3, "AP", team("TBL"), team("BUF"), event("CAP")).
forward_combo(46, 5, "AP", nationality("USA"), event("NG"), team("PIT")).
forward_combo(47, 6, "AP", team("NY"), team("MTL"), team("BOS")).
forward_combo(48, 6, "AP", team("MIN"), team("SEA"), team("VAN")).
forward_combo(49, 6, "AP", event("HH"), team("DET"), team("SEA")).
forward_combo(53, 1, "AP", event("HUTC"), team("MTL"), event("GB")).
"""

FWD_OVR_C = """
forward_combo(3, 2, "OVR", team("BOS"), event("GM"), team("OTT")).
forward_combo(4, 1, "OVR", team("TOR"), team("BOS"), team("MTL")).
forward_combo(6, 1, "OVR", event("GM"), team("NYR"), nationality("USA")).
forward_combo(7, 1, "OVR", team("OTT"), nationality("CANADA"), event("SOTM")).
forward_combo(8, 2, "OVR", nationality("GERMANY"), event("ICON"), team("DAL")).
forward_combo(9, 2, "OVR", team("TBL"), event("COM"), team("WSH")).
forward_combo(10, 1, "OVR", nationality("SWEDEN"), event("COM"), team("NSH")).
forward_combo(11, 1, "OVR", team("LAK"), team("SJS"), event("COM")).
forward_combo(12, 1, "OVR", event("COM"), team("SJS"), event("NG")).
forward_combo(18, 1, "OVR", event("CHEL"), event("CHEL"), event("CHEL")).
forward_combo(19, 1, "OVR", event("SPOT"), team("SJS"), event("ICON")).
forward_combo(50, 1, "OVR", team("TBL"), team("BUF"), team("DET")).
forward_combo(51, 1, "OVR", nationality("FINLAND"), event("NG"), team("NIA")).
forward_combo(52, 1, "OVR", team("STL"), event("NG"), nationality("CANADA")).
forward_combo(54, 1, "OVR", event("HH"), event("ICON"), event("FANT")).
forward_combo(55, 1, "OVR", event("NG"), team("PHI"), team("WSH")).
forward_combo(56, 1, "OVR", event("TOTW"), team("FLA"), team("NYI")).
forward_combo(57, 1, "OVR", team("DAL"), team("WPG"), event("NG")).
forward_combo(58, 1, "OVR", nationality("SWEDEN"), event("ROOK"), team("TOR")).
forward_combo(59, 1, "OVR", nationality("GERMANY"), event("XP"), team("EDM")).
forward_combo(60, 1, "OVR", team("EDM"), event("ICON"), event("ALUM")).
forward_combo(61, 1, "OVR", team("MTL"), team("TOR"), team("OTT")).
forward_combo(62, 1, "OVR", team("NY"), team("OTT"), team("VAN")).
"""

FWD_SAL_C = """
forward_combo(5, 6, "SAL", team("OTT"), nationality("USA"), team("BOS")).
forward_combo(13, 7, "SAL", nationality("SWEDEN"), nationality("SWEDEN"), nationality("SWEDEN")).
forward_combo(20, 6, "SAL", team("ANA"), team("ANA"), team("ANA")).
forward_combo(21, 6, "SAL", team("BOS"), team("BOS"), team("BOS")).
forward_combo(22, 7, "SAL", nationality("USA"), nationality("USA"), nationality("USA")).
forward_combo(23, 20, "SAL", event("FANT"), event("FANT"), event("FANT")).
forward_combo(24, 7, "SAL", event("CAP"), team("NJD"), team("PIT")).
forward_combo(25, 7, "SAL", team("EDM"), team("COL"), team("MIN")).
forward_combo(26, 5, "SAL", team("VAN"), team("SEA"), team("SJS")).
forward_combo(27, 6, "SAL", team("TOR"), team("OTT"), nationality("SLOVAKIA")).
forward_combo(28, 7, "SAL", team("NYR"), team("DET"), team("CHI")).
forward_combo(29, 9, "SAL", team("MTL"), team("NY"), team("MIN")).
forward_combo(30, 9, "SAL", team("BOS"), team("MIN"), team("OTT")).
forward_combo(31, 9, "SAL", team("TOR"), team("VAN"), team("MTL")).
forward_combo(32, 9, "SAL", event("CAP"), team("TOR"), team("SEA")).
"""