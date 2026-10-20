"""
Generate the two SYNTHETIC datasets used by the ML components:

  ml/dataset/crime_hotspot_dataset.csv          -> Crime Hotspot Analysis (DBSCAN)
  ml/dataset/complaint_similarity_dataset.csv   -> Complaint Similarity (TF-IDF + cosine)
  ml/dataset/complaint_similarity_groundtruth.csv
      (complaint_id -> incident_id, for evaluating the similarity model)

ALL RECORDS ARE SYNTHETIC. They do not describe real incidents or real people.
Uses only the Python standard library. The output is reproducible (fixed seed).

Usage:  python ml/generate_datasets.py
"""
import csv
import os
import random
import re
from datetime import date, timedelta

from tn_localities import (LOCALITIES, TOWNS, PROFILES, COMPLAINT_CRIME_TYPES,
                           location_label)

SEED = 42
N_RECORDS = 1000
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset')
START_DATE = date(2024, 1, 1)
END_DATE = date(2026, 9, 20)

CRIME_CSV = os.path.join(OUT_DIR, 'crime_hotspot_dataset.csv')
COMPLAINT_CSV = os.path.join(OUT_DIR, 'complaint_similarity_dataset.csv')
GROUNDTRUTH_CSV = os.path.join(OUT_DIR, 'complaint_similarity_groundtruth.csv')


def random_date(rng, start=START_DATE, end=END_DATE):
    return start + timedelta(days=rng.randint(0, (end - start).days))


def truncated_gauss(rng, sigma, limit=2.5):
    while True:
        v = rng.gauss(0, sigma)
        if abs(v) <= limit * sigma:
            return v


def weighted_choice(rng, weights):
    return rng.choices(list(weights), weights=list(weights.values()))[0]


# ---------------------------------------------------------------------------
# Dataset 1: crime hotspots
# ---------------------------------------------------------------------------

def build_crime_dataset(rng, n=N_RECORDS):
    """80% tight clusters around hotspots, 12% city-wide background, 8% small towns."""
    n_hotspot = int(n * 0.80)
    n_diffuse = int(n * 0.12)
    hotspots = [loc for loc in LOCALITIES if loc[5] > 0]
    rows, seen = [], set()

    def add(name, city, lat, lon, profile):
        key = (round(lat, 6), round(lon, 6))
        if key in seen:
            return
        seen.add(key)
        rows.append({
            'crime_type': weighted_choice(rng, PROFILES[profile]),
            'location': location_label(name, city),
            'latitude': f'{lat:.6f}',
            'longitude': f'{lon:.6f}',
            'date': random_date(rng),
        })

    while len(rows) < n_hotspot:
        name, city, lat, lon, profile, _, spread, max_lon = rng.choices(
            hotspots, weights=[h[5] for h in hotspots])[0]
        plat = lat + truncated_gauss(rng, spread)
        plon = lon + truncated_gauss(rng, spread)
        if max_lon:
            plon = min(plon, max_lon)
        add(name, city, plat, plon, profile)

    # Background incidents spread across each city, labelled with the nearest locality.
    while len(rows) < n_hotspot + n_diffuse:
        base = rng.choice(LOCALITIES)
        city = base[1]
        plat = base[2] + truncated_gauss(rng, 0.008)
        plon = base[3] + truncated_gauss(rng, 0.008)
        same_city = [loc for loc in LOCALITIES if loc[1] == city]
        near = min(same_city, key=lambda l: (l[2] - plat) ** 2 + (l[3] - plon) ** 2)
        limits = [m for m in (base[7], near[7]) if m]
        if limits:
            plon = min(plon, min(limits))
        add(near[0], city, plat, plon, near[4])

    while len(rows) < n:
        name, lat, lon = rng.choice(TOWNS)
        add(name, name, lat + truncated_gauss(rng, 0.006), lon + truncated_gauss(rng, 0.006), 'town')

    rows.sort(key=lambda r: (r['date'], r['location']))
    for i, row in enumerate(rows, 1):
        row['crime_id'] = f'SYN-CR-{i:04d}'
        row['date'] = row['date'].isoformat()
    return rows


# ---------------------------------------------------------------------------
# Dataset 2: complaint similarity
# ---------------------------------------------------------------------------
# Values that are lists are re-picked for every complaint in an incident group,
# so complaints about the same incident share key facts but not wording.

VEHICLES = [
    ('Hero Splendor', ['motorcycle', 'bike', 'two-wheeler']),
    ('Honda Activa', ['scooter', 'scooty', 'two-wheeler']),
    ('TVS Jupiter', ['scooter', 'two-wheeler']),
    ('Bajaj Pulsar', ['motorcycle', 'bike']),
    ('TVS Apache', ['motorcycle', 'bike']),
    ('Royal Enfield Classic 350', ['motorcycle', 'bullet', 'bike']),
    ('TVS XL100', ['moped', 'two-wheeler']),
    ('Yamaha FZ', ['motorcycle', 'bike']),
    ('Maruti Swift', ['car', 'hatchback car']),
    ('Hyundai i10', ['car']),
    ('Bajaj autorickshaw', ['auto', 'autorickshaw']),
]
COLORS = ['black', 'red', 'blue', 'grey', 'white', 'silver', 'maroon']

TEMPLATES = {
    'Vehicle Theft': [
        "My {color} {model} {vt} was stolen {P} {W}.",
        "Someone stole my {vt} {P} {W}. It is a {color} {model}.",
        "I had parked my {model} {P} and when I came back {W} it was not there.",
        "{W}, my {color} {model} went missing from where I parked it {P}.",
        "Reporting the theft of a {color} {model} {vt} that was parked {P}. It was taken {W}.",
        "Unknown persons took away my {vt} ({model}, {color} colour) {P} {W}.",
        "I cannot find my {model} which I left {P} {W}. I believe it has been stolen.",
    ],
    'Theft': [
        "My {item} was stolen {P} {W}.",
        "While I was {activity} {P} {W}, someone took my {item}.",
        "I lost my {item} to a pickpocket {P} {W}.",
        "{W} my {item} disappeared from my bag {P}. I think someone took it in the crowd.",
        "Someone picked my pocket {P} {W} and took my {item}.",
        "I want to complain about the theft of my {item} {P}. It happened {W} while I was {activity}.",
        "My {item} went missing {P} {W}, I am sure it was stolen when I was {activity}.",
    ],
    'Robbery': [
        "{att} came {veh} and stopped me {P} {W}. They threatened me {weapon} and took {loot}.",
        "I was robbed {P} {W}. {att} threatened me {weapon} and snatched {loot}.",
        "{W}, {att} blocked my way {P} and forced me to hand over {loot}.",
        "While walking home {P} {W}, I was surrounded by {att} who took {loot}.",
        "I am writing to report that {att} robbed me {P} {W}. They took {loot} after threatening me {weapon}.",
        "{att} {veh} waylaid me {P} {W} and escaped with {loot}.",
    ],
    'Burglary': [
        "Our {res} {R} was broken into {W} {absence}. They stole {loot}.",
        "Thieves entered my {res} {R} {absence}; {entry}. They took {loot}.",
        "{W} we found that {entry} at our {res} {R}, and {loot} was missing.",
        "I would like to report a burglary at my {res} {R}. It happened {W} {absence}, and {loot} was taken.",
        "When we returned {W}, our {res} {R} had been ransacked and {loot} was gone.",
        "Break-in at my {res} {R}: {entry} and {loot} was stolen {absence}.",
    ],
    'Assault': [
        "I was attacked by {att} {P} {W} because of {reason}.",
        "{att} beat me {P} {W} over {reason}. {injury}.",
        "{W}, {att} assaulted me {P}. The fight started because of {reason}.",
        "I want to lodge a complaint against {att}, who hit me {P} {W}. {injury}.",
        "I saw {att} beating a man {P} {W}. It seemed to be over {reason}.",
        "Please take action: {att} attacked me with a stick {P} {W} after a quarrel about {reason}.",
    ],
    'Chain Snatching': [
        "{att} {bike} snatched my {chain} {P} {W}.",
        "While I was walking {P} {W}, {att} came {bike} from behind and pulled my {chain}.",
        "My {chain} was snatched {P} {W} by {att} riding {bike_noun}.",
        "{W}, as I was returning from the temple {P}, {att} grabbed my {chain} and sped away.",
        "I saw {att} {bike} snatch a gold chain from an elderly woman {P} {W}.",
        "My mother's {chain} was snatched {P} {W} by {att} {bike}.",
        "Chain snatching {P} {W}. {att} {bike} took my {chain} and escaped.",
    ],
    'Vandalism': [
        "Unknown persons {act} {target} {P} {W}.",
        "Someone deliberately {act} {target} {P} {W}.",
        "{W}, a group of youths {act} {target} {P}.",
        "I want to report damage to {target} {P}. It happened {W}.",
        "I saw some drunk men damaging {target} {P} {W}.",
        "Miscreants {act} {target} {P} {W} and ran away before anyone could stop them.",
    ],
    'Cyber Crime': [
        "I live {R}. {W}, {hook}. {loss}.",
        "{hook} {W}. As a result, {loss}.",
        "Online fraud complaint: {hook} {W}, and {loss}.",
        "I have been cheated online. {W} {hook}, and {loss}. I stay {R}.",
        "Please help me recover my money. {hook}; {loss}.",
        "I am from {R_plain}. I need to report cyber fraud: {hook} {W}. {loss}.",
    ],
    'Missing Person': [
        "{person} has been missing since {W}. {pron} was last seen {P}, {clothing}.",
        "{person} went out {W} and has not returned home. {pron} was last seen {P}.",
        "We are unable to find {person}. {pron} left the house {W}, {clothing}, and was last seen {P}.",
        "Missing person: {person}, last seen {P} {W}, {clothing}.",
        "Please help us trace {person}, who went missing {P} {W}.",
        "{person} did not come back home after going out {W}. {pron} was last seen {P}, {clothing}.",
    ],
}

DETAILS = {
    'Vehicle Theft': ["The handle lock was on, but it seems they broke it.",
                      "I had parked it for only about {mins} minutes.",
                      "There is a CCTV camera at a shop nearby which may have recorded it.",
                      "The RC book and insurance papers were inside.",
                      "I searched the nearby streets but could not find it."],
    'Theft': ["It had about Rs. {amt} in cash and my ID cards.",
              "The place was very crowded at that time.",
              "I have the purchase bill with me.",
              "I noticed it only after reaching home."],
    'Robbery': ["They escaped towards the main road.",
                "I could not note down the vehicle number because it was dark.",
                "I can identify them if I see them again."],
    'Burglary': ["The almirah was broken open and clothes were thrown around.",
                 "Our neighbours did not hear anything.",
                 "There is a CCTV camera at the house opposite ours."],
    'Assault': ["Some people nearby saw the incident.",
                "I have taken treatment at the government hospital.",
                "They also threatened me with dire consequences."],
    'Chain Snatching': ["I fell down and got hurt on my hand.",
                        "They were wearing helmets so I could not see their faces.",
                        "They went towards the main road very fast."],
    'Vandalism': ["This is the second time such damage has happened here.",
                  "The damage will cost a lot to repair.",
                  "There may be CCTV footage from the nearby shops."],
    'Cyber Crime': ["I have screenshots of the messages and the transaction details.",
                    "I have already informed my bank and blocked my card.",
                    "The number they used is now switched off."],
    'Missing Person': ["We have searched with relatives and friends but could not find any trace.",
                       "We have a recent photograph to share with the police.",
                       "This has never happened before and the family is very worried."],
}

# Incident "fingerprints": facts that every complaint about the same incident mentions,
# each in its own words (a nearby shop, a street, a suspect's clothing, a clue).
# They are combinatorial, so unrelated incidents rarely share them - just as two real
# complaints about different incidents rarely name the same shop and the same suspect.
# Shop and street names are invented, generic Tamil words.
SHOP_PREFIXES = ['Anbu', 'Sakthi', 'Vel', 'Amman', 'Balaji', 'Thangam', 'Arasan', 'Malar', 'Senthil',
                 'Kaveri', 'Vaigai', 'Chola', 'Annai', 'Ponni', 'Thendral', 'Nila', 'Kurinji', 'Mullai',
                 'Marutham', 'Sri Ganesh', 'Selvi', 'Vetri', 'Kalai', 'Muthu', 'Jothi', 'Lakshmi',
                 'Kumaran', 'Aruna', 'Bharathi', 'Deepam', 'Ezhil', 'Guru', 'Mani', 'Ravi', 'Kathir',
                 'Poongodi', 'Iniya', 'Magizh', 'Oviya', 'Yazhini']
SHOP_KINDS = ['Tea Stall', 'Bakery', 'Medicals', 'Textiles', 'Mobiles', 'Jewellers', 'Sweets', 'Mess',
              'Hardware', 'Fruit Stall', 'Mahal', 'Stores', 'Opticals', 'Electricals', 'Traders',
              'Fancy Store', 'Furniture', 'Book Centre', 'Flower Shop', 'Tailors']
SPOT_PREPS = ['next to', 'beside', 'opposite', 'in front of', 'close to', 'near']
STREETS = ['Gandhi', 'Nehru', 'Kamarajar', 'Bharathiyar', 'Thiruvalluvar', 'Vivekananda', 'Kambar',
           'Ilango', 'Avvaiyar', 'Pillaiyar Kovil', 'Mariamman Kovil', 'Nethaji', 'Rajaji', 'VOC',
           'Ambedkar', 'Kattabomman', 'Velu Nachiyar', 'Pudu', 'Middle', 'Kalaivanar', 'Bharathidasan']
STREET_KINDS = ['Street', 'Cross Street', 'Main Road', '2nd Street', '3rd Cross', 'Lane']

CLUE_COLORS = ['red', 'yellow', 'green', 'orange', 'purple', 'white', 'black', 'brown', 'pink', 'maroon']
GARMENTS = ['cap', 'jacket', 't-shirt', 'checked shirt', 'raincoat', 'helmet', 'lungi', 'sweater']
BAGS = ['backpack', 'cloth bag', 'handbag', 'shoulder bag', 'plastic carry bag', 'travel bag']
STATES = ['Jharkhand', 'West Bengal', 'Rajasthan', 'Bihar', 'Assam', 'Odisha', 'Haryana',
          'Uttar Pradesh', 'Gujarat', 'Madhya Pradesh', 'Maharashtra', 'Punjab']


def fingerprint_clues(rng, crime_type):
    """One or two facts about the incident, each as a list of paraphrases."""
    c = rng.choice(CLUE_COLORS)
    if crime_type == 'Missing Person':
        bag = rng.choice(BAGS)
        facts = [[f"{{pron}} was carrying a {c} {bag}.", f"{{pos}} {c} {bag} is also missing.",
                  f"{{pron}} had a {c} {bag} with {{pos}}."]]
    elif crime_type == 'Cyber Crime':
        state = rng.choice(STATES)
        facts = [[f"The money was transferred to a bank account in {state}.",
                  f"The bank told me the account that received the money is in {state}.",
                  f"My money went to an account registered in {state}."]]
    elif crime_type == 'Burglary':
        facts = []
    else:
        g = rng.choice(GARMENTS)
        facts = [[f"One of them wore a {c} {g}.", f"I noticed a {c} {g} on one of them.",
                  f"The culprit was wearing a {c} {g}.", f"The person had a {c} {g} on."]]
    if crime_type in CLUES or rng.random() < 0.5:
        facts.append(rng.choice(CLUES.get(crime_type, SUSPECT_CLUES)))
    return facts

SUSPECT_CLUES = [
    ["One of them wore a red cap.", "One man had a red cap on.", "I noticed a red cap on one of them."],
    ["The man had a thick beard and wore a yellow shirt.", "He was bearded and dressed in a yellow shirt.",
     "A bearded man in a yellow shirt was involved."],
    ["Their vehicle had no number plate.", "The two-wheeler they used had no registration plate.",
     "There was no number plate on their vehicle."],
    ["They spoke in a mix of Tamil and Telugu.", "I heard them talking in Telugu and Tamil.",
     "They were speaking Telugu and some Tamil."],
    ["The person had a tattoo of a scorpion on his right hand.", "I saw a scorpion tattoo on his right hand.",
     "He had a scorpion tattoo on the right arm."],
    ["They were wearing black masks.", "Both had their faces covered with black masks.",
     "Their faces were hidden behind black masks."],
    ["A security guard at the nearby shop saw it happen.", "The watchman of the next shop witnessed it.",
     "The shop security guard nearby saw everything."],
    ["A green autorickshaw was waiting nearby for them.", "They left in a green auto that was waiting close by.",
     "A green autorickshaw picked them up afterwards."],
    ["The person was limping slightly on the left leg.", "He walked with a limp in his left leg.",
     "I noticed he was limping on his left leg."],
    ["He was wearing a blue raincoat.", "The man had on a blue raincoat.", "He wore a blue colour raincoat."],
]
CLUES = {
    'Burglary': [
        ["A white van was seen parked near our gate that night.", "Neighbours noticed a white van near our gate.",
         "There was an unknown white van parked outside our gate."],
        ["The CCTV camera wires were cut.", "They had cut the cable of our CCTV camera.",
         "The CCTV camera was disconnected by cutting its wires."],
        ["Muddy footprints were found near the kitchen window.", "We saw muddy foot marks near the kitchen window.",
         "There were mud footprints by the kitchen window."],
        ["Our pet dog was found tied up in the backyard.", "Someone had tied up our dog in the backyard.",
         "The dog was tied to the backyard pole when we returned."],
        ["A ladder from the neighbouring construction site was used.",
         "They used a ladder taken from the construction site next door.",
         "The ladder from the building work next door was left against our wall."],
        ["The iron safe was dragged into the bathroom.", "They pulled the iron safe into the bathroom.",
         "We found the iron safe moved into the bathroom."],
    ],
    'Cyber Crime': [
        ["The caller spoke only in Hindi.", "He talked to me in Hindi.", "The person on the call was speaking Hindi."],
        ["They sent a fake ID card photo to convince me.", "A photo of a fake identity card was sent to me.",
         "To make me believe them, they shared a fake ID card image."],
        ["The link looked exactly like the real bank website.", "The website in the link copied the bank's page.",
         "The page looked like a genuine bank website."],
        ["The WhatsApp profile used a company logo as its display picture.",
         "Their WhatsApp display picture was a company logo.", "The WhatsApp account showed a company logo."],
        ["They kept calling from different numbers every day.", "Calls came from a different number each day.",
         "Every day they called using new numbers."],
        ["The messages were in poor English with many spelling mistakes.",
         "Their messages had a lot of spelling errors.", "The messages were full of spelling mistakes."],
    ],
    'Missing Person': [
        ["{pron} was carrying a blue backpack.", "{pron} had a blue backpack with {pos}.",
         "{pos} blue backpack is also missing."],
        ["{pron} has a mole on the left cheek.", "There is a mole on {pos} left cheek.",
         "A mole on the left cheek is an identifying mark."],
        ["{pron} did not take {pos} mobile phone.", "{pos} phone was left at home.",
         "{pron} left without {pos} mobile phone."],
        ["{pron} wears spectacles with a black frame.", "{pron} uses black frame glasses.",
         "{pron} has black-rimmed spectacles."],
        ["{pron} has a scar on the forehead.", "There is a scar on {pos} forehead.",
         "A forehead scar is an identification mark."],
        ["{pron} was holding a white cloth bag.", "{pron} carried a white cloth bag.",
         "{pron} had a white cloth bag in hand."],
    ],
}

OPENERS = ['', '', '', 'Respected Sir/Madam,', 'Sir,', 'Hello,', 'Dear Officer,',
           'This is to report an incident.', 'I need urgent help.']
CLOSERS = ['', '', 'Kindly take necessary action.', 'Please help me.',
           'Please look into this matter at the earliest.', 'I request you to register my complaint.',
           'Please do the needful.', 'Kindly investigate this.']

LANDMARK_WORDS = ('Bus Stand', 'Temple', 'Junction', 'Central', 'Fort')


def place_phrases(name, city):
    """Different ways to mention a place; every variant names the locality or city."""
    if name == city:  # small town
        return [f"in {city}", f"at {city} town", f"near the {city} bus stand", f"in {city} town"]
    if name in ('Bus Stand', 'Old Bus Stand', 'New Bus Stand', 'Central Bus Stand'):
        lower = name.lower()
        return [f"near the {city} {lower}", f"at the {lower} in {city}",
                f"around the {lower}, {city}", f"close to the {city} {lower}"]
    if any(w in name for w in LANDMARK_WORDS):
        the = '' if city in name else 'the '
        suffix = '' if city in name else f", {city}"
        in_city = '' if city in name else f" in {city}"
        return [f"near {the}{name}{suffix}", f"at {the}{name}{in_city}",
                f"around {the}{name}{suffix}", f"in front of {the}{name}{in_city}",
                f"close to {the}{name}{suffix}"]
    return [f"in {name}, {city}", f"at {name} in {city}", f"near {name}, {city}",
            f"around the {name} area in {city}", f"on the main road in {name}, {city}"]


def residence_phrases(name, city):
    if name == city:
        return [f"in {city}", f"in {city} town"]
    if city in name:
        return [f"near {name}", f"close to {name}"]
    if any(w in name for w in LANDMARK_WORDS):
        return [f"near the {name} area in {city}", f"close to the {name}, {city}"]
    return [f"in {name}, {city}", f"at {name} in {city}", f"in the {name} area of {city}"]


def when_phrases(incident, filed, hour):
    off = (filed - incident).days
    period = ('morning' if hour < 12 else 'afternoon' if hour < 17
              else 'evening' if hour < 21 else 'night')
    h12, ampm = (hour % 12 or 12), ('am' if hour < 12 else 'pm')
    if off == 0:
        day, short = 'today', f"this {period}" if period != 'night' else 'tonight'
    elif off == 1:
        day, short = 'yesterday', f"yesterday {period}" if period != 'night' else 'last night'
    elif off < 7:
        day = f"last {incident:%A}"
        short = f"{day} {period}"
    else:
        day = f"on {incident.day} {incident:%B}"
        short = f"{day} in the {period}"
    return [short, f"{day} around {h12} {ampm}", f"{day} at about {h12} {ampm}"]


def make_slots(rng, crime_type):
    amt = f"{rng.choice([2, 3, 4, 5, 6, 8, 10, 12, 15, 18, 20, 25, 35, 45, 60, 75]) * 1000:,}"
    sov = rng.choice([2, 3, 4, 5, 6, 8])
    color = rng.choice(COLORS)
    if crime_type == 'Vehicle Theft':
        model, vts = rng.choice(VEHICLES)
        return dict(model=model, vt=vts, color=color, mins=str(rng.choice([10, 15, 20, 30, 45])))
    if crime_type == 'Theft':
        item = rng.choice([['Samsung mobile phone', 'Samsung phone'], ['Redmi mobile phone', 'Redmi phone'],
                           ['Vivo smartphone', 'Vivo phone'], ['iPhone', 'Apple iPhone'],
                           ['brown leather wallet', 'leather wallet'], ['ladies purse', 'purse'],
                           ['black laptop bag', 'laptop bag'], ['gold finger ring', 'gold ring']])
        activity = rng.choice(['boarding the bus', 'waiting in the ticket queue', 'buying vegetables',
                               'standing in the crowd', 'paying at the shop counter'])
        return dict(item=item, activity=activity, amt=amt)
    if crime_type == 'Robbery':
        return dict(att=rng.choice(['two men', 'three youths', 'two masked men', 'a gang of four men']),
                    veh=rng.choice(['on a motorcycle', 'on a bike without a number plate',
                                    'in an autorickshaw']),
                    weapon=rng.choice(['with a knife', 'with a sickle', 'with a knife and a stick']),
                    loot=rng.choice([f"my mobile phone and Rs. {amt} in cash", 'my gold bracelet and wallet',
                                     f"my bag containing Rs. {amt}", 'my wallet and wrist watch']))
    if crime_type == 'Burglary':
        return dict(res=rng.choice(['house', 'flat', 'shop', 'house']),
                    absence=rng.choice([f"while we were away at a family function in {rng.choice(TOWNS)[0]}",
                                        'while we were out of town', 'while I was at work',
                                        'while the family was sleeping upstairs']),
                    entry=rng.choice(['the front door lock had been broken',
                                      'the back window grill had been cut',
                                      'the gate lock and the main door lock were broken']),
                    loot=rng.choice([f"{sov} sovereigns of gold jewellery",
                                     f"Rs. {amt} in cash kept in the almirah",
                                     'a laptop and an LED television', f"silver articles and Rs. {amt} in cash"]))
    if crime_type == 'Assault':
        return dict(att=rng.choice(['my neighbour', 'a group of three men', 'an auto driver',
                                    'a drunk man', 'two youths from the next street']),
                    reason=rng.choice(['a parking issue', 'money I had lent', 'a minor road accident',
                                       'sharing the water tap', 'loud music at night']),
                    injury=['I have injuries on my head and hand', 'I got a cut on my forehead',
                            'I had to get stitches on my arm'])
    if crime_type == 'Chain Snatching':
        i = rng.randrange(3)
        return dict(att=rng.choice(['a man', 'two men', 'two youths wearing helmets', 'a young man']),
                    bike=[f"on a {color} bike", 'on a two-wheeler', 'on a scooter'][i],
                    bike_noun=[f"a {color} bike", 'a two-wheeler', 'a scooter'][i],
                    chain=[f"{sov}-sovereign gold chain", f"gold chain of {sov} sovereigns",
                           f"{sov} sovereign thali chain"])
    if crime_type == 'Vandalism':
        return dict(target=rng.choice(['the windshield of my car', 'the glass door of our shop',
                                       'the street lights on our road', 'the bus shelter',
                                       'the compound wall of our house', 'the two-wheelers parked on our street']),
                    act=['smashed', 'damaged', 'broke'])
    if crime_type == 'Cyber Crime':
        item2 = rng.choice(['sofa', 'refrigerator', 'laptop', 'washing machine', 'study table', 'bicycle',
                            'air cooler', 'dining table', 'gas stove', 'tablet'])
        card = rng.choice(['debit card', 'credit card', 'pension account', 'savings account'])
        reason = rng.choice(['to unblock it', 'to raise the limit', 'to link it with Aadhaar',
                             'to redeem reward points', 'to stop a suspicious transaction'])
        task = rng.choice(['liking YouTube videos', 'rating hotels on a website', 'reviewing products',
                           'data entry typing work', 'following Instagram pages'])
        channel = rng.choice(['SMS', 'WhatsApp message', 'email'])
        platform = rng.choice(['Instagram', 'Facebook', 'WhatsApp'])
        bill = rng.choice(['electricity', 'gas connection', 'mobile postpaid'])
        scams = {
            'otp': ([f"a caller pretending to be from my bank asked for the OTP on my {card} {reason}",
                     f"someone claiming to be a bank officer called about my {card} {reason} and I shared the OTP",
                     f"a fake bank executive phoned me about my {card}, saying it was {reason}, and got the OTP"],
                    [f"Rs. {amt} was debited from my account", f"I lost Rs. {amt}"]),
            'upi': ([f"I was selling my old {item2} online and the buyer sent a UPI collect request that I approved",
                     f"a buyer for my {item2} on an online marketplace tricked me into scanning a QR code",
                     f"while selling my {item2} online, the so-called buyer made me scan a QR code"],
                    [f"Rs. {amt} was taken from my account through UPI", f"I lost Rs. {amt} via UPI"]),
            'job': ([f"a part-time job offer for {task} asked me to pay deposits for bigger tasks",
                     f"I joined an online job of {task} and they made me pay money to unlock earnings",
                     f"someone offered me work-from-home income for {task} and collected advance payments"],
                    [f"I paid Rs. {amt} in total and got nothing back", f"I have lost Rs. {amt} to them"]),
            'kyc': ([f"a {channel} asked me to update my KYC and I entered my bank details in the link",
                     f"I clicked a KYC update link sent by {channel} and typed my net banking details",
                     f"a {channel} said my account would be blocked without a KYC update, so I used the link"],
                    [f"Rs. {amt} was withdrawn from my account", f"Rs. {amt} disappeared from my bank account"]),
            'bill': ([f"a message said my {bill} connection would be cut tonight unless I paid a pending bill",
                      f"someone warned that my {bill} service would be disconnected and sent a payment app link",
                      f"I got a fake {bill} disconnection notice and installed the app they suggested"],
                     [f"Rs. {amt} was taken from my account", f"they took Rs. {amt} from me"]),
            'loan': (["a loan app is threatening me with morphed photos after I took a small loan",
                      "after borrowing from an instant loan app, they are sending my morphed photos to my contacts",
                      "the recovery agents of a loan app are harassing my contacts with morphed pictures"],
                     [f"they are demanding Rs. {amt} even though I repaid the loan",
                      f"they want Rs. {amt} more than I borrowed"]),
            'social': ([f"my {platform} account was hacked and the hacker is asking my friends for money",
                        f"someone hacked my {platform} and is messaging my contacts for money",
                        f"my {platform} profile was taken over and money requests were sent to my friends"],
                       [f"my friends have already sent Rs. {amt} to the hacker",
                        f"two of my friends lost Rs. {amt} because of this"]),
            'invest': (["a Telegram group promising stock market tips made me invest through a fake trading app",
                        "I was added to a share trading tips group that got me to deposit money in a fake app",
                        "a so-called trading expert on Telegram convinced me to invest in an app that is now blocked"],
                       [f"I invested Rs. {amt} and cannot withdraw anything", f"Rs. {amt} of my savings is stuck"]),
        }
        hooks, losses = scams[rng.choice(list(scams))]
        return dict(hook=hooks, loss=losses)
    if crime_type == 'Missing Person':
        who = rng.choice([("my father, aged {age}, who has memory loss", 'he', (65, 80)),
                          ("my {age}-year-old son", 'he', (9, 16)),
                          ("my younger sister, aged {age}", 'she', (17, 24)),
                          ("my grandmother, aged {age}", 'she', (68, 85)),
                          ("my {age}-year-old daughter who studies in college", 'she', (18, 21)),
                          ("my elder brother, aged {age}, who has a mental health condition", 'he', (25, 45))])
        desc, pron, (lo, hi) = who
        c1, c2 = rng.sample(CLUE_COLORS + ['blue', 'grey', 'cream'], 2)
        clothing = rng.choice([f'wearing a {c1} shirt and a {c2} lungi', f'wearing a {c1} checked shirt and {c2} trousers',
                               f'wearing a {c1} t-shirt and {c2} track pants'] if pron == 'he' else
                              [f'wearing a {c1} saree', f'wearing a {c1} churidar with a {c2} shawl',
                               f'wearing a {c1} top and {c2} jeans'])
        return dict(person=desc.format(age=rng.randint(lo, hi)), pron=pron, clothing=clothing,
                    pos='his' if pron == 'he' else 'her')
    raise ValueError(crime_type)


def pick_location(rng, crime_type):
    places = [(loc[0], loc[1], loc[4]) for loc in LOCALITIES]
    places += [(n, n, 'town') for n, _, _ in TOWNS]
    weights = [PROFILES[p].get(crime_type, 6) for _, _, p in places]
    name, city, _ = rng.choices(places, weights=weights)[0]
    return name, city


def sentence_case(text):
    text = re.sub(r'\s+', ' ', text).strip()
    return re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)


# Phrase alternatives applied to template wording (never to the incident facts), so two
# complaints built from the same template still read differently.
PARAPHRASES = {
    'was stolen': ['was stolen', 'got stolen', 'was taken', 'was lifted'],
    'stole': ['stole', 'took', 'made off with', 'lifted'],
    'Someone': ['Someone', 'Somebody', 'An unknown person', 'Some stranger'],
    'someone': ['someone', 'somebody', 'an unknown person', 'a stranger'],
    'Unknown persons': ['Unknown persons', 'Some unidentified people', 'Strangers', 'Unidentified men'],
    'I want to': ['I want to', 'I would like to', 'I wish to', 'I am writing to'],
    'I would like to': ['I would like to', 'I want to', 'I wish to'],
    'I am writing to': ['I am writing to', 'I wish to', 'I want to'],
    'report': ['report', 'inform you about', 'bring to your notice'],
    'went missing': ['went missing', 'vanished', 'disappeared', 'was gone'],
    'disappeared': ['disappeared', 'vanished', 'went missing'],
    'I believe': ['I believe', 'I am sure', 'I strongly feel', 'I suspect'],
    'I think': ['I think', 'I feel', 'I suspect', 'probably'],
    'came back': ['came back', 'returned', 'got back'],
    'returned': ['returned', 'came back', 'got back home'],
    'parked': ['parked', 'left', 'kept'],
    'took': ['took', 'grabbed', 'seized', 'carried off'],
    'snatched': ['snatched', 'grabbed', 'pulled away', 'yanked'],
    'escaped': ['escaped', 'fled', 'rode away', 'got away'],
    'sped away': ['sped away', 'raced off', 'rode off quickly', 'fled'],
    'threatened me': ['threatened me', 'frightened me', 'intimidated me', 'scared me'],
    'attacked': ['attacked', 'beat', 'hit', 'thrashed'],
    'assaulted': ['assaulted', 'beat up', 'manhandled', 'attacked'],
    'beat me': ['beat me', 'hit me', 'thrashed me', 'slapped and kicked me'],
    'damaged': ['damaged', 'wrecked', 'spoiled'],
    'damage to': ['damage to', 'destruction of', 'deliberate damage to'],
    'deliberately': ['deliberately', 'purposely', 'intentionally'],
    'a group of youths': ['a group of youths', 'some young men', 'a gang of boys', 'a few youngsters'],
    'Miscreants': ['Miscreants', 'Some rowdies', 'Anti-social elements', 'Troublemakers'],
    'was broken into': ['was broken into', 'was burgled', 'was burgled by thieves'],
    'ransacked': ['ransacked', 'turned upside down', 'searched and messed up'],
    'Thieves': ['Thieves', 'Burglars', 'Some intruders'],
    'has been missing': ['has been missing', 'has not been seen', 'has been untraceable'],
    'last seen': ['last seen', 'last spotted', 'last noticed'],
    'unable to find': ['unable to find', 'not able to trace', 'searching everywhere for'],
    'trace': ['trace', 'find', 'locate'],
    'cheated': ['cheated', 'duped', 'scammed', 'defrauded'],
    'Please help me recover my money': ['Please help me recover my money', 'Kindly help me get my money back',
                                        'I request you to recover my money'],
    'Online fraud complaint': ['Online fraud complaint', 'Complaint about online cheating',
                               'Cyber fraud report'],
    'As a result': ['As a result', 'Because of this', 'Due to that'],
    'While walking home': ['While walking home', 'On my way home', 'As I was going back home'],
    'surrounded by': ['surrounded by', 'cornered by', 'blocked by'],
    'I was robbed': ['I was robbed', 'I was looted', 'Robbers targeted me'],
}
_PARAPHRASE_RE = re.compile(r'\b(' + '|'.join(sorted(map(re.escape, PARAPHRASES), key=len, reverse=True)) + r')\b')


def paraphrase(rng, template):
    return _PARAPHRASE_RE.sub(lambda m: rng.choice(PARAPHRASES[m.group(1)]), template)


def render(rng, slots, template, place, residence, when, opener, closer, clues, detail):
    values = {k: (rng.choice(v) if isinstance(v, list) else v) for k, v in slots.items()}
    values.update(P=place, R=residence, R_plain=residence.split(' ', 1)[1], W=when)
    body = paraphrase(rng, template).format(**values)
    if opener.endswith(',') and not re.match(r"I\b", body):
        body = body[0].lower() + body[1:]  # "Sir, my bike..." rather than "Sir, My bike..."
    parts = [opener, body] + [c.format(**values) for c in clues]
    if rng.random() < 0.25:
        parts.append(detail.format(**values))
    parts.append(closer)
    return sentence_case(' '.join(p for p in parts if p))


def build_complaint_dataset(rng, n=N_RECORDS, grouped_target=560):
    group_sizes = []
    while sum(group_sizes) < grouped_target:
        group_sizes.append(min(rng.choice([2, 2, 2, 3, 3, 4]), max(2, grouped_target - sum(group_sizes))))
    group_sizes += [1] * (n - sum(group_sizes))

    rows, texts = [], set()
    for inc_no, size in enumerate(group_sizes, 1):
        crime_type = rng.choice(COMPLAINT_CRIME_TYPES)
        name, city = pick_location(rng, crime_type)
        slots = make_slots(rng, crime_type)
        incident = random_date(rng, end=END_DATE - timedelta(days=4))
        hour = rng.choice(list(range(6, 24)))
        templates = rng.sample(TEMPLATES[crime_type], size)
        openers = rng.sample(OPENERS, size)
        closers = rng.sample(CLOSERS, size)
        spot = f"{rng.choice(SHOP_PREFIXES)} {rng.choice(SHOP_KINDS)}"
        places = [f"{rng.choice(SPOT_PREPS)} {spot} {p}" for p in place_phrases(name, city)]
        street = f"{rng.choice(STREETS)} {rng.choice(STREET_KINDS)}"
        residences = [f"on {street} {r}" for r in residence_phrases(name, city)]
        rng.shuffle(places)
        facts = [rng.sample(f, len(f)) for f in fingerprint_clues(rng, crime_type)]
        detail = rng.choice(DETAILS[crime_type])
        for m in range(size):
            off = rng.randint(1 if hour >= 21 else 0, 3)
            filed = incident + timedelta(days=off)
            for _ in range(50):
                clues = [f[m % len(f)] for f in facts if rng.random() < 0.85]
                text = render(rng, slots, templates[m], places[m % len(places)],
                              rng.choice(residences), rng.choice(when_phrases(incident, filed, hour)),
                              openers[m], closers[m], clues, detail)
                if text not in texts:
                    break
                rng.shuffle(places)
            else:
                raise RuntimeError('could not produce a unique complaint text')
            texts.add(text)
            rows.append({'complaint_text': text, 'crime_type': crime_type,
                         'location': location_label(name, city), 'date': filed.isoformat(),
                         'incident_id': f'SYN-INC-{inc_no:04d}', 'group_size': size})

    rng.shuffle(rows)
    for i, row in enumerate(rows, 1):
        row['complaint_id'] = f'SYN-CMP-{i:04d}'
    return rows


def write_csv(path, fields, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    crimes = build_crime_dataset(random.Random(SEED))
    write_csv(CRIME_CSV, ['crime_id', 'crime_type', 'location', 'latitude', 'longitude', 'date'], crimes)

    complaints = build_complaint_dataset(random.Random(SEED + 1))
    write_csv(COMPLAINT_CSV, ['complaint_id', 'complaint_text', 'crime_type', 'location', 'date'], complaints)
    write_csv(GROUNDTRUTH_CSV, ['complaint_id', 'incident_id', 'group_size'],
              sorted(complaints, key=lambda r: r['complaint_id']))

    print(f"SYNTHETIC DATA written:\n  {CRIME_CSV} ({len(crimes)} rows)\n"
          f"  {COMPLAINT_CSV} ({len(complaints)} rows)\n  {GROUNDTRUTH_CSV}")


if __name__ == '__main__':
    main()
