import pandas as pd


def get_token_id(symbol, instrument, exchange):
    df = pd.read_json('http://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json')
    df = df[df['Symbol'] == symbol & df['instrumenttype'] == instrument & df['exch_seg'] == exchange]
    return df


def create_data():
    df = pd.read_json('http://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json')
    unique_exchange = df['exch_seg'].unique()
    unique_instrument = df['instrumenttype'].unique()
    return unique_instrument, unique_exchange


if __name__ == '__main__':
    create_data()
