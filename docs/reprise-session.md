# Point d'etape / Reprise de session

> Ce fichier resume ou on en est. Pour reprendre avec Claude dans une nouvelle
> session : ouvre ce fichier et demande "lis docs/reprise-session.md et continue".

Derniere mise a jour : 10/06/2026

---

## 1. Le projet en 1 phrase
Mesurer le cout energetique d'une requete a un LLM (Llama-3.2-1B) tournant sur
Raspberry Pi 5 (16 Go), et trouver quels parametres font le plus consommer.
Voir aussi : docs/roadmap.md (plan complet) et docs/journal.md (suivi jour par jour).

---

## 2. Ou on en est (statut)
- Semaine 1 : machinerie complete sur PC -> FAIT.
- Semaine 2 : warm-up (2.1) + repetitions (2.2) -> FAIT.
- Prochaine etape concrete : S2.3 (ranger le code en fonctions) ou S2.4/2.5
  (etat de l'art + protocole). Le Pi n'est pas encore arrive.

---

## 3. Les fichiers de code et leur role
- src/inference.py : BRIQUE d'apprentissage. 1 requete -> reponse + tokens + duree + energie.
- src/measure.py : BRIQUE d'apprentissage. CPU/frequence (psutil) + energie (CodeCarbon).
- src/campaign.py : LE SCRIPT PRINCIPAL (a reutiliser et faire grandir).
  Charge le modele 1 fois -> inference de chauffe -> pour chaque prompt, repete
  N fois la mesure -> ecrit data/raw/resultats.csv.
  => C'est CE fichier qui partira sur le Pi et qui evoluera (meme code, pas un autre).

---

## 4. Bases comprises (pour reviser)
- LLM = programme qui predit le mot suivant. Prompt = ce qu'on tape. Token = bout de mot.
- Inference = le modele qui repond (c'est ce qu'on mesure).
- Parametres (1B, 3B...) = taille du "cerveau" : + gros = + malin mais + lent/gourmand.
- Quantification (Q2/Q4/Q8) = arrondir les nombres du modele pour l'alleger (comme un JPEG).
  GGUF = format de fichier du modele. llama.cpp = le "lecteur" de .gguf.
- RAM (16 Go) = plan de travail (pas un souci). CPU = l'ouvrier lent (le vrai goulot).
- Energie : Watt = puissance instantanee ; Joule = energie totale (= puissance x duree).
  1 kWh = 3 600 000 J.

---

## 5. Methodologie de mesure (3 methodes possibles sur le Pi)
1. CodeCarbon (logiciel, dans le code) : estimation, automatique, par requete. Approximatif.
2. Prise connectee (physique, externe) : mesure au mur (inclut pertes du chargeur),
   LENTE -> mesurer par paquets de requetes + moyenne ; soustraire la conso au repos.
3. PMIC du Pi 5 (materiel interne) : commande `vcgencmd pmic_read_adc` (n'existe QUE
   sur le Pi). Capteur de courant/tension sur la carte -> bonne precision. A AJOUTER en S3.
- Les faire EN MEME TEMPS = comparaison equitable (memes conditions).
- Effet observateur : CodeCarbon/PMIC tournent sur le Pi -> petit surcout CPU vu par la
  prise, mais negligeable (le LLM sature le CPU). On peut le quantifier (repos seul vs
  repos + outil).

---

## 6. Lecons deja observees (pour le rapport)
- Moins de tokens = moins de temps = moins d'energie (64 tok ~100 J vs 2 tok ~18 J).
- Energie non proportionnelle : cout fixe + cout par token.
- 1ere inference faussee (warm-up) -> on la jette.
- Une seule mesure ment (88 J a 364 J pour la meme requete !) -> repeter + moyenner.
- Le modele a du hasard (temperature) -> nb de tokens varie ; envisager temperature=0
  pour des runs comparables.

---

## 7. A ne pas oublier
- Le modele .gguf et le CSV ne sont PAS dans git (.gitignore). A retelecharger sur le Pi.
- Pousse sur GitHub (commit 7c4d224). Amine peut `git pull origin main`.
- Pieges Windows : llama-cpp-python via wheel pre-compile ; pas de dossier a la racine de D:.
- Quand le Pi arrive : installer OS -> git clone -> venv + deps (ARM = delicat) ->
  retelecharger modele -> brancher prise -> mesurer conso au repos.
