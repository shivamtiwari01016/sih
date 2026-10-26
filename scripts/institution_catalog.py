"""Curated institution catalog used by the demo importer/seeder.

Contents
--------
* All 23 Indian Institutes of Technology (IITs).
* A broad, curated set of real universities, engineering colleges,
  polytechnics and management institutes across Maharashtra districts.

This is a representative demo catalog, not the official AICTE register. The
``aicte_permanent_id`` column is intentionally left blank for these rows
because AICTE permanent IDs must come from the official source data; inventing
them would create misleading records. Websites are included only where the
public domain is well established.

Run ``python3 scripts/import_institution_catalog.py`` to add missing rows
without deleting institutions or complaints already in the database.
"""

MAHARASHTRA = "Maharashtra"


def _maharashtra(
    name,
    city,
    district,
    institution_type,
    affiliation,
    established_year,
    ownership,
    website=None,
    address=None,
):
    return {
        "institution_name": name,
        "institution_type": institution_type,
        "address": address or f"{city}, {district} district, Maharashtra, India",
        "city": city,
        "state": MAHARASHTRA,
        "region": "West",
        "district": district,
        "website": website,
        "established_year": established_year,
        "ownership": ownership,
        "affiliation": affiliation,
    }


def _iit(name, city, district, state, region, year, website, address):
    return {
        "institution_name": name,
        "institution_type": "Engineering",
        "address": address,
        "city": city,
        "state": state,
        "region": region,
        "district": district,
        "website": website,
        "established_year": year,
        "ownership": "Government",
        "affiliation": "Institute of National Importance (Autonomous)",
    }


IITS = [
    _iit("Indian Institute of Technology Bombay", "Mumbai", "Mumbai Suburban", MAHARASHTRA, "West", 1958, "https://www.iitb.ac.in", "IIT Bombay, Powai, Mumbai 400076"),
    _iit("Indian Institute of Technology Delhi", "New Delhi", "New Delhi", "Delhi", "North", 1961, "https://home.iitd.ac.in", "Hauz Khas, New Delhi 110016"),
    _iit("Indian Institute of Technology Kanpur", "Kanpur", "Kanpur Nagar", "Uttar Pradesh", "North", 1959, "https://www.iitk.ac.in", "Kalyanpur, Kanpur 208016"),
    _iit("Indian Institute of Technology Kharagpur", "Kharagpur", "Paschim Medinipur", "West Bengal", "East", 1951, "https://www.iitkgp.ac.in", "IIT Kharagpur, Kharagpur 721302"),
    _iit("Indian Institute of Technology Madras", "Chennai", "Chennai", "Tamil Nadu", "South", 1959, "https://www.iitm.ac.in", "IIT Post Office, Chennai 600036"),
    _iit("Indian Institute of Technology Roorkee", "Roorkee", "Haridwar", "Uttarakhand", "North", 1847, "https://www.iitr.ac.in", "Roorkee 247667"),
    _iit("Indian Institute of Technology Guwahati", "Guwahati", "Kamrup", "Assam", "Northeast", 1994, "https://www.iitg.ac.in", "Amingaon, Guwahati 781039"),
    _iit("Indian Institute of Technology Hyderabad", "Sangareddy", "Sangareddy", "Telangana", "South", 2008, "https://www.iith.ac.in", "Kandi, Sangareddy 502285"),
    _iit("Indian Institute of Technology Gandhinagar", "Gandhinagar", "Gandhinagar", "Gujarat", "West", 2008, "https://www.iitgn.ac.in", "Palaj, Gandhinagar 382355"),
    _iit("Indian Institute of Technology Ropar", "Rupnagar", "Rupnagar", "Punjab", "North", 2008, "https://www.iitrpr.ac.in", "Birla Farms, Rupnagar 140001"),
    _iit("Indian Institute of Technology Bhubaneswar", "Bhubaneswar", "Khordha", "Odisha", "East", 2008, "https://www.iitbbs.ac.in", "Argul, Jatni, Bhubaneswar 752050"),
    _iit("Indian Institute of Technology Patna", "Bihta", "Patna", "Bihar", "East", 2008, "https://www.iitp.ac.in", "Bihta, Patna 801106"),
    _iit("Indian Institute of Technology Jodhpur", "Jodhpur", "Jodhpur", "Rajasthan", "North", 2008, "https://www.iitj.ac.in", "Karwar, Jodhpur 342030"),
    _iit("Indian Institute of Technology Mandi", "Kamand", "Mandi", "Himachal Pradesh", "North", 2009, "https://www.iitmandi.ac.in", "Kamand, Mandi 175005"),
    _iit("Indian Institute of Technology Indore", "Indore", "Indore", "Madhya Pradesh", "Central", 2009, "https://www.iiti.ac.in", "Khandwa Road, Simrol, Indore 453552"),
    _iit("Indian Institute of Technology (BHU) Varanasi", "Varanasi", "Varanasi", "Uttar Pradesh", "North", 1919, "https://www.iitbhu.ac.in", "Banaras Hindu University Campus, Varanasi 221005"),
    _iit("Indian Institute of Technology Palakkad", "Palakkad", "Palakkad", "Kerala", "South", 2015, "https://www.iitpkd.ac.in", "Ahalia Integrated Campus, Kozhippara, Palakkad 678557"),
    _iit("Indian Institute of Technology Tirupati", "Tirupati", "Tirupati", "Andhra Pradesh", "South", 2015, "https://www.iittp.ac.in", "Yerpedu, Tirupati 517619"),
    _iit("Indian Institute of Technology (ISM) Dhanbad", "Dhanbad", "Dhanbad", "Jharkhand", "East", 1926, "https://www.iitism.ac.in", "Sardar Patel Nagar, Dhanbad 826004"),
    _iit("Indian Institute of Technology Bhilai", "Bhilai", "Durg", "Chhattisgarh", "Central", 2016, "https://www.iitbhilai.ac.in", "Transit Campus, Government Engineering College, Sejbahar, Raipur 492015"),
    _iit("Indian Institute of Technology Goa", "Ponda", "South Goa", "Goa", "West", 2016, "https://www.iitgoa.ac.in", "Farmagudi, Ponda 403401"),
    _iit("Indian Institute of Technology Jammu", "Jammu", "Jammu", "Jammu and Kashmir", "North", 2016, "https://www.iitjammu.ac.in", "Jagti, Nagrota, Jammu 181221"),
    _iit("Indian Institute of Technology Dharwad", "Dharwad", "Dharwad", "Karnataka", "South", 2016, "https://www.iitdh.ac.in", "WALMI Campus, PB Road, Dharwad 580011"),
]


MAHARASHTRA_INSTITUTIONS = [
    # Mumbai city and Mumbai suburban
    _maharashtra("University of Mumbai", "Mumbai", "Mumbai City", "University", "State University", 1857, "Government", "https://mu.ac.in", "Fort Campus, Mahatma Gandhi Road, Mumbai 400032"),
    _maharashtra("Institute of Chemical Technology", "Mumbai", "Mumbai City", "Deemed University", "Deemed University (Autonomous)", 1933, "Government", "https://www.ictmumbai.edu.in", "Nathalal Parekh Marg, Matunga, Mumbai 400019"),
    _maharashtra("Veermata Jijabai Technological Institute", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai (Autonomous)", 1887, "Government", "https://www.vjti.ac.in", "H. R. Mahajani Road, Matunga, Mumbai 400019"),
    _maharashtra("Sardar Patel College of Engineering", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai (Autonomous)", 1962, "Government-aided", "https://www.spce.ac.in", "Bhavan's Campus, Munshi Nagar, Andheri West, Mumbai 400058"),
    _maharashtra("Dwarkadas J. Sanghvi College of Engineering", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai", 1994, "Private", "https://www.djsce.ac.in", "No. U-15, J.V.P.D. Scheme, Vile Parle West, Mumbai 400056"),
    _maharashtra("K. J. Somaiya College of Engineering", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai (Autonomous)", 1983, "Private", "https://kjsce.somaiya.edu", "Vidyanagar, Vidyavihar, Mumbai 400077"),
    _maharashtra("Thadomal Shahani Engineering College", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai", 1983, "Private", "https://www.tsec.edu", "P. G. Kher Marg, TPS III, Bandra West, Mumbai 400050"),
    _maharashtra("Fr. Conceicao Rodrigues College of Engineering", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai", 1984, "Private", "https://www.frcrce.ac.in", "Father Agnel Ashram, Bandstand, Bandra West, Mumbai 400050"),
    _maharashtra("Xavier Institute of Engineering", "Mumbai", "Mumbai City", "Engineering", "University of Mumbai", 2005, "Private", "https://www.xavierengg.com", "Mahim Causeway, Mahim West, Mumbai 400016"),
    _maharashtra("Shah and Anchor Kutchhi Engineering College", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai", 1985, "Private", "https://www.sakec.ac.in", "Mahavir Education Trust Chowk, Chembur, Mumbai 400088"),
    _maharashtra("Vidyalankar Institute of Technology", "Mumbai", "Mumbai City", "Engineering", "University of Mumbai", 1999, "Private", "https://www.vit.edu.in", "Vidyalankar Campus, Wadala East, Mumbai 400037"),
    _maharashtra("Vivekanand Education Society's Institute of Technology", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai", 1984, "Private", "https://vesit.ves.ac.in", "Hashu Advani Memorial Complex, Collector's Colony, Chembur, Mumbai 400074"),
    _maharashtra("St. Francis Institute of Technology", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai", 1996, "Private", "https://www.sfit.ac.in", "Mount Poinsur, S.V.P. Road, Borivali West, Mumbai 400103"),
    _maharashtra("Don Bosco Institute of Technology", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai", 2001, "Private", "https://www.dbit.in", "Premier Automobiles Road, Kurla West, Mumbai 400070"),
    _maharashtra("Thakur College of Engineering and Technology", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai (Autonomous)", 2001, "Private", "https://www.tcetmumbai.in", "A-Block, Thakur Educational Campus, Shyamnarayan Thakur Marg, Kandivali East, Mumbai 400101"),
    _maharashtra("Atharva College of Engineering", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai", 1999, "Private", "https://www.atharva.edu.in", "Malad-Marve Road, Charkop Naka, Malad West, Mumbai 400095"),
    _maharashtra("Rizvi College of Engineering", "Mumbai", "Mumbai Suburban", "Engineering", "University of Mumbai", 1998, "Private", "https://www.rizvicoe.org", "New Rizvi Educational Complex, Off Carter Road, Bandra West, Mumbai 400050"),
    _maharashtra("M. H. Saboo Siddik College of Engineering", "Mumbai", "Mumbai City", "Engineering", "University of Mumbai", 1984, "Private", None, "8, Saboo Siddik Polytechnic Road, Byculla, Mumbai 400008"),
    _maharashtra("Government Polytechnic Mumbai", "Mumbai", "Mumbai Suburban", "Polytechnic", "Maharashtra State Board of Technical Education", 1948, "Government", "https://gpmumbai.ac.in", "49, Ali Yavar Jung Marg, Kherwadi, Bandra East, Mumbai 400051"),
    _maharashtra("Narsee Monjee Institute of Management Studies", "Mumbai", "Mumbai Suburban", "Deemed University", "Deemed University", 1981, "Private", "https://www.nmims.edu", "V. L. Mehta Road, Vile Parle West, Mumbai 400056"),
    _maharashtra("S. P. Jain Institute of Management and Research", "Mumbai", "Mumbai Suburban", "Management", "Autonomous (AICTE approved)", 1981, "Private", "https://www.spjimr.org", "Bhavan's Campus, Munshi Nagar, Andheri West, Mumbai 400058"),
    _maharashtra("Jamnalal Bajaj Institute of Management Studies", "Mumbai", "Mumbai City", "Management", "University of Mumbai", 1965, "Government-aided", "https://www.jbims.edu", "Dadabhai Naoroji Road, Churchgate, Mumbai 400020"),
    _maharashtra("Welingkar Institute of Management Development and Research", "Mumbai", "Mumbai City", "Management", "Autonomous (AICTE approved)", 1977, "Private", "https://www.welingkar.org", "L. Napoo Road, Matunga, Mumbai 400019"),
    _maharashtra("SNDT Women's University", "Mumbai", "Mumbai City", "University", "State University", 1916, "Government", "https://sndt.ac.in", "1, Nathibai Thackersey Road, New Marine Lines, Mumbai 400020"),
    _maharashtra("Tata Institute of Social Sciences", "Mumbai", "Mumbai Suburban", "Deemed University", "Deemed University", 1936, "Government-aided", "https://www.tiss.edu", "V. N. Purav Marg, Deonar, Mumbai 400088"),
    _maharashtra("Government Law College", "Mumbai", "Mumbai City", "Other", "University of Mumbai", 1855, "Government", None, "A Road, Churchgate, Mumbai 400020"),
    _maharashtra("Indian Institute of Management Mumbai", "Mumbai", "Mumbai Suburban", "Management", "Institute of National Importance", 1963, "Government", "https://www.iimmumbai.ac.in", "Vihar Lake Road, Powai, Mumbai 400087"),

    # Thane, Palghar, Navi Mumbai and Raigad
    _maharashtra("Lokmanya Tilak College of Engineering", "Navi Mumbai", "Thane", "Engineering", "University of Mumbai", 1994, "Private", "https://www.ltce.in", "Sector 4, Koparkhairane, Navi Mumbai 400709"),
    _maharashtra("K. C. College of Engineering", "Thane", "Thane", "Engineering", "University of Mumbai", 2001, "Private", None, "Mith Bunder Road, Kopri, Thane East 400603"),
    _maharashtra("Smt. Indira Gandhi College of Engineering", "Navi Mumbai", "Thane", "Engineering", "University of Mumbai", 1994, "Private", None, "Sector 16, Ghansoli, Navi Mumbai 400701"),
    _maharashtra("Terna Engineering College", "Navi Mumbai", "Thane", "Engineering", "University of Mumbai", 1991, "Private", "https://www.terna.org", "Sector 22, Phase II, Nerul, Navi Mumbai 400706"),
    _maharashtra("Ramrao Adik Institute of Technology", "Navi Mumbai", "Thane", "Engineering", "University of Mumbai (Autonomous)", 1983, "Private", "https://www.rait.ac.in", "Sector 7, Phase I, Nerul, Navi Mumbai 400706"),
    _maharashtra("Datta Meghe College of Engineering", "Navi Mumbai", "Thane", "Engineering", "University of Mumbai", 1988, "Private", "https://www.dmce.ac.in", "Sector 3, Airoli, Navi Mumbai 400708"),
    _maharashtra("SIES Graduate School of Technology", "Navi Mumbai", "Thane", "Engineering", "University of Mumbai", 2002, "Private", "https://www.siesgst.edu.in", "Sri Chandrasekarendra Saraswati Vidyapuram, Sector V, Nerul, Navi Mumbai 400706"),
    _maharashtra("Bharati Vidyapeeth College of Engineering, Navi Mumbai", "Navi Mumbai", "Raigad", "Engineering", "Bharati Vidyapeeth Deemed University", 1990, "Private", "https://www.bvcoenm.edu.in", "Sector 7, Belpada, Kharghar, Navi Mumbai 410210"),
    _maharashtra("Pillai College of Engineering", "New Panvel", "Raigad", "Engineering", "University of Mumbai", 1996, "Private", "https://www.pce.ac.in", "Dr. K. M. Vasudevan Pillai Campus, Sector 16, New Panvel 410206"),
    _maharashtra("MGM College of Engineering and Technology", "Kamothe", "Raigad", "Engineering", "University of Mumbai", 2014, "Private", "https://mgm.edu.in", "MGM Educational Campus, Sector 1, Kamothe, Navi Mumbai 410209"),
    _maharashtra("Pillai HOC College of Engineering and Technology", "Rasayani", "Raigad", "Engineering", "University of Mumbai", 2011, "Private", "https://www.phcet.ac.in", "Pillai HOC Campus, Rasayani, Raigad 410207"),
    _maharashtra("St. John College of Engineering and Management", "Palghar", "Palghar", "Engineering", "University of Mumbai", 2009, "Private", "https://www.sjcem.edu.in", "St. John Technical Campus, Vevoor, Manor Road, Palghar 401404"),
    _maharashtra("Viva Institute of Technology", "Virar", "Palghar", "Engineering", "University of Mumbai", 2009, "Private", "https://www.viva-technology.org", "At. Shirgaon, Virar East, Palghar 401305"),

    # Pune
    _maharashtra("Savitribai Phule Pune University", "Pune", "Pune", "University", "State University", 1949, "Government", "https://www.unipune.ac.in", "Ganeshkhind, Pune 411007"),
    _maharashtra("College of Engineering, Pune", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University (Autonomous)", 1854, "Government", "https://www.coep.org.in", "Wellesley Road, Shivajinagar, Pune 411005"),
    _maharashtra("Pune Institute of Computer Technology", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University", 1983, "Private", "https://www.pict.edu", "Sr. No. 27, Dhankawadi, Pune 411043"),
    _maharashtra("Maharashtra Institute of Technology", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University", 1983, "Private", "https://mitwpu.edu.in", "S. No. 124, Paud Road, Kothrud, Pune 411038"),
    _maharashtra("Vishwakarma Institute of Technology", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University (Autonomous)", 1983, "Private", "https://www.vit.edu", "666, Upper Indiranagar, Bibwewadi, Pune 411037"),
    _maharashtra("Cummins College of Engineering for Women", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University (Autonomous)", 1991, "Private", "https://www.cumminscollege.in", "Karve Nagar, Pune 411052"),
    _maharashtra("PES Modern College of Engineering", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University", 1999, "Private", "https://www.moderncoe.edu.in", "1186, Shivajinagar, Pune 411005"),
    _maharashtra("Sinhgad College of Engineering", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University", 1996, "Private", "https://www.sinhgad.edu", "44/1, Vadgaon Budruk, Off Sinhgad Road, Pune 411041"),
    _maharashtra("Pimpri Chinchwad College of Engineering", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University (Autonomous)", 1999, "Private", "https://www.pccoepune.org", "Sector 26, Pradhikaran, Nigdi, Pune 411044"),
    _maharashtra("Symbiosis Institute of Technology", "Pune", "Pune", "Engineering", "Symbiosis International University", 2008, "Private", "https://www.sitpune.edu.in", "Symbiosis Knowledge Village, Lavale, Mulshi, Pune 412115"),
    _maharashtra("Bharati Vidyapeeth College of Engineering, Pune", "Pune", "Pune", "Engineering", "Bharati Vidyapeeth Deemed University", 1983, "Private", "https://www.bvcoepune.edu.in", "Sector 7, Dhankawadi, Pune 411043"),
    _maharashtra("Dr. D. Y. Patil College of Engineering", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University", 1983, "Private", "https://www.dypcoeakurdi.ac.in", "Sant Tukaram Nagar, Pimpri, Pune 411044"),
    _maharashtra("Army Institute of Technology", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University", 1994, "Private", "https://www.aitpune.com", "Dighi Hills, Alandi Road, Pune 411015"),
    _maharashtra("Vishwakarma Institute of Information Technology", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University", 2002, "Private", "https://www.viit.ac.in", "Survey No. 2/3/4, Kondhwa Budruk, Pune 411048"),
    _maharashtra("MIT Academy of Engineering", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University", 1999, "Private", "https://www.mitaoe.ac.in", "Dumbarwadi, Alandi Road, Pune 412105"),
    _maharashtra("Marathwada Mitra Mandal's College of Engineering", "Pune", "Pune", "Engineering", "Savitribai Phule Pune University", 1997, "Private", "https://www.mmcoe.edu.in", "Sr. No. 18, Plot No. 5/3, Karvenagar, Pune 411052"),
    _maharashtra("Fergusson College", "Pune", "Pune", "Other", "Savitribai Phule Pune University (Autonomous)", 1885, "Government-aided", "https://www.fergusson.edu", "F.C. Road, Shivajinagar, Pune 411004"),
    _maharashtra("Brihan Maharashtra College of Commerce", "Pune", "Pune", "Management", "Savitribai Phule Pune University", 1943, "Private-aided", "https://www.bmcc.ac.in", "845, Shivajinagar, Pune 411004"),
    _maharashtra("Symbiosis International University", "Pune", "Pune", "University", "Private University", 1971, "Private", "https://www.siu.edu.in", "Gram Lavale, Taluka Mulshi, Pune 412115"),
    _maharashtra("Indian Institute of Science Education and Research Pune", "Pune", "Pune", "Other", "Institute of National Importance", 2006, "Government", "https://www.iiserpune.ac.in", "Dr. Homi Bhabha Road, Pashan, Pune 411008"),
    _maharashtra("Film and Television Institute of India", "Pune", "Pune", "Other", "Autonomous (Ministry of Information and Broadcasting)", 1960, "Government", "https://www.ftii.ac.in", "Law College Road, Pune 411004"),
    _maharashtra("MIT World Peace University", "Pune", "Pune", "University", "Private University", 1983, "Private", "https://mitwpu.edu.in", "S. No. 124, Paud Road, Kothrud, Pune 411038"),
    _maharashtra("Deccan College Post-Graduate and Research Institute", "Pune", "Pune", "Deemed University", "Deemed University", 1821, "Government-aided", "https://www.deccancollegepune.ac.in", "Yerawada, Pune 411006"),
    _maharashtra("Gokhale Institute of Politics and Economics", "Pune", "Pune", "Deemed University", "Deemed University", 1930, "Government-aided", "https://www.gipe.ac.in", "846, BMCC Road, Deccan Gymkhana, Pune 411004"),
    _maharashtra("Symbiosis Institute of Business Management", "Pune", "Pune", "Management", "Symbiosis International University", 1978, "Private", "https://www.sibmpune.edu.in", "Symbiosis Knowledge Village, Lavale, Pune 412115"),
    _maharashtra("Symbiosis Centre for Management and Human Resource Development", "Pune", "Pune", "Management", "Symbiosis International University", 1993, "Private", "https://www.scmhrd.edu", "Symbiosis Knowledge Village, Lavale, Pune 412115"),
    _maharashtra("FLAME University", "Pune", "Pune", "University", "Private University", 2015, "Private", "https://www.flame.edu.in", "Gat No. 1270, Lavale, Vadgaon Bk., Pune 412115"),
    _maharashtra("Symbiosis Law School", "Pune", "Pune", "Other", "Symbiosis International University", 1977, "Private", "https://www.symlaw.ac.in", "Symbiosis Knowledge Village, Lavale, Pune 412115"),

    # Nashik
    _maharashtra("K. K. Wagh Institute of Engineering Education and Research", "Nashik", "Nashik", "Engineering", "Savitribai Phule Pune University (Autonomous)", 1984, "Private", "https://www.kkwagh.edu.in", "Hirabai Haridas Vidyanagari, Amrutdham, Panchavati, Nashik 422003"),
    _maharashtra("Sandip Institute of Technology and Research Centre", "Nashik", "Nashik", "Engineering", "Savitribai Phule Pune University", 2008, "Private", "https://www.sandipfoundation.org", "Mahiravani, Trimbak Road, Nashik 422213"),
    _maharashtra("Gokhale Education Society's R. H. Sapat College of Engineering, Management Studies and Research", "Nashik", "Nashik", "Engineering", "Savitribai Phule Pune University", 2009, "Private", "https://www.rhsapat.edu.in", "Prin. T. A. Kulkarni Vidyanagar, College Road, Nashik 422005"),
    _maharashtra("Matoshri College of Engineering and Research Centre", "Nashik", "Nashik", "Engineering", "Savitribai Phule Pune University", 2008, "Private", None, "Eklahare, Odha, Nashik 422105"),
    _maharashtra("SNJB's Late Sau. K. B. Jain College of Engineering", "Chandwad", "Nashik", "Engineering", "Savitribai Phule Pune University", 2004, "Private", "https://www.snjb.org", "Neminagar, Chandwad, Nashik 423101"),
    _maharashtra("Yashwantrao Chavan Maharashtra Open University", "Nashik", "Nashik", "University", "State Open University", 1989, "Government", "https://www.ycmou.ac.in", "Dnyangangotri, Govardhan, Nashik 422222"),
    _maharashtra("Maharashtra University of Health Sciences", "Nashik", "Nashik", "University", "State University", 1998, "Government", "https://www.muhs.ac.in", "Vani-Dindori Road, Mhasrul, Nashik 422004"),

    # Nagpur
    _maharashtra("Visvesvaraya National Institute of Technology", "Nagpur", "Nagpur", "Engineering", "Institute of National Importance", 1960, "Government", "https://www.vnit.ac.in", "South Ambazari Road, Nagpur 440010"),
    _maharashtra("Government College of Engineering, Nagpur", "Nagpur", "Nagpur", "Engineering", "Rashtrasant Tukadoji Maharaj Nagpur University", 1956, "Government", "https://www.gcoen.ac.in", "Near Kalmeshwar Square, Nagpur 441501"),
    _maharashtra("Shri Ramdeobaba College of Engineering and Management", "Nagpur", "Nagpur", "Engineering", "Rashtrasant Tukadoji Maharaj Nagpur University (Autonomous)", 1984, "Private", "https://www.rcoem.ac.in", "Ramdeo Tekdi, Gittikhadan, Katol Road, Nagpur 440013"),
    _maharashtra("Yeshwantrao Chavan College of Engineering", "Nagpur", "Nagpur", "Engineering", "Rashtrasant Tukadoji Maharaj Nagpur University (Autonomous)", 1984, "Private", "https://www.ycce.edu", "Hingna Road, Wanadongri, Nagpur 441110"),
    _maharashtra("G. H. Raisoni College of Engineering", "Nagpur", "Nagpur", "Engineering", "Rashtrasant Tukadoji Maharaj Nagpur University (Autonomous)", 1996, "Private", "https://ghrce.raisoni.net", "CRPF Gate No. 3, Hingna Road, Digdoh Hills, Nagpur 440016"),
    _maharashtra("Priyadarshini College of Engineering", "Nagpur", "Nagpur", "Engineering", "Rashtrasant Tukadoji Maharaj Nagpur University", 1993, "Private", None, "Near CRPF Gate No. 1, Hingna Road, Nagpur 440019"),
    _maharashtra("Nagpur Institute of Technology", "Nagpur", "Nagpur", "Engineering", "Rashtrasant Tukadoji Maharaj Nagpur University", 2008, "Private", None, "Survey No. 13/2, Mahurzari, Katol Road, Nagpur 441501"),
    _maharashtra("Rashtrasant Tukadoji Maharaj Nagpur University", "Nagpur", "Nagpur", "University", "State University", 1923, "Government", "https://www.nagpuruniversity.ac.in", "Chhatrapati Shivaji Maharaj Administrative Premises, Ravindranath Tagore Marg, Nagpur 440001"),
    _maharashtra("Maharashtra National Law University, Nagpur", "Nagpur", "Nagpur", "Other", "State University", 2014, "Government", "https://www.mnlunagpur.ac.in", "Waranga, Mauza Bahadura, Nagpur 441110"),

    # Chhatrapati Sambhajinagar (Aurangabad)
    _maharashtra("Dr. Babasaheb Ambedkar Marathwada University", "Chhatrapati Sambhajinagar", "Chhatrapati Sambhajinagar", "University", "State University", 1958, "Government", "https://www.bamu.ac.in", "University Campus, Aurangabad 431004"),
    _maharashtra("Government College of Engineering, Chhatrapati Sambhajinagar", "Chhatrapati Sambhajinagar", "Chhatrapati Sambhajinagar", "Engineering", "Dr. Babasaheb Ambedkar Marathwada University (Autonomous)", 1960, "Government", "https://www.geca.ac.in", "Station Road, Osmanpura, Chhatrapati Sambhajinagar 431005"),
    _maharashtra("Maharashtra Institute of Technology, Chhatrapati Sambhajinagar", "Chhatrapati Sambhajinagar", "Chhatrapati Sambhajinagar", "Engineering", "Dr. Babasaheb Ambedkar Marathwada University", 1982, "Private", "https://www.mit.asia", "Satyam Campus, Beed Bypass Road, Chhatrapati Sambhajinagar 431028"),
    _maharashtra("PES College of Engineering", "Chhatrapati Sambhajinagar", "Chhatrapati Sambhajinagar", "Engineering", "Dr. Babasaheb Ambedkar Marathwada University", 1994, "Private", None, "PES Campus, Nagsenvana, Chhatrapati Sambhajinagar 431002"),
    _maharashtra("Deogiri Institute of Engineering and Management Studies", "Chhatrapati Sambhajinagar", "Chhatrapati Sambhajinagar", "Engineering", "Dr. Babasaheb Ambedkar Marathwada University", 2009, "Private", "https://www.deogirigroup.org", "Railway Station Road, Chhatrapati Sambhajinagar 431005"),
    _maharashtra("Jawaharlal Nehru Engineering College", "Chhatrapati Sambhajinagar", "Chhatrapati Sambhajinagar", "Engineering", "MGM University", 1982, "Private", "https://www.jnec.ac.in", "MGM Campus, N-6 CIDCO, Chhatrapati Sambhajinagar 431003"),
    _maharashtra("MGM University", "Chhatrapati Sambhajinagar", "Chhatrapati Sambhajinagar", "University", "Private University", 2019, "Private", "https://www.mgmu.ac.in", "MGM Campus, N-6 CIDCO, Chhatrapati Sambhajinagar 431003"),

    # Amravati
    _maharashtra("Sant Gadge Baba Amravati University", "Amravati", "Amravati", "University", "State University", 1983, "Government", "https://www.sgbau.ac.in", "Camp Road, Amravati 444602"),
    _maharashtra("Government College of Engineering, Amravati", "Amravati", "Amravati", "Engineering", "Sant Gadge Baba Amravati University (Autonomous)", 1964, "Government", "https://www.gcoea.ac.in", "Station Road, Amravati 444604"),
    _maharashtra("Prof. Ram Meghe Institute of Technology and Research", "Badnera", "Amravati", "Engineering", "Sant Gadge Baba Amravati University", 1983, "Private", "https://www.mitra.ac.in", "Anjangaon Bari Road, Badnera, Amravati 444701"),
    _maharashtra("Sipna College of Engineering and Technology", "Amravati", "Amravati", "Engineering", "Sant Gadge Baba Amravati University", 1999, "Private", "https://www.sipna.org", "Sipna Campus, In front of Nemani Godown, Badnera Road, Amravati 444605"),
    _maharashtra("HVPM College of Engineering and Technology", "Amravati", "Amravati", "Engineering", "Sant Gadge Baba Amravati University", 1983, "Private-aided", None, "Hanuman Vyayam Prasarak Mandal Campus, Amravati 444605"),

    # Kolhapur, Sangli, Satara
    _maharashtra("Shivaji University", "Kolhapur", "Kolhapur", "University", "State University", 1962, "Government", "https://www.unishivaji.ac.in", "Vidyanagar, Kolhapur 416004"),
    _maharashtra("Kolhapur Institute of Technology's College of Engineering", "Kolhapur", "Kolhapur", "Engineering", "Shivaji University (Autonomous)", 1983, "Private", "https://www.kitcoek.in", "Gokul Shirgaon, Kolhapur 416234"),
    _maharashtra("Sanjay Ghodawat University", "Kolhapur", "Kolhapur", "University", "Private University", 2017, "Private", "https://www.sanjayghodawatuniversity.ac.in", "Atigre, Hatkanangale, Kolhapur 416118"),
    _maharashtra("D. Y. Patil College of Engineering", "Kolhapur", "Kolhapur", "Engineering", "Shivaji University", 1984, "Private", None, "Kasaba Bawada, Kolhapur 416006"),
    _maharashtra("Walchand College of Engineering", "Sangli", "Sangli", "Engineering", "Shivaji University (Autonomous)", 1947, "Government-aided", "https://www.walchandsangli.ac.in", "Vishrambag, Sangli 416415"),
    _maharashtra("Annasaheb Dange College of Engineering and Technology", "Ashta", "Sangli", "Engineering", "Shivaji University", 1998, "Private", "https://www.adcet.edu.in", "Ashta, Taluka Walwa, Sangli 416301"),
    _maharashtra("Padmabhooshan Vasantdada Patil Institute of Technology", "Budhgaon", "Sangli", "Engineering", "Shivaji University", 1983, "Private", None, "Budhgaon, Taluka Miraj, Sangli 416304"),
    _maharashtra("Government College of Engineering, Karad", "Karad", "Satara", "Engineering", "Shivaji University (Autonomous)", 1960, "Government", "https://www.gcekarad.ac.in", "Vidyanagar, Karad, Satara 415124"),
    _maharashtra("Karmaveer Bhaurao Patil College of Engineering", "Satara", "Satara", "Engineering", "Shivaji University", 1983, "Private", None, "Varye, Satara 415015"),
    _maharashtra("Yashwantrao Chavan Institute of Science", "Satara", "Satara", "Other", "Shivaji University", 1958, "Private-aided", None, "Sadar Bazar, Satara 415001"),

    # Solapur
    _maharashtra("Punyashlok Ahilyadevi Holkar Solapur University", "Solapur", "Solapur", "University", "State University", 2004, "Government", "https://www.solapuruniversity.ac.in", "Solapur-Pune National Highway, Kegaon, Solapur 413255"),
    _maharashtra("Walchand Institute of Technology", "Solapur", "Solapur", "Engineering", "Punyashlok Ahilyadevi Holkar Solapur University (Autonomous)", 1983, "Private", "https://www.witsolapur.org", "Ashok Chowk, Seth Walchand Hirachand Marg, Solapur 413006"),
    _maharashtra("SVERI's College of Engineering", "Pandharpur", "Solapur", "Engineering", "Punyashlok Ahilyadevi Holkar Solapur University", 1998, "Private", "https://www.sveri.ac.in", "Gopalpur, Pandharpur, Solapur 413304"),
    _maharashtra("N. K. Orchid College of Engineering and Technology", "Solapur", "Solapur", "Engineering", "Punyashlok Ahilyadevi Holkar Solapur University", 2008, "Private", None, "Gut No. 16, Solapur-Tuljapur Road, Tale Hipparagi, Solapur 413002"),

    # Marathwada
    _maharashtra("Swami Ramanand Teerth Marathwada University", "Nanded", "Nanded", "University", "State University", 1994, "Government", "https://www.srtmun.ac.in", "Dnyanteerth, Vishnupuri, Nanded 431606"),
    _maharashtra("Shri Guru Gobind Singhji Institute of Engineering and Technology", "Nanded", "Nanded", "Engineering", "Swami Ramanand Teerth Marathwada University (Autonomous)", 1981, "Government-aided", "https://www.sggs.ac.in", "Vishnupuri, Nanded 431606"),
    _maharashtra("M. S. Bidve Engineering College", "Latur", "Latur", "Engineering", "Swami Ramanand Teerth Marathwada University", 1983, "Private", None, "Barshi Road, Latur 413512"),
    _maharashtra("Dayanand College of Engineering", "Latur", "Latur", "Engineering", "Swami Ramanand Teerth Marathwada University", 2008, "Private", None, "Dayanand Nagar, Latur 413512"),

    # Khandesh and North Maharashtra
    _maharashtra("Government College of Engineering, Jalgaon", "Jalgaon", "Jalgaon", "Engineering", "Kavayitri Bahinabai Chaudhari North Maharashtra University", 1997, "Government", "https://www.gcoej.ac.in", "NH-6, Near Village Pal, Jalgaon 425002"),
    _maharashtra("Kavayitri Bahinabai Chaudhari North Maharashtra University", "Jalgaon", "Jalgaon", "University", "State University", 1990, "Government", "https://www.nmu.ac.in", "Umavi Nagar, P. B. No. 80, Jalgaon 425001"),
    _maharashtra("Khandesh College Education Society's College of Engineering and Management", "Jalgaon", "Jalgaon", "Engineering", "Kavayitri Bahinabai Chaudhari North Maharashtra University", 2009, "Private", None, "Jilha Peth, Jalgaon 425002"),
    _maharashtra("SVKM's Institute of Technology", "Dhule", "Dhule", "Engineering", "Kavayitri Bahinabai Chaudhari North Maharashtra University", 2009, "Private", None, "Survey No. 499, Plot No. 2, Mumbai-Agra Road, Dhule 424001"),
    _maharashtra("Zulal Bhilajirao Patil College", "Dhule", "Dhule", "Other", "Kavayitri Bahinabai Chaudhari North Maharashtra University", 1960, "Private-aided", None, "Deopur, Dhule 424002"),
    _maharashtra("Pravara Rural Engineering College", "Loni", "Ahmednagar", "Engineering", "Savitribai Phule Pune University", 1983, "Private", "https://www.pravara.com", "At. Loni, Taluka Rahata, Ahmednagar 413736"),
    _maharashtra("Amrutvahini College of Engineering", "Sangamner", "Ahmednagar", "Engineering", "Savitribai Phule Pune University", 1983, "Private", "https://www.avcoe.org", "P. O. Sangamner S.K., Ahmednagar 422608"),
    _maharashtra("Sanjivani College of Engineering", "Kopargaon", "Ahmednagar", "Engineering", "Savitribai Phule Pune University (Autonomous)", 1983, "Private", "https://www.sanjivani.org", "At. Sahajanandnagar, P. O. Shingnapur, Kopargaon, Ahmednagar 423603"),
    _maharashtra("SND College of Engineering and Research Centre", "Yeola", "Nashik", "Engineering", "Savitribai Phule Pune University", 2009, "Private", None, "Babhulgaon, Yeola, Nashik 423401"),

    # Vidarbha
    _maharashtra("Government College of Engineering, Yavatmal", "Yavatmal", "Yavatmal", "Engineering", "Sant Gadge Baba Amravati University", 2016, "Government", None, "At. Dhamangaon Road, Village Kinhi, Yavatmal 445001"),
    _maharashtra("Government College of Engineering, Chandrapur", "Chandrapur", "Chandrapur", "Engineering", "Sant Gadge Baba Amravati University", 2016, "Government", None, "Ballarpur Bypass Road, Chandrapur 442406"),
    _maharashtra("Rajiv Gandhi College of Engineering, Research and Technology", "Chandrapur", "Chandrapur", "Engineering", "Sant Gadge Baba Amravati University", 2008, "Private", None, "Ballarpur Road, Babupeth, Chandrapur 442403"),
    _maharashtra("Manoharbhai Patel Institute of Engineering and Technology", "Gondia", "Gondia", "Engineering", "Rashtrasant Tukadoji Maharaj Nagpur University", 1999, "Private", None, "Kudwa, Gondia 441614"),
    _maharashtra("Bapurao Deshmukh College of Engineering", "Sevagram", "Wardha", "Engineering", "Rashtrasant Tukadoji Maharaj Nagpur University", 1983, "Private", None, "Sevagram, Wardha 442102"),
    _maharashtra("Government College of Engineering, Akola", "Akola", "Akola", "Engineering", "Sant Gadge Baba Amravati University", 2016, "Government", None, "Kathora Naka, Akola 444004"),
    _maharashtra("Shri Sant Gajanan Maharaj College of Engineering", "Shegaon", "Buldhana", "Engineering", "Sant Gadge Baba Amravati University", 1983, "Private", "https://www.ssgmce.ac.in", "Khamgaon Road, Shegaon, Buldhana 444203"),
    _maharashtra("Anuradha Engineering College", "Chikhli", "Buldhana", "Engineering", "Sant Gadge Baba Amravati University", 1993, "Private", None, "Anuradha Nagar, Sakegaon Road, Chikhli, Buldhana 443201"),

    # Konkan
    _maharashtra("Finolex Academy of Management and Technology", "Ratnagiri", "Ratnagiri", "Engineering", "University of Mumbai", 1996, "Private", "https://www.famt.ac.in", "P-60, P-60/1, MIDC, Mirjole Block, Ratnagiri 415639"),
    _maharashtra("Government College of Engineering, Ratnagiri", "Ratnagiri", "Ratnagiri", "Engineering", "University of Mumbai", 2016, "Government", None, "Survey No. 128, 129, Village Nive, Taluka Lanja, Ratnagiri 416701"),
]


CATALOG = IITS + MAHARASHTRA_INSTITUTIONS
