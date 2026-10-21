"""
Generate the SYNTHETIC complaint priority dataset used to train the
AI Complaint Priority model (ml/train_priority_model.py).

Every record is invented (IDs start with SYN-PRI-). Priority labels come from a
hidden scoring rule plus random noise, so the model has to learn the pattern
rather than memorise a lookup table:
  * how severe the complaint text is (weapons, injuries, ongoing danger, amount lost)
  * the crime category chosen by the citizen
  * the time of the incident (night incidents score higher)
  * the location type (crowded landmarks / city centre score higher)
  * previous related reports in the same area (repeat problems score higher)

Usage:  python ml/generate_priority_dataset.py      (fixed seed, same output every run)
"""
import csv
import os
import random

SEED = 42
N_RECORDS = 10000
OUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset', 'complaint_priority_dataset.csv')

FIELDS = ['complaint_id', 'title', 'complaint_description', 'crime_category', 'location',
          'location_type', 'incident_time', 'previous_related_reports', 'priority']

LOCALITIES = {
    'Area': ['Anna Nagar', 'K.K. Nagar', 'Sellur', 'Goripalayam', 'Tallakulam', 'Koodal Nagar',
             'Arapalayam', 'Bibikulam', 'Narimedu', 'Ponmeni', 'Villapuram', 'S.S. Colony'],
    'Village': ['Karuppayurani', 'Vadapalanji', 'Kallanthiri', 'Chathirapatti', 'Poovanthi'],
    'Town': ['Melur', 'Thirumangalam', 'Usilampatti', 'Vadipatti', 'Peraiyur'],
    'Landmark': ['Periyar Bus Stand', 'Mattuthavani Bus Stand', 'Meenakshi Amman Temple',
                 'Madurai Junction', 'Simmakkal Market'],
    'City Center': ['Madurai City Center'],
    'Unknown': ['Not specified'],
}
LOCATION_TYPE_WEIGHTS = {'Area': 50, 'Village': 17, 'Town': 14, 'Landmark': 10, 'City Center': 4, 'Unknown': 5}
LOCATION_BONUS = {'Area': 0.0, 'Village': -0.15, 'Town': 0.0, 'Landmark': 0.45, 'City Center': 0.45, 'Unknown': 0.0}

CATEGORY_WEIGHTS = {'Theft': 20, 'Cybercrime': 15, 'Fraud': 11, 'Harassment': 13,
                    'Accident': 11, 'Assault': 12, 'Vandalism': 9, 'Other': 9}
CATEGORY_BASE = {'Assault': 1.2, 'Accident': 1.0, 'Harassment': 0.7, 'Theft': 0.6,
                 'Fraud': 0.5, 'Cybercrime': 0.5, 'Vandalism': 0.1, 'Other': 0.0}
# Chance of the text being low / medium / high severity, per category.
SEVERITY_WEIGHTS = {'Assault': (20, 40, 40), 'Accident': (30, 40, 30), 'Harassment': (35, 40, 25),
                    'Theft': (35, 45, 20), 'Fraud': (35, 45, 20), 'Cybercrime': (40, 40, 20),
                    'Vandalism': (55, 35, 10), 'Other': (60, 30, 10)}

# Templates per category and severity (0 = low, 1 = medium, 2 = high).
TEMPLATES = {
    'Theft': [
        ["My {item} worth Rs. {small} was stolen from outside my house in {place}. Nobody was hurt.",
         "Someone took my {item} kept near the gate in {place}. It is a minor loss but please note it.",
         "A small amount of Rs. {small} went missing from my shop counter in {place}. No one was harmed."],
        ["My house in {place} was broken into and Rs. {medium} in cash and my {item} were stolen.",
         "Thieves stole my two-wheeler parked near {place}. The lock was broken.",
         "My gold chain worth Rs. {medium} was stolen while travelling near {place}."],
        ["Armed men broke into our house in {place} while we were inside and took gold jewellery worth Rs. {large}. They threatened us with a knife.",
         "A gang is breaking into houses in {place} right now. They took Rs. {large} and threatened my family.",
         "Thieves with weapons attacked the watchman and looted the shop in {place}. Goods worth Rs. {large} were taken."],
    ],
    'Cybercrime': [
        ["I received a suspicious message asking for my OTP. I did not share it and lost no money.",
         "Someone created a fake social media profile using my photo. No money was lost.",
         "I keep getting spam calls about a lottery prize. I have not lost any money."],
        ["I was cheated online and Rs. {medium} was debited from my bank account after clicking a KYC link.",
         "My social media account was hacked and the hacker is asking my friends for money.",
         "I paid Rs. {medium} to an online seller for a phone and never received it."],
        ["Someone is blackmailing me with morphed photos and threatening to post them online unless I pay.",
         "Rs. {large} was drained from my bank account through fraudulent transactions within an hour. My whole savings are gone.",
         "An online gang is threatening to harm my family and is extorting money from me every day."],
    ],
    'Fraud': [
        ["A shopkeeper in {place} overcharged me Rs. {small} and refused to refund it.",
         "I was given a fake receipt for Rs. {small} by a local vendor in {place}.",
         "A salesman sold me a defective product for Rs. {small} and is not answering calls."],
        ["A person promised me a job and took Rs. {medium} as a fee, then disappeared.",
         "A chit fund agent in {place} collected Rs. {medium} from me and stopped paying.",
         "Someone sold me a fake land document and took Rs. {medium} as advance."],
        ["A finance company in {place} collected Rs. {large} from hundreds of families and the owners have fled.",
         "A gang cheated many elderly people in {place} out of their pension. I lost Rs. {large}.",
         "My business partner forged my signature and transferred Rs. {large}. He is threatening me now."],
    ],
    'Harassment': [
        ["My neighbour in {place} keeps playing loud music late at night and shouting at us.",
         "A person keeps passing rude comments when I walk to work in {place}.",
         "I am getting repeated annoying calls from an unknown number."],
        ["A man has been following me from the bus stop in {place} for the past week.",
         "My neighbour verbally abuses and threatens my family over a parking dispute in {place}.",
         "I am being repeatedly stalked and receiving obscene messages from a known person."],
        ["A man is stalking my daughter every day near {place} and threatened to throw acid on her.",
         "My husband beats me and threatened to kill me. I am afraid for my life and my children.",
         "A group of men harassed and threatened a woman near {place}. She is in danger right now."],
    ],
    'Accident': [
        ["A car scratched my parked bike near {place}. No one was injured.",
         "A minor collision happened between two bikes near {place}. Nobody was hurt.",
         "An auto hit the side mirror of my car in {place} and drove away. No injuries."],
        ["A bike hit a pedestrian near {place} and he has minor injuries. The rider fled.",
         "A car rammed into our compound wall in {place} and damaged it badly. The driver was drunk.",
         "Two vehicles collided near {place} and one person is injured."],
        ["A speeding lorry hit a family on a bike near {place}. They are seriously injured and bleeding.",
         "A bus accident happened near {place}. Many passengers are injured and need an ambulance.",
         "A hit-and-run near {place} left a man unconscious on the road. The vehicle escaped."],
    ],
    'Assault': [
        ["There was a small argument with my neighbour in {place} and he pushed me. I am not hurt.",
         "A drunk man slapped my friend during a quarrel in {place}. No serious injury.",
         "Two shopkeepers in {place} had a scuffle. Nobody needed treatment."],
        ["I was beaten by three people near {place} and got injuries on my hand.",
         "My brother was attacked with sticks by our neighbours in {place} over a land dispute.",
         "A gang assaulted my son near {place} and he has minor injuries."],
        ["A man was stabbed with a knife near {place} and is bleeding heavily. The attackers are still around.",
         "A group attacked my father with sickles in {place}. He is seriously injured and in hospital.",
         "Rowdies attacked our family with weapons in {place} and threatened to kill us."],
    ],
    'Vandalism': [
        ["Someone drew graffiti on our compound wall in {place}.",
         "Children broke the street light near our house in {place}.",
         "Someone damaged the flower pots outside my shop in {place}."],
        ["Unknown persons broke the windows of my car parked in {place}.",
         "Someone damaged the shutter of my shop in {place} at night.",
         "A group damaged the public bus shelter in {place}."],
        ["A mob set fire to vehicles in {place} and is damaging shops. The situation is tense.",
         "Unknown persons threw petrol bombs at our house in {place}.",
         "A gang is smashing shops in {place} right now and threatening the owners."],
    ],
    'Other': [
        ["Stray dogs are troubling people on our street in {place}.",
         "Garbage is being dumped on the road in {place}.",
         "I lost my bag with some documents near {place}."],
        ["Illegal liquor is being sold near the school in {place}.",
         "People are gambling in the open ground in {place} every evening.",
         "A suspicious person has been roaming around houses in {place}."],
        ["An elderly man with dementia has gone missing from {place} since this morning.",
         "A child is missing from {place} since school hours and we cannot find her.",
         "An unattended bag is lying near {place} and people are panicking."],
    ],
}
ITEMS = ['mobile phone', 'bicycle', 'gas cylinder', 'laptop', 'handbag', 'water motor', 'purse']
OPENERS = ['', '', 'Respected Sir, ', 'Sir, ', 'Please help. ']
FILLERS = ['', '', 'I request you to take action.', 'Kindly investigate this matter.',
           'I have informed my family.', 'There are CCTV cameras nearby.',
           'This happened in front of many people.', 'Please look into this.']
TITLES = {
    'Theft': ['Theft complaint', 'Items stolen', 'House break-in', 'Theft at home'],
    'Cybercrime': ['Online fraud', 'Cyber complaint', 'Account hacked', 'Online cheating'],
    'Fraud': ['Cheating complaint', 'Money fraud', 'Financial fraud'],
    'Harassment': ['Harassment complaint', 'Stalking issue', 'Being threatened'],
    'Accident': ['Road accident', 'Vehicle collision', 'Accident report'],
    'Assault': ['Assault complaint', 'Physical attack', 'Attacked by persons'],
    'Vandalism': ['Property damage', 'Vandalism complaint', 'Damage to property'],
    'Other': ['General complaint', 'Public nuisance', 'Need police help'],
}


def money(rng, lo, hi):
    return f"{rng.randrange(lo, hi, 500):,}"


def random_time(rng):
    hour = rng.choices(range(24), weights=[3, 2, 2, 2, 2, 3, 4, 5, 6, 6, 6, 6,
                                           6, 6, 6, 6, 6, 6, 7, 7, 7, 6, 5, 4])[0]
    return f"{hour:02d}:{rng.randrange(0, 60, 5):02d}"


def make_record(rng, i):
    category = rng.choices(list(CATEGORY_WEIGHTS), weights=CATEGORY_WEIGHTS.values())[0]
    severity = rng.choices([0, 1, 2], weights=SEVERITY_WEIGHTS[category])[0]
    loc_type = rng.choices(list(LOCATION_TYPE_WEIGHTS), weights=LOCATION_TYPE_WEIGHTS.values())[0]
    place = rng.choice(LOCALITIES[loc_type])
    incident_time = random_time(rng)
    hour = int(incident_time[:2])
    night = hour >= 22 or hour < 6
    prev = rng.choices([0, 1, 2, 3, 4, 5, 6, 8], weights=[45, 20, 12, 8, 6, 4, 3, 2])[0]

    body = rng.choice(TEMPLATES[category][severity]).format(
        place=place if loc_type != 'Unknown' else 'my area', item=rng.choice(ITEMS),
        small=money(rng, 500, 4000), medium=money(rng, 5000, 60000),
        large=money(rng, 100000, 900000))
    text = ' '.join(p for p in [rng.choice(OPENERS) + body, rng.choice(FILLERS)] if p).strip()

    # Hidden scoring rule + noise -> priority label.
    score = (1.6 * severity + CATEGORY_BASE[category] + (0.5 if night else 0.0)
             + LOCATION_BONUS[loc_type] + 0.3 * min(prev, 5) + rng.gauss(0, 0.45))
    priority = 'Low' if score < 1.9 else 'Medium' if score < 3.5 else 'High'

    return {
        'complaint_id': f'SYN-PRI-{i:04d}',
        'title': rng.choice(TITLES[category]),
        'complaint_description': text,
        'crime_category': category,
        'location': place,
        'location_type': loc_type,
        'incident_time': incident_time,
        'previous_related_reports': prev,
        'priority': priority,
    }


def main():
    rng = random.Random(SEED)
    rows = [make_record(rng, i) for i in range(1, N_RECORDS + 1)]
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    counts = {p: sum(r['priority'] == p for r in rows) for p in ('Low', 'Medium', 'High')}
    print(f"Wrote {len(rows)} SYNTHETIC records to {OUT_CSV}")
    print('Priority distribution: ' + ', '.join(f'{k}={v}' for k, v in counts.items()))


if __name__ == '__main__':
    main()
