# Skript na extrakci prvních vět, odstavců, celého textu a na generování znalostní báze pro všechny stránky české wikipedie

#### Složka projektu:
  */mnt/minerva1/nlp/projects/czech_wikipedia*
#### Github:
  *https://github.com/KNOT-FIT-BUT/czech_wikipedia*

#### Soubory:
* **wikiextractor/** - obsahuje _WikiExtractor.py_ (https://github.com/attardi/wikiextractor), který se používá při první fázi extrakce dat z wikidumpu (viz Postup extrakce dat)
* **czechwiki_extractor.py** - vlastní skript, který extrahuje data z předzpracovaného dumpu od *WikiExtractor.py*.
* **cs-wiki-latest-pages-articles_link.xml** - symlink na český wikidump: /mnt/minerva1/nlp/corpora_datasets/monolingual/czech/wikipedia/cswiki-latest-pages-articles.xml.
* **preprocessed_dump_<DATETIME>**, **results_<DATETIME>** - soubory generované při extrakci dat z dumpu. Adresář *results_<DATETIME>* obsahuje konečné výsledné soubory extrakce.
* **work** - složka s poznámkami a BASH skripty pro urychlení práce.
* **abbreviation_added_to_nltk.txt, czech_abbreviations.txt** - soubory se zkratkami, které jsou předány extraktoru vět NLTK.
## Postup extrakce dat

1) Spustit **wikiextractor/WikiExtractor.py --templates --filter_disambig_pages <templatefile> -ns Soubor --html --output <outputdir> <wikidumpfile.xml>**, kde:
* <templatefile> - soubor, kde si WikiExtractor extrahuje definici Wikišablon. Pokud neexistuje, je automaticky vytvořen a skript do něj extrahuje šablony. Pokud již existuje (a obsahuje šablony), je použit k urychlení předzpracování dumpu. Každopádně je nutné parametr "--templates" uvést, aby ve výstupu byly expandované Wikišablony.
* -ns Soubor - výstup bude obsahovat odkazy na soubory (např. obrázky), které se použijí při generování knowledgebase.
* --html - czechwiki_extractor.py očekává HTML vstup
* <outputdir> - složka, kam se předzpracovaný výstup ukládá. Zde budou složky s názvy "AA", "AB", "AC" atd. Tuto složku je třeba uvést jako parametr "--datadir <preprocessed_dump_dir>" při spuštění czechwiki_extractor.py
* <wikidumpfile.xml> - vlastní wiki dump

2) Spustit **czechwiki_extractor.py --datadir <preprocessed_dump_dir> --outputdir <outputdir> [-s] [-p] [-f] [--kb] [--logfile <logfile>]**, kde:
* <dumpdir> - složka obsahující předzpracované soubory od WikiExtractor.py (viz krok 1).
* <outputdir> - kam má czechwiki_extractor ukládat výsledné soubory/složky.
* -s - extrahuj URI a první věty článků do "<outputdir>/sentences.txt".
* -p - extrahuj URI a první odstavce článků do "<outputdir>/paragraphs.txt".
* -f - extrahuj celý text každého článku do samostatného souboru se jménem jména článku do složky "<outputdir>/fulltexts". 
* --kb - vygeneruj znalostní bázi každé wiki stránky do souboru "<outputdir>/knowledgebase.txt".
* --logfile <logfile> - pokud chcete logovat zprávy do souboru (bez --logfile se vypisují pouze na STDERR)

## Poznámky

Nejefektivnější je spustit czechwiki_extractor.py se všemi parametry zároveň (-s -p -f --kb). Kvůli zjednodušení skriptu se stejně extrahují všechna data zároveň téměř kompletně, tyto flagy pouze rozhodují o tom, zda se zapíší výsledky do souborů.

Oblasti změn v kódu WikiExtractor.py jsou ohraničené komentáři ### MODIFY_START - ### MODIFY_END.

Extrakce odstavců a vět nefunguje 100 % správně, formáty některých wikičlánků nebo větné konstrukce extraktor nezvládá. Úspěšnost extrakce je odhadem 95 %.
## Minulá řešení

Projekty pro extrakci vět, odstavců a celých textů již byly v minulosti řešeny:
* Skript na získavanie prvých viet/odstavců z textov z Wikipédie (xkoron00, xkralb00, xrusin03): https://knot.fit.vutbr.cz/wiki/index.php/Decipher_wikipedia#Skript_na_z.C3.ADskavanie_prv.C3.BDch_viet.2Fodstavc.C5.AF_z_textov_z_Wikip.C3.A9die_.28xkoron00.2C_xkralb00.2C_xrusin03.29
* Skript na získavání celých textů z Wikipedie (xnedel08): https://knot.fit.vutbr.cz/wiki/index.php/Decipher_wikipedia#Skript_na_z.C3.ADskav.C3.A1n.C3.AD_cel.C3.BDch_text.C5.AF_z_Wikipedie_.28xnedel08.29

Oba skripty také používají modul WikiExtractor, ale pouze jednu jeho funkci - 'clean()'. Tato funkce odstraňuje z textu z wikidumpu zbytečné konstrukce (viz WikiExtractor.py). Pokud je však použita samostatně jako v těchto projektech, odstraní z textu i důležité konstrukce jako referenční odkazy na jiné články a Wiki šablony. Výstup se tedy zběžně tváří v pořadku, ale chybí v něm slova či celé úseky textu. Tyto konstrukce správným způsobem zpracuje WikiExtractor.py dříve před zavoláním funkce clean().
Současné řešení nechá WikiExtractor předzpracovat wikidump do jednoduše parsovatelného HTML formátu, kde jsou konstrukce jako šablony a odkazy a další správně nahrazeny.

## Výsledky extrakce

Výsledky jsou ve složce:
    /mnt/minerva1/nlp/projects/czech_wikipedia/results

Soubory:
* sentences.txt - každý řádek obsahuje URI a první větu jednoho článku.
* paragraphs.txt - každý řádek obsahuje URI a první odstavec jednoho článku. 
* fulltexts/ - složka obsahující soubory pro každý článek wikipedie pojmenovaný "wp_pagetitle" (jako "wiki page"). Soubor obsahuje celý text článku včetně nadpisů sekcí. Soubory jsou roztříděné do složek "d_LL", kde "LL" jsou první dvě písmena titulu wiki článku.
* knowledgebase.txt - každý řádek obsahuje: Název, URI, ID, první odstavec a seznam souborů (obrázků, ...). Položky jsou ooděleny tabulátorem, jednotlivé odkazy na soubory jsou odděleny znakem '|'.

### Testování 
Testování proběhlo na serveru athena1.
Skript WikiExtractor.py byl spuštěn následovně:
   **wikiextractor/WikiExtractor.py --templates template_defs.tmpl -ns Soubor --html --output preprocessed_dump cs-wiki-latest-pages-articles_link.xml**
   Program běžel 18 525 sekund (~ 5 hodin 8 minut), z toho extrakce šablon zabrala cca 3 minuty.

   Skript czechwiki_extractor.py byl spuštěn následovně:
       **czechwiki_extractor.py --datadir preprocessed_dump --outputdir results -s -p -f --kb**
	   Program běžel 233 sekund (necelé 4 minuty). Zpracoval celkem 398 287 článků wikipedie.

