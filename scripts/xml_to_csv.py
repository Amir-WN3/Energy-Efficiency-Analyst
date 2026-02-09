import pandas as pd
import xml.etree.ElementTree as ET
import os
from pathlib import Path

def parse_ape_xml(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    features = {}

    # Feature extraction functions, 53 features total
    features.update(extract_dati_attestato(root))
    features.update(extract_dati_generali(root))
    features.update(extract_prestazione_globale(root))
    features.update(extract_prestazione_impianti(root))
    features.update(extract_raccomandazioni(root))
    features.update(extract_dati_fabbricato(root))
    features.update(extract_dati_impianti(root))
    features.update(extract_dati_extra(root))
    features.update(extract_dati_calcolo(root))
    
    
    # Metadata
    features['xml_filename'] = Path(xml_file_path).name
    features['file_timestamp'] = os.path.getmtime(xml_file_path)

    return features



def extract_dati_attestato(root):   # Potentially unnecessary # 1
    features = {}

    try:
        dati = root.find('.//datiAttestato')
        if dati is not None:
            features['scadenza'] = dati.findtext('dataScadenza', '')

    except:
        pass

    return features

def extract_dati_generali(root): 
    features = {}

    try:
        dati = root.find('.//datiGenerali')
        if dati is not None:
            # Building usage
            features['uso_edificio'] = dati.findtext('destinazioneUso', '0')
            features['oggetto_attestato'] = dati.findtext('oggettoAttestato', '1')
            features['num_unita'] = int(dati.findtext('numeroUnitaImmobiliari', '1'))

            # Building/Location info
            features['zona_climatica'] = dati.findtext('.//datiIdentificativi/zonaClimatica', '')
            features['anno_costruzione'] = int(dati.findtext('.//datiIdentificativi/annoCostruzione', ''))
            features['superficie_riscaldata'] = float(dati.findtext('.//datiIdentificativi/superficieUtileRiscaldata', '0'))
            features['superficie_raffrescata'] = float(dati.findtext('.//datiIdentificativi/superficieUtileRaffrescata', '0'))
            features['vol_lordo_riscaldato'] = float(dati.findtext('.//datiIdentificativi/volumeLordoRiscaldato', '0'))
            features['vol_lordo_raffrescato'] = float(dati.findtext('.//datiIdentificativi/volumeLordoRaffrescato', '0'))

            # Energy services
            servizi = dati.find('.//serviziEnergeticiPresenti')
            
            if servizi:
                services = ['climatizzazioneInvernale', 'climatizzazioneEstiva', 'produzioneAcquaCaldaSanitaria', 'ventilazioneMeccanica']
                for service in services:
                    features[service] = servizi.findtext(service, '0')
            
    except:
        pass

    return features        


def extract_prestazione_globale(root): 
    features = {}

    try:
        prest = root.find('.//prestazioneGlobale')
        if prest is not None:

            # <inverno>2</inverno>
            # <estate>1</estate>  unsure

            features['classe_energetica'] = prest.findtext('.//classificazione/classeEnergetica', '')
            features['epglnren'] = float(prest.findtext('.//classificazione/epglnren', '0'))
         #  features['inverno_rating']
         #  features['estate_rating']

            # Reference standards
            nuovi = prest.find('.//classificazioneNuovi')
            if nuovi:
                features['classe_nuovi'] = nuovi.findtext('classeEnergetica', '')
                features['ep_nuovi'] = float(nuovi.findtext('epglnren', '0'))

            esistenti = prest.find('.//classificazioneEsistenti')
            if esistenti:
                features['classe_esistenti'] = esistenti.findtext('classeEnergetica', '')
                features['ep_esistenti'] = float(esistenti.findtext('epglnren', '0'))
    except:
        pass
    
    return features


def extract_prestazione_impianti(root): 
    features = {}

    try:
        imp = root.find('.//prestazioneImpianti')
        if imp is not None:

            # Electricity
            ele = imp.find('.//energiaElettricaRete')
            if ele:
                features['elettricita_kwh'] = float(ele.findtext('consumoAnnuo', '0'))

            # Gas
            gas = imp.find('.//gasNaturale')
            if gas:
                features['gas_smc'] = float(gas.findtext('consumoAnnuo', '0'))

            # Performance
            features['epglren_impianti'] = float(imp.findtext('epglren', '0')) # Renewable energy
            features['epglnren_impianti'] = float(imp.findtext('epglnren', '0')) # Non Renewable energy
            features['co2_emissioni'] = float(imp.findtext('emissioniCO2', '0'))
    except:
        pass

    return features

def extract_raccomandazioni(root): 
    features = {}
    try:
        racc = root.find('.//raccomandazioni')

        if racc is not None:
            # Recommended intervention
            intervento = racc.find('interventoRaccomandato')
            if intervento:
                features['intervento_consigliato'] = intervento.findtext('tipoInterventoRaccomandato', '')
                features['ROI_anni'] = float(intervento.findtext('tempoRitornoInvestimento', '0'))
                features['ristrutturazione_importante'] = intervento.findtext('ristrutturazioneImportante', '0')

                raggiungibile = intervento.find('.//classificazioneRaggiungibile')
                if raggiungibile:
                    features['classe_raggiungibile'] = raggiungibile.findtext('classeEnergetica', '')
                    features['ep_raggiungibile'] = float(raggiungibile.findtext('epglnren', '0'))
    except:
        pass
    return features

def extract_dati_fabbricato(root): 
    features = {}
    try:
        fabb = root.find('.//datiFabbricato')
        if fabb is not None:
            features['volume_riscaldato'] = float(fabb.findtext('volumeRiscaldato', '0'))
            features['superficie_disperdente'] = float(fabb.findtext('superficieDisperdente', '0'))
            features['rapporto_sv'] = float(fabb.findtext('rapportoSV', '0'))

            features['ephnd'] = float(fabb.findtext('ephnd', '0')) # Heating demand
            features['yie'] = float(fabb.findtext('yie', '0')) # Summer index

            features['rapporto_solare'] = float(fabb.findtext('rapportoAsolAsupUtile', '0'))

    except:
        pass
    return features

def extract_dati_impianti(root): 
    features = {}
    try:
        risc = root.find('.//datiImpianti')
        if risc:
            impianto = risc.find('.//climatizzazioneInvernale/impianto')
            if impianto:
                features['tipo_riscaldamento'] = impianto.findtext('descrizioneImpianto', '')
                features['anno_installazione_risc'] = int(impianto.findtext('annoInstallazione', '0'))
                features['potenza_nominale_risc'] = float(impianto.findtext('potenzaNominale', '0'))

            features['efficienza_risc'] = float(risc.findtext('efficienza', '0'))

        acs = root.find('.//produzioneACS')
        if acs:
            features['efficienza_acs'] = float(acs.findtext('efficienza', '0'))
    except:
        pass
    return features

def extract_dati_extra(root): 
    features = {}
    try:
        extra = root.find('.//datiExtra')
        if extra:
            features['gradi_giorno'] = int(extra.findtext('gradiGiorno', '0'))
            
            features['tipologia_edilizia'] = extra.findtext('tipologiaEdilizia', '0')
            features['tipologia_costruttiva'] = extra.findtext('tipologiaCostruttiva', '0')
            
            
            features['ephnd_limit'] = float(extra.findtext('ephndLim', '0'))
            features['ep_standard'] = float(extra.findtext('EPglnrenRifStandard', '0'))
    except:
        pass
    return features

def extract_dati_calcolo(root): 
    features = {}
    try:
        calc = root.find('.//datiCalcolo')
        if calc:
            sintetici = calc.find('.//altriDatiSintetici')
            if sintetici:
                features['u_opaco_medio'] = float(sintetici.findtext('superficieOpacaTrasmittanzaMedia', '0'))
                features['superficie_opaca_tot'] = float(sintetici.findtext('superficieOpacaTotale', '0'))
                features['u_vetrato_medio'] = float(sintetici.findtext('superficieVetrataTrasmittanzaMedia'))
                features['superficie_vetrata_tot'] = float(sintetici.findtext('superficieVetrataTotale', '0'))
                
            ventilazione = calc.find('.//ventilazione/ricambiAria')
            if ventilazione is not None:
                features['ricambi_aria_ora'] = float(ventilazione.text)
    except:
        pass
    return features


def process_all_xml_files(xml_file_path, output_csv = 'ape_dataset_marche.csv'):

    all_features = []

    xml_files = list(Path(xml_file_path).glob('*.xml'))

    print(f"Found {len(xml_files)} XML files to process")

    for i, xml_file in enumerate(xml_files):
        try:
            features = parse_ape_xml(xml_file)
            
            all_features.append(features)
            
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(xml_files)} files")
                
        except Exception as e:
            print(f"Error processing {xml_file.name}: {e}")
            
            continue
    
    df = pd.DataFrame(all_features)
    
    df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"\n Saved {len(df)} records to {output_csv}")
    print(f"\nFeatures extracted: {len(df.columns)}")
    
    return df



if __name__ == "__main__":
    
    XML_FOLDER = 'C:\\Users\\AmirN\\Desktop\\APEdata\\APExml'
    OUTPUT_CSV = "C:\\Users\\AmirN\Desktop\\projects\\Energy-Efficiency-Analyst\\data\\raw\\ape_marche_dataset.csv"
    
    print('Converting...')
    
    df = process_all_xml_files(XML_FOLDER, OUTPUT_CSV)
    
    print(f"Conversion complete. Check {OUTPUT_CSV}")