"""Data class representing the key information of a LOTUS entry."""

from typing import List, Any, Optional, Iterator
from dataclasses import dataclass
import pandas as pd
import numpy as np
from monolith.data.otl_class import Match


NPC_PATHWAYS: List[str] = [
    "Alkaloids",
    "Amino acids and Peptides",
    "Carbohydrates",
    "Fatty acids",
    "Polyketides",
    "Shikimates and Phenylpropanoids",
    "Terpenoids",
]
NPC_SUPERCLASSES: List[str] = [
    "Alkylresorcinols",
    "Amino acid glycosides",
    "Aminosugars and aminoglycosides",
    "Anthranilic acid alkaloids",
    "Apocarotenoids",
    "Aromatic polyketides",
    "Carotenoids (C40)",
    "Carotenoids (C45)",
    "Carotenoids (C50)",
    "Chromanes",
    "Coumarins",
    "Cyclic polyketides",
    "Diarylheptanoids",
    "Diazotetronic acids and derivatives",
    "Diphenyl ethers (DPEs)",
    "Diterpenoids",
    "Docosanoids",
    "Eicosanoids",
    "Fatty Acids and Conjugates",
    "Fatty acyl glycosides",
    "Fatty acyls",
    "Fatty amides",
    "Fatty esters",
    "Flavonoids",
    "Fluorenes",
    "Glycerolipids",
    "Glycerophospholipids",
    "Guanidine alkaloids",
    "Histidine alkaloids",
    "Isoflavonoids",
    "Lignans",
    "Linear polyketides",
    "Lysine alkaloids",
    "Macrolides",
    "Meroterpenoids",
    "Miscellaneous alkaloids",
    "Miscellaneous polyketides",
    "Mitomycin derivatives",
    "Monoterpenoids",
    "Mycosporine derivatives",
    "Naphthalenes",
    "Nicotinic acid alkaloids",
    "Nucleosides",
    "Octadecanoids",
    "Oligopeptides",
    "Ornithine alkaloids",
    "Peptide alkaloids",
    "Phenanthrenoids",
    "Phenolic acids (C6-C1)",
    "Phenylethanoids (C6-C2)",
    "Phenylpropanoids (C6-C3)",
    "Phloroglucinols",
    "Polycyclic aromatic polyketides",
    "Polyethers",
    "Polyols",
    "Polyprenols",
    "Proline alkaloids",
    "Pseudoalkaloids",
    "Pseudoalkaloids (transamidation)",
    "Saccharides",
    "Serine alkaloids",
    "Sesquiterpenoids",
    "Sesterterpenoids",
    "Small peptides",
    "Sphingolipids",
    "Steroids",
    "Stilbenoids",
    "Styrylpyrones",
    "Terphenyls",
    "Tetramate alkaloids",
    "Triterpenoids",
    "Tropolones",
    "Tryptophan alkaloids",
    "Tyrosine alkaloids",
    "Xanthones",
    "\u03b2-lactams",
    "\u03b3-lactam-\u03b2-lactones",
]
NPC_CLASSES: List[str] = [
    "12-oxophytodienoic acid metabolites",
    "2-arylbenzofurans",
    "2-pyrone derivatives",
    "3-Decalinoyltetramic acids",
    "3-Spirotetramic acids",
    "3-acyl tetramic acids",
    "3-oligoenoyltetramic acids",
    "4-pyrone derivatives",
    "Abeoabietane diterpenoids",
    "Abeolupane triterpenoids",
    "Abeotaxane diterpenoids",
    "Abietane diterpenoids",
    "Acetate-derived alkaloids",
    "Acetogenins",
    "Acidic glycosphingolipids",
    "Acorane sesquiterpenoids",
    "Acridone alkaloids",
    "Actinomycins",
    "Acutumine alkaloids",
    "Acyclic guanidine alkaloids",
    "Acyclic monoterpenoids",
    "Acyclic triterpenoids",
    "Acyl phloroglucinols",
    "Adianane triterpenoids",
    "Aeruginosins",
    "Aflatoxins",
    "Africanane sesquiterpenoids",
    "Agarofuran sesquiterpenoids",
    "Ahp-containing cyclodepsipeptides",
    "Alliacane sesquiterpenoids",
    "Allohimachalane sesquiterpenoids",
    "Amarylidaceae alkaloids",
    "Amino cyclitols",
    "Amino fatty acids",
    "Aminoacids",
    "Aminoglycosides",
    "Aminosugars",
    "Amphilectane diterpenoids",
    "Anabaenopeptins",
    "Androstane steroids",
    "Angucyclines",
    "Ansa macrolides",
    "Ansa peptide alkaloids",
    "Anthocyanidins",
    "Anthracyclines",
    "Anthranillic acid derivatives",
    "Anthraquinones and anthrones",
    "Antimycins",
    "Aphidicolane diterpenoids",
    "Aplysiatoxins",
    "Apocarotenoids (C30, \u03a8-\u03a8)",
    "Apocarotenoids (\u03a8-)",
    "Apocarotenoids (\u03b2-)",
    "Apocarotenoids(\u03b5-)",
    "Aporphine alkaloids",
    "Apotirucallane triterpenoids",
    "Aristolane sesquiterpenoids",
    "Aromadendrane sesquiterpenoids",
    "Aromatic polyketides with side chains",
    "Arteminisin",
    "Arylnaphthalene and aryltetralin lignans",
    "Asbestinane diterpenoids",
    "Ascarosides",
    "Ascomycins and Rapamycins",
    "Asperane sesterterpenoids",
    "Aspidosperma type",
    "Aspidosperma-Iboga hybrid type (Vinca alkaloids)",
    "Asteriscane sesquiterpenoids",
    "Atisane diterpenoids",
    "Aurones",
    "Avermectins",
    "Azaphilones",
    "Azo and Azoxy alkaloids",
    "Baccharane triterpenoids",
    "Bactoprenols",
    "Bafilomycins",
    "Bagremycins",
    "Bauerane triterpenoids",
    "Benastatins and derivatives",
    "Benzodiazepine alkaloids",
    "Benzophenones",
    "Benzoquinones",
    "Bergamotane sesquiterpenoids",
    "Betaestacin-type sesterterpenoids",
    "Betalain alkaloids",
    "Beyerane diterpenoids",
    "Biaryl type diarylheptanoids",
    "Bicyclic guanidine alkaloids",
    "Bicyclogermacrane sesquiterpenoids",
    "Bicyclohumulane sesquiterpenoids",
    "Bisabolane sesquiterpenoids",
    "Bisnaphthalenes",
    "Bleomycins",
    "Boromycins",
    "Botryane sesquiterpenoids",
    "Bourbonane sesquiterpenoids",
    "Branched fatty acids",
    "Brasilane sesquiterpenoids",
    "Breviane diterpenoids",
    "Briarane diterpenoids",
    "Bryostatins",
    "Bufadienolides",
    "CDP-Glycerols",
    "Cadinane sesquiterpenoids",
    "Camphane monoterpenoids",
    "Campherenane sesquiterpenoids",
    "Cannabinoids",
    "Capnellane sesquiterpenoids",
    "Capsaicins and Capsaicinoids",
    "Carabrane sesquiterpenoids",
    "Carane monoterpenoids",
    "Carbapenems",
    "Carbazole alkaloids",
    "Carbocyclic fatty acids",
    "Carboline alkaloids",
    "Cardenolides",
    "Carotenoids (C40, \u03a7-\u03a7)",
    "Carotenoids (C40, \u03a7-\u03a8)",
    "Carotenoids (C40, \u03a8-\u03a8)",
    "Carotenoids (C40, \u03b2-\u03a7)",
    "Carotenoids (C40, \u03b2-\u03a8)",
    "Carotenoids (C40, \u03b2-\u03b2)",
    "Carotenoids (C40, \u03b2-\u03b3)",
    "Carotenoids (C40, \u03b2-\u03b5)",
    "Carotenoids (C40, \u03b2-\u03ba)",
    "Carotenoids (C40, \u03b2-\u03c0)",
    "Carotenoids (C40, \u03b3-\u03a8)",
    "Carotenoids (C40, \u03b3-\u03b5)",
    "Carotenoids (C40, \u03b5-\u03a8)",
    "Carotenoids (C40, \u03b5-\u03b5)",
    "Carotenoids (C40, \u03ba-\u03a7)",
    "Carotenoids (C40, \u03ba-\u03ba)",
    "Carotenoids (C40, \u03c0-\u03a7)",
    "Carotenoids (C40, \u03c0-\u03a8)",
    "Carotenoids (C40, \u03c0-\u03c0)",
    "Carotenoids (C45, \u03a8-\u03a8)",
    "Carotenoids (C45, \u03b2-\u03a8)",
    "Carotenoids (C45, \u03b5-\u03a8)",
    "Carotenoids (C50, \u03a8-\u03a8)",
    "Carotenoids (C50, \u03b2-\u03a8)",
    "Carotenoids (C50, \u03b2-\u03b2)",
    "Carotenoids (C50, \u03b3-\u03b3)",
    "Carotenoids (C50, \u03b5-\u03b5)",
    "Caryolane sesquiterpenoids",
    "Caryophyllane sesquiterpenoids",
    "Casbane diterpenoids",
    "Cassane diterpenoids",
    "Catechols with side chains",
    "Cedrane and Isocedrane sesquiterpenoids",
    "Cembrane diterpenoids",
    "Cephalosporins",
    "Cephalotaxus alkaloids",
    "Cephamycins",
    "Ceramides",
    "Cericerane sesterterpenoids",
    "Chalcones",
    "Chamigrane sesquiterpenoids",
    "Cheilanthane sesterterpenoids",
    "Chiloscyphane sesquiterpenoids",
    "Cholane steroids",
    "Cholestane steroids",
    "Chromones",
    "Cinnamic acid amides",
    "Cinnamic acids and derivatives",
    "Cinnamoyl phenols",
    "Clavams",
    "Clavulones",
    "Cleistanthane diterpenoids",
    "Clovane sesquiterpenoids",
    "Colensane and Clerodane diterpenoids",
    "Coloratane sesquiterpenoids",
    "Copaane sesquiterpenoids",
    "Copacamphane sesquiterpenoids",
    "Corynanthe type",
    "Coumarinolignans",
    "Coumaronochromones",
    "Coumestan",
    "Cryptophycins",
    "Cubebane sesquiterpenoids",
    "Cucurbitane triterpenoids",
    "Cuparane sesquiterpenoids",
    "Cyano esters",
    "Cyanogenic glycosides",
    "Cyathane diterpenoids",
    "Cyclic peptides",
    "Cyclitols",
    "Cycloabietane diterpenoids",
    "Cycloamphilectane diterpenoids",
    "Cycloapotirucallane triterpenoids",
    "Cycloartane triterpenoids",
    "Cyclobisabolane sesquiterpenoids",
    "Cycloeudesmane sesquiterpenoids",
    "Cyclofarnesane sesquiterpenoids",
    "Cyclogermacrane sesquiterpenoids",
    "Cyclolaurane sesquiterpenoids",
    "Cyclonerane sesquiterpenoids",
    "Cyclophytane diterpenoids",
    "Cyclopiane diterpenoids",
    "Cyclopiazonic acid-tpye tetramate alkaloids",
    "Cytochalasan alkaloids",
    "Cytosporins",
    "DKXanthenes and derivatives",
    "Dactylomelane diterpenoids",
    "Dammarane and Protostane triterpenoids",
    "Daphnane diterpenoids",
    "Daucane sesquiterpenoids",
    "Decalins with 2-pyrones",
    "Decalins with side chains",
    "Decipiane diterpenoids",
    "Depsides",
    "Depsidones",
    "Depsipeptides",
    "Devadarane diterpenoids",
    "Diacylglycerols",
    "Dialkylresorcinols",
    "Diarylether type diarylheptanoids",
    "Dibenzocyclooctadienes lignans",
    "Dibenzylbutane lignans",
    "Dibenzylbutyrolactone lignans",
    "Dicarboxylic acids",
    "Dihydroflavonols",
    "Dimeric phloroglucinols",
    "Dipeptides",
    "Disaccharides",
    "Docosa-1,2-dioxolanes",
    "Dolabellane diterpenoids",
    "Dolastane diterpenoids",
    "Dolichols",
    "Drimane sesquiterpenoids",
    "Duclauxin and derivatives",
    "Dunniane sesquiterpenoids",
    "Ecdysteroids",
    "Eicosa-1,2-dioxolanes",
    "Elemane sesquiterpenoids",
    "Elfamycins",
    "Enediynes",
    "Epothilones",
    "Epoxy fatty acids",
    "Epoxyeicosatrienoic acids",
    "Eremane diterpenoids",
    "Eremophilane sesquiterpenoids",
    "Ergostane steroids",
    "Ergot alkaloids",
    "Ericamycins",
    "Erythromycins",
    "Erythroxylane diterpenoids",
    "Estrane steroids",
    "Eudesmane sesquiterpenoids",
    "Eunicellane diterpenoids",
    "Farnesane sesquiterpenoids",
    "Fasamycins and derivatives",
    "Fatty acid estolides",
    "Fatty acyl CoAs",
    "Fatty acyl carnitines",
    "Fatty acyl glycosides of mono- and disaccharides",
    "Fatty acyl homoserine lactones",
    "Fatty alcohols",
    "Fatty aldehydes",
    "Fatty ethers",
    "Fatty nitriles",
    "Fenchane monoterpenoids",
    "Fernane and Arborinane triterpenoids",
    "Filicane triterpenoids",
    "Flavan-3-ols",
    "Flavandiols (Leucoanthocyanidins)",
    "Flavanones",
    "Flavans",
    "Flavones",
    "Flavonolignans",
    "Flavonols",
    "Flavonostilbenes",
    "Friedelane triterpenoids",
    "Fukinane sesquiterpenoids",
    "Fungal DPEs",
    "Fungal cyclic polyketides (Miscellaneous)",
    "Furanoabietane diterpenoids",
    "Furanoid lignans",
    "Furans",
    "Furocoumarins",
    "Furofuranoid lignans",
    "Furostane steroids",
    "Fusicoccane diterpenoids",
    "Fusidane triterpenoids",
    "Gallotannins",
    "Gammacerane triterpenoids",
    "Germacrane sesquiterpenoids",
    "Gersemiane diterpenoids",
    "Gibberellins",
    "Glucosinolates",
    "Glutinane triterpenoids",
    "Glycerophosphates",
    "Glycerophosphocholines",
    "Glycerophosphoethanolamines",
    "Glycerophosphoglycerols",
    "Glycerophosphoglycerophosphates",
    "Glycerophosphoglycerophosphoglycerols",
    "Glycerophosphoinositol phosphates",
    "Glycerophosphoinositolglycans",
    "Glycerophosphoinositols",
    "Glycerophosphoserines",
    "Glycosyldiacylglycerols",
    "Glycosylglycerophospholipids",
    "Glycosylmonoacylglycerols",
    "Gorgonane sesquiterpenoids",
    "Grayanotoxane diterpenoids",
    "Griseofulvins",
    "Guaiane sesquiterpenoids",
    "Guanacastane diterpenoids",
    "Gymnomitrane sesquiterpenoids",
    "Halimane diterpenoids",
    "Halogenated hydrocarbons",
    "Hamigerane sesquiterpenoids",
    "Hapalindole alkaloids",
    "Hasubanan alkaloids",
    "Hepoxilins",
    "Herbertane sesquiterpenoids",
    "Heterocyclic fatty acids",
    "Himachalane sesquiterpenoids",
    "Hirsutane sesquiterpenoids",
    "Homoerythrina alkaloids",
    "Homofarnesane sesquiterpenoids",
    "Hopane and Moretane triterpenoids",
    "Humbertiane sesquiterpenoids",
    "Humulane sesquiterpenoids",
    "Hydrocarbons",
    "Hydroperoxy fatty acids",
    "Hydroxy fatty acids",
    "Hydroxy-hydroperoxyeicosapentaenoic acids",
    "Hydroxy-hydroperoxyeicosatetraenoic acids",
    "Hydroxy-hydroperoxyeicosatrienoic acids",
    "Iboga type",
    "Icetexane diterpenoids",
    "Illudalane sesquiterpenoids",
    "Illudane sesquiterpenoids",
    "Imidazole alkaloids",
    "Indole diketopiperazine alkaloids (L-Trp, L-Ala)",
    "Indole diketopiperazine alkaloids (L-Trp, L-Pro)",
    "Indole diketopiperazine alkaloids (L-Trp, L-Trp)",
    "Indole-Diterpenoid alkaloids (Penitrems)",
    "Indolizidine alkaloids",
    "Ingenane diterpenoids",
    "Iphionane sesquiterpenoids",
    "Iridoids monoterpenoids",
    "Irregular monoterpenoids",
    "Isariotin alkaloids",
    "Ishwarane sesquiterpenoids",
    "Isoaurones",
    "Isocomane sesquiterpenoids",
    "Isocoumarins",
    "Isodaucane sesquiterpenoids",
    "Isoflavanones",
    "Isoflavones",
    "Isofurans",
    "Isoindole alkaloids",
    "Isolactarane sesquiterpenoids",
    "Isoprostanes",
    "Isoquinoline alkaloids",
    "Ivaxillarane sesquiterpenoids",
    "Jasmonic acids",
    "Jatrophane diterpenoids",
    "Jatropholane diterpenoids",
    "Kaurane and Phyllocladane diterpenoids",
    "Kavalactones and derivatives",
    "Kempane diterpenoids",
    "Labdane diterpenoids",
    "Lactam bearing macrolide lactones",
    "Lactarane sesquiterpenoids",
    "Lactones",
    "Ladder polyethers",
    "Lanostane, Tirucallane and Euphane triterpenoids",
    "Lathyrane diterpenoids",
    "Laurane sesquiterpenoids",
    "Leukotrienes",
    "Levuglandins",
    "Limonoids",
    "Linear diarylheptanoids",
    "Linear peptides",
    "Linear polyenes",
    "Linear sesterterpenoids",
    "Linear tetronates",
    "Lipopeptides",
    "Lipoxins",
    "Lippifoliane sesquiterpenoids",
    "Lobane diterpenoids",
    "Long-Chain Bicyclic Phosphotriester",
    "Longibornane sesquiterpenoids",
    "Longifolane sesquiterpenoids",
    "Longipinane sesquiterpenoids",
    "Luminacins and derivatives",
    "Lupane triterpenoids",
    "Macrocyclic tetramic acids",
    "Macrolide lactams",
    "Macrolide lactones",
    "Macrotetrolides",
    "Malabaricane triterpenoids",
    "Mangicol-type sesterterpenoids",
    "Marasmane sesquiterpenoids",
    "Maresins",
    "Marine-bacterial DPEs",
    "Megastigmanes",
    "Melithiazole and Myxothiazole derivatives",
    "Menthane monoterpenoids",
    "Merohemiterpenoids",
    "Meromonoterpenoids",
    "Merosesquiterpenoids",
    "Meroterpenoids with 5- or 6-membered ring",
    "Meroterpenoids with bridged ring",
    "Methoxy fatty acids",
    "Methyl xanthones",
    "Microcolins and mirabimids",
    "Microcystins",
    "Microginins",
    "Minor lignans",
    "Miscellaneous alkaloids",
    "Miscellaneous apocarotenoids",
    "Miscellaneous meroterpenoids",
    "Miscellaneous polyketides",
    "Mitomycins",
    "Monacolins and Monacolin derivatives",
    "Monoacylglycerols",
    "Monoalkylresorcinols",
    "Monocarbocyclic sesterterpenoids",
    "Monocyclic guanidine alkaloids",
    "Monocyclic monoterpenoids",
    "Monocyclic \u03b2-lactams",
    "Monomeric stilbenes",
    "Monosaccharides",
    "Morphinan alkaloids",
    "Mulinane diterpenoids",
    "Multiflorane triterpenoids",
    "Mycolic acids",
    "Mycosporine and Mycosporine-like amino acids",
    "Myrsinane diterpenoids",
    "N-acyl amines",
    "N-acyl ethanolamines (endocannabinoids)",
    "Nagilactone diterpenoids",
    "Naphthalenes and derivatives",
    "Naphthalenones",
    "Naphthoquinones",
    "Nardosinane sesquiterpenoids",
    "Neoflavonoids",
    "Neohopane triterpenoids",
    "Neolignans",
    "Neurofurans",
    "Neuroprostanes",
    "Neutral glycosphingolipids",
    "Nitro fatty acids",
    "Nonadrides",
    "Norcembrane diterpenoids",
    "Noreremophilane sesquiterpenoids",
    "Noreudesmane sesquiterpenoids",
    "Norkaurane diterpenoids",
    "Norlabdane diterpenoids",
    "Norpimarane and Norisopimarane diterpenoids",
    "Norsesterterpenoids",
    "Oblogolides",
    "Obtusane diterpenoids",
    "Oleanane triterpenoids",
    "Oligomeric phloroglucinols (phlorotannins)",
    "Oligomeric stibenes",
    "Oligomycins",
    "Onocerane triterpenoids",
    "Open-chain polyketides",
    "Open-chained neoflavonoids",
    "Ophiobolane sesterterpenoids",
    "Oplopane sesquiterpenoids",
    "Oppositane sesquiterpenoids",
    "Orthosomycins",
    "Other Docosanoids",
    "Other Eicosanoids",
    "Other Octadecanoids",
    "Other indole diketopiperazine alkaloids",
    "Other polyketide meroterpenoids",
    "Oxa-Bridged Macrolides",
    "Oxasqualenoids",
    "Oxazole alkaloids",
    "Oxidized glycerophospholipids",
    "Oxo fatty acids",
    "Oxygenated hydrocarbons",
    "Pachydictyane diterpenoids",
    "Pachysanane triterpenoids",
    "Pacifigorgiane sesquiterpenoids",
    "Panasinsane sesquiterpenoids",
    "Paraconic acids and derivatives",
    "Paraliane diterpenoids",
    "Parguerane diterpenoids",
    "Patchoulane sesquiterpenoids",
    "Paulomycins and derivatives",
    "Penicillins",
    "Pentacyclic guanidine alkaloids",
    "Pentalenane sesquiterpenoids",
    "Pepluane diterpenoids",
    "Peptaibols",
    "Perforane sesquiterpenoids",
    "Phenalens",
    "Phenanthrenes",
    "Phenazine alkaloids",
    "Phenethylisoquinoline alkaloids",
    "Phenoxazine alkaloids",
    "Phenylalanine-derived alkaloids",
    "Phenylethanoids",
    "Phenylethylamines",
    "Phloroglucinol-terpene hybrids",
    "Phoslactomycins or Phosphazomycins",
    "Phosphosphingolipids",
    "Phthalide derivatives",
    "Phytane diterpenoids",
    "Phytofurans",
    "Phytoprostanes",
    "Picrotoxane sesquiterpenoids",
    "Pimarane and Isopimarane diterpenoids",
    "Pimprinine alkaloids",
    "Pinane monoterpenoids",
    "Pinguisane sesquiterpenoids",
    "Piperidine alkaloids",
    "Plant xanthones",
    "Platensimycin and Platencins",
    "Podocarpane diterpenoids",
    "Polyamines",
    "Polyene macrolides",
    "Polyesters",
    "Polyether ionophores",
    "Polypodane triterpenoids",
    "Polyprenol derivatives",
    "Polyprenylated cyclic polyketides (Hop meroterpenoids)",
    "Polysaccharides",
    "Pradimicins",
    "Pregnane steroids",
    "Premyrsinane diterpenoids",
    "Prenyl quinone meroterpenoids",
    "Prenylated,geranylated phloroglucinols",
    "Prenylbisabolane diterpenoids",
    "Prenyleudesmane diterpenoids",
    "Presilphiperfolane and Probotryane sesquiterpenoids",
    "Prezizaane sesquiterpenoids",
    "Primary amides",
    "Proanthocyanins",
    "Prodigiosins",
    "Prostaglandins",
    "Protoberberine alkaloids",
    "Protoilludane sesquiterpenoids",
    "Protopine alkaloids",
    "Pseudoguaiane sesquiterpenoids",
    "Pseudopterane diterpenoids",
    "Pterocarpan",
    "Pulvinones",
    "Purine alkaloids",
    "Purine nucleos(t)ides",
    "Pyranocoumarins",
    "Pyrazine and Piperazine alkaloids",
    "Pyridine alkaloids",
    "Pyrimidine nucleos(t)ides",
    "Pyrrocidine tetramate alkaloids",
    "Pyrrole alkaloids",
    "Pyrrolidine alkaloids",
    "Pyrrolizidine alkaloids",
    "Pyrroloindole alkaloids",
    "Pyrroloquinoline alkaloids",
    "Quadrane sesquiterpenoids",
    "Quassinoids",
    "Quinazoline alkaloids",
    "Quinoline alkaloids",
    "Quinolizidine alkaloids",
    "Resin glycosides",
    "Resolvin Ds",
    "Resolvin Es",
    "Rhamnofolane diterpenoids",
    "Rhamnolipids",
    "Rhizoxins",
    "RiPPs-Amatoxins and Phallotoxins",
    "RiPPs-Bottromycins",
    "RiPPs-Cyanobactins",
    "RiPPs-Lanthipeptides",
    "RiPPs-Lasso peptides",
    "RiPPs-Microcins",
    "RiPPs-Thiopeptides",
    "Rotenoids",
    "Rotundane sesquiterpenoids",
    "Sacculatane diterpenoids",
    "Salinosporamides",
    "Santalane sesquiterpenoids",
    "Saponaceolide triterpenoids",
    "Sativane sesquiterpenoids",
    "Saxitoxins",
    "Scalarane sesterterpenoids",
    "Secoabietane diterpenoids",
    "Secochamigrane sesquiterpenoids",
    "Secoeudesmane sesquiterpenoids",
    "Secogermacrane sesquiterpenoids",
    "Secoiridoid monoterpenoids",
    "Secokaurane diterpenoids",
    "Secolabdane diterpenoids",
    "Segetane diterpenoids",
    "Selaginellins",
    "Serratane triterpenoids",
    "Serrulatane and Biflorane diterpenoids",
    "Shikimic acids and derivatives",
    "Shionane triterpenoids",
    "Silphinane sesquiterpenoids",
    "Silphiperfolane sesquiterpenoids",
    "Simple amide alkaloids",
    "Simple aromatic polyketides",
    "Simple coumarins",
    "Simple cyclic polyketides",
    "Simple diketopiperazine alkaloids",
    "Simple indole alkaloids",
    "Simple oxindole alkaloids",
    "Simple phenolic acids",
    "Simple tetramate alkaloids",
    "Sinularane sesquiterpenoids",
    "Sophorolipids",
    "Sorbicilinoids",
    "Sphaerane diterpenoids",
    "Sphaeroane diterpenoids",
    "Sphenolobane diterpenoids",
    "Sphingoid bases",
    "Spiroaxane sesquiterpenoids",
    "Spirodioxynaphthalenes",
    "Spirostane steroids",
    "Spirotetronate macrolides",
    "Spirovetivane sesquiterpenoids",
    "Spongiane diterpenoids",
    "Spriromeroterpenoids",
    "Stemona alkaloids",
    "Steroidal alkaloids",
    "Sterpurane sesquiterpenoids",
    "Stictane triterpenoids",
    "Stigmastane steroids",
    "Stilbenolignans",
    "Streptogramins",
    "Streptothricins and derivatives",
    "Strobilurins and derivatives",
    "Strychnos type",
    "Tantazoles and mirabazoles",
    "Taraxerane triterpenoids",
    "Taxane diterpenoids",
    "Terpenoid alkaloids",
    "Terpenoid tetrahydroisoquinoline alkaloids",
    "Tetracyclic diterpenoids",
    "Tetracyclines",
    "Tetrahydroisoquinoline alkaloids",
    "Tetraketide meroterpenoids",
    "Tetrodotoxins",
    "Thapsane sesquiterpenoids",
    "Thia fatty acids",
    "Thiazole alkaloids",
    "Thiodiketopiperazine alkaloids",
    "Thromboxanes",
    "Thujane monoterpenoids",
    "Thujopsane sesquiterpenoids",
    "Tigliane diterpenoids",
    "Totarane diterpenoids",
    "Trachylobane diterpenoids",
    "Tremulane sesquiterpenoids",
    "Triacylglycerols",
    "Trichothecane sesquiterpenoids",
    "Tricyclic guanidine alkaloids",
    "Triketide meroterpenoids",
    "Trinervitane diterpenoids",
    "Tripeptides",
    "Tropane alkaloids",
    "Tropolones and derivatives (PKS)",
    "Tropolones and derivatives (Shikimate)",
    "Tylosins",
    "Unsaturated fatty acids",
    "Ursane and Taraxastane triterpenoids",
    "Usnic acid and derivatives",
    "Valerane sesquiterpenoids",
    "Valerenane sesquiterpenoids",
    "Valparane diterpenoids",
    "Vancomycins and Teicoplanins",
    "Verrucosane diterpenoids",
    "Verticillane diterpenoids",
    "Villanovane diterpenoids",
    "Viscidane diterpenoids",
    "Vitamin D2 and derivatives",
    "Vitamin D3 and derivatives",
    "Wax diesters",
    "Wax monoesters",
    "Xeniaphyllane diterpenoids",
    "Xenicane diterpenoids",
    "Yohimbine-like alkaloids",
    "Zearalenones",
    "Zizaane sesquiterpenoids",
    "m-Terphenyls",
    "p-Terphenyls",
    "pteridine alkaloids",
]

NUMBER_OF_NPC_PATHWAYS: int = len(NPC_PATHWAYS)
NUMBER_OF_NPC_SUPERCLASSES: int = len(NPC_SUPERCLASSES)
NUMBER_OF_NPC_CLASSES: int = len(NPC_CLASSES)
MAXIMAL_TAXONOMICAL_SCORE: float = 8.0



@dataclass
class Lotus:
    """Data class representing the key information of a LOTUS entry."""

    structure_wikidata: str
    structure_inchikey: str
    structure_inchi: str
    structure_smiles: str
    structure_molecular_formula: str
    structure_exact_mass: float
    structure_xlogp: float
    structure_smiles_2d: str
    structure_cid: int
    structure_name_iupac: str
    structure_name_traditional: str
    structure_stereocenters_total: int
    structure_stereocenters_unspecified: int
    structure_taxonomy_npclassifier_01pathway: Optional[str]
    structure_taxonomy_npclassifier_02superclass: Optional[str]
    structure_taxonomy_npclassifier_03class: Optional[str]
    structure_taxonomy_classyfire_chemontid: str
    structure_taxonomy_classyfire_01kingdom: str
    structure_taxonomy_classyfire_02superclass: str
    structure_taxonomy_classyfire_03class: str
    structure_taxonomy_classyfire_04directparent: str
    organism_wikidata: str
    organism_name: str
    organism_taxonomy_gbifid: int
    organism_taxonomy_ncbiid: int
    organism_taxonomy_ottid: int
    domain: str
    kingdom: str
    phylum: str
    klass: str
    order: str
    family: str
    tribe: str
    genus: str
    species: str
    varietas: str
    reference_wikidata: str
    reference_doi: str
    manual_validation: bool

    @staticmethod
    def setup_lotus_columns(columns: List[str]):
        """Set up the columns of the LOTUS DataFrame."""

        Lotus._columns = {column: i for i, column in enumerate(columns)}

    @staticmethod
    def from_pandas_series(series: List[Any]) -> "Lotus":
        """Create a Lotus object from a pandas Series."""

        # We normalize the NaN values to None
        series = [None if pd.isna(value) else value for value in series]

        return Lotus(
            structure_wikidata=series[Lotus._columns["structure_wikidata"]],
            structure_inchikey=series[Lotus._columns["structure_inchikey"]],
            structure_inchi=series[Lotus._columns["structure_inchi"]],
            structure_smiles=series[Lotus._columns["structure_smiles"]],
            structure_molecular_formula=series[
                Lotus._columns["structure_molecular_formula"]
            ],
            structure_exact_mass=series[Lotus._columns["structure_exact_mass"]],
            structure_xlogp=series[Lotus._columns["structure_xlogp"]],
            structure_smiles_2d=series[Lotus._columns["structure_smiles_2D"]],
            structure_cid=series[Lotus._columns["structure_cid"]],
            structure_name_iupac=series[Lotus._columns["structure_nameIupac"]],
            structure_name_traditional=series[
                Lotus._columns["structure_nameTraditional"]
            ],
            structure_stereocenters_total=series[
                Lotus._columns["structure_stereocenters_total"]
            ],
            structure_stereocenters_unspecified=series[
                Lotus._columns["structure_stereocenters_unspecified"]
            ],
            structure_taxonomy_npclassifier_01pathway=series[
                Lotus._columns["structure_taxonomy_npclassifier_01pathway"]
            ],
            structure_taxonomy_npclassifier_02superclass=series[
                Lotus._columns["structure_taxonomy_npclassifier_02superclass"]
            ],
            structure_taxonomy_npclassifier_03class=series[
                Lotus._columns["structure_taxonomy_npclassifier_03class"]
            ],
            structure_taxonomy_classyfire_chemontid=series[
                Lotus._columns["structure_taxonomy_classyfire_chemontid"]
            ],
            structure_taxonomy_classyfire_01kingdom=series[
                Lotus._columns["structure_taxonomy_classyfire_01kingdom"]
            ],
            structure_taxonomy_classyfire_02superclass=series[
                Lotus._columns["structure_taxonomy_classyfire_02superclass"]
            ],
            structure_taxonomy_classyfire_03class=series[
                Lotus._columns["structure_taxonomy_classyfire_03class"]
            ],
            structure_taxonomy_classyfire_04directparent=series[
                Lotus._columns["structure_taxonomy_classyfire_04directparent"]
            ],
            organism_wikidata=series[Lotus._columns["organism_wikidata"]],
            organism_name=series[Lotus._columns["organism_name"]],
            organism_taxonomy_gbifid=series[Lotus._columns["organism_taxonomy_gbifid"]],
            organism_taxonomy_ncbiid=series[Lotus._columns["organism_taxonomy_ncbiid"]],
            organism_taxonomy_ottid=series[Lotus._columns["organism_taxonomy_ottid"]],
            domain=series[Lotus._columns["organism_taxonomy_01domain"]],
            kingdom=series[Lotus._columns["organism_taxonomy_02kingdom"]],
            phylum=series[Lotus._columns["organism_taxonomy_03phylum"]],
            klass=series[Lotus._columns["organism_taxonomy_04class"]],
            order=series[Lotus._columns["organism_taxonomy_05order"]],
            family=series[Lotus._columns["organism_taxonomy_06family"]],
            tribe=series[Lotus._columns["organism_taxonomy_07tribe"]],
            genus=series[Lotus._columns["organism_taxonomy_08genus"]],
            species=series[Lotus._columns["organism_taxonomy_09species"]],
            varietas=series[Lotus._columns["organism_taxonomy_10varietas"]],
            reference_wikidata=series[Lotus._columns["reference_wikidata"]],
            reference_doi=series[Lotus._columns["reference_doi"]],
            manual_validation=series[Lotus._columns["manual_validation"]],
        )

    def __hash__(self) -> int:
        """Return the hash of the InChIKey."""
        return hash((
            self.structure_inchikey,
            self.organism_taxonomy_ottid
        ))

    @property
    def short_inchikey(self) -> str:
        """Return the first 14 characters of the InChIKey."""
        return self.structure_inchikey[:14]

    def iter_npc_pathways(self) -> Iterator[int]:
        """Iterate over the NPC pathways."""
        for i, npc_pathway in enumerate(NPC_PATHWAYS):
            if npc_pathway == self.structure_taxonomy_npclassifier_01pathway:
                yield i

    def iter_npc_superclasses(self) -> Iterator[int]:
        """Iterate over the NPC superclasses."""
        for i, npc_superclass in enumerate(NPC_SUPERCLASSES):
            if npc_superclass == self.structure_taxonomy_npclassifier_02superclass:
                yield i

    def iter_npc_classes(self) -> Iterator[int]:
        """Iterate over the NPC classes."""
        for i, npc_class in enumerate(NPC_CLASSES):
            if npc_class == self.structure_taxonomy_npclassifier_03class:
                yield i

    @property
    def one_hot_encoded_npc_pathway(self) -> np.ndarray:
        """Return the NPC pathway number."""
        if self.structure_taxonomy_npclassifier_01pathway is None:
            return np.zeros((NUMBER_OF_NPC_PATHWAYS,))
        
        one_hot_encoded = np.zeros((NUMBER_OF_NPC_PATHWAYS,))
        one_hot_encoded[NPC_PATHWAYS.index(self.structure_taxonomy_npclassifier_01pathway)] = 1
        return one_hot_encoded

    @property
    def one_hot_encoded_npc_superclass(self) -> np.ndarray:
        """Return the NPC superclass number."""
        if self.structure_taxonomy_npclassifier_02superclass is None:
            return np.zeros((NUMBER_OF_NPC_SUPERCLASSES,))
            
        one_hot_encoded = np.zeros((NUMBER_OF_NPC_SUPERCLASSES,))
        one_hot_encoded[NPC_SUPERCLASSES.index(self.structure_taxonomy_npclassifier_02superclass)] = 1
        return one_hot_encoded

    @property
    def one_hot_encoded_npc_class(self) -> np.ndarray:
        """Return the NPC class number."""
        if self.structure_taxonomy_npclassifier_03class is None:
            return np.zeros((NUMBER_OF_NPC_CLASSES,))

        one_hot_encoded = np.zeros((NUMBER_OF_NPC_CLASSES,))
        one_hot_encoded[NPC_CLASSES.index(self.structure_taxonomy_npclassifier_03class)] = 1
        return one_hot_encoded

    def taxonomical_similarity_with_otl_match(self, match: Match) -> float:
        """Calculate the taxonomical similarity with an OTL match.

        Implementative details
        ----------------------
        The taxonomical similarity is calculated as the number of shared taxonomic ranks
        between the LOTUS organism and the OTL match organism. The ranks are ordered from
        domain to species, and the similarity is calculated as the number of ranks that
        are the same between the two organisms.
        """
        if self.species == match.species:
            return 8.0

        if self.genus == match.genus:
            return 7.0

        if self.family == match.family:
            return 6.0

        if self.order == match.order:
            return 5.0

        if self.klass == match.klass:
            return 4.0

        if self.phylum == match.phylum:
            return 3.0

        if self.kingdom == match.kingdom:
            return 2.0

        if self.domain == match.domain:
            return 1.0

        return 0.0

    def normalized_taxonomical_similarity_with_otl_match(self, match: Match) -> float:
        """Calculate the normalized taxonomical similarity with an OTL match.

        Implementative details
        ----------------------
        The normalized taxonomical similarity is calculated as the taxonomical similarity
        divided by the maximum possible similarity (8).
        """
        match_score = self.taxonomical_similarity_with_otl_match(match)
        assert (
            match_score <= MAXIMAL_TAXONOMICAL_SCORE
        ), f"Expected a maximal score of {MAXIMAL_TAXONOMICAL_SCORE}, got {match_score}."
        return match_score / MAXIMAL_TAXONOMICAL_SCORE
