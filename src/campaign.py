from llama_cpp import Llama
from codecarbon import EmissionsTracker
from pmic import MesurePMIC      # methode 2 : mesure onboard REELLE du Pi 5 (mock hors Pi) [Amine]
from prise import MesurePrise    # methode 3 : mesure au MUR via prise Z-Wave (mock hors Pi) [Amine]
import pandas as pd
import json
import os
import time
import contextlib
import itertools
from datetime import datetime

# ============================================================
#  REGLAGES DE LA CAMPAGNE  (tout se modifie ICI)
# ============================================================
MACHINE = "Pi5"                         # "PC" maintenant, "Pi5" plus tard
TEMPERATURE = 0.0                       # 0 = reponses deterministes (reproductibles)
N_REPETITIONS = 3                       # nb de mesures par configuration
MAX_TOKENS_VALEURS = [16, 64, 256]      # grille de longueurs de reponse a tester

# --- Methode 3 : prise connectee (mesure au mur) ---
MESURER_PRISE = True                     # True = on utilise la prise
PRISE_NODE_ID = 3                       # numero du noeud de la prise (voir zwave-js-ui apres appairage)
BASELINE_W = 3.5                        # puissance idle au mur a soustraire (W). Mesurer Pi au repos :
                                        #   python src/prise.py --duree 120   -> reporter la "Puissance moyenne"

# Liste des modeles a tester : on en ajoute/enleve autant qu'on veut.
# (Il faut que le fichier .gguf existe dans models/ ; sinon il est ignore.)
#MODELES = [
#    {"nom": "Gemma-3-1B", "quantification": "Q3_K_M", "path": "models/gemma-3-1b-it-Q3_K_M.gguf"},
#    {"nom": "Gemma-3-1B", "quantification": "Q4_K_M", "path": "models/gemma-3-1b-it-Q4_K_M.gguf"},
#    {"nom": "Gemma-3-1B", "quantification": "Q8_0",   "path": "models/gemma-3-1b-it-Q8_0.gguf"},
#]
# ---- CAMPAGNE n_threads : décommenter ce bloc, commenter le bloc ci-dessus ----
MODELES = []
for nom, quants, paths in [
    ("Llama-3.2-1B", ["Q3_K_L","Q4_K_M","Q8_0"], ["models/Llama-3.2-1B-Instruct-Q3_K_L.gguf","models/Llama-3.2-1B-Instruct-Q4_K_M.gguf","models/Llama-3.2-1B-Instruct-Q8_0.gguf"]),
    ("Gemma-3-1B",   ["Q3_K_M","Q4_K_M","Q8_0"], ["models/gemma-3-1b-it-Q3_K_M.gguf","models/gemma-3-1b-it-Q4_K_M.gguf","models/gemma-3-1b-it-Q8_0.gguf"]),
    ("Qwen2.5-1.5B", ["Q3_K_L","Q4_K_M","Q8_0"], ["models/Qwen2.5-1.5B-Instruct-Q3_K_L.gguf","models/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf","models/Qwen2.5-1.5B-Instruct-Q8_0.gguf"]),
]:
    for q, p in zip(quants, paths):
        for t in [1, 2, 4]:
            MODELES.append({"nom": nom, "quantification": q, "path": p, "n_threads": t, "n_ctx": 2048})

# ---- CAMPAGNE n_ctx : décommenter ce bloc, commenter les blocs ci-dessus ----
# MODELES = []
# for nom, quants, paths in [
#     ("Llama-3.2-1B", ["Q3_K_L","Q4_K_M","Q8_0"], ["models/Llama-3.2-1B-Instruct-Q3_K_L.gguf","models/Llama-3.2-1B-Instruct-Q4_K_M.gguf","models/Llama-3.2-1B-Instruct-Q8_0.gguf"]),
#     ("Gemma-3-1B",   ["Q3_K_M","Q4_K_M","Q8_0"], ["models/gemma-3-1b-it-Q3_K_M.gguf","models/gemma-3-1b-it-Q4_K_M.gguf","models/gemma-3-1b-it-Q8_0.gguf"]),
#     ("Qwen2.5-1.5B", ["Q3_K_L","Q4_K_M","Q8_0"], ["models/Qwen2.5-1.5B-Instruct-Q3_K_L.gguf","models/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf","models/Qwen2.5-1.5B-Instruct-Q8_0.gguf"]),
# ]:
#     for q, p in zip(quants, paths):
#         for ctx in [512, 2048, 8192]:
#             MODELES.append({"nom": nom, "quantification": q, "path": p, "n_threads": 4, "n_ctx": ctx})
# ============================================================

# 1. Charger notre echantillon fige de prompts (cree par build_prompts.py)
with open("prompts/prompts.json", encoding="utf-8") as f:
    fiches = json.load(f)

# 2. Liste vide qui va recevoir TOUS les resultats (tous modeles confondus)
resultats = []

# Chemin fixe au demarrage (pas a la fin) : permet de sauvegarder au fur et a mesure,
# meme si la campagne est interrompue avant la fin (crash, coupure, temps insuffisant).
horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%M")
chemin = f"data/raw/resultats_{MACHINE}_{horodatage}.csv"

chemin_prise = f"data/raw/resultats_{MACHINE}_{horodatage}_prise.csv"
resumes_prise = []   # un resume par MODELE (pas par campagne entiere) -> ecrit au fur et a mesure

# 3. Boucle EXTERNE : par MODELE (regroupe les configs quantif/threads d'un meme modele).
# La prise est ouverte/fermee PAR MODELE (pas sur toute la campagne) : plus petit lot,
# mais un resume prise est deja dispo des qu'un modele est fini, pas seulement a la toute fin.
for nom_modele, configs_du_modele in itertools.groupby(MODELES, key=lambda c: c["nom"]):
    configs_du_modele = list(configs_du_modele)
    idx_debut_lot = len(resultats)   # marque le debut des resultats de CE modele dans la liste globale

    ctx_prise = MesurePrise(node_id=PRISE_NODE_ID, baseline_w=BASELINE_W) if MESURER_PRISE else contextlib.nullcontext()
    with ctx_prise as prise:
        for config in configs_du_modele:

            # 3a. Si le fichier .gguf n'existe pas, on saute ce modele (sans planter)
            if not os.path.exists(config["path"]):
                print(f"!! Fichier introuvable, modele ignore : {config['path']}")
                continue

            print(f"\n===== Modele {config['nom']} {config['quantification']} =====")

            # 3b. Charger CE modele (une fois) + inference de chauffe
            modele = Llama(
                model_path=config["path"],
                verbose=False,
                n_threads=config.get("n_threads", 4),
                n_ctx=config.get("n_ctx", 2048),
            )
            modele("Bonjour", max_tokens=8, temperature=TEMPERATURE)

            # 3c. Boucles internes : max_tokens -> prompt -> repetitions
            for max_tokens in MAX_TOKENS_VALEURS:
                for fiche in fiches:
                    prompt = fiche["prompt"]
                    for run in range(N_REPETITIONS):
                        # Vider le cache du modele -> chaque repetition refait la LECTURE complete
                        # du prompt (prefill). Sinon llama.cpp reutilise le prompt deja traite et
                        # les runs 2,3... ne mesurent plus que la generation (biais a la baisse).
                        modele.reset()

                        tracker = EmissionsTracker(save_to_file=False, log_level="error")
                        tracker.start()
                        debut = time.perf_counter()

                        # Le PMIC echantillonne la puissance onboard en // pendant l'inference (methode 2)
                        with MesurePMIC() as pmic:
                            sortie = modele(prompt, max_tokens=max_tokens, temperature=TEMPERATURE)

                        duree = time.perf_counter() - debut
                        tracker.stop()
                        energie = tracker.final_emissions_data.energy_consumed

                        nb_tokens = sortie["usage"]["completion_tokens"]
                        joules = energie * 3_600_000

                        resultats.append({
                            "machine": MACHINE,
                            "modele": config["nom"],
                            "quantification": config["quantification"],
                            "n_threads": config.get("n_threads", 4),
                            "n_ctx": config.get("n_ctx", 2048),
                            "prompt": prompt,
                            "classe": fiche["classe"],
                            "n_caracteres": fiche["n_caracteres"],
                            "max_tokens": max_tokens,
                            "run": run + 1,
                            "tokens": nb_tokens,
                            "duree_s": round(duree, 2),
                            "energie_kWh": energie,
                            "joules": round(joules, 1),                          # methode 1 : CodeCarbon (estimation)
                            "joules_pmic": round(pmic.energie_joules, 1),        # methode 2 : PMIC (mesure reelle onboard)
                            "joules_pmic_cpu": round(pmic.energie_par_rail.get("VDD_CORE", 0), 1),  # rail CPU seul
                            "w_moyen_pmic": round(pmic.puissance_moyenne_w, 2),  # puissance moyenne onboard
                        })

                        print(f"[{config['quantification']}] [max_tokens={max_tokens}] "
                              f"[run {run + 1}/{N_REPETITIONS}] ({fiche['classe']}) "
                              f"{prompt[:30]}...  ->  {nb_tokens} tok, {duree:.2f} s, "
                              f"{joules:.1f} J (CodeCarbon) / {pmic.energie_joules:.1f} J (PMIC)")

            # 3d. CHECKPOINT : sauvegarde apres CHAQUE config terminee (pas d'attente fin de campagne).
            # Si la campagne s'arrete/plante plus tard, tout ce qui est fait jusqu'ici est deja sur disque.
            pd.DataFrame(resultats).to_csv(chemin, index=False)
            print(f"[checkpoint] {len(resultats)} mesures sauvegardees "
                  f"({config['nom']} {config['quantification']} n_threads={config.get('n_threads', 4)} termine) -> {chemin}")

    # 3e. Resume PRISE pour CE MODELE (des la sortie du with, prise.kwh_fin est lu) + checkpoint CSV
    resultats_du_lot = resultats[idx_debut_lot:]
    if prise is not None and resultats_du_lot:
        nb = len(resultats_du_lot)
        somme_pmic = sum(r["joules_pmic"] for r in resultats_du_lot)
        somme_cc = sum(r["joules"] for r in resultats_du_lot)
        resume = {
            "machine": MACHINE,
            "modele": nom_modele,
            "nb_requetes": nb,
            "duree_lot_s": round(prise.duree_s, 1),
            "baseline_w": BASELINE_W,
            "kwh_debut": prise.kwh_debut,
            "kwh_fin": prise.kwh_fin,
            "energie_mur_J": round(prise.energie_joules, 1),                 # methode 3 : energie au mur (lot)
            "energie_mur_marginale_J": round(prise.energie_marginale_joules, 1),  # apres soustraction idle
            "J_par_requete_mur": round(prise.energie_joules / nb, 1),
            "puissance_moyenne_mur_W": round(prise.puissance_moyenne_w, 2),
            "somme_J_pmic": round(somme_pmic, 1),                            # total onboard (methode 2)
            "somme_J_codecarbon": round(somme_cc, 1),                        # total estime (methode 1)
            # rendement indicatif : part de l'energie mur qui atteint les puces (reste = pertes alim + idle)
            "rendement_pmic_sur_mur_pct": round(100 * somme_pmic / prise.energie_joules, 1) if prise.energie_joules else None,
        }
        resumes_prise.append(resume)
        pd.DataFrame(resumes_prise).to_csv(chemin_prise, index=False)
        prise.sauver_courbe_csv(f"data/raw/courbe_prise_{MACHINE}_{horodatage}_{nom_modele}.csv")
        print(f"[prise] {nom_modele} : {resume['energie_mur_J']} J au mur sur {nb} requetes "
              f"({resume['J_par_requete_mur']} J/req), rendement PMIC/mur {resume['rendement_pmic_sur_mur_pct']}% "
              f"-> {chemin_prise}")
        if prise.energie_joules == 0 and not prise.mock:
            print("  /!\\ delta kWh = 0 : lot trop court pour la resolution du compteur -> rallonger.")

# 4. Sauvegarde finale (redondante avec les checkpoints, mais confirme la fin propre)
pd.DataFrame(resultats).to_csv(chemin, index=False)
print(f"\n{len(resultats)} mesures enregistrees dans {chemin}")