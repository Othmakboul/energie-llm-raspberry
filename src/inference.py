"""Inférence d'un LLM quantifié via llama-cpp-python.

Charge un modèle .gguf, exécute un prompt et renvoie le texte généré ainsi que
quelques statistiques (tokens, durée). Sert de brique de base pour les campagnes.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class ResultatInference:
    prompt_id: str
    texte_genere: str
    n_tokens_generes: int
    duree_s: float
    parametres: dict


def lancer_inference(
    modele_path: str,
    prompt: str,
    prompt_id: str = "manuel",
    max_tokens: int = 128,
    temperature: float = 0.7,
    n_threads: int | None = None,
) -> ResultatInference:
    """Exécute un prompt sur le modèle et mesure la durée.

    NB : import local pour éviter de charger llama_cpp tant qu'on n'infère pas.
    """
    from llama_cpp import Llama

    llm = Llama(model_path=modele_path, n_threads=n_threads, verbose=False)

    debut = time.perf_counter()
    sortie = llm(prompt, max_tokens=max_tokens, temperature=temperature)
    duree = time.perf_counter() - debut

    texte = sortie["choices"][0]["text"]
    n_tokens = sortie.get("usage", {}).get("completion_tokens", 0)

    return ResultatInference(
        prompt_id=prompt_id,
        texte_genere=texte,
        n_tokens_generes=n_tokens,
        duree_s=duree,
        parametres={
            "max_tokens": max_tokens,
            "temperature": temperature,
            "n_threads": n_threads,
        },
    )


if __name__ == "__main__":
    # Exemple : adapter le chemin du modèle .gguf téléchargé dans models/
    res = lancer_inference(
        modele_path="models/modele.gguf",
        prompt="Quelle est la capitale de la France ?",
    )
    print(res.texte_genere)
    print(f"{res.n_tokens_generes} tokens en {res.duree_s:.2f} s")
