"""Interface language: English, French, Kinyarwanda.

The cited survey sentences on the district and method pages stay in
English. The choice screen, the field sheet, and the planner chrome follow
the language stored in the session.
"""

from __future__ import annotations

LANGS = ("en", "fr", "rw")
LABELS = (("en", "en"), ("fr", "fra"), ("rw", "kin"))

COPY = {
    "who_title": {"en": "Who is reading?", "fr": "Qui lit ?", "rw": "Ni nde usoma?"},
    "who_lead": {"en": "Choose once.", "fr": "Choisissez une fois.", "rw": "Hitamo inshuro imwe."},
    "farmer": {"en": "Farmer", "fr": "Agriculteur", "rw": "Umuhinzi"},
    "planner": {"en": "Planner", "fr": "Planificateur", "rw": "Umuyobozi"},
    "nav_field": {"en": "Farmer map", "fr": "Carte du champ", "rw": "Ikarita y'umuhinzi"},
    "nav_crops": {"en": "Crops", "fr": "Cultures", "rw": "Ibihingwa"},
    "nav_districts": {"en": "District map", "fr": "Carte des districts", "rw": "Ikarita y'uturere"},
    "nav_method": {"en": "Method", "fr": "Méthode", "rw": "Uburyo"},
    "nav_sector": {"en": "Your sector", "fr": "Votre secteur", "rw": "Umurenge wawe"},
    "change": {"en": "Change", "fr": "Changer", "rw": "Hindura"},
    "change_long": {"en": "Change who is reading", "fr": "Changer le lecteur", "rw": "Hindura uwisoma"},
    "search": {"en": "Search a village", "fr": "Chercher un village", "rw": "Shakisha umudugudu"},
    "where": {"en": "Where I am", "fr": "Où je suis", "rw": "Aho ndi"},
    "voice": {"en": "Speak", "fr": "Parler", "rw": "Vuga"},
    "hearing": {"en": "Listening…", "fr": "J'écoute…", "rw": "Ndumva…"},
    "brand_farmer": {"en": "Advice for your field", "fr": "Conseil pour votre champ", "rw": "Inama ku murima wawe"},
    "brand_sector": {"en": "The district's advice", "fr": "Le conseil du district", "rw": "Inama y'akarere"},
    "prompt_farmer": {
        "en": "Tap the map where you will plant.",
        "fr": "Touchez la carte là où vous allez cultiver.",
        "rw": "Kanda ku karita aho uzahinga.",
    },
    "prompt_place": {
        "en": "Select the village where you will plant.",
        "fr": "Choisissez le village où vous allez cultiver.",
        "rw": "Hitamo umudugudu uzahingamo.",
    },
    "prompt_crops": {
        "en": "Select the crops.",
        "fr": "Choisissez les cultures.",
        "rw": "Hitamo ibihingwa.",
    },
    "prompt_sector": {
        "en": "Find your sector. No sector table. The numbers are the district's.",
        "fr": "Trouvez votre secteur. Pas de tableau par secteur. Les chiffres sont ceux du district.",
        "rw": "Shaka umurenge wawe. Nta mibare y'umurenge. Imibare ni iy'akarere.",
    },
    "office_district": {
        "en": "Which district do you read?",
        "fr": "Quel district lisez-vous ?",
        "rw": "Ni akahe karere usoma?",
    },
    "office_sector": {
        "en": "Which sector do you read?",
        "fr": "Quel secteur lisez-vous ?",
        "rw": "Ni uwuhe murenge usoma?",
    },
    "office_open": {"en": "Open", "fr": "Ouvrir", "rw": "Fungura"},
    "office_sectors": {
        "en": "Show the sectors",
        "fr": "Montrer les secteurs",
        "rw": "Erekana imirenge",
    },
    "office_hint": {
        "en": "You will see this place only.",
        "fr": "Vous ne verrez que ce lieu.",
        "rw": "Uzabona aha hantu gusa.",
    },
    "ladder": {"en": "Choose the place", "fr": "Choisir le lieu", "rw": "Hindura ahantu"},
    "ladder_hint": {
        "en": "District, sector, cell, village",
        "fr": "District, secteur, cellule, village",
        "rw": "Akarere, umurenge, akagari, umudugudu",
    },
    "pick_district": {"en": "District", "fr": "District", "rw": "Akarere"},
    "pick_sector": {"en": "Sector", "fr": "Secteur", "rw": "Umurenge"},
    "pick_cell": {"en": "Cell", "fr": "Cellule", "rw": "Akagari"},
    "pick_village": {"en": "Village", "fr": "Village", "rw": "Umudugudu"},
    "opt_district": {"en": "Choose a district", "fr": "Choisir un district", "rw": "Hitamo akarere"},
    "opt_sector": {"en": "Choose a sector", "fr": "Choisir un secteur", "rw": "Hitamo umurenge"},
    "opt_cell": {"en": "Choose a cell", "fr": "Choisir une cellule", "rw": "Hitamo akagari"},
    "opt_village": {"en": "Choose a village", "fr": "Choisir un village", "rw": "Hitamo umudugudu"},
    "tap_village": {"en": "Tap your village.", "fr": "Touchez votre village.", "rw": "Kanda umudugudu wawe."},
    "open_district": {"en": "Read {name}.", "fr": "Lire {name}.", "rw": "Soma akarere ka {name}."},
    "board_blank": {"en": "blank", "fr": "vide", "rw": "ntabwo"},
    "board_pick": {
        "en": "Choose a crop to add its yield.",
        "fr": "Choisissez une culture pour ajouter son rendement.",
        "rw": "Hitamo igihingwa kugira ngo umusaruro wongerwe.",
    },
    "plans": {"en": "Saved aims", "fr": "Objectifs enregistrés", "rw": "Intego wabitse"},
    "you": {"en": "You", "fr": "Vous", "rw": "Wowe"},
    "us": {"en": "Umusaruro", "fr": "Umusaruro", "rw": "Umusaruro"},
    "need_village": {
        "en": "Tap the village on the map first.",
        "fr": "Touchez d'abord le village sur la carte.",
        "rw": "Banza ukande umudugudu ku karita.",
    },
    "saved": {"en": "Aim saved", "fr": "Objectif enregistré", "rw": "Intego yabitswe"},
    "no_geo": {
        "en": "This device cannot show where you are. Tap the map.",
        "fr": "Cet appareil ne montre pas où vous êtes. Touchez la carte.",
        "rw": "Iyi mudasobwa ntayerekana aho uri. Kanda ku karita.",
    },
    "no_fix": {
        "en": "Where you are could not be found. Tap the map.",
        "fr": "L'endroit n'a pas été trouvé. Touchez la carte.",
        "rw": "Ntabwo nabonye aho uri. Kanda ku karita.",
    },
    "no_voice": {
        "en": "This device does not hear speech. Type or tap the map.",
        "fr": "Cet appareil n'entend pas la voix. Écrivez ou touchez la carte.",
        "rw": "Iyi mudasobwa ntumva ijwi. Koresha amagambo cyangwa kanda ku karita.",
    },
    "not_heard": {
        "en": "That was not heard. Say it again, or type the village.",
        "fr": "Ce n'était pas entendu. Répétez, ou écrivez le village.",
        "rw": "Ntabwo numvise. Ongera uvuge, cyangwa andika izina ry'umudugudu.",
    },
    "failed": {"en": "That did not save.", "fr": "L'enregistrement a échoué.", "rw": "Ntibyakunze."},
    "no_place": {"en": "That tap is outside Rwanda.", "fr": "Cet endroit est hors du Rwanda.", "rw": "Aho wakandagiye ntibirimo mu Rwanda."},
    "need_crop": {"en": "Choose a district and a crop.", "fr": "Choisissez un district et une culture.", "rw": "Hitamo akarere n'igihingwa."},
    "unknown_district": {"en": "That district was not found.", "fr": "Ce district est introuvable.", "rw": "Aka karere ntikabonetse."},
    "empty_voice": {"en": "No words were heard.", "fr": "Aucun mot n'a été entendu.", "rw": "Ntabwo navunikiwe ijambo."},
    "need_crop_only": {"en": "Choose a crop.", "fr": "Choisissez une culture.", "rw": "Hitamo igihingwa."},
    "bad_target": {"en": "Write the aim in kg per hectare.", "fr": "Écrivez l'objectif en kg par hectare.", "rw": "Andika intego mu kg kuri hegitari."},
    "rejected_target": {"en": "That aim is not accepted.", "fr": "Cet objectif n'est pas accepté.", "rw": "Intego ntiyemewe."},
    "advisor_h1": {"en": "Every crop. Three stages.", "fr": "Chaque culture. Trois étapes.", "rw": "Igihingwa cyose. Intambwe eshatu."},
    "overview_h1": {"en": "The field, beside the reading.", "fr": "Le terrain, à côté de la lecture.", "rw": "Umurima, hafi y'isosomo."},
    "tag": {"en": "Cultivation advisor", "fr": "Conseil de culture", "rw": "Umujyanama w'ubuhinzi"},
    "lang_name": {"en": "Language", "fr": "Langue", "rw": "Ururimi"},
    "flag_name": {"en": "What to do", "fr": "Quoi faire", "rw": "Icyo gukora"},
    "flag_plant": {"en": "Plant", "fr": "Cultiver", "rw": "Hinga"},
    "flag_check": {"en": "Check", "fr": "Vérifier", "rw": "Reba"},
    "flag_stop": {"en": "Stop", "fr": "Arrêt", "rw": "Hagarara"},
    "flag_wait": {
        "en": "Choose a crop. The color will say what to do.",
        "fr": "Choisissez une culture. La couleur dira quoi faire.",
        "rw": "Hitamo igihingwa. Ibara rizakubwira icyo gukora.",
    },
    "flag_plant_line": {
        "en": "The survey printed a harvest for this crop in this district. You can set an aim.",
        "fr": "L'enquête a imprimé une récolte pour cette culture dans ce district. Vous pouvez fixer un objectif.",
        "rw": "Raporo yanditse umusaruro w'iki gihingwa muri aka karere. Ushobora gushyiraho intego.",
    },
    "flag_check_line": {
        "en": "Read the card. Water, seed, or fertilizer needs a look in this district.",
        "fr": "Lisez la carte. L'eau, la semence ou l'engrais demande un regard dans ce district.",
        "rw": "Soma ikarita. Amazi, imbuto, cyangwa ifumbire bisaba kureba muri aka karere.",
    },
    "flag_stop_line": {
        "en": "This crop was not printed for this district. A blank is not zero.",
        "fr": "Cette culture n'a pas été imprimée pour ce district. Une case vide n'est pas zéro.",
        "rw": "Iki gihingwa ntikanditswe muri aka karere. Ahatagira umubare si zeru.",
    },
    "ask_seed": {
        "en": "What seed will you plant?",
        "fr": "Quelle semence allez-vous planter ?",
        "rw": "Ni iyihe mbuto uzahinga?",
    },
    "seed_improved": {"en": "Improved seed", "fr": "Semence améliorée", "rw": "Imbuto y'ingeri"},
    "seed_saved": {"en": "Seed I kept from last harvest", "fr": "Semence gardée de la dernière récolte", "rw": "Imbuto nabikije ku musaruro ushize"},
    "seed_unset": {"en": "I have not chosen yet", "fr": "Je n'ai pas encore choisi", "rw": "Sinahisemo"},
    "ask_water": {
        "en": "How will the crop get water?",
        "fr": "Comment la culture aura-t-elle de l'eau ?",
        "rw": "Igihingwa kizabonera amazi he?",
    },
    "water_rain": {"en": "Rain only", "fr": "La pluie seulement", "rw": "Imvura gusa"},
    "water_add": {"en": "I can add water", "fr": "Je peux ajouter de l'eau", "rw": "Nshobora kongeramo amazi"},
    "ask_purpose": {
        "en": "What do you want from the harvest?",
        "fr": "Que voulez-vous de la récolte ?",
        "rw": "Umusaruro ubukenera iki?",
    },
    "purpose_food": {"en": "Food at home", "fr": "À manger à la maison", "rw": "Ibiryo mu rugo"},
    "purpose_sell": {"en": "To sell", "fr": "À vendre", "rw": "Kugurisha"},
    "purpose_both": {"en": "Both", "fr": "Les deux", "rw": "Byombi"},
    "plan_goals": {"en": "Goals", "fr": "Objectifs", "rw": "Intego"},
    "plan_seed": {"en": "Seed", "fr": "Semence", "rw": "Imbuto"},
    "plan_daily": {"en": "Each day", "fr": "Chaque jour", "rw": "Buri munsi"},
    "plan_weekly": {"en": "Each week", "fr": "Chaque semaine", "rw": "Buri cyumweru"},
    "save_aim": {"en": "Save the aim", "fr": "Enregistrer l'objectif", "rw": "Bika intego"},
    "save_plan": {"en": "Save my plan", "fr": "Enregistrer mon plan", "rw": "Bika igahunda yanjye"},
    "plan_saved": {"en": "Plan saved", "fr": "Plan enregistré", "rw": "Igahunda yabitswe"},
    "cal_title": {"en": "Calendar", "fr": "Calendrier", "rw": "Kalendari"},
    "cal_today": {"en": "Today", "fr": "Aujourd'hui", "rw": "Uyu munsi"},
    "cal_week": {"en": "This week", "fr": "Cette semaine", "rw": "Iki cyumweru"},
    "cal_day": {"en": "Day {day} of {total}.", "fr": "Jour {day} sur {total}.", "rw": "Umunsi wa {day} muri {total}."},
    "cal_choice": {
        "en": "You can mark a task when you want to remember it.",
        "fr": "Vous pouvez cocher une tâche quand vous voulez vous en souvenir.",
        "rw": "Ushobora gushyira akamenyetso ku gikorwa iyo ushaka kwibuka.",
    },
    "cal_marked": {
        "en": "You have marked {n} tasks.",
        "fr": "Vous avez coché {n} tâches.",
        "rw": "Washyizeho akamenyetso ku bikorwa {n}.",
    },
    "cal_weekdays": {
        "en": "Mo,Tu,We,Th,Fr,Sa,Su",
        "fr": "lu,ma,me,je,ve,sa,di",
        "rw": "Mbe,Kab,Gat,Kan,Gtn,Gtd,Cyu",
    },
    "cal_months": {
        "en": "January,February,March,April,May,June,July,August,September,October,November,December",
        "fr": "janvier,février,mars,avril,mai,juin,juillet,août,septembre,octobre,novembre,décembre",
        "rw": "Mutarama,Gashyantare,Werurwe,Mata,Gicurasi,Kamena,Nyakanga,Kanama,Nzeli,Ukwakira,Ugushyingo,Ukuboza",
    },
    "change_answers": {"en": "Change your answers", "fr": "Changer vos réponses", "rw": "Hindura ibisubizo"},
    "step_place": {"en": "Place", "fr": "Lieu", "rw": "Ahantu"},
    "step_crops": {"en": "Crops", "fr": "Cultures", "rw": "Ibihingwa"},
    "step_ask": {"en": "Questions", "fr": "Questions", "rw": "Ibibazo"},
    "step_note": {"en": "Note", "fr": "Note", "rw": "Inyandiko"},
    "popup_farm": {"en": "The farm", "fr": "La ferme", "rw": "Umurima"},
    "popup_garden": {"en": "This garden", "fr": "Ce jardin", "rw": "Uru rugo"},
    "farm_size": {"en": "How big is the farm?", "fr": "Quelle est la taille de la ferme ?", "rw": "Umurima ungana iki?"},
    "unit_ha": {"en": "hectares", "fr": "hectares", "rw": "hegitari"},
    "unit_m2": {"en": "square metres", "fr": "mètres carrés", "rw": "metero kare"},
    "portion_for": {
        "en": "On what scale, in {unit}, will you plant {name}?",
        "fr": "Sur quelle surface, en {unit}, allez-vous planter {name} ?",
        "rw": "Uzahinga {name} ku bunini bwangana iki, mu {unit}?",
    },
    "your_target": {
        "en": "What is your goal from that land, in kg?",
        "fr": "Quel est votre objectif sur cette terre, en kg ?",
        "rw": "Intego yawe kuri ubwo butaka ni kg zingahe?",
    },
    "digits_only": {
        "en": "That is not a number.",
        "fr": "Ce n'est pas un nombre.",
        "rw": "Ibyo si umubare.",
    },
    "letters_only": {
        "en": "That is not a letter.",
        "fr": "Ce n'est pas une lettre.",
        "rw": "Ibyo si inyuguti.",
    },
    "country_goal": {"en": "Country goal on the farm", "fr": "Objectif du pays sur la ferme", "rw": "Intego y'igihugu ku murima"},
    "country_harvest": {"en": "Country harvest on the farm", "fr": "Récolte du pays sur la ferme", "rw": "Umusaruro w'igihugu ku murima"},
    "per_ha": {"en": "kg/ha", "fr": "kg/ha", "rw": "kg/ha"},
    "on_land": {
        "en": "max on this land: {kg} kg.",
        "fr": "maximum sur cette terre : {kg} kg.",
        "rw": "ingano ntarengwa kuri ubu butaka: {kg} kg.",
    },
    "together": {
        "en": "Together that is {used} {unit}.",
        "fr": "Ensemble, cela fait {used} {unit}.",
        "rw": "Hamwe ni {used} {unit}.",
    },
    "exceed_farm": {
        "en": "You are exceeding the size of the farm.",
        "fr": "Vous dépassez la taille de la ferme.",
        "rw": "Urenga ubunini bw'umurima.",
    },
    "exceed_max": {
        "en": "You are exceeding the maximum on this land.",
        "fr": "Vous dépassez le maximum sur cette terre.",
        "rw": "Urenga ingano ntarengwa kuri ubu butaka.",
    },
    "over_max": {
        "en": "The maximum on this land is {max} kg.",
        "fr": "Le maximum sur cette terre est {max} kg.",
        "rw": "Ingano ntarengwa kuri ubu butaka ni {max} kg.",
    },
    "farm_cap": {
        "en": "The farm is {farm} {unit}.",
        "fr": "La ferme fait {farm} {unit}.",
        "rw": "Umurima ni {farm} {unit}.",
    },
    "over_farm": {
        "en": "The farm is {farm} {unit}. That is {over} {unit} more than the farm.",
        "fr": "La ferme fait {farm} {unit}. C'est {over} {unit} de plus que la ferme.",
        "rw": "Umurima ni {farm} {unit}. Biruta umurima {over} {unit}.",
    },
    "fit_farm": {
        "en": "The farm is {farm} {unit}. {left} {unit} are still open.",
        "fr": "La ferme fait {farm} {unit}. Il reste {left} {unit}.",
        "rw": "Umurima ni {farm} {unit}. Hasigaye {left} {unit}.",
    },
    "popup_done": {"en": "Done", "fr": "Terminer", "rw": "Byarangiye"},
    "summary_title": {"en": "Summary", "fr": "Résumé", "rw": "Incamake"},
    "plan_title": {"en": "Your plan", "fr": "Votre plan", "rw": "Igahunda yawe"},
    "plan_daily": {"en": "Daily", "fr": "Chaque jour", "rw": "Buri munsi"},
    "plan_weekly": {"en": "Weekly", "fr": "Chaque semaine", "rw": "Buri cyumweru"},
    "popup_close": {"en": "Close", "fr": "Fermer", "rw": "Funga"},
    "continue_ask": {"en": "Answer the questions", "fr": "Répondre aux questions", "rw": "Subiza ibibazo"},
    "continue_note": {"en": "Read the note", "fr": "Lire la note", "rw": "Soma inyandiko"},
    "no_country": {
        "en": "The country figure for this crop was not printed.",
        "fr": "Le chiffre du pays pour cette culture n'a pas été imprimé.",
        "rw": "Umubare w'igihugu kuri iki gihingwa ntiwanditswe.",
    },
    "change_farm": {"en": "Change the answers", "fr": "Changer les réponses", "rw": "Hindura ibisubizo"},
    "chat_open": {"en": "Ask", "fr": "Demander", "rw": "Baza"},
    "chat_title": {"en": "Ask Umusaruro", "fr": "Demander à Umusaruro", "rw": "Baza Umusaruro"},
    "chat_hint": {
        "en": "Ask about a village, a district, or a crop in this survey.",
        "fr": "Demandez un village, un district, ou une culture de cette enquête.",
        "rw": "Baza umudugudu, akarere, cyangwa igihingwa muri iyi raporo.",
    },
    "chat_send": {"en": "Send", "fr": "Envoyer", "rw": "Ohereza"},
    "chat_wait": {"en": "Reading the survey…", "fr": "Lecture de l'enquête…", "rw": "Ndasoma raporo…"},
    "chat_outside": {
        "en": "Umusaruro cannot answer that. Ask about a village or a district in Rwanda, and a crop this survey prints. For example: What did maize yield in Kicukiro? You can also ask about rain, irrigation, improved seed, or fertilizer in that district.",
        "fr": "Umusaruro ne peut pas répondre à cela. Demandez un village ou un district du Rwanda, et une culture de cette enquête. Par exemple : Quel est le rendement du maïs à Kicukiro ? Vous pouvez aussi demander la pluie, l'irrigation, la semence améliorée ou l'engrais de ce district.",
        "rw": "Umusaruro ntibishobora kubisubiza. Baza umudugudu cyangwa akarere mu Rwanda, n'igihingwa iyi raporo ivuga. Urugero: Umusaruro w'ibigori muri Kicukiro ni uwuhe? Ushobora kandi kubaza imvura, kuvoma, imbuto zizungu, cyangwa ifumbire muri ako karere.",
    },
    "chat_hello": {
        "en": "Hello. I can help with a village or a district in Rwanda, and a crop this survey prints. Ask about the harvest, rain, irrigation, improved seed, or fertilizer. For example: What did maize yield in Kicukiro?",
        "fr": "Bonjour. Je peux aider pour un village ou un district du Rwanda, et une culture de cette enquête. Demandez la récolte, la pluie, l'irrigation, la semence améliorée ou l'engrais. Par exemple : Quel est le rendement du maïs à Kicukiro ?",
        "rw": "Muraho. Nshobora kugufasha ku mudugudu cyangwa akarere mu Rwanda, n'igihingwa iyi raporo ivuga. Baza umusaruro, imvura, kuvoma, imbuto zizungu, cyangwa ifumbire. Urugero: Umusaruro w'ibigori muri Kicukiro ni uwuhe?",
    },
    "chat_offline": {
        "en": "The chat is not connected yet. The server needs an NVIDIA API key.",
        "fr": "Le dialogue n'est pas encore relié. Le serveur a besoin d'une clé API NVIDIA.",
        "rw": "Iki kiganiro ntikirahuza. Seriveri ikeneye urufunguzo rwa NVIDIA.",
    },
    "chat_fail": {
        "en": "The model did not answer. Ask again in one sentence that names a place and a crop.",
        "fr": "Le modèle n'a pas répondu. Redemandez en une phrase qui nomme un lieu et une culture.",
        "rw": "Icyo model ntikibashije gusubiza. Baza incuro imwe uvuga ahantu n'igihingwa.",
    },
    "chat_later": {
        "en": "That is enough questions for this visit. Ask again later.",
        "fr": "Cela suffit pour cette visite. Redemandez plus tard.",
        "rw": "Ibibazo byahagije kuri ubu. Ongera ubaze nyuma.",
    },
    "chat_name_place": {
        "en": "Name a village or a district, and a crop this survey prints. For example: What did maize yield in Kicukiro?",
        "fr": "Nommez un village ou un district, et une culture de cette enquête. Par exemple : Quel est le rendement du maïs à Kicukiro ?",
        "rw": "Vuga umudugudu cyangwa akarere, n'igihingwa iyi raporo ivuga. Urugero: Umusaruro w'ibigori muri Kicukiro ni uwuhe?",
    },
    "chat_two": {
        "en": "Name one district. You named {a} and {b}.",
        "fr": "Nommez un seul district. Vous avez nommé {a} et {b}.",
        "rw": "Vuga akarere kamwe. Wavuzwe {a} na {b}.",
    },
    "chat_one_at_a_time": {
        "en": "Name one district at a time.",
        "fr": "Nommez un district à la fois.",
        "rw": "Vuga akarere kamwe ku nshuro.",
    },
    "chat_shared": {
        "en": "{name} is the name of more than one place: {places}. Name the district as well.",
        "fr": "{name} est le nom de plus d'un lieu : {places}. Nommez aussi le district.",
        "rw": "{name} ni izina ry'ahantu henshi: {places}. Vuga n'akarere.",
    },
    "chat_shared_one": {
        "en": "{name} is more than one place in {district}: {places}. The figures below are for that district.",
        "fr": "{name} est plus d'un lieu dans {district} : {places}. Les chiffres ci-dessous sont ceux de ce district.",
        "rw": "{name} ni ahantu henshi muri {district}: {places}. Imibare iri hepfo ni iy'ako karere.",
    },
    "chat_locked": {
        "en": "You read {district} only.",
        "fr": "Vous ne lisez que {district}.",
        "rw": "Usoma {district} gusa.",
    },
    "chat_sector": {
        "en": "There is no sector table for {sector}. These figures are for {district} district.",
        "fr": "Il n'y a pas de tableau pour le secteur de {sector}. Ces chiffres sont ceux du district de {district}.",
        "rw": "Nta mibare y'umurenge wa {sector}. Imibare ni iya karere ka {district}.",
    },
    "chat_village": {
        "en": "{village} is a village in {cell}, {sector}, {district}. The survey is not published for one village. These figures are for {district} district.",
        "fr": "{village} est un village de {cell}, {sector}, {district}. L'enquête n'est pas publiée pour un village. Ces chiffres sont ceux du district de {district}.",
        "rw": "{village} ni umudugudu uri mu kagari ka {cell}, umurenge wa {sector}, akarere ka {district}. Raporo ntisoza umudugudu. Imibare ni iya karere ka {district}.",
    },
}


def current_lang(request) -> str:
    lang = request.session.get("lang")
    return lang if lang in LANGS else "en"


def text(request, key: str) -> str:
    row = COPY[key]
    return row.get(current_lang(request)) or row["en"]


def pack(lang: str) -> dict:
    return {key: row.get(lang) or row["en"] for key, row in COPY.items()}


def safe_next(value: str | None) -> str:
    if not value or not value.startswith("/") or value.startswith("//"):
        return "/"
    return value
