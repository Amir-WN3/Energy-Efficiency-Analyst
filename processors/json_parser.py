import json
from pandas import json_normalize
import pandas as pd

def flatten_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    if isinstance(data, list):
        df = json_normalize(data)
    else:
        df = json_normalize([data])
        
    
    def extract_servizi(row):
        servizi = row.get('servizi') or []
        result = {}
        
        for i, servizio in enumerate(servizi):
            if not isinstance(servizio, dict):
                continue
            servizio_type = servizio.get('servizio_energetico', 'placeholder')
            prefix = f"servizio_{servizio_type}"
            
            result[f'{prefix}_pnominale'] = servizio.get('potenza_nominale', 0)
            result[f'{prefix}_epren'] = servizio.get('epren', 0)
            result[f'{prefix}_epnren'] = servizio.get('epnren', 0)
            result[f'{prefix}_efficienza'] = servizio.get('efficienza_media_stagionale', 0)
            imp_sim = servizio.get('impianto_simulato') or ''
            result[f'{prefix}_simulato'] = 1 if 'SIMULATO' in imp_sim else 0
            
        return pd.Series(result)
    
    servizi_features = df.apply(extract_servizi, axis=1)
    df = df.drop('servizi', axis=1).join(servizi_features)
    
    return df
