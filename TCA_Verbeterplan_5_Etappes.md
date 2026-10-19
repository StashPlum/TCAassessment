# TCA verbeterplan in vijf etappes

## Advies en gebruik

Voer de wijzigingen uit in vijf opeenvolgende etappes in dezelfde bestaande repository. Houd één volledige wijzigingslijst als geheugen, maar geef Codex per run één afgebakende etappe. Dat vermindert de kans dat verschillende datamodellen, beoordelingsregels en visuele componenten tegelijk uit elkaar gaan lopen. Dezelfde featurebranch kan vijf controleerbare commits/milestones bevatten.

Plaats dit bestand en het oorspronkelijke Word-document in de projectmap. Voer onderstaande prompts in volgorde uit. Etappe 1 leest de bron volledig en maakt een compacte dekkingslijst; volgende etappes gebruiken die lijst en raadplegen Word bij twijfel. Hervat een onderbroken etappe voordat je de volgende start. De nieuwe Word-tekst bepaalt de nieuwe functionele opdracht waar eerdere prompts daarvan afwijken. Bronnen en historische records worden niet overschreven.

| Etappe | Resultaat | Waarom hier |
| --- | --- | --- |
| 1 | Rollen, Advisory-passregel en versieerbare siteconfiguratie | Dashboards, invoer en exports moeten dezelfde betekenis gebruiken |
| 2 | CEVA-designbasis, Overview en doorklikbare TCA-matrix | Een consistente visuele richting voorkomt herwerk in latere schermen |
| 3 | Voorbereiden, plannen, uitvoeren en assessmenthistorie | De complete auditreis gebruikt de foundation en gedeelde componenten |
| 4 | Kaizen, teams/Gantt, A3/A4 en sensei-review | Alle event- en rapportagefuncties delen dezelfde opgeslagen gegevens |
| 5 | Learning, evidence, reportfilters en integrale eindcontrole | Kennisdeling en exports moeten aansluiten op de gehele gebruikersreis |

## Twee betekenissen die expliciet moeten worden vastgelegd

De Word-tekst verklaart antwoord A als Advisory en een pass met verbeteropvolging. Eerdere prompts hielden de betekenis open. De ingevoegde screenshotlegenda omschrijft Advisory anders. Behandel de nieuwe Word-tekst als de expliciete gebruikersinstructie voor de nieuwe versie, registreer het verschil en bewaar oude uitslagen onder hun toenmalige regelversie. Antwoord A is een ander veld dan maturitycode A voor Showcase.

Beoordeeld is een ingevuld Y/A/N-antwoord. Voldoet betekent onder de nieuwe regel een geaccepteerd Y of Advisory. Open Advisory-opvolging blijft zichtbaar, ook als het een pass is. De screenshot met 56 Y, 19 Advisory en 75 N heeft alle 150 vragen beoordeeld, maar 75/150 die voldoen onder de nieuwe passregel. 100% beoordeeld en 50% voldoet zijn verschillende meetgetallen.

Certified/Advanced/Showcase volgen hun bestaande requirementgates en laagste-sectieregel; geen percentage vervangt die beoordeling. De kaart moet compact blijven met duidelijk gelabelde waarden en doorklik naar detail. Officiële CAT-confirmatie, lokale gereedheid en werkplanning blijven herkenbaar.

## Visuele werkwijze

Mijn voorkeursroute is Codex in de bestaande codebase. Begin in etappe 2 met drie daadwerkelijk renderende referentieschermen: Overview, de TCA-matrix en Conduct assessment. Gebruik synthetische data, bestaande goedgekeurde CEVA-assets en dezelfde databetekenis uit etappe 1. Leg de gekozen kleurenrollen, typografie, spacing, filterbalken, statussen, tabellen, diagrammen en responsieve regels vast. Implementeer daarna dezelfde componenten op de overige routes. Herhaal de visuele controle aan het einde van etappe 5.

Een tekst als 'maak futuristisch' geeft onvoldoende richting. Beschrijf per scherm welke informatie dominant is, wat pas na doorklik zichtbaar wordt, en welke concrete referentie gevolgd moet worden. Vraag Codex de gerenderde pagina naast de referentie te beoordelen op hiërarchie, uitlijning, witruimte, informatiedichtheid, leesbaarheid en interactie. Een geslaagde build is geen visuele inspectie.

De matrix is hier de belangrijkste datavisualisatie: secties als rijen, requirements per maturityband als kolommen, kleuren plus letters/symbolen voor Y/Advisory/N/onbeoordeeld en klikken voor bewijs, opmerkingen, opvolging en verbeteracties. Gebruik een compacte balk voor globale voortgang en een echte Gantt voor planning. Selecteer grafieken op de vraag van de gebruiker; extra decoratieve grafieken voegen weinig toe.

### Base44 als optionele uitvoering van dezelfde visuele etappe

Base44 en de afzonderlijke Base Code-route zijn verschillende werkwijzen. De actuele Base Code-documentatie beschrijft het aansluiten van een bestaande GitHub-codebase, werken op een branch, een live developmentpreview en review via pull requests. Dat maakt Base Code een optionele uitvoerder van etappe 2; het is geen noodzaak voor een beter ontwerp. Ondersteuning van jouw concrete runtime/setup en toegang moet in de gekozen omgeving worden vastgesteld.

Als je Base Code wilt proberen:
1. Rond etappe 1 af en push de featurebranch met de status/dekkingslijst.
2. Verbind uitsluitend de juiste bestaande GitHub-repository en kies/importeer de actuele werkbranch. Controleer setupwijzigingen en start de bestaande app met synthetische data.
3. Geef daar prompt 2, dezelfde CEVA-referenties en het Word-document. Houd de opdracht bij ontwerp/presentatie en bestaande routes. Verander datamodel, scoring en rechten alleen in de daarvoor aangewezen etappes.
4. Inspecteer de preview en diff. Laat geen tweede platformarchitectuur of fictieve datalaag de werkende applicatie vervangen.
5. Laat de wijzigingen naar de werkbranch terugkomen. Haal die branch in Codex op, controleer de relevante regressies en ga met etappe 3 verder. Laat Codex en Base Code niet tegelijk dezelfde componenten wijzigen.
6. Volg de bestaande review-/mergeprocedure. Een automatische branch-push is geen opdracht voor een main-merge of productiedeployment.

Deze route valt binnen etappe 2; zij is geen zesde etappe. Voor alleen een visueel concept kun je ook een los Base44-prototype met synthetische data maken en screenshots als referentie aan Codex geven. Die prototypecode hoeft niet naar de productierepository te worden gekopieerd. Voor dit bestaande project heeft doorwerken in Codex mijn voorkeur omdat dat een extra overdracht vermijdt.

De ervaring 'functioneel goed, visueel minder' bewijst niet dat Codex geen goede interface kan maken. Het is een aanwijzing om de ontwerprichtlijn, referenties en render/inspecteer/verbeter-cyclus expliciet te maken.

## Dekkingslijst van het Word-document

W-nummers zijn wijzigingspunten uit dit document, geen nieuwe officiële TCA-requirement-IDs.

| ID | Gevraagde wijziging | Bron | Etappe |
| --- | --- | --- | --- |
| W01 | Vier rollen en passende focus | p.1 rollen | 1,2 |
| W02 | Volledige toegestane informatie via passend abstractieniveau/doorklik | p.1 | 1,2,5 |
| W03 | CEVA-stijl en geavanceerde visuele weergave zonder generieke AI-look | p.1 | 2,5 |
| W04 | Minder headertekst, strakke typografie, spacing, dropdowns en click-throughs | p.1 | 2,5 |
| W05 | Overview compact percentage, beoordeeld-teller en level | p.1 Overview | 1,2,5 |
| W06 | Authorized locations voorlopig uit de interface | p.2 | 2 |
| W07 | Prepare evidence XLSX en gestructureerde CEVA-PDF | p.2 | 3 |
| W08 | Auditor kan benodigde documentatie wijzigen | p.2 | 1,3 |
| W09 | Vooraf afstemmen en bevestigen van operationele personeelsinzet | p.2 Plan | 3 |
| W10 | Laagdrempelige planning en motiverende verbetercultuur | p.2 Plan | 3,4 |
| W11 | Site kiezen en vraagstelling/benodigdheden in voorbereidingsdashboard wijzigen | p.2 Plan | 1,3 |
| W12 | Wijzigingen en eerdere assessmentversies opslaan/archiveren | p.2 Plan | 1,3 |
| W13 | A is Advisory-pass; vorige A uitlichten en expliciet hertoetsen | p.2 Plan | 1,3,5 |
| W14 | Conduct assessmentkeuze met meest recente relevante versie als default | p.3 | 3 |
| W15 | Conduct filters sectie en evidence-type | p.3 | 3 |
| W16 | Drie views: alle vragen, per sectie, één vraag | p.3 | 3 |
| W17 | Y/A/N en opmerkingen invoeren | p.3 | 1,3 |
| W18 | Assessment history volledige PDF en Excel | p.3 | 3 |
| W19 | History filter jaar, site, versie, auditor | p.3 | 3 |
| W20 | Improvement opportunities als matrix op basis van ingevoegde referentie | p.3 afbeelding | 2 |
| W21 | Small/Medium/Extensive behouden met kortere uitleg | p.3–4 | 4 |
| W22 | Lean-toolbox eenvoudiger begrijpen met uitleg-link/pagina | p.4 | 4 |
| W23 | Toolvisualisaties strakker en leesbaarder | p.4 | 4 |
| W24 | In teams aan Kaizens werken | p.4 | 4 |
| W25 | Taken toewijzen aan teamleden | p.4 | 4 |
| W26 | Gantt-planning in Plan | p.4 | 4 |
| W27 | Verbetercultuur, eenvoudig gebruik en minimale administratie | p.4 | 1,2,3,4,5 |
| W28 | A3/A4 ook functioneel onderscheiden conform CEVA | p.4 | 4 |
| W29 | Volledige Kaizen opslaan in de software | p.4 | 4 |
| W30 | A3/A4 PDF/XLSX downloaden vanuit sensei-review voor handmatige Teams-opslag | p.4 | 4 |
| W31 | Sensei-review visueler met kleinere filters | p.4 | 4 |
| W32 | Meest recente relevante Kaizens direct zichtbaar | p.4 | 4 |
| W33 | PDF/XLSX-export vanuit reviewqueue | p.4 | 4 |
| W34 | Learning filter op specifieke TCA-vraag | p.4 | 5 |
| W35 | Korte lessons learned andere sites met Kaizen-documentatie | p.4 | 5 |
| W36 | Best practices met uitleg hoe ze zijn bereikt | p.5 | 5 |
| W37 | Learning overzichtelijk met compacte filters/spacing | p.5 | 5 |
| W38 | Evidence library laten aansluiten op alle wijzigingen | p.5 | 5 |
| W39 | Slimme filters voor Reports en guidance | p.5 | 5 |

## Prompt 1

Werk in de bestaande TCA-repository. Lees AGENTS.md, de projectstatus, "software aanpassingen.docx" inclusief de ingevoegde matrixafbeelding, en TCA_Verbeterplan_5_Etappes.md. Voer alleen etappe 1 uit. Bewaar werkende functies, bronbestanden en gebruikerswijzigingen; hergebruik de huidige stack.

Maak docs/CHANGESET_2026-10-19.md met alle wijzigingspunten uit Word, bronverwijzing, verantwoordelijke etappe, acceptatiecriterium en status. Gebruik de dekkingslijst uit het verbeterplan, maar controleer deze tegen het Word-bestand. Houd besluiten en echte testresultaten bij; latere etappes lezen dit compacte bestand in plaats van alle eerdere gesprekken.

Leg vast en implementeer:
- Rollen TCA-auditor, site manager, sensei en Kaizen-teamlid, met passende startpagina/navigatie en een expliciete rechtenmatrix. De auditor heeft de benodigde volledige inzage binnen zijn toegestane sites. Managers zien resultaten/blockers, senseis coaching/review, teamleden hun projecten/taken en het starten van Kaizens vanuit findings. Een rol bepaalt de standaardweergave; beschermde data en bevoegdheden worden server-side afgedwongen. Bestaande beheerdersrollen blijven beschikbaar.
- Antwoord A betekent nu Advisory: een pass met een open verbeterpunt en expliciete hertoetsing bij de volgende assessment. Dit vervangt eerdere instructies waarin A onbekend was. Sla antwoordcode en maturitycode apart op. Y en A tellen als pass onder deze nieuwe, versieerbare regel; N niet. Bewaar Advisory als amber, met opmerking, opvolging en hertoetsstatus. Maak historische adviezen zichtbaar, ook als een nieuwe review ze sluit. Wijzig historische goedgekeurde uitslagen niet stilzwijgend.
- Scheid beoordeeld (Y/A/N ingevuld), voldoet (geaccepteerd Y/A), open Advisory-opvolging, lokale gereedheid en officieel bevestigde classificatie. Eventafronding of een siteclaim geeft geen automatische TCA-pass. Behoud gate-, lowest-section-, frequentie- en CAT-controles.
- Maak sitegebonden vraagformuleringen en evidence-lijsten bewerkbaar in een versieerbare assessmentconfiguratie. Bewaar globale bron/IDs, auteurs, reden, verschillen en eerdere versies. Onderscheid lokale toelichting van wijziging van een officiële verplichting; behoud het toepasselijke goedkeuringspad. Een gestart assessment gebruikt een vaste snapshot.

Het screenshot heeft een oudere Advisory-legenda. Gebruik de expliciete definitie in de nieuwe Word-tekst voor de nieuwe applicatieregel en registreer het verschil. Kopieer geplande/bevestigde siteacties uit de afbeelding niet als officiële assessmentantwoorden.

Gebruik additieve migraties. Test oude records, rol/site-afscherming, Y/A/N, Advisory-opvolging, versieverschillen en onveranderlijke historie. Eindig met een werkende foundation en compacte status voor etappe 2.

Voor deze en volgende etappes geldt: implementeer, test relevante wijzigingen, herstel fouten, werk de dekkingslijst bij en commit/push na succesvolle controles naar dezelfde featurebranch in de bestaande GitHub-repository. Geen force-push, main-merge of productiedeployment; geen secrets, databases of private uploads committen. Meld ontbrekende toegang eerlijk. Stop na de gevraagde etappe, zonder routinewerk steeds ter bevestiging voor te leggen.

## Prompt 2

Voer alleen etappe 2 uit in de bestaande repository. Lees AGENTS.md en docs/CHANGESET_2026-10-19.md. Bouw voort op etappe 1 en behoud de huidige businessregels en opgeslagen informatie.

Werk als senior productdesigner en frontend engineer. Maak de CEVA-ontwerprichtlijn concreet: bestaande goedgekeurde kleuren/logo/fonts eerst; consistente typografie, een vaste spacing-schaal, strakke uitlijning, beperkte accenten, leesbare datavisualisaties en korte doelgerichte animaties. Vertaal "futuristisch" naar een moderne zakelijke applicatie. Vermijd decoratieve hero-secties, generieke kaartmuren, overdreven afgeronde panelen, lange introducties en overmatige gradients. Leg de gekozen tokens en componenten vast.

Maak eerst drie representatieve schermen op synthetische fixtures: Overview, de TCA-matrix en Conduct assessment. Implementeer ze op de echte lokale routes en inspecteer browserscreenshots voordat je de componenten breder toepast. Leg kleine ontwerpkeuzes zelf vast; lever een samenhangend resultaat in plaats van alleen CSS of een ontwerpdocument.

Overview: vervang de tekstzware coverage-weergave door een compacte balk of ring met betekenisvol gelabeld percentage, teller/noemer en level. Verplaats uitleg naar een uitklapbaar detailpaneel. Houd 'beoordeeld' en 'voldoet' herkenbaar gescheiden; 100% ingevuld betekent geen 100% conformiteit. Behoud de gevraagde beoordeeld-teller als aparte compacte indicator waar nodig. Toon 150 alleen wanneer de effectieve scope daadwerkelijk 150 is. Verberg voorlopig het blok Authorized locations; behoud de sitekeuze en autorisatiecontroles.

Improvement opportunities: maak een klikbare 15-secties-bij-10-requirementsmatrix voor de standaardcatalogus, met banden voor Certified/Advanced/Showcase, Y groen, Advisory amber, N rood en onbeoordeeld neutraal. Toon status ook met tekst/symbolen. Ondersteun afwijkende goedgekeurde profielen. Een cel opent bronvraag, bewijs, eerdere opmerking, Advisory-opvolging en gekoppelde acties/Kaizens. Lokale planningsstatussen blijven apart van auditorantwoorden. Laat prioriteiten en blockers direct doorlopen naar acties en learning.

Gebruik op alle schermen dezelfde compacte filterbalk, uitklapbare extra filters, labels boven controls, heldere actieve filters en een reset. Houd dropdowns binnen viewport/modal, met toetsenbordbediening en consistente afmetingen. Maak rolspecifieke samenvattingen met doorklik naar toegestane details. Minder tekst betekent geen verwijderde informatie.

Inspecteer minimaal 1440, 1024 en 390 pixels breed, lange labels, lege/foutstatussen en een druk gevulde matrix. Behoud zo nodig scroll binnen de matrix, zonder horizontale pagina-overflow. Controleer focus, contrast, klikroutes en datagelijkheid met de detailweergave. Werk de dekkingslijst bij, commit en push volgens de opgeslagen werkafspraken, en stop na etappe 2.

## Prompt 3

Voer alleen etappe 3 uit. Lees AGENTS.md en docs/CHANGESET_2026-10-19.md. Maak de assessmentreis compleet met de componenten en regels uit etappes 1–2.

Prepare evidence: laat de auditor een sitegebonden lijst met benodigde documentatie aanpassen, met versie, reden en herkomst. Wijzig daarmee geen oorspronkelijke requirement zonder het passende wijzigingspad. Genereer echte XLSX-werkmappen en leesbare CEVA-gebrande PDFs met categorie, requirement-ID, exacte verplichting, evidence, eigenaar en relevante periode/datum. Maak exportbereik en actieve filters expliciet; exporteer alle geselecteerde records, ook buiten de zichtbare paginering.

Plan assessment: bied een laagdrempelige voorbereiding met doel, scope/secties, deelnemers en verwachte inzet per tijdsblok. Laat de site manager de beschikbaarheid bevestigen of direct een alternatief/backup voorstellen. Maak knelpunten vóór het assessment zichtbaar. Een late operationele wijziging krijgt reden, impact, nieuwe afspraak en verantwoordelijke opvolging; software kan personeelsbeschikbaarheid niet afdwingen. Gebruik ondersteunende taal, passende reminders binnen de app en korte blokken waar dat de assessmentkwaliteit toelaat. Voeg geen onbevestigde externe agenda-/mailintegratie toe.

Na sitekeuze krijgt de auditor een voorbereidingswerkplek om vraagformuleringen, evidence-behoeften en assessmentversie te bekijken/bewerken volgens etappe 1. Archiveer verschillen en eerdere versies. Licht vorige Advisory-antwoorden uit, met eerder bewijs, open verbeterpunt en expliciete hertoetsactie; neem geen pass automatisch over.

Conduct assessment: laat een gepland/bestaand assessment kiezen, met de meest recente relevante versie standaard geselecteerd. Een al gestart dossier blijft aan zijn vaste snapshot gekoppeld; een nieuwere template wordt niet automatisch ingevoegd. Bied drie gesynchroniseerde views: alle vragen, per sectie en één vraag tegelijk. Filter op sectie en evidence-type. Laat Y/A/N en opmerkingen duidelijk invoeren, met evidence en Advisory-opvolging in context. Autosave toont succes/falen; wisselen van view/filter of herladen behoudt antwoorden.

Assessment history: filter op jaar, site, versie en auditor. Download één of een selectie assessments als volledige PDF/XLSX, met snapshot, regelversie, exacte vragen, antwoorden, opmerkingen, bewijsverwijzingen en opvolging. Historische exports gebruiken historische inhoud; geef onvolledige dossiers hun echte status.

Test beschikbaarheid/rescheduling, keuze van site/versie, eerdere Advisory-hertoetsing, alle drie views, autosave/foutafhandeling, filters, volledige XLSX/PDF-exports en onbevoegde directe requests. Inspecteer gegenereerde PDFs en open XLSX-structuur/inhoud. Werk status bij, commit/push volgens de werkafspraken en stop na etappe 3.

## Prompt 4

Voer alleen etappe 4 uit. Lees AGENTS.md, docs/CHANGESET_2026-10-19.md en de relevante bestaande Kaizen-bronmapping. Verfijn Kaizen en sensei-review; behoud de al goed werkende toolbox en eventgegevens.

Maak Small/Medium/Extensive compacte keuzes met één korte uitleg en optionele hulp. Houd een eenvoudige PDCA-werkplek met autosave, direct toegankelijke bijlagen en één gedeelde registratie van team, acties en metingen. Geef iedere Lean-methode een herkenbare help-link/paneel met doel, stappen, benodigde invoer en een kort logistiek voorbeeld. Verbeter de gegenereerde diagrammen: consistente typografie, afstanden, labels, schaalbaarheid, leesbare exports en behoud van lange/dynamische inhoud.

Voeg teamleden en taaktoewijzing toe binnen bestaande rechten. Laat teamleden hun eigen verantwoordelijkheden en wijzigingen zien. Bouw in Plan een werkende Gantt-weergave uit dezelfde acties, met eigenaar, begin/eind, voortgang en datumvalidatie. Bewaar geen tweede planning naast de actielijst. Houd bekijken/bewerken ook mogelijk via een toegankelijke tabel en voorkom stille overschrijving bij gelijktijdige wijzigingen.

Maak het onderscheid tussen CEVA A3- en A4-eventtypen functioneel op basis van de goedgekeurde bronregels; wijzig niet uitsluitend het papierformaat. Houd Small/Medium/Extensive, methodologisch eventtype en rapportformaat afzonderlijk. Forceer geen onbevestigde mapping zoals Small=A4. Behoud verplichte/conditionele velden, financiële validatie en afzonderlijke coach/kwaliteitscriteria. Ontbrekende CEVA-interpretaties worden gericht als open punt vastgelegd; bestaande werkende lokale invoer blijft bruikbaar.

Sla het gehele event met analyses, bijlagen, meetreeksen, taken, versies en review op. Genereer bij de geldende finalisatiestap passende A3/A4-PDF én echte XLSX. Maak een compacte, leesbare rapportage met volledige ondersteunende informatie in vervolgbladen/bijlagen; verwijder geen broninhoud om het document passend te maken. Bewaar goedgekeurde rapportversies. Download moet mogelijk zijn vanuit het event en sensei-review, zodat gebruikers de bestanden zelf in Teams kunnen opslaan.

Maak de sensei-reviewqueue visueel compacter, met kleine filters, standaard de recentst ingediende relevante Kaizens bovenaan, zichtbare reviewstatus en korte resultaten. Open details, wijzigingen en bewijs via doorklik. Bied PDF/XLSX-export van één of geselecteerde events; toon review- en validatiestatus eerlijk. Laat de sensei feedback geven zonder dubbele invoer. Afronden/goedkeuren van een event geeft geen automatische TCA-pass.

Test teams/rechten, taak- en Gantt-synchronisatie, profiel-/typewissels zonder verlies, diagramdata, bronregels A3/A4, bijlagen, correcte recente sortering en alle downloadroutes. Inspecteer A3/A4-PDFs op ware schaal en controleer XLSX-inhoud tegen het event. Werk status bij, commit/push en stop na etappe 4.

## Prompt 5

Voer alleen etappe 5 uit. Lees AGENTS.md en docs/CHANGESET_2026-10-19.md. Rond kennisdeling, libraries, rapportfilters en de integrale visuele/werkingcontrole af.

Learning repository: maak de exacte TCA-requirement-ID het belangrijkste inhoudelijke filter. Toon korte lessons learned van toegestane andere sites met probleem/context, aanpak, resultaat, borging en de bijbehorende Kaizen-documentatie. Toon apart welke voorbeelden als best practice zijn gevalideerd, door wie, en hoe ze tot stand kwamen. Een afgesloten event krijgt niet automatisch het label best practice. Respecteer templateversie/lineage en laat overdraagbaarheid en relevante profielverschillen zien. Overnemen maakt een nieuw gekoppeld dossier, zonder gekopieerde approvals, bewijsclaims of TCA-antwoorden.

Evidence library: gebruik dezelfde evidence-objecten en herkomst-/versiegegevens als assessments, voorbereidingslijsten, Kaizens en rapporten. Filter op requirement, categorie, site, type, periode, eigenaar en status voor zover die velden bestaan. Maak geldigheid en links zichtbaar; voorkom dubbele uploads bij het koppelen van hetzelfde bestand. Bescherm ook zoekresultaten, downloads en exports tegen ongeautoriseerde toegang.

Reports en guidance: voeg passende slimme filters toe, zoals site/country, jaar/periode, auditor/eigenaar, assessment-/templateversie, sectie/requirement, niveau, Advisory/reviewstatus, Kaizenprofiel en A3/A4-type. Toon alleen relevante filters per inhoudstype, standaard compact met meer filters uitklapbaar. Zorg voor consistente reset, lege resultaten, exportbereik, geldige parametercombinaties en actuele-versus-gearchiveerde guidance.

Doe een integrale gebruikersreis voor auditor, site manager, sensei en teamlid: voorbereiding, personeelsafspraak, siteversie, Y/A/N, eerdere Advisory opnieuw toetsen, historie-export, matrix, Kaizen met team/Gantt/tool, sensei-review, A3/A4-download en leren via dezelfde TCA-vraag op een andere site.

Controleer in dezelfde fixture de tellers: 56 Y, 19 Advisory en 75 N op 150 geeft 150/150 beoordeeld, 75/150 voldoet onder de nieuwe Advisory-passregel en 19 Advisory-opvolgpunten. De screenshotkleuren/legenda zijn geen vervanging voor die expliciete regel. Behoud onbekende/noemer- en historische regelversies. Een gerichte requirementreview reset geen volledige sectiefrequentie.

Inspecteer alle gewijzigde schermen op desktop/tablet/mobiel met synthetische data, inclusief rolverschillen, filters, dropdowns, lange teksten, fouten en gegenereerde rapporten. Corrigeer resterende visuele inconsistenties via de gedeelde componenten. Voer relevante regressie-, migratie-, rechten-, berekenings- en exportchecks uit en herstel materiële fouten.

Reconcileer ieder Word-wijzigingspunt met de dekkingslijst: gedaan met bewijs, al correct met verificatie, of concreet geblokkeerd. Lever geen ongefundeerde claim dat alles klaar is. Werk instructies/status bij, commit/push de featurebranch, controleer de remote commit en toepasselijke CI. Meld wat werkt, echte verificatie, eventuele beperkingen, branch, SHA en GitHub-link. Geen main-merge of productiedeployment.

## Bronnen en grenzen van dit verbeterplan

Het document is gebaseerd op de vijf pagina's van "software aanpassingen.docx", inclusief de ingesloten Site DIY Plan Summary-afbeelding. De onvolledige zin bij de senseirol is niet aangevuld met verzonnen bevoegdheden. De globale CEVA-bronnen en bestaande rolconfiguratie bepalen aanvullende bevoegdheden.

- OpenAI, Build responsive front-end designs: https://learn.chatgpt.com/use-cases/frontend-designs
- OpenAI, Designing delightful frontends: https://developers.openai.com/blog/designing-delightful-frontends-with-gpt-5-4
- Base44, Using Base Code: https://docs.base44.com/Getting-Started/base-code
- Base44, Customizing design: https://docs.base44.com/Building-your-app/Design

De platformdocumentatie is op 19 oktober 2026 gecontroleerd. Zij ondersteunt de beschreven werkwijze, niet een belofte dat één platform automatisch beter ontwerpt. Er zijn in deze opdracht geen wijzigingen aan de applicatie uitgevoerd. De vijf prompts zijn bedoeld voor Codex of de expliciet gekozen Base Code-omgeving waar de bestaande repository beschikbaar is.
