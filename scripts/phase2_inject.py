#!/usr/bin/env python3
"""Phase 2: Inject Vrkshayurveda references into matching herb pages."""

import json
import re
import os
from datetime import datetime

DOCS = "/Volumes/T9/Saaranga/Ayurwiki/docs/herbs"
INDEX = "/Volumes/T9/Saaranga/Ayurwiki/references/index.json"
LOG_FILE = "/Volumes/T9/Saaranga/Ayurwiki/references/injection-log.json"
PHASE_LOG = "/Volumes/T9/Saaranga/Ayurwiki/logs/phase2-vrkshayurveda-{}.log".format(
    datetime.now().strftime("%Y-%m-%d")
)

# Mapping from index latin_name to herb page filename
FILE_MAP = {
    "Aegle marmelos": "Aegle_marmelos_-_Bilva.md",
    "Ficus religiosa": None,  # no page
    "Emblica officinalis": "Phyllanthus_emblica_-_Emblic,_Amalaki.md",
    "Ficus benghalensis": None,  # no page
    "Azadirachta indica": "Azadiracta_indica_-_Nimba,_Neem.md",
    "Ficus lacor": "Ficus_lacor.md",
    "Mangifera indica": "Mangifera_Indica_-_Mango.md",
    "Butea monosperma": "Butea_monosperma_-_Palāśaḥ.md",
    "Ficus glomerata": None,  # no page
    "Punica granatum": "Punica_granatum_-_Dadima.md",
    "Musa paradisiaca": "Musa_paradisiaca_-_Rambha.md",
    "Artocarpus heterophyllus": "Artocarpus_heterophyllus_-_Panasa,_Jackfruit.md",
    "Artocarpus lakoocha": "Artocarpus_lacucha.md",
    "Cocos nucifera": "Cocos_nucifera_-_Coconut_tree.md",
    "Moringa oleifera": "Moringa_oleifera_-_Drumstick.md",
    "Alstonia scholaris": "Alstonia_scholaris_-_Saptaparna,_Doddapala.md",
    "Nyctanthes arbor-tristis": "Nyctanthes_arbor-tristis_-_Parijata.md",
    "Prosopis cineraria": "Prosopis_cineraria_-_Indian_mesquite.md",
    "Capparis decidua": None,  # no exact page
    "Zizyphus nummularia": "Ziziphus_nummularia_-_Balakapriya.md",
    "Mimusops elengi": "Mimusops_elengi_-_Bakula,_Ranjal.md",
    "Saraca asoca": "Saraca_asoca_-_Ashoka,_Ashoka_tree.md",
    "Borassus flabellifer": "Borassus_flabellifer_-_Talah.md",
    "Bambusa arundinacea": "Bambusa_bambos.md",
    "Phoenix sylvestris": "Phoenix_sylvestris_-_Kharjura.md",
    "Areca catechu": None,  # no page
    "Vitis vinifera": "Vitis_vinifera_-_Draksha,_Grape.md",
    "Michelia champaca": None,  # reclassified, skip
    "Hiptage benghalensis": "Hiptage_benghalensis_-_Madhavi_lata.md",
    "Callicarpa macrophylla": "Callicarpa_macrophylla.md",
    "Citrus limon": "Citrus_limon_-_Bijapuraka,_Jambira.md",
    "Citrus medica": "Citrus_medica_linn_-_Maatulunga.md",
    "Citrus reticulata": "Citrus_reticulata_-_Naaranga.md",
    "Benincasa hispida": "Benincasa_hispida_-_Kushmanda,_Winter_melon.md",
    "Rosa centifolia": "Rosa_centifolia.md",
    "Cucumis sativus": "Cucumis_sativus_-_Cucumber,_Kantakilata.md",
    "Crocus sativus": "Crocus_sativus_-_Kesara.md",
    "Origanum majorana": "Origanum_majorana_-_Ajanmasurabhi,_Majorana.md",
    "Curcuma longa": "Curcuma_longa_-_Haridra.md",
    "Embelia ribes": "Embelia_ribes_-_Vidanga.md",
    "Momordica charantia": "Momordica_charantia_-_Karavellaka,_Karabellam.md",
    "Albizia lebbeck": "Albizia_lebbeck_-_Shirisha.md",
    "Carissa carandas": "Carissa_carandas.md",
    "Grewia asiatica": "Grewia_asiatica.md",
    "Sesamum indicum": "Sesamum_indicum_-_Sesame,_Snehaphala.md",
    "Trichosanthes dioica": "Trichosanthes_dioica_-_Patola.md",
    "Solanum melongena": None,  # no page
    "Glycyrrhiza glabra": "Glycyrrhiza_glabra_-_Yashtimadhu.md",
    "Diospyros tomentosa": "Diospyros_tomentosa.md",
    "Aconitum heterophyllum": "Aconitum_heterophyllum_-_Ativisa,_Indian_Atees.md",
    "Acorus calamus": "Acorus_calamus_-_Jatila.md",
    "Saussurea lappa": "Saussurea_lappa_-_Kusta.md",
    "Rubia cordifolia": "Rubia_cordifolia_-_Manjishtha.md",
    "Symplocos racemosa": None,  # different species files only
    "Terminalia arjuna": "Terminalia_arjuna_-_Arjuna,_White_Marudah.md",
    "Terminalia bellirica": "Terminalia_bellerica_roxb_-_Bibhitaki.md",
    "Terminalia chebula": "Terminalia_chebula_-_Haritaki.md",
    "Hordeum vulgare": "Hordeum_vulgare_-_Aksata.md",
    "Pueraria tuberosa": "Pueraria_tuberosa_-_Vidarikanda.md",
    "Ricinus communis": "Ricinus_communis_-_Gandharvataila.md",
    "Tamarindus indica": "Tamarindus_indica_-_Amalika.md",
    "Bauhinia variegata": "Bauhinia_variegata_-_Kaancanara.md",
    "Alangium lamarckii": "Alangium_lamarcki.md",
    "Jasminum sambac": "Jasminum_sambac_-_Mallika.md",
    "Zizyphus mauritiana": "Ziziphus_mauritiana_-_Common_jujube.md",
    "Pandanus tectorius": "Pandanus_tectorius_-_Ketaka.md",
    "Nelumbo nucifera": "Nelumbo_nucifera.md",
    "Nerium indicum": None,  # no page
    "Cyperus rotundus": "Cyperus_rotundus_-_Mustaka.md",
    "Stereospermum suaveolens": "Stereospermum_chelonoides_-_Patala.md",
    "Zingiber officinale": "Zingiber_officinale.md",
    "Elettaria cardamomum": "Elettaria_cardamomum_-_Ela,_Cardamom.md",
    "Manilkara hexandra": "Manilkara_hexandra_-_Kshirini.md",
    "Indigofera tinctoria": "Indigofera_tinctoria_-_Asita,_Nili.md",
    "Desmostachya bipinnata": "Desmostachya_bipinnata_-_Darbha.md",
    "Saccharum munja": "Saccharum_munja_-_Munja.md",
    "Cucurbita maxima": "Cucurbita_maxima_-_Alambu,_Kola.md",
    "Luffa acutangula": "Luffa_acutangula_-_Jaalini.md",
    "Oryza sativa": None,  # skip Oryza - not a herb page match
    "Ocimum sanctum": "Ocimum_tenuiflorum_-_Tulsi_plant.md",
}

SOURCE = {
    "title": "Vrksayurveda of Surapala",
    "author": "Pandey, Gyanendra (translator)",
    "publisher": "Chowkhamba Sanskrit Series Office, Varanasi",
    "year": "2010",
}


def condense_summary(medicinal_uses, dosage_preparation):
    """Condense the index entry into 1-3 sentences for citation."""
    # Take medicinal_uses, truncate to ~2-3 sentences
    sentences = re.split(r'(?<=[.!])\s+', medicinal_uses.strip())
    # Pick first 2-3 sentences that fit well
    summary = ""
    for s in sentences[:3]:
        if len(summary) + len(s) < 400:
            summary += s + " "
        else:
            break
    summary = summary.strip()
    if not summary:
        summary = medicinal_uses[:300].strip()
    # Add dosage info if short enough
    if dosage_preparation and len(summary) < 250:
        dose_sentences = re.split(r'(?<=[.!])\s+', dosage_preparation.strip())
        if dose_sentences:
            summary += " " + dose_sentences[0]
    return summary


def find_last_ref_number(content):
    """Find the highest numbered reference in the last ## References section."""
    # Find all ## References positions
    ref_positions = [m.start() for m in re.finditer(r'^## References', content, re.MULTILINE)]
    if not ref_positions:
        return 0, len(content)

    last_ref_pos = ref_positions[-1]
    # Get content after the last ## References
    after_ref = content[last_ref_pos:]

    # Find next ## heading after References (if any)
    next_heading = re.search(r'\n## [^R]', after_ref[len("## References"):])
    if next_heading:
        section_end = last_ref_pos + len("## References") + next_heading.start()
    else:
        section_end = len(content)

    # Find highest numbered reference
    section_text = content[last_ref_pos:section_end]
    numbers = re.findall(r'^(\d+)\.', section_text, re.MULTILINE)
    if numbers:
        return max(int(n) for n in numbers), section_end
    return 0, section_end


def format_citation(entry, ref_number):
    """Format a single citation entry."""
    pages = entry.get("page_number", "")
    page_str = f"pp. {pages}" if "," in pages or "-" in pages else f"p. {pages}"

    summary = condense_summary(
        entry.get("medicinal_uses", ""),
        entry.get("dosage_preparation", "")
    )

    citation = (
        f"{ref_number}. **{SOURCE['author']}. "
        f"*{SOURCE['title']}*. "
        f"{SOURCE['publisher']}, {SOURCE['year']}, {page_str}.**\n"
        f"   {summary}"
    )

    # Add classical citations as blockquotes
    classical = entry.get("classical_citations", [])
    if classical:
        for c in classical:
            citation += f"\n   > *As cited in: {c}*"

    return citation


def inject_reference(filepath, entry):
    """Inject a reference into a herb page. Returns status dict."""
    if not os.path.exists(filepath):
        return {"status": "error", "note": f"File not found: {filepath}"}

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if Vrkshayurveda is already cited
    if "Vrksayurveda" in content or "Vrkshayurveda" in content:
        return {"status": "skipped", "note": "Vrkshayurveda already cited"}

    last_num, section_end = find_last_ref_number(content)
    new_num = last_num + 1

    citation = format_citation(entry, new_num)

    # Find insertion point: end of last ## References section content
    # We insert before the section_end
    # Find the last non-empty line before section_end
    before = content[:section_end].rstrip()
    after = content[section_end:]

    new_content = before + "\n" + citation + "\n" + after

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    return {"status": "ok", "ref_number": new_num}


def main():
    with open(INDEX, "r", encoding="utf-8") as f:
        index = json.load(f)

    injection_log = []
    stats = {"ok": 0, "skipped": 0, "no_match": 0, "error": 0}
    processed = 0

    for entry in index:
        latin = entry["latin_name"]
        plant = entry["plant_name"]
        filename = FILE_MAP.get(latin)

        if filename is None:
            injection_log.append({
                "file": None,
                "plant": plant,
                "latin_name": latin,
                "references_added": 0,
                "sources_used": [],
                "status": "no_match"
            })
            stats["no_match"] += 1
            processed += 1
            continue

        filepath = os.path.join(DOCS, filename)
        result = inject_reference(filepath, entry)

        log_entry = {
            "file": f"docs/herbs/{filename}",
            "plant": plant,
            "latin_name": latin,
            "references_added": 1 if result["status"] == "ok" else 0,
            "sources_used": ["Vrksayurveda of Surapala"] if result["status"] == "ok" else [],
            "status": result["status"]
        }
        if "note" in result:
            log_entry["note"] = result["note"]

        injection_log.append(log_entry)
        stats[result["status"]] += 1
        processed += 1

        if processed % 10 == 0:
            print(f"Progress: {processed}/{len(index)} | "
                  f"ok={stats['ok']} skipped={stats['skipped']} "
                  f"no_match={stats['no_match']} error={stats['error']}")

    # Write injection log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(injection_log, f, indent=2, ensure_ascii=False)

    # Write phase log
    with open(PHASE_LOG, "w", encoding="utf-8") as f:
        f.write(f"Phase 2 Injection Log\n")
        f.write(f"{'='*50}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: Vrksayurveda of Surapala\n\n")
        f.write(f"Results:\n")
        f.write(f"  Total entries processed: {len(index)}\n")
        f.write(f"  References injected (ok): {stats['ok']}\n")
        f.write(f"  Skipped (already cited): {stats['skipped']}\n")
        f.write(f"  No matching page: {stats['no_match']}\n")
        f.write(f"  Errors: {stats['error']}\n\n")
        f.write(f"Files modified:\n")
        for log in injection_log:
            if log["status"] == "ok":
                f.write(f"  {log['file']} ({log['plant']})\n")

    print(f"\n{'='*50}")
    print(f"Phase 2 Complete")
    print(f"{'='*50}")
    print(f"Total: {len(index)} | OK: {stats['ok']} | "
          f"Skipped: {stats['skipped']} | No match: {stats['no_match']} | "
          f"Error: {stats['error']}")
    print(f"Injection log: {LOG_FILE}")
    print(f"Phase log: {PHASE_LOG}")


if __name__ == "__main__":
    main()
