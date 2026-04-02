#!/usr/bin/env python3
"""Add cultivation information from KAMPA book to Ayurwiki herb pages.

This script:
1. Creates 3 new herb page stubs (Gloriosa superba, Alpinia calcarata, Senna alexandrina)
2. Adds cultivation info from KAMPA book to all 24 herb pages
3. Adds KAMPA reference citation to each page
"""

import os
import re
import glob

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERBS_DIR = os.path.join(ROOT_DIR, "docs", "herbs")

KAMPA_REF_PATH = "../resources/books/KAMPA_Medicinal_Plants_Cultivation_Handbook.md"
KAMPA_REF_TITLE = "KAMPA - ಔಷಧಿ ಸಸ್ಯಗಳ ಕೃಷಿ ಕೈಪಿಡಿ (Medicinal Plants Cultivation Handbook)"

# ── New herb page stubs ──────────────────────────────────────────────

NEW_PAGES = {
    "Gloriosa_superba_-_Glory_Lily,_ಗೌರಿ_ಹೂವು,_Kalihari,_Addinabhi,_Adavi_Nabhi.md": {
        "title": "Gloriosa superba - Glory Lily, ಗೌರಿ ಹೂವು, Kalihari, Addinabhi, Adavi Nabhi",
        "content": """---
title: "Gloriosa superba - Glory Lily, ಗೌರಿ ಹೂವು, Kalihari, Addinabhi, Adavi Nabhi"
categories:
  - "Herbs_with_common_name_in_Kannada"
  - "Herbs_with_common_name_in_Hindi"
  - "Herbs_with_common_name_in_Tamil"
  - "Herbs_with_common_name_in_English"
  - "Herbs_with_common_name_in_Sanskrit"
  - "Herbs_with_Tuber_used_in_medicine"
  - "Herbs_with_Seeds_used_in_medicine"
  - "Ayurvedic_Herbs_known_to_be_helpful_to_treat_Gout"
  - "Ayurvedic_Herbs_known_to_be_helpful_to_treat_Skin_diseases"
  - "Ayurvedic_Herbs_known_to_be_helpful_to_treat_Parasites"
  - "Habit_-_Vine"
  - "Herbs"
  - "Index_of_Plants_which_can_be_propagated_by_Tubers"
  - "Colchicaceae"
date: 2024-01-01
---
# Gloriosa superba - Glory Lily, ಗೌರಿ ಹೂವು, Kalihari, Addinabhi, Adavi Nabhi

[TOC]

**Gloriosa superba** is a perennial climbing herb of the family Colchicaceae, known for its striking flame-like flowers with reflexed petals. The plant grows to 3.5-6 m height using leaf-tip tendrils for support. It is found in tropical and subtropical forests of India, particularly in the Western Ghats of Karnataka.

## Uses
Gout, Skin diseases, Parasitic infections, Joint pain, Inflammatory conditions, Wound healing.

## Parts Used
Tubers, Seeds.

## Chemical Composition
The tubers and seeds contain the alkaloid **Colchicine**, which is used in the treatment of gout and in cell biology research. Other alkaloids include gloriosine and superbine.

## Common names
| Language | Names |
| --- | --- |
| Kannada | ಗೌರಿ ಹೂವು Gauri Hoovu, ಅಕ್ಕ ತಂಗಿ ಬಳ್ಳಿ Akka Tangi Balli, ಜಗಳ ಗಂಟಿ ಗಿಡ Jagala Ganti Gida |
| Sanskrit | Langali, Agnishikhe |
| Hindi | Kalihari, Languli |
| Tamil | Addinabhi, Kartigaimoo |
| English | Glory Lily, Flame Lily, Climbing Lily |

## Properties
Reference: Dravya - Substance, Rasa - Taste, Guna - Qualities, Veerya - Potency, Vipaka - Post-digesion effect, Karma - Pharmacological activity, Prabhava - Therepeutics.
### Dravya
### Rasa
Tikta (Bitter), Katu (Pungent)
### Guna
Laghu (Light), Teekshna (Sharp)
### Veerya
Ushna (Hot)
### Vipaka
Katu (Pungent)
### Karma
Jvarahara (anti-fever), Krimighna (anti-parasitic), Shothahara (anti-inflammatory)
### Prabhava

## Habit
Vine

## Identification
### Leaf
Simple, alternate, sessile, lanceolate with tendril-tipped apex used for climbing. Leaves are 10-18 cm long.

### Flower
Bisexual, solitary, axillary. Petals 6, reflexed, initially green then turning bright yellow, orange, and red. Stamens 6, spreading.

### Fruit
Capsule, oblong, 5-7 cm long, containing numerous globose red seeds.

### Other features

## List of Ayurvedic medicine in which the herb is used

## Where to get the saplings
## Mode of Propagation
Tubers.

## How to plant/cultivate

## Commonly seen growing in areas
Tropical and subtropical forests, Western Ghats.

## Photo Gallery

## References

## External Links
""",
    },
    "Alpinia_calcarata_-_Lesser_Galangal,_ರಾಸ್ನಗಡ್ಡೆ,_Kulanjan,_Sittarutthe,_Rasna.md": {
        "title": "Alpinia calcarata - Lesser Galangal, ರಾಸ್ನಗಡ್ಡೆ, Kulanjan, Sittarutthe, Rasna",
        "content": """---
title: "Alpinia calcarata - Lesser Galangal, ರಾಸ್ನಗಡ್ಡೆ, Kulanjan, Sittarutthe, Rasna"
categories:
  - "Herbs_with_common_name_in_Kannada"
  - "Herbs_with_common_name_in_Hindi"
  - "Herbs_with_common_name_in_Tamil"
  - "Herbs_with_common_name_in_Telugu"
  - "Herbs_with_common_name_in_English"
  - "Herbs_with_common_name_in_Sanskrit"
  - "Herbs_with_Rhizome_used_in_medicine"
  - "Ayurvedic_Herbs_known_to_be_helpful_to_treat_Rheumatism"
  - "Ayurvedic_Herbs_known_to_be_helpful_to_treat_Fever"
  - "Ayurvedic_Herbs_known_to_be_helpful_to_treat_Cough"
  - "Habit_-_Herb"
  - "Herbs"
  - "Index_of_Plants_which_can_be_propagated_by_Rhizome"
  - "Zingiberaceae"
date: 2024-01-01
---
# Alpinia calcarata - Lesser Galangal, ರಾಸ್ನಗಡ್ಡೆ, Kulanjan, Sittarutthe, Rasna

[TOC]

**Alpinia calcarata** is a perennial herbaceous plant of the family Zingiberaceae, growing 1-2 m tall with highly aromatic rhizomes. It is found in the tropical and humid regions of South India, particularly in the Western Ghats and coastal Karnataka.

## Uses
Rheumatism, Fever, Indigestion, Cough, Cold, Skin diseases, Inflammation, Respiratory problems.

## Parts Used
Rhizome.

## Chemical Composition
The rhizome contains essential oils rich in 1,8-cineole, camphor, and other terpenoids.

## Common names
| Language | Names |
| --- | --- |
| Kannada | ರಾಸ್ನಗಡ್ಡೆ Rasnagadde, ರಸ್ಸೆ ಗಡ್ಡೆ Rasse Gadde |
| Sanskrit | Rasna |
| Hindi | Kulanjan |
| Tamil | Sittarutthe |
| Telugu | Chinne Dumparastamu |
| English | Lesser Galangal |

## Properties
Reference: Dravya - Substance, Rasa - Taste, Guna - Qualities, Veerya - Potency, Vipaka - Post-digesion effect, Karma - Pharmacological activity, Prabhava - Therepeutics.
### Dravya
### Rasa
Katu (Pungent)
### Guna
Laghu (Light), Teekshna (Sharp)
### Veerya
Ushna (Hot)
### Vipaka
Katu (Pungent)
### Karma
Vatahara (anti-Vata), Shothahara (anti-inflammatory)
### Prabhava

## Habit
Herb

## Identification
### Leaf
Simple, alternate, lanceolate, 30-60 cm long, pointed. Green with reddish tinge on stems.

### Flower
White with pink veins, arranged in terminal panicles.

### Fruit
Capsule, globose, red when ripe.

### Other features
Rhizomes are thick, aromatic, branching underground.

## List of Ayurvedic medicine in which the herb is used

## Where to get the saplings
## Mode of Propagation
Rhizome.

## How to plant/cultivate

## Commonly seen growing in areas
Tropical and humid forests, Coastal Karnataka, Western Ghats.

## Photo Gallery

## References

## External Links
""",
    },
    "Senna_alexandrina_-_Senna,_ಸೋನಾಮುಖಿ,_Senay,_Nelavirai,_Nelahonne,_Swarnapatri.md": {
        "title": "Senna alexandrina - Senna, ಸೋನಾಮುಖಿ, Senay, Nelavirai, Nelahonne, Swarnapatri",
        "content": """---
title: "Senna alexandrina - Senna, ಸೋನಾಮುಖಿ, Senay, Nelavirai, Nelahonne, Swarnapatri"
categories:
  - "Herbs_with_common_name_in_Kannada"
  - "Herbs_with_common_name_in_Hindi"
  - "Herbs_with_common_name_in_Tamil"
  - "Herbs_with_common_name_in_Telugu"
  - "Herbs_with_common_name_in_English"
  - "Herbs_with_common_name_in_Sanskrit"
  - "Herbs_with_Leaves_used_in_medicine"
  - "Ayurvedic_Herbs_known_to_be_helpful_to_treat_Constipation"
  - "Ayurvedic_Herbs_known_to_be_helpful_to_treat_Liver_disorders"
  - "Habit_-_Shrub"
  - "Herbs"
  - "Index_of_Plants_which_can_be_propagated_by_Seeds"
  - "Fabaceae"
date: 2024-01-01
---
# Senna alexandrina - Senna, ಸೋನಾಮುಖಿ, Senay, Nelavirai, Nelahonne, Swarnapatri

[TOC]

**Senna alexandrina** is a perennial shrub of the family Fabaceae, growing up to 1.8 m in height. It has compound leaves with 3-9 pairs of leaflets that are greenish-blue when fresh, turning yellow-green at maturity. The plant produces yellowish flowers and flat pods containing 5-7 kidney-shaped seeds. It is widely cultivated in semi-arid regions for its leaves and pods, which are used as a natural laxative.

## Uses
Constipation, Liver disorders, Blood purification, Digestive disorders, Kidney and urinary disorders.

## Parts Used
Leaves, Pods (Fruits).

## Chemical Composition
The leaves and pods contain sennosides (anthraquinone glycosides), primarily sennoside A and sennoside B, which are the active laxative compounds.

## Common names
| Language | Names |
| --- | --- |
| Kannada | ಸೋನಾಮುಖಿ Sonamukhi |
| Sanskrit | Swarnapatri |
| Hindi | Senay |
| Tamil | Nelavirai |
| Telugu | Nelahonne |
| English | Senna, Alexandrian Senna, Tinnevelly Senna |

## Properties
Reference: Dravya - Substance, Rasa - Taste, Guna - Qualities, Veerya - Potency, Vipaka - Post-digesion effect, Karma - Pharmacological activity, Prabhava - Therepeutics.
### Dravya
### Rasa
Tikta (Bitter)
### Guna
Laghu (Light), Ruksha (Dry)
### Veerya
Ushna (Hot)
### Vipaka
Katu (Pungent)
### Karma
Rechaka (laxative), Bhedana (purgative)
### Prabhava

## Habit
Shrub

## Identification
### Leaf
Compound, paripinnate, with 3-9 pairs of ovate-lanceolate leaflets, 1.5-5 cm long and 0.4-2 cm wide.

### Flower
Yellow, in axillary racemes.

### Fruit
Flat pod, 3.5-6.5 cm long, containing 5-7 flat kidney-shaped seeds.

### Other features

## List of Ayurvedic medicine in which the herb is used

## Where to get the saplings
## Mode of Propagation
Seeds.

## How to plant/cultivate

## Commonly seen growing in areas
Semi-arid regions, Sandy soils.

## Photo Gallery

## References

## External Links
""",
    },
}

# ── Cultivation data for all 24 plants ───────────────────────────────

KAMPA_DATA = [
    {
        "glob": "Tinospora_cordifolia_-_*",
        "pages": "09-12",
        "cultivation": (
            "Grows in all types of soil, including sandy soil. Found across India in moist deciduous forests. "
            "Propagated primarily through **stem cuttings** of about 15 cm length; seed germination is low. "
            "Plant at 1 x 1 m spacing in the main field with support trees for climbing. "
            "Irrigate regularly through drip system during summer. Weed once every 30 days. "
            "No major pest or disease problems. "
            "Harvest mature stems of 2.5 cm diameter by cutting from the base. "
            "Yield: approximately 1,500 kg fresh stems per hectare, yielding about 300 kg dried material. "
            "Economics: Rs. 30-40/kg; net profit Rs. 60,000-90,000 per hectare."
        ),
    },
    {
        "glob": "Withania_somnifera_-_*",
        "pages": "13-16",
        "cultivation": (
            "Drought-resistant plant suited for semi-arid regions. Ideal soil pH 7.5-8, sandy loam or light red soil. "
            "Annual rainfall of 150-600 mm is ideal. "
            "Propagated through **seeds** (5 kg per hectare). Sow at 1-2 cm depth in nursery beds of 10 x 1 m. "
            "Transplant after 24 days of germination at 60 x 90 cm spacing. Apply FYM at 10 tonnes/hectare. "
            "Generally rainfed; 3-4 irrigations during dry spells if needed. 1-2 weedings at 30-day intervals. "
            "Crop matures in **150-170 days**. Harvest when leaves yellow and berries turn red by uprooting. "
            "Yield: 3-4 quintals dried roots per hectare. "
            "Economics: Rs. 120-180/kg; net profit Rs. 75,000-1,00,000 per hectare. "
            "Improved varieties: CIM-Pushti, Jawahar Asgandh-20, Jawahar Asgandh-134, Arka Ashwagandha, Poshita, Nimidha."
        ),
    },
    {
        "glob": "Justicia_adhatoda_-_Malabar_nut,_Aadu*",
        "pages": "17-19",
        "cultivation": (
            "Thrives in fertile, well-drained loamy soils with 700-1700 mm annual rainfall and 12-32°C temperature range. "
            "Propagated through **semi-hardwood stem cuttings** of 15-20 cm with 3-4 nodes. "
            "Plant during June-July in nursery beds of 10 x 1 m. Transplant at 60 x 90 cm or 1 x 1 m spacing. "
            "Irrigate at 3-4 day intervals during establishment, then reduce. "
            "Pest-resistant due to bitter alkaloid content (vasicine). "
            "Harvest leaves **2 years** after planting. Perennial crop with 2-3 cuttings per year. "
            "Yield: 2,500-4,500 kg fresh leaves per hectare per year."
        ),
    },
    {
        "glob": "Salacia_chinensis_-_*",
        "pages": "20-22",
        "cultivation": (
            "Grows in tropical and subtropical forest regions. Found naturally in the Western Ghats. "
            "A woody climbing shrub with red/orange fruits containing 1-4 seeds. "
            "Propagated from **seeds** and **stem cuttings**. Plant at 6 x 7 m spacing for commercial cultivation. "
            "Irrigate at 3-4 day intervals during summer; maintain soil moisture. Minimal weeding after first year. "
            "Harvest roots and stems after **3-4 years** of maturity. "
            "Yield: approximately 18 tonnes dried material per hectare per harvest cycle. "
            "Economics: roots at Rs. 100-125/kg; net profit Rs. 1,50,000 in first year."
        ),
    },
    {
        "glob": "Centella_asiatica_-_*",
        "pages": "23-26",
        "cultivation": (
            "Perennial creeping herb found in moist, shady habitats along streams and marshy areas. "
            "Requires consistent moisture and partial shade. Soil should be rich in organic matter. "
            "Propagated through **stolons/runners** with 2-3 nodes each. Plant at 30 x 30 cm spacing. "
            "Irrigate every 3-4 days; maintain soil moisture at all times but avoid waterlogging. "
            "Pests: leaf-eating caterpillars and leaf spot diseases; manage with neem-based pesticides. "
            "Harvest leaves and stems at 3-4 month intervals. Multiple cuttings per year. "
            "Yield: 30-50 quintals fresh leaves per hectare per year (15-20 quintals dried). "
            "Economics: Rs. 60-70/kg; net profit Rs. 75,000-90,000 per hectare. "
            "Improved varieties: Arka Prabhavi (CA-13), Arka Divya (CA-1), Vallabha Medha."
        ),
    },
    {
        "glob": "Gloriosa_superba_-_*",
        "pages": "27-29",
        "cultivation": (
            "Grows in warm, humid tropical/subtropical areas with 300-400 cm annual rainfall. "
            "Red or loamy soils with good drainage and organic matter are ideal. pH 6-7. "
            "Propagated through **V-shaped tubers** (50-60 g each) planted at 10 cm depth. Seeds can be used but germination is slow. "
            "Requires support structures (trellis/stakes) for climbing. "
            "Irrigate at 4-day intervals after sprouting; avoid overwatering to prevent tuber rot. "
            "Perform 4-5 weedings during the crop period. "
            "Pests: lily bulb borer, hairy caterpillars. Diseases: leaf spot, tuber rot. Treat seed tubers with fungicide. "
            "Harvest tubers after 5-6 months when aerial parts dry. Collect seeds from ripe red-orange fruits at 7-8 months. "
            "Yield: 200-300 kg tubers and 150-180 kg seeds per hectare. "
            "Economics: seeds at Rs. 2,000-2,500/kg, tubers at Rs. 400-500/kg; net profit Rs. 15,00,000-20,00,000 over 4 years."
        ),
    },
    {
        "glob": "Plumbago_zeylanica_-_*",
        "pages": "30-32",
        "cultivation": (
            "Two varieties: white (*P. zeylanica*) and red (*P. indica*). Grows in sandy soil with good drainage. "
            "Perennial shrub reaching 1.5-2 m height. "
            "Propagated through **stem cuttings** of 10-15 cm with 2-3 nodes from previous year's growth. "
            "Plant in March-April at 60 x 40 cm or 45 x 30 cm spacing. Apply 10 tonnes FYM per hectare. "
            "Irrigate 4-5 times during dry months. Weed monthly during initial growth. "
            "No major pest or disease problems; use neem oil formulation if needed. "
            "Harvest roots after **10-12 months**. Clean and dry roots to 5-7.5 cm size. "
            "Yield: approximately 7,000 kg fresh roots per hectare. "
            "Economics: Rs. 90-100/kg; net profit Rs. 5,00,000 per hectare."
        ),
    },
    {
        "glob": "Ocimum_tenuiflorum_-_*",
        "pages": "33-36",
        "cultivation": (
            "Grows in almost all soil types; loamy, laterite, and well-drained soils are most suitable. "
            "Six varieties: Rama Tulasi (green, broad leaves), Krishna Tulasi (dark, reddish stems), "
            "Vana Tulasi (*O. gratissimum*), Karpura Tulasi, Nimbe Tulasi (*O. africanum*), Kasturi Tulasi (*O. basilicum*). "
            "Propagated through **seeds** (300 g mixed with sand per hectare). Sow in June in seedbeds. "
            "Seedlings emerge in 5 days; transplant at 4-6 weeks at 60 x 40 cm spacing. "
            "Irrigate 4-5 times after monsoon during dry months. Weed monthly. "
            "No major pest or disease problems. "
            "Harvest above-ground parts at 10-12 months and subsequently. Multiple harvests per year. "
            "Dried leaf yield: approximately 500 kg per hectare; essential oil content about 0.5%. "
            "Economics: leaves at Rs. 100-120/kg; net profit Rs. 2,00,000-2,50,000 per hectare. "
            "Improved varieties: CIM-Angna, CIM-Ayu, CIM-Kanchan, CIM-Soumya, CIM-Jyoti."
        ),
    },
    {
        "glob": "Alpinia_calcarata_-_*",
        "pages": "37-39",
        "cultivation": (
            "Grows in moist sandy loam and clay loam soils in tropical humid regions. "
            "Naturally found in forests of South India, Western Ghats, and coastal Karnataka. "
            "Propagated through **rhizome pieces**. Plow land 1-3 times, add 10 tonnes FYM per hectare. "
            "Plant rhizome segments at 30 x 30 cm or 45 x 30 cm spacing. Use 3.5-5.5 tonnes planting material per hectare. "
            "Irrigate regularly, 4-5 times after planting during dry months. Weed monthly. "
            "No major pest or disease issues; use neem oil spray if needed. "
            "Harvest rhizomes after **18-24 months** when leaves turn yellow. "
            "Yield: 12 tonnes fresh rhizome per hectare; 4 tonnes dried per hectare. "
            "Economics: Rs. 200-250/kg; net profit Rs. 2,95,000 per hectare."
        ),
    },
    {
        "glob": "Mucuna_pruriens_-_*",
        "pages": "40-43",
        "cultivation": (
            "Annual climbing legume suited for humid tropical and coastal areas. "
            "Grows in sandy loam to clay loam soils at 28-32°C with 60-65% humidity. "
            "Propagated through **seeds** (12 kg per acre). Sow directly in June-July at 30 x 30 cm spacing. "
            "Apply 10 tonnes FYM per hectare. Good drainage essential; no waterlogging. "
            "Irrigate every 15-20 days in November-December. Weed 2-3 times during growing season. "
            "Pests: grasshoppers and leaf-eating caterpillars; use neem oil spray. "
            "Harvest pods at **3-4 months** when mature but before opening. Handle carefully (pod hairs cause irritation). "
            "Yield: 1,500-1,750 kg dried seeds per hectare. Store at 10°C with <10% moisture. "
            "Economics: Rs. 60-80/kg; net profit Rs. 80,000-1,00,000 per hectare."
        ),
    },
    {
        "glob": "Bacopa_monnieri_-_*",
        "pages": "44-47",
        "cultivation": (
            "Perennial creeping herb growing in wet, marshy areas and waterlogged soils. "
            "Requires warm humid conditions (28-32°C, 60-65% humidity). "
            "Propagated through **stem cuttings** of 15 cm with at least one node. "
            "Plant at 15-30 cm spacing within rows. Apply 10 tonnes FYM per hectare. "
            "Requires consistent high moisture; irrigate every 3-4 days in summer. "
            "Weed 2-3 times at 30-day intervals. No major diseases; use neem oil for minor fungal issues. "
            "Harvest whole plant by cutting above crown level. First harvest at 3 months; subsequent every 2-3 months. "
            "Yield: 10 tonnes fresh herb per hectare annually; 3,000-3,500 kg dried. "
            "Economics: Rs. 60-80/quintal; net profit Rs. 55,000 per hectare. "
            "Improved varieties: CIM-Jagriti (1.94-2.07% Bacoside-A), Pragutshe, Subodhak."
        ),
    },
    {
        "glob": "Moringa_oleifera_-_*",
        "pages": "48-52",
        "cultivation": (
            "Medium-sized tree (10-15 m) suited for dry to semi-arid areas with all soil types. "
            "Sandy loam soils are most suitable; well-drained soils preferred. "
            "Propagated through **grafted seedlings** or **stem cuttings**. Apply 25 tonnes FYM per hectare. "
            "Plant at 3.25 x 5 m spacing. Grafted trees start fruiting at 8 months. "
            "Irrigate every 15 days in summer; fairly drought-tolerant when established. Weed 2-3 times in first year. "
            "Pests: sap-sucking lice, stem borers, pod borers. Diseases: root rot, leaf spot. Use neem-based sprays. "
            "Grafted varieties produce 200-250 pods per tree from second year. Each tree yields 40-50 kg leaves/year. "
            "Varieties: Jaffna, Chavakad Murungi, JKMK-1, Bhagya (KDM-01) -- 350-1000 pods/tree from second year. "
            "Economics: leaves Rs. 80-100/kg, pods Rs. 40-120/kg; net profit Rs. 1,00,000-2,00,000 per hectare."
        ),
    },
    {
        "glob": "Phyllanthus_niruri_-_*",
        "pages": "53-55",
        "cultivation": (
            "Small seasonal herb (10-50 cm) that resembles the amla plant. "
            "Grows in various soils in the Deccan plateau; propagates naturally through seeds with onset of rains. "
            "Can be cultivated as both rainy season and summer crop. Seeds: 400 g per acre. "
            "Apply 4 tonnes FYM per acre. "
            "Harvest entire three-month-old plants by pulling from the ground. Wash and dry in shade. "
            "Yield: 15-20 quintals dried herb per hectare. "
            "Economics: Rs. 70/kg; net profit Rs. 1,00,000-1,20,000 per hectare. "
            "Improved varieties: CIM Jeevan (Phyllanthin 0.77%)."
        ),
    },
    {
        "glob": "Andrographis_paniculata_-_*",
        "pages": "56-58",
        "cultivation": (
            "Annual herb growing 1-2 feet tall in fields, gardens, and wastelands. "
            "Grows in sandy and clayey mixed soils with 750-1500 mm rainfall. "
            "Propagated through **seeds**. Prepare seedbed in March-April. Sow in nursery at 10 tonnes FYM per hectare. "
            "Transplant 30-day-old seedlings at 30 x 30 cm spacing in June-July. "
            "Irrigate as needed (approximately every 5 cm daily). Weed at 30 days after planting. "
            "Harvest at flowering stage, approximately **2-3 months** after transplanting. Remove entire plant, dry in shade. "
            "Yield: 40-50 quintals per hectare (dried leaf and whole plant). "
            "Economics: net profit Rs. 60,000-1,00,000 per hectare. "
            "Improved variety: CIM-Megha."
        ),
    },
    {
        "glob": "Acorus_calamus_-_*",
        "pages": "59-61",
        "cultivation": (
            "Semi-aquatic plant with aromatic rhizomes, suited for hot humid tropical/subtropical regions. "
            "Grows in marshy areas and well-irrigated soil with adequate moisture. "
            "Propagated through **rhizome pieces** of 2-3 inches with well-developed buds. "
            "Plow field 4 times, apply 10 tonnes FYM per hectare. Plant at 30 x 30 cm spacing at 5 cm depth in June-July. "
            "Water regularly to maintain moisture but avoid waterlogging. Weed at 30 days after planting. "
            "No significant pest or disease problems. "
            "Harvest after **10-12 months**. Cut leaves, dig up rhizomes, clean and sun-dry. "
            "Yield: approximately 2,500 kg fresh rhizome per acre. "
            "Economics: Rs. 60-70/kg; net profit Rs. 90,000 per hectare."
        ),
    },
    {
        "glob": "Aegle_marmelos_-_*",
        "pages": "62-64",
        "cultivation": (
            "Hardy deciduous tree (6-10 m) growing in light to heavy soils. "
            "Tolerates alkaline soils (pH 6.5-9.5), 250-1500 mm rainfall, and extreme temperatures. "
            "Propagated through **seeds** collected from ripe fruits. Seeds germinate in 10-12 days in nursery. "
            "Raise seedlings in polythene bags; transplant to main field at 10-12 m spacing. "
            "Moderate watering during first season and dry periods; drought-tolerant when established. "
            "No major pest or disease problems commercially. Weed around tree base regularly. "
            "Trees start bearing fruit at **7-8 years**. One tree yields 300-400 fruits per season. "
            "Varieties: Panta Aparna, Panta Shivani, Panta Sujata, Narendra Bael-5, 6, 9, 16, 17. "
            "Economics: fruit Rs. 40-60/kg, bark Rs. 50-70/kg, root Rs. 70-100/kg."
        ),
    },
    {
        "glob": "Phyllanthus_emblica_-_*Gooseberry*",
        "pages": "65-69",
        "cultivation": (
            "Small to medium deciduous tree (8-10 m) grown in forests and orchards. "
            "Fruit contains 200 mg Vitamin C per 100 g, one of the richest natural sources. "
            "Sandy loam to medium black soils with good drainage; pH 6.5-9.5; 250-1500 mm rainfall. "
            "Propagated through **seeds** and **budding** (shield budding at 60° angle). "
            "Prepare pits of 2.5 x 1.8 m at 0.5 m depth in March-April. Plant during June-July. About 900 plants per acre. "
            "Irrigate every 3-6 days during dry season and flowering. Weed in initial years; apply mulch around base. "
            "Pests: bark borers, shootfly, fruit borers. Diseases: leaf blight, leaf spot. Use Bordeaux mixture and neem sprays. "
            "Trees bear fruit after **4-5 years**. Fruits mature in November, harvested by hand. "
            "Yield: 50-70 kg fruit per tree per year; 10,000-15,000 kg green fruit per hectare. Trees produce 20+ years. "
            "Varieties: Banarasi, Krishna, Chakaiya, Kanchan, Narendra Amla-6, 7, 9, 10. "
            "Economics: fruit Rs. 20-30/kg, powder Rs. 80-120/kg."
        ),
    },
    {
        "glob": "Gymnema_sylvestre_-_*",
        "pages": "70-73",
        "cultivation": (
            "Woody climbing vine that suppresses sweet taste when chewed (hence 'Madhunashini' -- destroyer of sugar). "
            "Found in Western and Eastern Ghats at 100-1000 m elevation. Needs support structures for climbing. "
            "Two varieties: small-leaved (1.5-2.5 cm, hilly regions) and large-leaved (3.5-5 cm, plains). "
            "Propagated through **seeds** and **stem cuttings**. Plant at 25 x 25 cm spacing in nursery; "
            "transplant during June-July in pits of 2.5 x 1.8 m at 0.5 m depth. About 900 plants per acre. "
            "Provide trellis/Y-shaped supports at 1 m intervals. "
            "Irrigate every 3-6 days; increase in summer. Weed regularly; mulch around base. "
            "Pests: leaf-eating caterpillars. Diseases: leaf blight, leaf spot. Use neem spray and Bordeaux mixture. "
            "First leaf harvest after **2 years**. Harvest leaves by hand once/year; dry in shade. "
            "Yield: 10,000-15,000 kg fresh leaves per hectare. "
            "Economics: dried leaf Rs. 50-80/kg; net profit Rs. 4,00,000-5,00,000 per hectare."
        ),
    },
    {
        "glob": "Decalepis_hamiltonii_-_*",
        "pages": "74-77",
        "cultivation": (
            "Perennial woody climber found in Western Ghats forests. Roots are thick, fragrant, up to 150 cm long. "
            "Endangered species with high commercial value. "
            "Sandy loam soil with good drainage and organic matter. Annual rainfall 800-1200 mm. "
            "Propagated through **seeds** (sow in February-March in nursery bags) and **stem cuttings** "
            "(2-3 node cuttings treated with 10 ppm IBA rooting hormone). "
            "Prepare pits of 45 x 45 x 45 cm at 3 x 3 m spacing. Add 10 kg FYM per pit. Plant in October-November. "
            "Provide trellis support. Irrigate every 4-7 days in dry season. Weed every 2-3 months. "
            "Harvest roots after **18-24 months**. Wash, shade-dry, and peel. "
            "Yield: 7,000-8,000 kg dried roots per hectare. "
            "Economics: fresh roots Rs. 250-350/kg; net profit Rs. 18,00,000-19,00,000 per hectare."
        ),
    },
    {
        "glob": "Asparagus_racemosus_-_*",
        "pages": "78-80",
        "cultivation": (
            "Perennial climbing herb with 15-40 cm long fleshy tuberous roots, 60-80 tubers per cluster. "
            "Grows in tropical/subtropical regions up to 1500 m. Sandy loam soil, pH 4.6-6.5. "
            "Annual rainfall 800-1200 mm; tolerates partial shade. "
            "Propagated through **seeds** (7 kg per hectare). Soak seeds for 2-3 days before sowing in October-November. "
            "Transplant 40-50 day seedlings at 45 x 30 cm spacing in May-June. Apply 10 tonnes FYM per hectare. "
            "Provide 4-6 feet support structures for climbing. "
            "Irrigate twice monthly in summer. Weed regularly after 30 days. "
            "Pests: stem borer, cluster bugs, mites. Diseases: leaf rot, powdery mildew. "
            "Harvest tuberous roots after **2-3 years**. Roots are 0.5-1 m long. "
            "Yield: approximately 3,300 kg dried roots per hectare; 6-10 kg dried roots per plant. "
            "Economics: Rs. 800-900/kg; net profit Rs. 14,70,000 per hectare. "
            "Variety: RS-1."
        ),
    },
    {
        "glob": "Rauvolfia_serpentina_-_*",
        "pages": "81-84",
        "cultivation": (
            "Important endangered perennial shrub (15-45 cm tall) with thick tuberous roots. "
            "Well-drained loamy to sandy loam soil, pH 4.6-6.5. Temperature 10-30°C. Prefers partial shade. "
            "Propagated through **seeds**, **root cuttings**, and **stem cuttings** (10-12 cm with nodes). "
            "Sow seeds in December-January in nursery bags at 25 x 20 cm spacing. Seeds germinate in ~15 days. "
            "Transplant after 3 months. Main field spacing 3 x 6 m; about 550 plants per hectare. "
            "Maintain moist conditions; irrigate during dry periods. Weed monthly. "
            "Naturally pest-resistant; no major diseases. "
            "Harvest roots after plant matures. Contains reserpine and serpentine alkaloids for treating hypertension. "
            "Economics: bark Rs. 150/kg."
        ),
    },
    {
        "glob": "Saraca_asoca_-_*",
        "pages": "85-88",
        "cultivation": (
            "Medium-sized evergreen tree (up to 9 m) with compound pinnate leaves and orange flower clusters. "
            "Grows in humid subtropical regions, preferring shade and well-drained soil. "
            "Found naturally in Western Ghats, Sri Lanka, Orissa, and Assam at up to 750 m elevation. "
            "Propagated through **seeds** sown in nursery bags at 25 x 20 cm spacing. Germination in ~15 days. "
            "Transplant 12-month seedlings at 3 x 3 m or 3 x 6 m spacing during monsoon (June-July). "
            "About 550 plants per hectare. Apply 10 tonnes FYM per hectare. "
            "Water young plants regularly for 2 years; drought-tolerant once established. "
            "Pests: aphids. Diseases: leaf-yellowing fungal infections. "
            "Bark is the main harvested part. Trees start producing harvestable bark from **6-8 years**. "
            "Bark should be harvested sustainably, allowing regeneration. "
            "Economics: bark Rs. 150/kg."
        ),
    },
    {
        "glob": "Senna_alexandrina_-_*",
        "pages": "89-92",
        "cultivation": (
            "Perennial shrub (up to 1.8 m) suited for semi-arid to arid climatic conditions. "
            "Grows in sandy loam and gravelly soil; pH 7-8.5. Suited for rainfed and irrigated conditions. "
            "Propagated through **seeds** (2 kg per hectare). Sow 110-115 days before main harvest. "
            "Plant in rows at 30 cm spacing; thin to 4-5 cm between plants at 15 days. "
            "Can be rainfed; provide 5-8 irrigations during prolonged dry spells. "
            "Weed at 25-30 days and 75-80 days after sowing. "
            "Pests: stem borer, caterpillars, pod borer. Diseases: leaf blight, powdery mildew, stem rot. "
            "Use neem seed kernel extract at 15-day intervals. "
            "First leaf harvest at **50-90 days**; second at 90-100 days; third at 130-150 days. 3 harvests per year. "
            "Dry leaves in shade. Pods collected when brown at 10-12 days after maturity. "
            "Yield: 15 quintals dry leaves and 7 quintals pods per hectare per year. "
            "Economics: Rs. 25-50/kg; net profit Rs. 50,000-80,000 per hectare. "
            "Varieties: Sona, Gujarat Anand Senna-1, KKM-Sel 1."
        ),
    },
    {
        "glob": "Piper_longum_-_*",
        "pages": "93-96+",
        "cultivation": (
            "Perennial climbing vine of the Piperaceae family, related to black pepper. "
            "Requires well-drained, fertile loamy soil rich in organic matter. Warm, humid climate with good rainfall. "
            "Propagated through **stem cuttings** and **root suckers** (5-10 cm with 2 nodes). "
            "Root cuttings in nursery beds with vermicompost. Rooted plants ready in 40-50 days. "
            "Provide shade during initial stages. Drip irrigation preferred; water every 15 days. Weed monthly. "
            "Pests: aphids. Diseases: leaf rot, yellowing. Use neem oil spray and Bordeaux mixture. "
            "Apply Trichoderma (5 kg/hectare) and Pseudomonas for biological pest control. "
            "Fruits start at **6 months**. Harvest green fruits before they turn reddish-brown. "
            "10 kg fresh fruits yield 1.5 kg dried Hippali. Shade-dry for 15 days then sun-dry. "
            "First year: ~160 kg/hectare; third year onwards: ~400 kg/hectare. Roots also harvestable after 3 years. "
            "Economics: fruit Rs. 200-250/kg, roots Rs. 80-100/kg; net profit Rs. 1,60,000-2,10,000 over 3 years."
        ),
    },
]


def find_herb_file(pattern):
    """Find the herb file matching a glob pattern."""
    matches = glob.glob(os.path.join(HERBS_DIR, pattern))
    if matches:
        return matches[0]
    return None


def get_next_ref_number(content):
    """Find the highest reference number in the file and return next one."""
    # Look for numbered references like "1." or "N."
    nums = re.findall(r"^(\d+)\.\s", content, re.MULTILINE)
    if nums:
        return max(int(n) for n in nums) + 1
    return 1


def add_cultivation_to_page(filepath, cultivation_text, pages):
    """Add KAMPA cultivation info and reference to a herb page."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    modified = False

    # 1. Add/enhance "How to plant/cultivate" section
    cultivation_section = f"\n{cultivation_text}\n"

    # Check if "## How to plant/cultivate" exists
    how_to_match = re.search(r"## How to plant/cultivate\n", content)
    if how_to_match:
        # Find the next ## section after "How to plant/cultivate"
        next_section = re.search(
            r"\n## ",
            content[how_to_match.end():]
        )
        if next_section:
            insert_pos = how_to_match.end() + next_section.start()
            existing_text = content[how_to_match.end():insert_pos].strip()
            # Only add if not already containing KAMPA info
            if "KAMPA" not in existing_text:
                if existing_text:
                    # Append after existing content
                    new_content = (
                        content[:insert_pos].rstrip()
                        + "\n\n"
                        + cultivation_section.strip()
                        + "\n\n"
                        + content[insert_pos:]
                    )
                else:
                    # Replace empty section
                    new_content = (
                        content[:how_to_match.end()]
                        + cultivation_section
                        + "\n"
                        + content[insert_pos:]
                    )
                content = new_content
                modified = True
        else:
            # Last section in file
            if "KAMPA" not in content[how_to_match.end():]:
                content = (
                    content[:how_to_match.end()]
                    + cultivation_section
                    + "\n"
                )
                modified = True
    else:
        # Find "## Commonly seen growing" or "## Photo Gallery" to insert before
        insert_before = re.search(
            r"\n## (Commonly seen growing|Photo Gallery|References)",
            content
        )
        if insert_before:
            pos = insert_before.start()
            content = (
                content[:pos]
                + "\n## How to plant/cultivate\n"
                + cultivation_section
                + content[pos:]
            )
            modified = True

    # 2. Add KAMPA reference
    if "KAMPA" not in content and "ಔಷಧಿ ಸಸ್ಯಗಳ ಕೃಷಿ ಕೈಪಿಡಿ" not in content:
        # Find the last "## References" section
        ref_positions = [m.start() for m in re.finditer(r"## References", content)]
        if ref_positions:
            last_ref = ref_positions[-1]
            # Find content after last "## References"
            after_ref = content[last_ref:]

            ref_num = get_next_ref_number(after_ref)

            # Find insertion point (before ## External Links or at end of references section)
            ext_links = re.search(r"\n## External Links", after_ref)
            if ext_links:
                insert_at = last_ref + ext_links.start()
            else:
                # Insert at end of file or before next major section
                next_major = re.search(r"\n## (?!References)", after_ref[len("## References"):])
                if next_major:
                    insert_at = last_ref + len("## References") + next_major.start()
                else:
                    insert_at = len(content)

            ref_entry = (
                f"\n{ref_num}. **[{KAMPA_REF_TITLE}]({KAMPA_REF_PATH})**. "
                f"Karnataka Medicinal Plants Authority (KAMPA), Bengaluru, 2024, pp. {pages}.\n"
                f"   Cultivation details including soil requirements, propagation methods, "
                f"planting, irrigation, harvest timing, yield estimates, and economics.\n"
            )
            content = content[:insert_at] + ref_entry + content[insert_at:]
            modified = True

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def create_new_pages():
    """Create new herb page stubs."""
    created = 0
    for filename, data in NEW_PAGES.items():
        filepath = os.path.join(HERBS_DIR, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(data["content"].lstrip())
            print(f"  Created: {filename}")
            created += 1
        else:
            print(f"  Already exists: {filename}")
    return created


def main():
    print("=== KAMPA Medicinal Plants Cultivation Info ===\n")

    # 1. Create new herb pages
    print("Step 1: Creating new herb page stubs...")
    created = create_new_pages()
    print(f"  Created {created} new pages\n")

    # 2. Add cultivation info to all 24 pages
    print("Step 2: Adding cultivation info to herb pages...")
    updated = 0
    errors = 0
    for entry in KAMPA_DATA:
        filepath = find_herb_file(entry["glob"])
        if not filepath:
            print(f"  NOT FOUND: {entry['glob']}")
            errors += 1
            continue

        filename = os.path.basename(filepath)
        success = add_cultivation_to_page(filepath, entry["cultivation"], entry["pages"])
        if success:
            print(f"  Updated: {filename[:80]}...")
            updated += 1
        else:
            print(f"  Skipped (already has KAMPA info): {filename[:80]}...")

    print(f"\nDone! Updated: {updated}, Errors: {errors}")


if __name__ == "__main__":
    main()
