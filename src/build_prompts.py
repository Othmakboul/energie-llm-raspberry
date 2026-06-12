"""Construit notre echantillon de prompts a partir du dataset Alpaca.

Methode (cf. docs/recherche-datasets-stats.md) :
- dataset officiel tatsu-lab/alpaca (Taori et al. 2023), 52 000 instructions
- echantillon STRATIFIE par longueur : 3 classes (court / moyen / long)
- 15 prompts par classe, tires avec une graine fixe -> tirage REPRODUCTIBLE
- resultat fige dans prompts/prompts.json (les memes prompts pour toutes les campagnes)

A lancer UNE SEULE FOIS : python src/build_prompts.py
"""

import json
import random

from datasets import load_dataset

# Graine aleatoire FIXE : le "hasard" donnera toujours le meme tirage.
# N'importe qui qui relance ce script obtient exactement les memes 45 prompts.
random.seed(42)

N_PAR_CLASSE = 15

# 1. Telecharger le dataset Alpaca (mis en cache apres la 1ere fois)
print("Telechargement du dataset Alpaca...")
ds = load_dataset("tatsu-lab/alpaca")["train"]
print(f"{len(ds)} entrees recuperees")

# 2. Construire la liste des prompts complets (instruction + input s'il existe)
tous_les_prompts = []
for entree in ds:
    prompt = entree["instruction"]
    if entree["input"]:                      # certains prompts ont un contexte en plus
        prompt = prompt + "\n" + entree["input"]
    tous_les_prompts.append(prompt)

# 3. Trier par longueur, puis piocher dans les EXTREMES pour un bon contraste :
#    court = les 10% les plus courts, moyen = les 10% du milieu,
#    long = les 10% les plus longs. (Couper en 3 tiers egaux donnait des classes
#    trop proches : la grande majorite des prompts Alpaca sont courts.)
tous_les_prompts.sort(key=len)               # du plus court au plus long
n = len(tous_les_prompts)
dixieme = n // 10                            # 10% du total (~5200 prompts)
milieu = n // 2                              # l'indice du milieu de la liste
classes = {
    "court": tous_les_prompts[:dixieme],                          # les 10% les plus courts
    "moyen": tous_les_prompts[milieu - dixieme // 2: milieu + dixieme // 2],  # les 10% du milieu
    "long":  tous_les_prompts[-dixieme:],                         # les 10% les plus longs
}

# 4. Tirer N prompts au hasard dans chaque classe
echantillon = []
for nom_classe, liste in classes.items():
    tirage = random.sample(liste, N_PAR_CLASSE)  # N prompts au hasard, sans doublon
    for prompt in tirage:
        echantillon.append({
            "classe": nom_classe,
            "n_caracteres": len(prompt),
            "prompt": prompt,
        })
    print(f"classe '{nom_classe}' : {N_PAR_CLASSE} prompts "
          f"(longueurs {len(tirage[0])} a {max(len(p) for p in tirage)} caracteres)")

# 5. Sauvegarder l'echantillon fige dans prompts/prompts.json
with open("prompts/prompts.json", "w", encoding="utf-8") as f:
    json.dump(echantillon, f, ensure_ascii=False, indent=2)

print(f"\n{len(echantillon)} prompts enregistres dans prompts/prompts.json")
