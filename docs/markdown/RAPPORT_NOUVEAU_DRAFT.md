# Rapport de Projet de Fin d'Etudes

## Conception et realisation d'une plateforme intelligente de veille sportive multilingue basee sur l'IA

### Auteur
[Votre Nom]

### Annee universitaire
2025-2026

### Encadrant
[A completer]

### Etablissement
[A completer]

---

## Dedicace

Je dedie ce travail a mes parents, a ma famille, a mes amis ainsi qu'a toutes les personnes qui m'ont soutenu tout au long de mon parcours universitaire. Leur confiance, leurs encouragements et leur patience ont constitue une source permanente de motivation.

---

## Remerciements

Je tiens a exprimer ma profonde gratitude a mon encadrant pour son accompagnement, ses conseils, sa disponibilite et la qualite de son suivi tout au long de ce projet de fin d'etudes. Je remercie egalement l'ensemble de mes enseignants pour la formation recue, ainsi que toutes les personnes ayant contribue de pres ou de loin a la realisation de ce travail.

---

## Resume

Dans un contexte marque par la surabondance de l'information numerique, en particulier dans le domaine sportif, il devient difficile pour un utilisateur, un journaliste ou un analyste de suivre l'actualite de maniere structuree, rapide et fiable. Le present projet a pour objectif de concevoir et de developper une plateforme intelligente de veille sportive multilingue capable de collecter automatiquement des articles depuis plusieurs sources web, de les nettoyer, de les classifier, de les enrichir, d'evaluer leur credibilite et de produire une revue de presse exploitable.

La solution proposee s'appuie sur un pipeline automatise de traitement de donnees, un backend de services, un frontend web de visualisation et un ensemble de diagrammes d'analyse et de conception permettant de formaliser les interactions entre les acteurs et le systeme. Le projet integre plusieurs use cases couvrant l'authentification, la consultation de la revue, le filtrage par sport, la publication, l'export et les traitements IA internes tels que la collecte, la verification, la classification, le calcul d'importance et la generation d'une synthese quotidienne.

Les resultats obtenus montrent qu'il est possible de produire automatiquement une revue de presse sportive structuree sous plusieurs formats, tout en proposant une interface lisible et une architecture evolutive. Ce projet constitue une contribution concrete dans le domaine de la veille informationnelle et ouvre la voie a des ameliorations futures, notamment en intelligence artificielle, en evaluation de la fiabilite des sources et en personnalisation de l'experience utilisateur.

### Mots-cles

Veille sportive, intelligence artificielle, scraping web, classification automatique, revue de presse, UML, FastAPI, interface web.

---

## Abstract

In a context characterized by information overload, especially in the sports domain, it becomes difficult for users, journalists and analysts to monitor news in a structured, fast and reliable way. This project aims to design and develop an intelligent multilingual sports monitoring platform capable of automatically collecting articles from multiple web sources, cleaning them, classifying them, enriching them, evaluating their credibility and producing an exploitable press review.

The proposed solution relies on an automated data-processing pipeline, a service-oriented backend, a visualization frontend and a set of analysis and design diagrams used to formalize interactions between actors and the system. The project integrates several use cases covering authentication, review consultation, sport filtering, publication, export and internal AI processes such as article collection, resource verification, classification, importance calculation and daily summary generation.

The obtained results show that it is possible to automatically generate a structured sports press review in multiple formats while providing a readable interface and an extensible architecture. This project represents a concrete contribution in the field of information monitoring and opens the way to future improvements, especially in artificial intelligence, source reliability assessment and personalized user experience.

### Keywords

Sports monitoring, artificial intelligence, web scraping, automatic classification, press review, UML, FastAPI, web interface.

---

## Table des matieres

1. Introduction generale
2. Chapitre 1 - Contexte general et cadrage du projet
3. Chapitre 2 - Analyse et conception
4. Chapitre 3 - Realisation et mise en oeuvre
5. Chapitre 4 - Tests, discussion et perspectives
6. Conclusion generale
7. Bibliographie
8. Annexes

---

## Liste des abreviations

- IA : Intelligence Artificielle
- UML : Unified Modeling Language
- API : Application Programming Interface
- NLP : Natural Language Processing
- UI : User Interface
- CSV : Comma-Separated Values
- HTML : HyperText Markup Language
- CSS : Cascading Style Sheets
- JS : JavaScript
- JSON : JavaScript Object Notation
- PFE : Projet de Fin d'Etudes

---

## Introduction generale

L'evolution des technologies numeriques a transforme en profondeur les modes de production, de diffusion et de consommation de l'information. Dans le domaine sportif, cette transformation est encore plus visible en raison du caractere immediat et dynamique des actualites, des resultats, des analyses et des reactions qui circulent en continu sur les plateformes web. Cette abondance d'information constitue une richesse, mais elle pose egalement un probleme majeur de surcharge informationnelle.

Dans ce contexte, la veille automatisee devient une necessite pour toute organisation ou tout utilisateur souhaitant suivre les contenus pertinents sans consacrer un temps excessif a une recherche manuelle. Le present projet propose la conception et la realisation d'une plateforme intelligente de veille sportive multilingue capable de collecter automatiquement des articles, de les organiser, de les enrichir, de les filtrer et de les presenter sous la forme d'une revue de presse exploitable.

L'originalite de cette solution repose sur l'integration conjointe de plusieurs dimensions : collecte web, traitement intelligent, evaluation de la credibilite, structuration des donnees, visualisation web et modelisation UML. Le systeme vise ainsi a repondre a une problematique reelle : comment automatiser efficacement la surveillance de l'actualite sportive tout en garantissant une presentation claire, un tri pertinent et une architecture logicielle maintenable.

Ce rapport presente l'ensemble du travail realise. Il s'articule autour de quatre chapitres. Le premier chapitre expose le contexte general, la problematique, les objectifs et la planification du projet. Le deuxieme chapitre detaille l'analyse et la conception fonctionnelle et technique, notamment au travers des cas d'utilisation et des diagrammes de sequence. Le troisieme chapitre decrit la realisation technique de la plateforme, les technologies adoptees et l'implementation des principaux modules. Enfin, le quatrieme chapitre presente les tests, les limites, les apports du projet et les perspectives d'amelioration.

---

## Chapitre 1 - Contexte general et cadrage du projet

### 1.1 Contexte general du projet

L'information sportive se distingue par son rythme rapide, son volume important et la diversite de ses sources. Les utilisateurs interessent par le sport consultent generalement plusieurs sites, blogs, journaux et plateformes sociales afin d'obtenir une vision complete des evenements. Cette demarche est couteuse en temps et ne garantit pas toujours une organisation satisfaisante des contenus.

Dans le cadre de ce projet, il a ete identifie un besoin concret : concevoir une plateforme capable d'automatiser cette veille informationnelle en centralisant les articles issus de plusieurs sources sportives, en les classant par discipline, en evaluant leur importance et en produisant une synthese quotidienne. Le projet prend egalement en compte la dimension multilingue des contenus ainsi que la necessite de distinguer les sources les plus credibles.

### 1.2 Problematique

La problematique principale de ce projet peut etre formulee comme suit :

Comment concevoir une plateforme intelligente capable de collecter, traiter, organiser et diffuser automatiquement l'information sportive issue de sources heterogenes, tout en garantissant la pertinence, la lisibilite et l'evolutivite de la solution ?

Cette problematique se decline en plusieurs sous-questions :

- comment automatiser la collecte des articles sportifs depuis plusieurs sources web ;
- comment classifier les contenus selon leurs disciplines sportives ;
- comment reduire le bruit informationnel en identifiant les articles les plus importants ;
- comment proposer une consultation claire des donnees collectees ;
- comment modeliser les interactions du systeme de facon rigoureuse pour faciliter son implementation.

### 1.3 Objectifs du projet

#### 1.3.1 Objectif general

L'objectif general est de concevoir et de realiser une plateforme de veille sportive intelligente capable de produire automatiquement une revue de presse sportive structuree a partir de plusieurs sources web.

#### 1.3.2 Objectifs specifiques

Les objectifs specifiques du projet sont les suivants :

- collecter automatiquement des articles sportifs depuis plusieurs sites ;
- verifier la disponibilite et la qualite minimale des ressources collectees ;
- classifier les articles selon les sports traites ;
- detecter les informations redondantes ou proches ;
- calculer un score d'importance pour prioriser les actualites ;
- stocker les donnees dans une structure exploitable ;
- generer une synthese quotidienne ;
- publier une revue de presse dans une interface web ;
- permettre aux utilisateurs de consulter, filtrer, archiver et exporter les contenus ;
- permettre a l'administrateur de superviser le fonctionnement global du systeme.

### 1.4 Methode de travail adoptee

La methode adoptee repose sur une approche incrementale et modulaire. Le projet a d'abord ete cadre par une analyse du besoin, puis formalise au moyen de cas d'utilisation et de diagrammes de sequence. La realisation a ensuite ete decoupee en modules fonctionnels : collecte, verification, classification, stockage, synthese, publication et administration.

Cette demarche presente plusieurs avantages :

- meilleure lisibilite du systeme ;
- reduction de la complexite de developpement ;
- possibilite de tester les modules de maniere independante ;
- facilitation de la maintenance et des evolutions futures.

### 1.5 Acteurs du systeme

L'analyse des besoins a permis d'identifier les acteurs suivants :

- **Journaliste** : utilisateur principal de la plateforme ; il consulte les revues, filtre les actualites, accede aux archives, exporte des contenus et peut proposer des sources ;
- **Utilisateur** : acteur generique pour les fonctionnalites d'authentification et de connexion ;
- **Agent IA** : composant central du traitement automatique ; il collecte, verifie, classe, calcule l'importance, stocke et genere les syntheses ;
- **Administrateur** : supervise le systeme, gere les utilisateurs, controle les sources et consulte les journaux d'activite.

### 1.6 Planification du projet

La planification constitue un element essentiel du pilotage d'un projet informatique. Elle permet d'organiser les taches, de visualiser les dependances, d'anticiper les contraintes et d'identifier les priorites.

#### 1.6.1 Diagramme de Gantt

Le diagramme de Gantt est un outil de planification qui represente les taches d'un projet en fonction du temps. Chaque tache est associee a une duree et a une position sur un calendrier, ce qui permet de visualiser l'enchainement des activites et leur chevauchement eventuel.

Dans le cadre de ce projet, le diagramme de Gantt permet de suivre les grandes phases suivantes :

- analyse des besoins ;
- modelisation UML ;
- conception de l'architecture ;
- developpement du pipeline ;
- developpement du frontend ;
- integration et tests ;
- redaction du rapport.

**Figure 1 - Diagramme de Gantt du projet**  
[Inserer ici la capture ou l'image du diagramme de Gantt]

#### 1.6.2 Diagramme PERT

Le diagramme PERT, pour Program Evaluation and Review Technique, est un outil de planification qui met l'accent sur l'enchainement logique des taches et leurs dependances. Il permet d'identifier le chemin critique du projet, c'est-a-dire la sequence d'activites dont tout retard impacte directement la date finale de livraison.

Pour ce projet, le diagramme PERT permet d'illustrer la relation entre les activites majeures :

- cadrage du projet ;
- formalisation des besoins ;
- conception des diagrammes ;
- implementation des modules de traitement ;
- integration de l'interface ;
- tests et validation ;
- finalisation de la documentation.

**Figure 2 - Diagramme PERT du projet**  
[Inserer ici la capture ou l'image du diagramme PERT]

### 1.7 Conclusion du chapitre

Ce premier chapitre a permis de poser le cadre general du projet, de definir sa problematique, ses objectifs, ses acteurs et ses principes de planification. Il constitue la base conceptuelle du travail realise. Le chapitre suivant sera consacre a l'analyse fonctionnelle et a la conception du systeme.

---

## Chapitre 2 - Analyse et conception

### 2.1 Introduction

L'analyse et la conception occupent une place centrale dans la realisation d'un projet logiciel. Elles permettent de transformer un besoin metier en specification exploitable, puis en architecture technique coherente. Dans ce projet, cette phase s'appuie principalement sur des cas d'utilisation et des diagrammes de sequence UML fournis dans le fichier `sequence.html`.

### 2.2 Vue d'ensemble des cas d'utilisation

Le fichier `sequence.html` contient **24 cas d'utilisation**, regroupes en quatre grandes familles fonctionnelles.

#### 2.2.1 Authentification

- UC-01 : S'inscrire
- UC-02 : Se connecter

#### 2.2.2 Consultation et publication

- UC-03 : Gerer profil
- UC-04 : Consulter revue
- UC-05 : Filtrer par sport
- UC-06 : Acceder archives
- UC-07 : Poster une source
- UC-08 : Exporter PDF
- UC-09 : Voir statistiques
- UC-10 : Voir references
- UC-11 : Ajouter liens

#### 2.2.3 Traitement IA

- UC-12 : Collecter articles
- UC-13 : Verifier ressources
- UC-14 : Classifier par sport
- UC-15 : Detecter meme info
- UC-16 : Compter nombre de journaux
- UC-17 : Calculer importance
- UC-18 : Stocker articles
- UC-19 : Generer resume quotidien
- UC-20 : Publier synthese quotidienne

#### 2.2.4 Administration

- UC-21 : Gerer utilisateurs
- UC-22 : Gerer Agent IA
- UC-23 : Verifier sources
- UC-24 : Voir logs

### 2.3 Analyse fonctionnelle

#### 2.3.1 Besoins fonctionnels

Le systeme doit permettre :

- l'authentification et la gestion du profil des utilisateurs ;
- la consultation des revues de presse et des archives ;
- le filtrage des contenus par sport ou critere de recherche ;
- la collecte automatisee des articles ;
- la verification des ressources et des sources ;
- la classification automatique des actualites ;
- le calcul d'un niveau d'importance ;
- la generation d'une synthese quotidienne ;
- la publication et l'export de la revue ;
- l'administration des utilisateurs et la supervision des traitements.

#### 2.3.2 Besoins non fonctionnels

Outre les besoins fonctionnels, la plateforme doit respecter plusieurs exigences non fonctionnelles :

- **performance** : traitement d'un volume important d'articles en un temps raisonnable ;
- **lisibilite** : presentation claire des contenus dans l'interface ;
- **maintenabilite** : architecture modulaire ;
- **scalabilite** : possibilite d'ajouter de nouvelles sources ou de nouveaux modules ;
- **fiabilite** : reduction des erreurs dans la collecte et le classement ;
- **securite** : gestion des acces et des operations d'administration.

### 2.4 Diagramme de cas d'utilisation general

Le diagramme de cas d'utilisation general synthétise les interactions entre les acteurs et le systeme. Il montre que le journaliste interagit principalement avec les fonctionnalites de consultation et de publication, tandis que l'Agent IA prend en charge les traitements internes automatises. L'administrateur, quant a lui, exerce une fonction de controle et de gouvernance.

**Figure 3 - Diagramme global de cas d'utilisation**  
[Inserer ici le diagramme de cas d'utilisation global]

### 2.5 Specification de cas d'utilisation representatifs

#### 2.5.1 UC-04 Consulter revue

**Acteur principal** : Journaliste  
**Declencheur** : demande de consultation de la revue de presse  
**Precondition** : le systeme dispose d'articles ou d'une synthese publiee  
**Postcondition** : l'utilisateur visualise les actualites organisees

**Scenario nominal**

1. Le journaliste accede a la page de revue.
2. Le systeme recupere la synthese et les statistiques associees.
3. Les articles sont regroupes et affiches.
4. L'utilisateur consulte les contenus disponibles.

**Figure 4 - Diagramme de sequence UC-04 Consulter revue**  
[Inserer ici la capture du diagramme correspondant]

#### 2.5.2 UC-05 Filtrer par sport

**Acteur principal** : Journaliste  
**Declencheur** : selection d'un sport  
**Postcondition** : les articles affiches correspondent au filtre applique

Ce cas d'utilisation decrit le comportement du systeme lorsque l'utilisateur souhaite limiter l'affichage a une discipline sportive donnee. Il illustre l'importance de la classification prealable et l'interaction entre l'interface et les donnees traitees.

**Figure 5 - Diagramme de sequence UC-05 Filtrer par sport**  
[Inserer ici la capture du diagramme correspondant]

#### 2.5.3 UC-12 Collecter articles

**Acteur principal** : Agent IA  
**Declencheur** : lancement du pipeline ou planification  
**Postcondition** : une liste d'articles bruts est recuperee

Ce cas d'utilisation correspond au point d'entree du pipeline de traitement. Il met en scene l'Agent IA, les ressources web externes et les objets internes charges de la collecte.

**Figure 6 - Diagramme de sequence UC-12 Collecter articles**  
[Inserer ici la capture du diagramme correspondant]

#### 2.5.4 UC-14 Classifier par sport

**Acteur principal** : Agent IA  
**Declencheur** : collecte terminee et contenu disponible  
**Postcondition** : chaque article recoit une categorie sportive

Cette fonctionnalite joue un role central dans la qualite de la revue finale. Elle permet d'organiser les actualites par discipline et de faciliter les operations de filtrage et de synthese.

**Figure 7 - Diagramme de sequence UC-14 Classifier par sport**  
[Inserer ici la capture du diagramme correspondant]

#### 2.5.5 UC-17 Calculer importance

**Acteur principal** : Agent IA  
**Declencheur** : phase post-classification  
**Postcondition** : chaque article recoit un score d'importance

Le calcul d'importance permet de prioriser les informations a forte valeur informative. Il facilite l'identification des actualites majeures et la generation de resumes plus pertinents.

**Figure 8 - Diagramme de sequence UC-17 Calculer importance**  
[Inserer ici la capture du diagramme correspondant]

#### 2.5.6 UC-19 Generer resume quotidien

**Acteur principal** : Agent IA (scheduler)  
**Declencheur** : fin de journee ou execution planifiee  
**Postcondition** : une synthese quotidienne est produite

Ce cas d'utilisation represente la phase de valorisation finale des donnees collectees et traitees. Le systeme genere une synthese structuree, limitee en taille, classee par sport et par source.

**Figure 9 - Diagramme de sequence UC-19 Generer resume quotidien**  
[Inserer ici la capture du diagramme correspondant]

#### 2.5.7 UC-23 Verifier sources

**Acteur principal** : Administrateur  
**Declencheur** : validation manuelle des sources  
**Postcondition** : la source est validee, rejetee ou mise a jour

Ce cas d'utilisation souligne le role de l'administrateur dans le maintien de la qualite informationnelle du systeme. Il contribue a renforcer la fiabilite globale de la plateforme.

**Figure 10 - Diagramme de sequence UC-23 Verifier sources**  
[Inserer ici la capture du diagramme correspondant]

### 2.6 Conception technique

#### 2.6.1 Architecture generale

L'architecture retenue se base sur une separation claire entre :

- un **frontend** pour la consultation des revues ;
- un **backend** pour l'orchestration des services ;
- un **pipeline de traitement** pour la collecte et l'analyse des contenus ;
- un **espace de stockage** pour les donnees et les rapports generes.

Cette architecture repond aux principes suivants :

- separation des responsabilites ;
- modularite ;
- lisibilite du code ;
- reutilisation des composants ;
- facilite d'integration future avec d'autres services.

**Figure 11 - Schema general de l'architecture de la solution**  
[Inserer ici le schema d'architecture globale]

#### 2.6.2 Principes de modelisation

La conception du systeme s'appuie sur :

- la modelisation des interactions via des diagrammes UML de sequence ;
- la decomposition du comportement en cas d'utilisation ;
- la definition des acteurs et des classes impliquees ;
- l'identification des dependances fonctionnelles entre modules.

### 2.7 Conclusion du chapitre

Ce chapitre a permis de formaliser les besoins du projet et de structurer sa conception. Les 24 cas d'utilisation identifies dans `sequence.html` constituent une base solide pour justifier les choix de realisation. Le chapitre suivant presente la mise en oeuvre technique de la plateforme.

---

## Chapitre 3 - Realisation et mise en oeuvre

### 3.1 Introduction

Apres la phase d'analyse et de conception, la realisation du projet a consisté a transformer les besoins formules en une solution logicielle fonctionnelle. Cette phase couvre le choix des technologies, l'organisation des composants, l'implementation des modules metier et la construction de l'interface utilisateur.

### 3.2 Technologies et outils utilises

Le projet a mobilise plusieurs technologies complementaires :

- **Python** : langage principal utilise pour le traitement des donnees et l'automatisation ;
- **FastAPI** : framework backend pour l'exposition de services API ;
- **Pandas** : manipulation des donnees tabulaires ;
- **BeautifulSoup** : scraping et extraction de contenus HTML ;
- **HTML / CSS / JavaScript** : construction de l'interface web ;
- **JSON** : echange et structuration de donnees ;
- **CSV** : format de stockage intermediaire ;
- **PlantUML** : formalisation des diagrammes de sequence ;
- **Git** : suivi de version.

**Figure 12 - Logos des technologies utilisees**  
[Inserer ici une planche de logos ou captures des technologies]

### 3.3 Organisation generale de la solution

La solution se compose de plusieurs espaces fonctionnels :

- `src/` pour les scripts de traitement ;
- `backend/` pour le service applicatif et les points d'entree API ;
- `frontend/` et `web/` pour l'interface de consultation ;
- `data/` pour les donnees d'entree, de sortie et les medias ;
- `docs/` pour les rapports generes ;
- `sequence.html` pour la documentation UML de reference.

### 3.4 Description des principaux modules

#### 3.4.1 Module de collecte

Le module de collecte a pour role d'extraire les articles depuis plusieurs sources sportives. Il se connecte a differents sites, analyse leur structure HTML et recupere les informations essentielles telles que le titre, la source, la date, le resume et l'URL de l'article.

**Capture d'ecran 1 - Resultat de collecte ou exemple d'articles extraits**  
[Inserer ici la capture d'ecran]

#### 3.4.2 Module de classification et d'enrichissement

Une fois les articles collectes, ils sont soumis a un traitement de normalisation puis a une classification automatique. Cette phase permet d'attribuer une categorie sportive a chaque contenu et d'ajouter des donnees utiles comme un resume, des mots-cles, des images ou des indicateurs de contexte.

**Capture d'ecran 2 - Exemple d'article enrichi**  
[Inserer ici la capture d'ecran]

#### 3.4.3 Module de verification et de credibilite

Le systeme integre un mecanisme de verification des ressources et des sources. Cette verification vise a distinguer les sources plus fiables, a limiter le bruit informationnel et a renforcer la pertinence des contenus publies.

**Capture d'ecran 3 - Vue des scores ou indicateurs de credibilite**  
[Inserer ici la capture d'ecran]

#### 3.4.4 Module de generation de rapport

Le module de generation produit une revue de presse quotidienne sous plusieurs formats, notamment HTML, JSON et texte brut. Il regroupe les articles, calcule des statistiques et structure une synthese des actualites principales.

**Capture d'ecran 4 - Exemple de revue de presse generee**  
[Inserer ici la capture d'ecran]

#### 3.4.5 Module de visualisation web

L'interface web permet de consulter les actualites, de filtrer les contenus, d'afficher des statistiques et d'acceder aux details des articles. L'accent a ete mis sur une organisation lisible des informations et une navigation simple.

**Capture d'ecran 5 - Interface d'accueil du systeme**  
[Inserer ici la capture d'ecran]

### 3.5 Architecture fonctionnelle de l'application

Le fonctionnement global du systeme peut etre resume comme suit :

1. le pipeline collecte les articles ;
2. les ressources sont verifiees ;
3. les articles sont classes et enrichis ;
4. un score d'importance est calcule ;
5. les donnees sont stockees ;
6. une synthese quotidienne est generee ;
7. la revue est publiee et rendue consultable.

**Figure 13 - Flux global de traitement de l'information**  
[Inserer ici un schema du pipeline]

### 3.6 Realisation des cas d'utilisation

#### 3.6.1 Authentification

La partie authentification couvre l'inscription, la connexion et la gestion de profil. Meme si certaines fonctionnalites peuvent rester simplifiees dans un prototype, elles ont ete modelisees afin de poser une base claire pour la gestion des roles et de la securite.

**Capture d'ecran 6 - Page d'inscription**  
[Inserer ici la capture d'ecran]

**Capture d'ecran 7 - Page de connexion**  
[Inserer ici la capture d'ecran]

#### 3.6.2 Consultation de la revue

La consultation de la revue permet au journaliste de visualiser les actualites du jour, de parcourir les rubriques sportives et d'acceder a une synthese structuree.

**Capture d'ecran 8 - Page de consultation de la revue**  
[Inserer ici la capture d'ecran]

#### 3.6.3 Filtrage par sport

Le filtrage par sport s'appuie sur les categories detectees lors du traitement. Il permet d'offrir une experience plus ciblee et plus pertinente pour l'utilisateur final.

**Capture d'ecran 9 - Filtrage des articles par discipline**  
[Inserer ici la capture d'ecran]

#### 3.6.4 Statistiques et references

La plateforme fournit egalement des donnees de synthese telles que le nombre d'articles, la repartition par sport et la liste des sources utilisees.

**Capture d'ecran 10 - Tableau ou graphique de statistiques**  
[Inserer ici la capture d'ecran]

### 3.7 Choix techniques et justification

Les choix techniques retenus se justifient par plusieurs raisons :

- Python facilite l'automatisation et le traitement textuel ;
- FastAPI fournit une structure moderne pour les services ;
- le decoupage frontend/backend ameliore la modularite ;
- les formats HTML, JSON et TXT offrent plusieurs niveaux d'exploitation des resultats ;
- PlantUML permet une documentation claire et evolutive de la logique systeme.

### 3.8 Conclusion du chapitre

Ce chapitre a presente la realisation technique de la plateforme de veille sportive. Il montre comment les besoins exprimes en amont ont ete traduits en composants concrets et en modules coherents. Le chapitre suivant evaluera les resultats, les tests et les limites du travail realise.

---

## Chapitre 4 - Tests, discussion et perspectives

### 4.1 Introduction

L'objectif de ce chapitre est d'evaluer la solution realisee, de presenter les principaux resultats obtenus et d'identifier les limites ainsi que les perspectives d'amelioration.

### 4.2 Resultats obtenus

La plateforme developpee permet :

- la collecte automatisee d'articles sportifs depuis plusieurs sources ;
- la structuration et le classement des contenus ;
- la generation de revues de presse exploitables ;
- la visualisation des actualites dans une interface web ;
- la modelisation precise des interactions metier a l'aide de 24 cas d'utilisation.

Parmi les sorties produites par le systeme, on retrouve :

- des rapports HTML ;
- des rapports JSON ;
- des rapports texte ;
- des images associees a certains contenus ;
- une base exploitable pour les statistiques et les archives.

### 4.3 Strategie de test

Les tests realises portent sur plusieurs niveaux :

- **tests de collecte** : verification de l'extraction correcte des articles ;
- **tests de traitement** : validation de la classification et de l'enrichissement ;
- **tests d'affichage** : controle du rendu de l'interface ;
- **tests fonctionnels** : verification des parcours utilisateur ;
- **tests de sortie** : controle de la generation des fichiers de revue.

**Tableau 1 - Exemple de synthese des tests effectues**  
[Inserer ici un tableau de tests fonctionnels]

### 4.4 Apports du projet

Le projet apporte plusieurs contributions :

- automatisation d'une tache traditionnellement manuelle ;
- centralisation de l'information sportive ;
- structuration des contenus selon une logique metier claire ;
- valorisation d'une approche hybride combinant veille, analyse et publication ;
- disponibilite d'une documentation UML riche facilitant la communication autour du systeme.

### 4.5 Limites du projet

Malgre ses apports, la solution presente certaines limites :

- la dependance a la structure HTML des sites source ;
- la variabilite de la qualite des contenus collectes ;
- la necessite d'ameliorer encore les mecanismes de desambiguïsation et de fusion des informations proches ;
- la possibilite de faux positifs ou faux negatifs dans la classification ;
- le besoin d'une administration plus poussee des sources.

### 4.6 Perspectives d'amelioration

Plusieurs pistes d'evolution peuvent etre envisagees :

- integration de modeles NLP plus avances ;
- systeme de recommandation personnalise ;
- tableau de bord analytique plus riche ;
- gestion avancee des utilisateurs et des droits ;
- publication automatique multicanal ;
- ajout d'une base de donnees relationnelle plus complete ;
- synchronisation avec des API sportives externes ;
- extension mobile ou Progressive Web App.

### 4.7 Discussion

Le projet montre qu'une plateforme de veille sportive intelligente peut etre construite a partir d'une architecture modulaire et de traitements automatises relativement accessibles. La richesse du fichier `sequence.html`, qui documente 24 cas d'utilisation, renforce la coherence entre l'analyse fonctionnelle et l'implementation. Cette correspondance est un point fort du projet, car elle facilite la traçabilite entre besoin, conception et realisation.

### 4.8 Conclusion du chapitre

Les resultats obtenus valident la faisabilite du projet et demontrent son interet pratique. Les limites identifiees ne remettent pas en cause la pertinence de la solution, mais constituent plutot des axes d'evolution pour une version plus industrielle du systeme.

---

## Conclusion generale

Ce projet de fin d'etudes avait pour objectif de concevoir et de realiser une plateforme intelligente de veille sportive multilingue capable de collecter, traiter, organiser et publier automatiquement des informations issues de plusieurs sources web. A travers l'analyse des besoins, la modelisation UML, la realisation technique et la mise en place d'un pipeline de traitement, il a ete possible de proposer une solution fonctionnelle, coherente et evolutive.

Le travail mene a permis d'atteindre les principaux objectifs fixes : automatisation de la collecte, classification des contenus, evaluation de leur importance, generation de rapports et visualisation des resultats. En outre, la documentation de conception, notamment les 24 diagrammes de sequence, constitue un support precieux pour la comprehension, la maintenance et l'amelioration future du systeme.

Au-dela des resultats techniques, ce projet a permis de mobiliser et de consolider des competences en analyse, modelisation UML, developpement backend, integration frontend, traitement de donnees et structuration de rapport technique. Il ouvre egalement plusieurs perspectives d'amelioration, particulierement dans le domaine de l'intelligence artificielle appliquee a la veille informationnelle.

En definitive, cette experience represente une etape importante dans un parcours de formation en informatique, en proposant une reponse concrete a un besoin reel de centralisation, de tri et de valorisation de l'information sportive.

---

## Bibliographie

### References documentaires

- Guide_PFE_IDS.pptx, guide de recommandations pour la redaction du rapport et la soutenance.
- PFENASSRAOUIRAPPORT[1].docx, rapport source d'inspiration pour la structure academique.
- sequence.html, documentation des diagrammes de sequence UML du systeme.

### References techniques

- Documentation Python.
- Documentation FastAPI.
- Documentation Pandas.
- Documentation BeautifulSoup.
- Documentation PlantUML.

### Remarque bibliographique

La bibliographie finale devra etre normalisee selon la forme demandee par l'etablissement, avec classement alphabetique et ajout des dates de consultation pour les sources web.

---

## Annexes

### Annexe 1 - Emplacements des figures et captures

- Figure 1 : Diagramme de Gantt
- Figure 2 : Diagramme PERT
- Figure 3 : Diagramme global de cas d'utilisation
- Figure 4 a Figure 10 : Diagrammes de sequence representatifs
- Figure 11 : Architecture generale
- Figure 12 : Technologies utilisees
- Figure 13 : Flux global de traitement
- Captures d'ecran 1 a 10 : Interfaces et resultats

### Annexe 2 - Liste complete des cas d'utilisation issus de `sequence.html`

| Code | Intitule | Groupe |
| --- | --- | --- |
| UC-01 | S'inscrire | Authentification |
| UC-02 | Se connecter | Authentification |
| UC-03 | Gerer profil | Consultation et publication |
| UC-04 | Consulter revue | Consultation et publication |
| UC-05 | Filtrer par sport | Consultation et publication |
| UC-06 | Acceder archives | Consultation et publication |
| UC-07 | Poster une source | Consultation et publication |
| UC-08 | Exporter PDF | Consultation et publication |
| UC-09 | Voir statistiques | Consultation et publication |
| UC-10 | Voir references | Consultation et publication |
| UC-11 | Ajouter liens | Consultation et publication |
| UC-12 | Collecter articles | Traitement IA |
| UC-13 | Verifier ressources | Traitement IA |
| UC-14 | Classifier par sport | Traitement IA |
| UC-15 | Detecter meme info | Traitement IA |
| UC-16 | Compter nombre de journaux | Traitement IA |
| UC-17 | Calculer importance | Traitement IA |
| UC-18 | Stocker articles | Traitement IA |
| UC-19 | Generer resume quotidien | Traitement IA |
| UC-20 | Publier synthese quotidienne | Traitement IA |
| UC-21 | Gerer utilisateurs | Administration |
| UC-22 | Gerer Agent IA | Administration |
| UC-23 | Verifier sources | Administration |
| UC-24 | Voir logs | Administration |

### Annexe 3 - Notes pour insertion des captures

Chaque emplacement de figure ou de capture d'ecran doit etre remplace par :

- une image nette ;
- une legende numerotee ;
- une reference dans le texte ;
- une explication concise de ce que montre la figure.

