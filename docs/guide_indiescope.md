# Guide IndieScope : le projet de A à Z

## Mode d'emploi

Ce guide te mène seul, étape par étape, de `games.csv` à une appli finie, documentée et présentée. C'est toi qui écris tout le code : le guide dit **quoi** faire, **avec quel outil du cours**, et **comment vérifier** que c'est juste. Il n'y a pas de limite de temps : avance à ton rythme, mais dans l'ordre.

**Ce qui fait la note** (cours 1, slide 7). Chaque étape du guide nourrit au moins un de ces critères :

| Critère du prof | Ce que le correcteur va regarder | Étapes concernées |
|---|---|---|
| Organisation du travail | Un repo GitHub propre, des commits réguliers et clairs, des branches, un Kanban | 1, 2, et toutes les autres |
| Valeur business | Un vrai problème, une réponse utile et chiffrée, des hypothèses justifiées | 1, 6, 7, 8, 9, 15 |
| Code et solution | Un code qui marche, découpé en fonctions, testé, sans plantage | 3 à 13 |
| Documentation | README, docstrings, commentaires, note de 5 pages | 4, 6, 14, 15 |

**Chaque étape suit le même schéma**
- **Objectif** : ce que tu dois avoir à la fin de l'étape.
- **Révision** : la notion du cours dont tu as besoin, et où la retrouver (notebook du dossier ou fiche du guide de révision).
- **À faire** : des micro-tâches à cocher une par une.
- **Indices** : les fonctions à chercher, jamais la solution complète.
- **Check** : comment savoir que c'est bon avant de passer à la suite.
- **Pour la note** : ce que tu gardes de cette étape pour la note de 5 pages ou la soutenance.
- **Questions d'examen** : à te poser sans regarder. Elles révisent le cours au passage.

**La méthode de travail**
- Une séance = une ou deux micro-tâches, 25 minutes, puis une pause. Mieux vaut 3 séances courtes qu'une longue.
- En début de séance, réponds de tête aux questions d'examen de l'étape d'avant (rappel actif).
- Bloqué plus de 15 minutes : lis la dernière ligne de l'erreur, cherche le message exact, puis envoie ton code à Claude. Tu reçois un indice, pas la réponse.
- Une micro-tâche qui marche = un commit sur GitHub avec un message clair.
- Tiens un fichier `journal.md` : une ligne par séance (ce que tu as fait, ce qui a coincé, ce que tu as décidé). Il te servira à écrire la note.
- Commente ton code en expliquant le **pourquoi** d'un choix, pas ce que fait chaque ligne.

## Vue d'ensemble

Les données traversent 6 étapes, et chacune est un fichier `.py` de ton projet. Chaque étape ne dépend que de la précédente : c'est ce qui rend le code testable et facile à expliquer.
- **Chargement** (`data_loader.py`) : `games.csv` brut → un DataFrame aux colonnes correctes.
- **Nettoyage** (`cleaning.py`) : → `games_clean.csv`, conforme au contrat de données du cadrage.
- **Estimations** (`estimation.py`) : → ventes et revenu net par jeu, en 3 scénarios.
- **Analyse** (`analysis.py`) : → niches, jeux comparables, revenu par tranche de prix.
- **Simulateur** (`simulator.py`) : un concept de jeu → fourchette de revenu, probabilité, GO / RISKY / NO-GO.
- **Présentation** (`charts.py`, `app.py`) : graphiques et interface Gradio.

**L'arborescence à viser** (tu la construis au fil des étapes) :

**Règle d'or** : les notebooks servent à essayer et à montrer. Une fois qu'une fonction marche dans un notebook, elle déménage dans le bon fichier de `src/`, et le notebook l'importe (cours 3, notebook 6 : les modules).

## Étape 0 : installer l'environnement de travail

**Objectif** : un dossier `indiescope` ouvert dans VS Code, avec le kernel `base` qui exécute un notebook, et toutes les bibliothèques du projet installées.

**Révision** : cours 1, slides 20 à 30 (VS Code, miniconda, pip, terminal, script, notebook). Fiche 0, parties 3 et 4.

**À faire**
- Créer le dossier `indiescope` et l'ouvrir dans VS Code. Y déplacer ton notebook `01_exploration.ipynb` (dans `notebooks/`) et `games.csv` (dans `data/`).
- Ouvrir le terminal de VS Code et vérifier que `(base)` est affiché.
- Écrire `requirements.txt` avec les bibliothèques du projet : pandas, numpy, plotly, gradio, ipykernel, et plus tard mirascope si tu fais le bonus.
- Tout installer d'un coup à partir de ce fichier.
- Dans le notebook, choisir le kernel `base` et vérifier que l'import de pandas, plotly et gradio ne renvoie aucune erreur.

**Indices**
- Dans le terminal : `pip install -r requirements.txt`. Dans un notebook, la même commande prend un `!` devant.
- Le chemin vers `games.csv` depuis un notebook rangé dans `notebooks/` : il faut remonter d'un dossier (`..`). Revois la fiche 6 sur les chemins relatifs.

**Check** : une cellule avec les 3 imports s'exécute sans erreur, et `os.listdir('../data')` affiche `games.csv`.

**Questions d'examen**
- Qu'est-ce qu'un environnement, et pourquoi faut-il tout réinstaller quand on en change ?
- Quelles sont les 3 façons d'exécuter du Python vues au cours 1, et à quoi sert chacune ?
- Que signifie `..` dans un chemin ?

## Étape 1 : cadrer le projet

**Objectif** : un fichier `docs/cadrage.md` que tu sais expliquer à l'oral sans le lire. Le contenu existe déjà dans le document 
- Cadrage IndieScope : ton travail est de te l'approprier et de le compléter.

**Révision** : cours 1, slides 39 à 43 (Framing a project, User story, Epic & features, Kanban, Decompose a task). Fiche 0, partie 7.

**À faire**
- Relire le cadrage et reformuler la user story **avec tes mots**, à voix haute, sans regarderPour chaque feature « cœur », écrire en une phrase ce qui se passerait si elle manquait. Si tu n'arrives pas à l'écrire, elle n'est peut-être pas cœur.
- Ajouter une section **Hypothèses** : 1 avis ≈ 20 à 60 ventes, commission Steam de 30 %, comparaison sur les tags. Tu la compléteras aux étapes 5 et 6.
- Ajouter une section **Limites connues** : par exemple, l'outil ne voit ni le marketing ni la qualité du jeu. Tu la compléteras au fil du projet.
- Copier le tout dans `docs/cadrage.md` (format Markdown).
- Choisir **un exemple fil rouge** : un concept de jeu précis (tags, prix, budget) que tu réutiliseras partout, du test du simulateur jusqu'à la démo. Par exemple, un studio de 2 personnes, 60 000 $ de budget, qui hésite entre un roguelike et un cozy game.

**Indices**
- Markdown : `#` pour un titre, `-` pour une liste, `|` pour un tableau. C'est le même format que les cellules texte de tes notebooks.
- Un exemple fil rouge rend la soutenance mémorable : le jury suit une histoire au lieu d'une suite de fonctions.

**Check** : tu peux expliquer en 1 minute, à quelqu'un qui ne connaît pas le projet, à qui sert l'outil, ce qu'il répond et sur quoi il se base.

**Pour la note** : la user story et le fil rouge ouvrent la partie 1 de la note.

**Questions d'examen**
- Quelles sont les 3 parties d'une user story, et à quoi sert le critère d'acceptation ?
- Quelle différence entre une epic, une feature et une tâche ?
- Pourquoi cadrer avant de coder, d'après le cours 1 ?

## Étape 2 : GitHub en solo

**Objectif** : un repo GitHub `indiescope` avec les branches `main` et `dev`, un Kanban rempli, et une première feature passée par le cycle complet branche → commit → pull request → merge. Même seul, tu suis le process du cours : c'est ce que le critère « organisation » note.

**Révision** : cours 1, slides 32 à 36 et 42 (diffs, branches, commits, pull requests, process `main` / `qa` / `dev`, Kanban). Fiche 0, partie 5.

**À faire**
- Créer le repo sur GitHub, puis relier ton dossier `indiescope` à ce repo (ou le cloner et y déplacer tes fichiers).
- Écrire le `.gitignore` **avant le premier commit** : le dossier `data/`, les dossiers `__pycache__/` et `.ipynb_checkpoints/`, et un futur fichier `.env`.
- Premier commit sur `main` : `README.md` (juste un titre pour l'instant), `requirements.txt`, `.gitignore`, `docs/cadrage.md`.
- Créer la branche `dev` et la pousser sur GitHub.
- Dans l'onglet **Projects** de GitHub, créer un tableau Kanban (To do, In progress, Done) et y ajouter une carte par étape de ce guide.
- Créer une **issue** GitHub par feature cœur du cadrage, et la relier à sa carte.
- Faire un premier cycle complet : branche `feat/exploration`, commit du notebook d'exploration, pull request vers `dev`, relecture de ta propre PR (relis le diff ligne par ligne), merge.

**Le cycle à répéter pour chaque étape de ce guide**
- Partir de `dev` à jour.
- Créer une branche `feat/<nom-de-l-etape>`.
- Coder par petits commits (un message = ce qui a changé et pourquoi).
- Ouvrir une pull request vers `dev`, avec une description de 3 lignes et `Closes #<numéro de l'issue>`.
- Relire le diff, merger, déplacer la carte en Done.
- À la fin du projet : merger `dev` dans `main` et créer une version `v1.0`.

**Indices**
- `git status` avant chaque commit : il montre ce qui va partir. Si `games.csv` apparaît, ton `.gitignore` ne marche pas.
- Un bon message de commit : « Add sales estimate in 3 scenarios » ; un mauvais : « update ».
- `Closes #3` dans une PR ferme automatiquement l'issue 3 au merge.

**Check** : sur GitHub, le dossier `data/` n'existe pas, le Kanban a toutes ses cartes, et une PR est mergée dans `dev`.

**Pour la note** : une capture du Kanban et de l'historique des commits pour la partie « organisation ».

**Questions d'examen**
- Quelle différence entre `commit` et `push` ?
- À quoi servent les branches `main` et `dev` ?
- Qu'est-ce qu'un diff, et pourquoi Git est fait pour du texte ?
- Pourquoi ne jamais mettre un fichier de 401 Mo ou une clé API sur GitHub ?

## Étape 3 : charger et explorer games.csv

**Objectif** : une fonction `load_games(path)` dans `src/data_loader.py` qui renvoie un DataFrame aux colonnes correctes, et un notebook `01_exploration.ipynb` qui raconte ce que contient le dataset.

**Révision** : cours 4, problem 3, étapes 1 et 3 (`pd.read_csv`, `head`, `columns`, `value_counts`). Cours 2, notebook 3 (les types). Cours 3, notebook 7 et fiche 6 (chemins de fichiers).

**À faire**
- Charger `games.csv` et afficher la taille, la liste des colonnes et les 5 premières lignes.
- **Le piège** : comparer le nom de chaque colonne avec ce qu'elle contient, surtout autour de `Price`. Trouver pourquoi tout est décalé d'une colonne.
- Corriger le décalage au chargement et revérifier.
- Ranger le chargement corrigé dans `load_games(path)`, avec une docstring qui explique le problème corrigé.
- Regarder le type de chaque colonne utile et compter les valeurs manquantes.
- Explorer avec des questions précises, une cellule par question : combien de jeux gratuits ? Quelle distribution des prix ? Combien de jeux ont moins de 10 avis ? Combien de jeux sortent par an ? Quels sont les 20 tags les plus fréquents ?
- Sous chaque réponse, une cellule Markdown d'une ou deux phrases : ce que tu en conclus.

**Indices**
- `df.shape`, `df.columns`, `df.dtypes`, `df.isna().sum()`.
- Le piège : regarde le nom `DiscountDLC count`. Compte les noms dans l'en-tête et les valeurs dans une ligne. Puis cherche dans `help(pd.read_csv)` le paramètre qui permet de **donner toi-même la liste des noms** de colonnes. Le problème est connu : l'onglet Discussion du dataset sur Kaggle en parle.
- Les tags d'un jeu sont dans une seule chaîne de texte : pour les compter, il faut d'abord les découper (`split`), puis compter. Cherche ce que fait la méthode `explode` d'une colonne pandas.
- Charge le fichier une seule fois dans une cellule, puis ne relance plus cette cellule : 401 Mo, c'est long.

**Check** : `df[['Name', 'Price', 'Positive', 'Negative', 'Tags']].head()` affiche un prix en dollars, deux nombres d'avis et des tags. Environ 125 000 lignes.

**Pour la note** : 2 ou 3 chiffres frappants (par exemple la part de jeux avec moins de 10 avis) pour la partie « problème business », et le piège du décalage pour la partie « données ».

**Questions d'examen**
- Que renvoie `df.shape`, et de quel type est ce résultat ?
- Quelle différence entre un attribut (`df.columns`) et une méthode (`df.head()`) ?
- Que fait `value_counts()`, et sur quel objet on l'utilise ?
- Que renvoie `"Indie,Action".split(",")` ?

## Étape 4 : nettoyer les données et documenter leur qualité

**Objectif** : `data/games_clean.csv`, conforme au contrat de données du cadrage (10 colonnes en snake_case), produit par une fonction `clean_games(df)` de `src/cleaning.py`, et un tableau qui dit combien de jeux chaque filtre a retiré et pourquoi.

**Révision** : cours 2, notebook 3 (méthodes `str` : `split`, `strip`, `lower` ; module `datetime` et `strptime`), notebook 4 (dictionnaires pour renommer). Cours 3, notebook 5 (`try` / `except`) et notebook 6 (fonctions, modules). Cours 4, problem 3, étape 2 (`apply` + une fonction qui gère les cases vides). Fiches 2, 3, 4 et 5.

**À faire** (une petite fonction par tâche, puis une fonction `clean_games` qui les enchaîne)
- Garder les colonnes du contrat et les renommer en snake_case.
- Retirer les doublons et les jeux sans nom.
- Retirer les jeux gratuits (prix à 0) : sans prix, pas de revenu à estimer.
- **Date** : transformer `"Aug 1, 2023"` en vraie date, créer `release_year`, et retirer les dates illisibles.
- **Owners** : transformer `"20000 - 50000"` en `owners_min` et `owners_max` (entiers).
- **Tags** : vérifier leur format et le rendre homogène (pas d'espaces parasites, séparateur unique).
- Retirer les jeux sortis il y a moins de 6 mois : leurs avis n'ont pas eu le temps d'arriver.
- Choisir une année de début (par exemple 2015) et justifier ce choix en une phrase : le marché de 2008 ne ressemble pas à celui d'aujourd'hui.
- **Rapport de qualité** : après chaque filtre, noter le nombre de lignes restantes dans un dictionnaire, puis l'afficher en tableau (étape, lignes retirées, lignes restantes, raison).
- Sauvegarder `games_clean.csv`, le recharger, et vérifier types et valeurs.

**Indices**
- Renommer : `df.rename(columns={...})` avec un dictionnaire ancien nom → nouveau nom.
- Filtrer : `df[df['price'] > 0]`. La condition entre crochets est une colonne de `True` / `False`.
- Date : essaie d'abord une petite fonction avec `datetime.strptime` et le code de format `%b %d, %Y` (à vérifier sur tes données), entourée d'un `try` / `except ValueError` qui renvoie `None`. Ensuite seulement, compare avec `pd.to_datetime(..., errors='coerce')`.
- Owners : `split(' - ')`, puis `int()` sur chaque morceau. Certaines valeurs peuvent être vides : gère-les.
- Pour le rapport : un dictionnaire `{nom_du_filtre: len(df)}` rempli au fil des filtres, puis `pd.DataFrame(...)` pour l'afficher.
- Sauvegarder : la méthode inverse de `read_csv`, sans écrire l'index.
- Si tu modifies `cleaning.py` après l'avoir importé : Restart du kernel (piège de la fiche 5).

**Check** : `df.dtypes` montre des nombres pour `price`, `positive`, `negative`, `owners_min`, `owners_max`, `release_year`. Aucun prix à 0, aucune année en dehors de ta fenêtre. Le rapport de qualité tombe juste : lignes de départ moins lignes retirées = lignes finales.

**Pour la note** : le rapport de qualité en tableau, tel quel. Un correcteur adore voir qu'on sait ce qu'on a retiré et pourquoi.

**Questions d'examen**
- Que renvoie `"20000 - 50000".split(' - ')`, et de quel type sont les éléments ?
- Quelle différence entre `strptime` et `strftime` ? Et entre `%m` et `%M` ?
- Que se passe-t-il dans un `try` quand l'erreur n'est pas du type indiqué dans le `except` ?
- Pourquoi une fonction utilisée avec `apply` doit-elle faire `return` et pas `print` ?

## Étape 5 : estimer ventes et revenus

**Objectif** : pour chaque jeu, les ventes et le revenu net du studio en 3 scénarios (bas, moyen, haut), calculés par des fonctions de `src/estimation.py` dont chaque hypothèse est une constante commentée.

**Révision** : cours 3, notebook 6 (fonctions, `return`, paramètres par défaut, docstring, modules). Cours 2, notebook 1-2 (constantes en MAJUSCULES) et notebook 4 (dictionnaires). Fiches 1, 3 et 5.

**La méthode** : Steam ne publie pas les ventes. On sait qu'un jeu reçoit en moyenne 1 avis pour 20 à 60 ventes (la « méthode Boxleiter », utilisée dans l'industrie). Steam garde 30 % du prix.

**À faire**
- En haut de `estimation.py`, définir les hypothèses en constantes : un dictionnaire des multiplicateurs par scénario et la part de Steam. Un commentaire par constante qui dit d'où vient le chiffre.
- Écrire `estimate_sales(n_reviews, scenario='mid')` avec une docstring. La tester à la main sur 3 valeurs avant de l'utiliser sur le DataFrame.
- Écrire `net_revenue(sales, price)`.
- Écrire `add_estimates(df)` qui ajoute `reviews`, puis `sales_low`, `sales_mid`, `sales_high` et `revenue_low`, `revenue_mid`, `revenue_high`, et renvoie le DataFrame enrichi.
- Ajouter deux hypothèses plus réalistes, chacune en constante commentée : une part de remboursements (autour de 10 %) et un prix moyen payé inférieur au prix affiché à cause des promotions. Comparer le revenu avant et après, et garder la version que tu sais justifier.
- Dans `03_estimation.ipynb`, afficher les 10 jeux au revenu estimé le plus haut : ce classement doit te paraître crédible.

**Indices**
- Pandas calcule colonne par colonne : `df['a'] + df['b']` additionne toutes les lignes d'un coup, sans boucle.
- Une fonction écrite pour un nombre marche souvent telle quelle sur une colonne entière : essaie `estimate_sales(df['reviews'])`.
- Pour créer les 3 colonnes de scénarios sans recopier 3 fois la même ligne : une boucle `for` sur les clés du dictionnaire, et une f-string pour le nom de la colonne (principe DRY, fiche 5).
- Classement : cherche la méthode `sort_values` et son paramètre `ascending`.

**Check** : un jeu à 1 000 avis et 10 $ donne 40 000 ventes et 280 000 $ de revenu net en scénario moyen (sans remboursements ni promotions). Fais le calcul à la main avant de comparer.

**Pour la note** : la formule, le tableau des hypothèses (valeur + source), et le top 10.

**Questions d'examen**
- Quelle différence entre un paramètre et un argument ? À quoi sert un paramètre par défaut ?
- Pourquoi écrire les hypothèses en constantes en MAJUSCULES plutôt que de taper les nombres dans les calculs ?
- Que renvoie une fonction sans `return` ?
- Quelles sont les 3 façons d'importer une fonction d'un module, et laquelle est déconseillée ?

## Étape 6 : valider la méthode d'estimation

**Objectif** : une preuve chiffrée que ton estimation des ventes est raisonnable, et une phrase honnête sur ses limites. C'est l'étape qui transforme un exercice de code en analyse sérieuse : peu de projets la font.

**Révision** : cours 2, notebook 3 (opérateurs de comparaison, booléens `and` / `or`). Cours 3, notebook 5 (boucles). Cours 4, problem 3, étape 6 (`px.box`). Fiches 2 et 4.

**À faire**
- **Comparaison avec SteamSpy** : pour chaque jeu, regarder si `sales_mid` tombe entre `owners_min` et `owners_max`. Calculer la part de jeux « dans la fourchette », « en dessous » et « au-dessus ».
- **Calibrer** : pour chaque jeu, calculer le ratio milieu de la fourchette d'owners / nombre d'avis, puis la médiane de ce ratio. Est-elle proche de 40 ? Change-t-elle selon le prix ou l'année de sortie ?
- Décider : garder 20 / 40 / 60, ou ajuster le multiplicateur. Écrire la décision et sa raison dans `docs/cadrage.md` (section Hypothèses).
- **Jeux connus** : choisir 3 jeux indé dont les ventes ont été annoncées publiquement par leur studio (par exemple Stardew Valley, Hollow Knight, Vampire Survivors). Chercher le chiffre officiel et sa source, puis comparer avec ton estimation.
- **Sensibilité** : sur ton exemple fil rouge, regarder si la recommandation GO / NO-GO change entre les scénarios bas et haut (à refaire une fois le simulateur fini, à l'étape 9).
- Écrire 3 limites dans la section Limites du cadrage : owners n'est pas égal à ventes (clés offertes, bundles), le ratio avis / ventes varie selon le genre, et les jeux supprimés de Steam ne sont pas dans le dataset (biais du survivant).

**Indices**
- « Dans la fourchette » = deux conditions combinées avec `&`, chacune entre parenthèses. La moyenne d'une colonne de `True` / `False` donne directement une proportion.
- Retire du calcul les jeux à 0 avis (division par zéro) et ceux dont la fourchette est « 0 - 20000 » (trop imprécise).
- Pour voir si le ratio change selon le prix : regroupe par tranche de prix et prends la médiane (tu reverras `groupby` à l'étape 7).
- Pour les chiffres officiels : un communiqué ou une interview du studio vaut mieux qu'un site d'estimation.

**Check** : tu peux dire en une phrase « notre estimation tombe dans la fourchette SteamSpy pour X % des jeux, et l'écart sur 3 jeux connus est de Y % ».

**Pour la note** : cette phrase, le tableau des 3 jeux connus avec leurs sources, et les 3 limites. C'est le cœur de la partie « méthode ».

**Questions d'examen**
- Pourquoi faut-il des parenthèses autour de chaque condition quand on les combine avec `&` en pandas ?
- Que vaut `True + True + False` en Python, et pourquoi la moyenne d'une colonne de booléens donne une proportion ?
- Qu'est-ce que le biais du survivant, avec un exemple tiré de ton projet ?

## Étape 7 : analyser les niches

**Objectif** : une fonction `niche_table(df, min_games=50)` dans `src/analysis.py` qui renvoie, pour chaque tag, le nombre de jeux (la concurrence), le revenu médian et la part de jeux « rentables », et une liste de 5 niches prometteuses que tu sais justifier.

**Révision** : cours 4, problem 1, étapes 2 et 3 (taguer des articles avec une boucle, puis compter les tags par catégorie dans un dictionnaire imbriqué) : c'est exactement la logique des niches. Cours 2, notebook 4 (dictionnaires). Fiches 3 et 4.

**À faire**
- **D'abord à la main, pour réviser** : avec une boucle `for` sur les jeux et un dictionnaire, compter le nombre de jeux par tag, comme dans le problem 1 du cours 4. Afficher les 10 plus fréquents.
- **Puis avec pandas** : obtenir le même comptage en 2 ou 3 lignes, et vérifier que les deux résultats sont identiques.
- Pour chaque tag : nombre de jeux, revenu médian, et part des jeux dont le revenu dépasse un seuil (par exemple 100 000 $, à mettre en constante).
- Ne garder que les tags avec au moins 50 jeux : en dessous, les chiffres ne veulent rien dire.
- Ajouter une mesure de **dynamique** : le nombre de jeux sortis dans ce tag sur les 2 dernières années, comparé aux 2 précédentes. Une niche qui se remplit vite est plus risquée.
- Ranger le tout dans `niche_table(...)`, avec une docstring.
- Choisir 5 niches prometteuses (peu de jeux, revenu médian élevé, bonne part de jeux rentables) et 3 niches à éviter. Une phrase de justification chacune, dans `04_analysis.ipynb`.
- Bonus : faire la même analyse sur les **paires** de tags (par exemple Roguelike + Deckbuilding). Les niches intéressantes sont souvent des combinaisons.

**Indices**
- Un jeu a plusieurs tags : pour grouper par tag, il faut une ligne par couple (jeu, tag). C'est le rôle de `split` puis `explode`.
- Grouper : `df.groupby('tag')` puis `.agg(...)` avec plusieurs calculs à la fois. Teste d'abord `df.groupby('tag')['revenue_mid'].median()`.
- **Médiane, pas moyenne** : quelques succès à plusieurs millions écrasent la moyenne. Calcule les deux sur un tag et compare : c'est un bon argument pour ta note.
- Les paires de tags : cherche `itertools.combinations`, un module intégré à Python.

**Check** : le tableau a quelques centaines de tags au plus, aucun avec moins de 50 jeux, et le comptage de ta boucle est identique à celui de pandas.

**Pour la note** : le classement des 5 niches prometteuses et des 3 à éviter, avec leurs chiffres.

**Questions d'examen**
- Comment ajouter 1 au compteur d'une clé dans un dictionnaire, même si la clé n'existe pas encore ?
- Quand la médiane est-elle plus fiable que la moyenne ?
- Qu'est-ce qu'un dictionnaire imbriqué, et comment on lit `report['Indie']['Roguelike']` ?

## Étape 8 : jeux comparables et analyse des prix

**Objectif** : une fonction qui trouve les jeux comparables à un concept (mêmes tags, prix proche, sortie récente), et une fonction qui recommande une tranche de prix à partir du revenu médian de chaque tranche.

**Révision** : cours 2, notebook 4 (les **sets** : sous-ensemble, intersection, union). Cours 3, notebook 6 (paramètres par défaut, `None`). Cours 4, problem 3, étape 6 (`isin`). Fiches 2, 3 et 5.

**À faire**
- Écrire `has_all_tags(game_tags, wanted_tags)`, qui renvoie `True` si le jeu a tous les tags demandés. La tester sur 4 cas écrits à la main : tous les tags, un tag manquant, une casse différente (« indie » contre « Indie »), une liste vide.
- Écrire `find_comparables(df, tags, price=None, since_year=None)` : filtre par tags, puis par prix (± 50 % par défaut, en constante) et par année si on les donne.
- Tester sur ton exemple fil rouge et sur 2 autres niches. Noter le nombre de comparables à chaque fois.
- Décider d'un **minimum de comparables** (par exemple 30) en dessous duquel l'outil prévient que le résultat est peu fiable. Constante + commentaire.
- Créer les tranches de prix : moins de 5 $, 5-10 $, 10-15 $, 15-20 $, 20-30 $, 30 $ et plus.
- Écrire `price_table(comparables)` : par tranche, le nombre de jeux, le revenu médian et la part de jeux rentables.
- Écrire `recommend_price(comparables, min_games=10)` : la tranche au revenu médian le plus élevé, en ignorant les tranches avec trop peu de jeux.
- Regarder si la tranche recommandée change d'une niche à l'autre. Si oui, c'est un résultat intéressant à montrer.

**Indices**
- Avec des sets : `set(a) <= set(b)` teste si `a` est inclus dans `b`. Mets tout en minuscules avant de comparer.
- Appliquer `has_all_tags` à chaque jeu avec `apply` donne une colonne de `True` / `False` qui sert de filtre. Pour passer `wanted_tags`, cherche comment `apply` transmet un argument supplémentaire (ou utilise une fonction `lambda`).
- `between(a, b)` sur une colonne teste une fourchette.
- Les tranches : `pd.cut` avec une liste de bornes et une liste de noms (`help(pd.cut)`).
- Les tranches d'en haut sont souvent peu remplies dans les petites niches : c'est pour ça qu'il faut `min_games`.

**Check** : avec les tags Indie et Roguelike, tu obtiens plusieurs centaines de comparables, et un tableau de 6 lignes, une par tranche.

**Pour la note** : le tableau des prix d'une niche, et la phrase « dans cette niche, la tranche X rapporte Y fois plus que la tranche Z ».

**Questions d'examen**
- Quelle différence entre une liste et un set ? Que renvoie `{'a', 'b'} & {'b', 'c'}` ?
- Pourquoi `if tag == 'Indie' or 'Roguelike':` est toujours vrai ?
- Pourquoi écrire `price=None` comme valeur par défaut, et comment teste-t-on `None` ?

## Étape 9 : le simulateur go / no-go

**Objectif** : dans `src/simulator.py`, une classe `GameConcept` (tags, prix, budget) avec une méthode `evaluate(df)` qui renvoie un dictionnaire : nombre de comparables, fourchette de revenu, probabilité de rembourser le budget dans les 3 scénarios, recommandation GO / RISKY / NO-GO, prix recommandé, et un avertissement si les comparables sont trop peu nombreux.

**Révision** : cours 3, notebook 5 (`if` / `elif` / `else` et l'ordre des seuils, `try` / `except`) et notebook 6 (classes, `__init__`, `self`, méthodes ; problem 6bis avec `Stock` et `Portfolio`). Fiches 4 et 5.

**La logique** : parmi les jeux comparables, la probabilité de rentabilité est la part de ceux dont le revenu net dépasse le budget du studio.

**À faire**
- Écrire `break_even_probability(comparables, budget, scenario='mid')`.
- Écrire `recommendation(probability)` avec des seuils en constantes (par exemple GO à partir de 50 %, RISKY de 25 à 50 %, NO-GO en dessous). Justifier les seuils dans un commentaire.
- Calculer la fourchette de revenu : 25e percentile, médiane, 75e percentile des comparables.
- Écrire la classe `GameConcept` : `__init__` stocke les tags, le prix et le budget ; `evaluate(df)` appelle tes fonctions des étapes 5 à 8 et renvoie le dictionnaire.
- Ajouter une méthode `summary()` qui renvoie une phrase lisible, par exemple : « 312 jeux comparables, 41 % ont remboursé 60 000 $ : RISKY. Prix conseillé : 15-20 $. »
- Gérer les cas limites sans plantage : aucun comparable, budget négatif ou nul, prix négatif, liste de tags vide.
- Tester 3 concepts contrastés : petit budget dans une niche porteuse, gros budget dans une niche saturée, niche presque vide. Les résultats ont-ils du sens ?
- Refaire le test de sensibilité de l'étape 6 sur ton fil rouge : la recommandation change-t-elle entre les scénarios bas et haut ?

**Indices**
- La moyenne d'une condition, `(serie >= budget).mean()`, donne directement une proportion entre 0 et 1.
- Percentiles : la méthode `quantile` d'une colonne.
- Seuils : du plus haut au plus bas dans le `if` / `elif`, sinon tout tombe dans la première condition (piège de la fiche 4).
- Entrées invalides : un `if` au début de `__init__` qui lève une erreur claire avec `raise ValueError("...")`. Cherche comment `raise` fonctionne : c'est l'inverse de `except`.
- La classe ne fait que regrouper : la logique reste dans tes fonctions, que la méthode appelle.

**Check** : `GameConcept(['Indie', 'Roguelike'], 15, 50000).evaluate(df)` renvoie un dictionnaire complet, et passer le budget à 500 000 fait baisser la probabilité.

**Pour la note** : ton exemple fil rouge, avec la sortie de `summary()` et le résultat dans les 3 scénarios.

**Questions d'examen**
- Dans un `if` / `elif` / `else`, combien de blocs s'exécutent au maximum ?
- À quoi servent `__init__` et `self` ? Pourquoi ne passe-t-on pas `self` à l'appel ?
- Quelle différence entre un attribut et une méthode, à l'écriture et à l'appel ?
- Quelle différence entre `raise` et `except` ?

## Étape 10 : tester le code et gérer les cas limites

**Objectif** : un fichier `tests/test_project.py` qui vérifie automatiquement tes fonctions principales sur un petit jeu de données inventé, et des notebooks qui tournent de bout en bout après un Restart. Un code testé est un argument fort pour le critère « code et solution ».

**Révision** : cours 1, slide 29 (script `.py` et `if __name__ == "__main__":`). Cours 3, notebook 6 (modules et imports) et notebook 5 (exceptions). Cours 4, problem 3, étape 5 (`pd.DataFrame` à partir d'une liste de dictionnaires). Fiches 0, 3 et 5.

**À faire**
- Construire à la main un mini DataFrame de 5 à 6 jeux inventés, dont tu connais d'avance tous les résultats (prix, avis, tags choisis pour ça).
- Écrire une fonction de test par fonction importante : `estimate_sales`, `net_revenue`, `has_all_tags`, `find_comparables`, `recommend_price`, `break_even_probability`, `recommendation`.
- Dans chaque test, des `assert` qui comparent le résultat à la valeur attendue que tu as calculée à la main.
- Tester les cas limites : aucun comparable, budget nul, tags en minuscules, prix à 0.
- En bas du fichier, sous `if __name__ == "__main__":`, appeler tous les tests et afficher « Tous les tests passent ».
- Lancer le fichier depuis le terminal. Puis casser volontairement une fonction pour vérifier qu'un test échoue bien.
- Pour chaque notebook : Restart, puis Run All. Aucune erreur, aucune cellule qui dépend d'un état caché.

**Indices**
- `assert condition, "message"` ne fait rien si la condition est vraie, et lève une `AssertionError` avec ton message sinon.
- Pour comparer des décimaux, évite `==` (fiche 2 : `0.1 + 0.2` ne vaut pas exactement `0.3`) : compare l'écart avec `abs(a - b) < 0.01`.
- Pour importer `src/estimation.py` depuis `tests/`, le plus simple est de lancer la commande depuis la racine du projet. Si ça coince, cherche `sys.path` (c'est la liste des dossiers où Python cherche les modules).
- Bonus : la bibliothèque `pytest` lance automatiquement toutes les fonctions qui commencent par `test_`.

**Check** : le terminal affiche « Tous les tests passent », et un test échoue quand tu casses une fonction.

**Pour la note** : une phrase dans la partie « outil » : combien de tests, sur quoi.

**Questions d'examen**
- Que fait `assert`, et que se passe-t-il quand la condition est fausse ?
- Pourquoi le bloc `if __name__ == "__main__":` ne s'exécute-t-il pas quand on importe le fichier ?
- Pourquoi faire Restart puis Run All avant de rendre un notebook ?

## Étape 11 : les graphiques

**Objectif** : 4 graphiques Plotly dans `src/charts.py`, chacun dans une fonction qui prend des données et **renvoie** une figure, avec un titre qui dit la conclusion.

**Révision** : cours 4, problem 2, étape 5 (`px.line`, arguments `x`, `y`, `title`, `labels`, `fig.show()`) et problem 3, étape 6 (`px.box` par catégorie). Cours 5, notebook dataviz.

| Fonction | Question à laquelle il répond | Type Plotly à chercher |
|---|---|---|
| `niche_map(niches)` | Quelles niches ont peu de concurrence et rapportent bien ? | nuage de points (`px.scatter`) : x = nombre de jeux, y = revenu médian, un point par tag |
| `price_chart(prices)` | À quel prix vendre dans cette niche ? | barres (`px.bar`) : une barre par tranche de prix |
| `revenue_distribution(comparables, budget)` | Quelles sont mes chances face à mon budget ? | boîte (`px.box`) ou histogramme (`px.histogram`), avec une ligne au niveau du budget |
| `releases_per_year(df, tags)` | Cette niche se remplit-elle vite ? | courbe (`px.line`) : jeux sortis par an |

**À faire**
- Faire chaque graphique d'abord dans le notebook avec `fig.show()`, puis le ranger dans sa fonction.
- Un titre qui dit ce qu'on voit (« Les roguelikes à 15-20 $ rapportent le plus »), pas ce qu'on mesure (« Revenu par prix »).
- Des noms d'axes en français avec les unités ($, nombre de jeux).
- Les revenus vont de quelques dollars à des millions : tester l'**échelle logarithmique** et garder la plus lisible.
- Dans la carte des niches, afficher le nom du tag au survol, et mettre en avant ta niche fil rouge.
- Enregistrer chaque graphique en image dans `docs/images/` pour le README et la note.

**Indices**
- `help(px.scatter)` : cherche `hover_name`, `log_x`, `log_y`, `color`.
- La ligne du budget : la méthode `add_hline` (ou `add_vline` pour un histogramme) d'une figure.
- Enregistrer en image : la méthode `write_image` (elle demande la bibliothèque `kaleido`), ou une capture d'écran propre.
- Une seule couleur par défaut ; une couleur vive seulement pour ce qui doit sauter aux yeux (ta niche, la ligne du budget).

**Check** : quelqu'un qui ne connaît pas le projet comprend chaque graphique sans explication orale.

**Pour la note** : les 4 images, chacune avec une phrase de lecture.

**Questions d'examen**
- Quelle différence entre `fig.show()` et `return fig` dans une fonction ?
- Dans `px.scatter(df, x=..., y=...)`, que doivent contenir `x` et `y` ?
- Pourquoi une échelle log aide quand les valeurs vont de 10 à 10 millions ?

## Étape 12 : l'interface Gradio

**Objectif** : un fichier `app.py` qui lance une appli à 3 onglets, utilisable par quelqu'un qui ne connaît ni Python ni le projet.

| Onglet | Ce que l'utilisateur fait | Ce qu'il voit |
|---|---|---|
| Carte du marché | Choisit un nombre minimum de jeux par niche | La carte des niches et le tableau des niches prometteuses |
| Simulateur | Coche ses tags, entre son prix et son budget, clique sur « Évaluer » | La recommandation, la fourchette de revenu, la probabilité dans les 3 scénarios, le prix conseillé, et 2 graphiques |
| Méthode | Lit | D'où viennent les données, les hypothèses, les limites (texte repris du cadrage) |

**Révision** : cours 5, notebook dataviz : exercice 1 (`gr.Slider` + bouton + `gr.DataFrame`), exercice 2 (zone de texte + bouton + fonction), exercice 3 (`gr.Tab`), exercice 4 (envoyer une information d'un onglet à l'autre), et `demo.launch(share=True)`.

**À faire**
- **Révision d'abord** : refaire de tête l'exercice 3 du cours 5 (2 onglets, un bouton chacun) dans un notebook vide.
- Dans `app.py`, charger `games_clean.csv` et ajouter les estimations **une seule fois**, au démarrage, en dehors de toute fonction.
- Construire l'onglet Simulateur : une liste de tags à cocher, un champ prix, un champ budget, un bouton.
- Écrire la fonction branchée sur le bouton : elle crée un `GameConcept`, appelle `evaluate`, et renvoie dans l'ordre ce que chaque sortie doit afficher.
- Afficher la recommandation très visiblement (un titre Markdown), puis le reste.
- Brancher les figures de `charts.py` dans des composants graphiques.
- Construire l'onglet Carte du marché, puis l'onglet Méthode.
- Cas limites : aucun tag coché, aucun comparable, prix ou budget invalides. Un message clair dans l'interface, jamais une erreur Python à l'écran.
- Pré-remplir le simulateur avec ton exemple fil rouge : la démo commence en un clic.
- Faire tester l'appli à 2 personnes qui ne connaissent pas le projet. Noter ce qu'elles ne comprennent pas, et corriger.

**Indices**
- Composants à chercher : `gr.CheckboxGroup` (tags), `gr.Number` (prix, budget), `gr.Button`, `gr.Markdown` (texte mis en forme), `gr.Plot` (figure Plotly), `gr.DataFrame` (tableau).
- La liste des tags proposés : les 40 plus fréquents suffisent (`value_counts`, encore).
- Une fonction branchée sur un bouton renvoie autant de valeurs qu'il y a de sorties, dans le même ordre que la liste `outputs` : un tuple.
- Afficher un message d'erreur proprement : cherche `gr.Warning` ou `gr.Error`.
- Lancer : `python app.py` dans le terminal, avec `demo.launch()` en bas du fichier sous `if __name__ == "__main__":`.

**Check** : une personne qui découvre l'appli obtient une recommandation en moins d'une minute, sans aide, et aucun cas limite ne fait apparaître d'erreur Python.

**Pour la note** : une capture de chaque onglet, et ce que les testeurs ont fait changer.

**Questions d'examen**
- Dans `bouton.click(fn=..., inputs=..., outputs=...)`, que contient chaque argument ?
- Pourquoi charger les données en dehors de la fonction du bouton ?
- À quoi sert `share=True`, et quel risque cela pose-t-il ?

## Étape 13 (bonus) : expliquer le résultat avec l'IA

**Objectif** : un bouton « Expliquer » dans l'onglet Simulateur qui transforme le dictionnaire de `evaluate` en un court avis rédigé, comme celui d'un consultant. À faire seulement quand les étapes 0 à 12 sont finies et testées.

**Révision** : cours 6, notebook mirascope : `@llm.call(MODEL)`, messages `system` et `user`, problème 2 (résumer avec un point d'attention), clé API en variable d'environnement.

**À faire**
- Refaire de tête le problème 2 du cours 6.
- Écrire `explain_result(result)` dans `src/assistant.py` : elle envoie les chiffres du simulateur (en texte, via une f-string) et demande 4 à 5 phrases d'avis pour un fondateur de studio.
- Dans le message `system`, interdire au modèle d'inventer des chiffres, et lui demander de citer les limites de la méthode.
- Brancher la fonction sur un bouton, et prévoir un message si la clé API est absente : l'appli doit marcher sans l'IA.
- Mettre la clé dans un fichier `.env` déjà listé dans `.gitignore`.

**Indices**
- Le dictionnaire renvoyé par `evaluate` contient déjà tout : il suffit de le transformer en texte.
- Pour lire le `.env` : la bibliothèque `python-dotenv`, ou `os.environ` comme dans le cours 6.

**Check** : l'avis reprend exactement les chiffres affichés, change quand tu changes le budget, et l'appli fonctionne quand la clé est retirée.

**Pour la note** : une phrase dans les perspectives, et une capture d'un avis généré.

**Questions d'examen**
- Qu'est-ce qu'une API, avec l'image du restaurant du cours 6 ?
- Quel rôle joue le message `system` par rapport au message `user` ?
- Pourquoi une clé API ne doit jamais être écrite dans le code ?

## Étape 14 : documenter le code et écrire le README

**Objectif** : un repo qu'un autre étudiant peut comprendre, installer et lancer seul, en suivant uniquement le README.

**Révision** : cours 1, slide 37 (documenter « as code » avec `#`) et slide 38 (débugger). Cours 3, notebook 6 (docstrings et `help()`). Fiches 0 et 5.

**À faire : le code**
- Chaque fonction et chaque classe a une docstring : ce qu'elle fait, ce qu'elle prend (avec les types), ce qu'elle renvoie. Vérifier avec `help(ma_fonction)`.
- Chaque fichier de `src/` commence par une docstring de 2 ou 3 lignes qui dit à quoi il sert.
- Les commentaires `#` expliquent les choix (seuils, multiplicateur, médiane, année de début), pas ce que fait chaque ligne.
- Aucun nombre « magique » dans les calculs : chaque hypothèse est une constante nommée et commentée.
- Les noms sont clairs et en snake_case (fiche 1) : `revenue_mid` plutôt que `r2`.
- Retirer le code mort : cellules d'essai, `print` de debug, fonctions inutilisées.

**À faire : le README** (dans cet ordre)
- Le titre et une phrase qui dit à quoi sert l'outil.
- Une capture de l'appli.
- Le problème business en 3 lignes (repris de la user story).
- L'installation : cloner, `pip install -r requirements.txt`, télécharger `games.csv` depuis Kaggle et le placer dans `data/`.
- L'utilisation : lancer le nettoyage, puis `python app.py`.
- L'arborescence du repo, avec une ligne par fichier.
- Le contrat de données.
- La méthode et les hypothèses, avec leurs sources.
- Les limites.
- Les tests : comment les lancer.
- La source des données (lien Kaggle, licence MIT).

**Indices**
- Pour qu'un correcteur regénère `games_clean.csv` en une commande, ajoute dans `cleaning.py` un bloc `if __name__ == "__main__":` qui charge, nettoie et sauvegarde.
- Une image dans un README : `![texte](docs/images/capture.png)`.

**Check** : cloner le repo dans un autre dossier, suivre le README à la lettre, et arriver à l'appli sans rien deviner. Mieux : le faire faire à quelqu'un d'autre.

**Questions d'examen**
- Quelle différence entre un commentaire `#` et une docstring ? Comment lit-on une docstring ?
- Qu'est-ce qu'un nombre « magique », et pourquoi l'éviter ?
- Pourquoi le prof compare-t-il un projet sans documentation à un immeuble invisible ?

## Étape 15 : la note de 5 pages

**Objectif** : une note qui répond explicitement aux 4 critères du prof, écrite à partir de tout ce que tu as mis de côté dans les rubriques « Pour la note » et dans `journal.md`. Si tu as suivi le guide, la matière est déjà là : il reste à l'assembler.

**Le plan proposé**

| Partie | Contenu | Place | Critère visé |
|---|---|---|---|
| 1. Le problème | Le marché Steam saturé (le chiffre de ta proposition : 19 112 jeux sortis en 2025, près de la moitié avec moins de 10 avis, source SteamDB via PC Gamer), les 3 décisions du fondateur, la user story, ton fil rouge | 0,5 page | Valeur business |
| 2. Les données | Source, licence, le piège du décalage, le rapport de qualité du nettoyage | 0,75 page | Code, documentation |
| 3. La méthode | Formule et hypothèses, validation SteamSpy et jeux connus, médiane plutôt que moyenne, seuils go / no-go | 1,25 page | Valeur business |
| 4. Les résultats | Les niches prometteuses, l'analyse des prix, le fil rouge simulé, avec 2 ou 3 graphiques | 1 page | Valeur business |
| 5. L'outil | Architecture du code (les 6 modules), l'appli et ses 3 onglets, les tests | 0,75 page | Code et solution |
| 6. Organisation, limites, suite | GitHub (Kanban, issues, PR), les limites, ce que tu ferais avec plus de données | 0,75 page | Organisation |

**À faire**
- Rassembler dans un brouillon tout ce qui est marqué « Pour la note » aux étapes précédentes.
- Écrire d'abord la phrase de conclusion de chaque partie, puis le reste autour.
- Chaque graphique a un numéro, un titre et une phrase de lecture dans le texte.
- Chaque chiffre externe a sa source (lien ou référence).
- Vérifier le chiffre du marché 2025 à sa source avant de le citer.
- Faire relire la note par quelqu'un qui ne connaît pas le projet. S'il ne comprend pas une phrase, elle est à réécrire.
- Ajouter le lien vers le repo GitHub en première page.

**Indices**
- Une partie = une idée principale, énoncée dans la première phrase.
- Parler des limites n'enlève pas de points : ça montre que tu sais ce que vaut ton outil.
- Le piège du décalage de colonnes est une très bonne anecdote : il prouve que tu as vérifié tes données au lieu de leur faire confiance.

**Check** : en lisant seulement les titres et la première phrase de chaque partie, on comprend le projet en entier, et chacun des 4 critères a sa partie.

## Étape 16 : la soutenance et la démo

**Objectif** : une présentation qui raconte l'histoire de ton fil rouge, une démo en direct qui ne peut pas rater, et des réponses prêtes aux questions probables.

**Le déroulé proposé**
- **Le problème** : un studio de 2 personnes, 60 000 $ de budget, hésite entre deux concepts. Que faire ?
- **Les données** : 125 000 jeux Steam, ce que tu as nettoyé, le piège trouvé.
- **La méthode** : comment on estime des ventes que personne ne publie, et comment tu l'as vérifié.
- **La démo** : la carte du marché, puis les deux concepts du fil rouge dans le simulateur. La réponse au problème du début.
- **Les limites et la suite**.
- **Le code et l'organisation** : l'arborescence, les tests, le Kanban, en une slide.

**À faire**
- Faire les slides : peu de texte, un graphique ou une capture par slide.
- Répéter la démo 3 fois en conditions réelles : ordinateur chargé, appli lancée à froid.
- Préparer un **plan B** : une vidéo de la démo (enregistrement d'écran) et des captures dans les slides, si l'appli ou le réseau lâchent.
- Lancer l'appli **avant** de commencer à parler : le chargement des données prend du temps.
- Préparer une réponse de 30 secondes à chacune des questions ci-dessous.

**Questions probables du jury**
- Pourquoi 40 ventes par avis, et que se passe-t-il si c'est faux ?
- Pourquoi la médiane et pas la moyenne ?
- Comment as-tu choisi les seuils GO / RISKY / NO-GO ?
- Que ne voit pas ton outil ?
- Montre-moi la fonction qui calcule la probabilité, et explique-la ligne par ligne.
- Que se passe-t-il si on coche un tag très rare ?
- Comment as-tu organisé ton travail sur GitHub ?

**Check** : tu fais la présentation complète, démo comprise, dans le temps imparti, et tu peux expliquer n'importe quelle fonction de ton code sans la relire.

## Checklist finale, critère par critère

À cocher juste avant le rendu. Chaque case non cochée est un point facile à aller chercher.

**Organisation du travail**
- Le Kanban GitHub est à jour, toutes les cartes cœur en Done.
- Chaque feature cœur a son issue fermée par une pull request.
- L'historique montre des commits réguliers, aux messages clairs.
- `dev` est mergée dans `main`, et la version `v1.0` existe.
- `journal.md` couvre toutes les séances.

**Valeur business**
- La user story et son critère d'acceptation sont respectés par l'appli.
- Chaque hypothèse a une valeur, une source et une justification.
- La méthode est validée (SteamSpy et 3 jeux connus) et ses limites sont écrites.
- Le fil rouge donne une réponse claire et chiffrée.

**Code et solution**
- Le code est découpé en 6 modules dans `src/`, sans code dupliqué.
- `python tests/test_project.py` affiche « Tous les tests passent ».
- Chaque notebook tourne après Restart + Run All.
- L'appli ne plante sur aucun cas limite.
- `games.csv`, `games_clean.csv` et `.env` ne sont pas sur GitHub.

**Documentation**
- Chaque fonction, classe et fichier a sa docstring.
- Aucun nombre magique : toutes les hypothèses sont des constantes commentées.
- Le README permet d'installer et de lancer le projet sans aide (testé sur un clone propre).
- La note fait 5 pages, couvre les 4 critères, et chaque chiffre externe a sa source.
- La démo a été répétée, avec un plan B prêt.

**Pour toi**
- Tu réponds sans regarder à toutes les questions d'examen de ce guide.

## Ce que le projet fait réviser, et sources

En suivant ce guide en entier, tu révises tout le cours. Avant l'examen, relis les questions d'examen des étapes liées au chapitre qui te pose problème.

| Cours | Notions | Étapes du guide |
|---|---|---|
| Cours 1 | Environnement, pip, notebook et script, Git et GitHub, cadrage, documentation | 0, 1, 2, 10, 14 |
| Cours 2 | Variables, constantes, types, méthodes `str`, dates, list / tuple / dict / set | 3, 4, 5, 7, 8 |
| Cours 3 | Boucles, conditions, `try` / `except`, fonctions, modules, classes, fichiers | 4, 5, 6, 7, 9, 10 |
| Cours 4 | pandas, `read_csv`, `apply`, `value_counts`, plotly | 3, 4, 7, 8, 11 |
| Cours 5 | Interface Gradio, onglets, boutons | 12 |
| Cours 6 | Appel d'un modèle d'IA | 13 |

**Sources**
- - Steam Games Dataset (FronkonGames) – Kaggle
- - Steam-Games-Scraper, liste des champs – GitHub
- - Cadrage IndieScope
- Tes cours : dossier Introduction Python (cours 1 à 6 et corrigés), et le guide de révision du projet.
