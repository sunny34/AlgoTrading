#!python
from pprint import pprint
import logging
from kiteconnect import KiteTicker
from kiteconnect import KiteConnect
import pandas as pd
import configparser
import numpy
import math
import talib
from datetime import timedelta
import sys

# sys.path.append('/home/pramod/setup/utils')
import os
import time
from utils.settings import ScalpSettings
from utils.orderUtil import place_order
import pickle
import expiry_date
from utils import algoUtils
import requests
import datetime
from src.strategy_code_base.adhoc.telegram_connection import send_alert, send_error_alert, send_trade_alert


def load_access_code():
    access_code_file = open("../setup/ZU9940.txt", "r")
    ScalpSettings['ZU9940']['access_code'] = access_code_file.read()

    access_code_file = open("../setup/CF8372.txt", "r")
    ScalpSettings['CF8372']['access_code'] = access_code_file.read()

    access_code_file = open("../setup/IZG276.txt", "r")
    ScalpSettings['IZG276']['access_code'] = access_code_file.read()

    access_code_file = open("../setup/ZL5202.txt", "r")
    ScalpSettings['ZL5202']['access_code'] = access_code_file.read()

    # Send Telegram Message


def getUCInfo(symbol):
    info = kite.quote("NFO:" + symbol)
    print(info)
    uc = info["NFO:" + symbol]['upper_circuit_limit']
    print(uc)
    if uc > 30:
        uc = 30
    print(uc)
    return uc


def set_token():
    """
    Function to set token

    :return:
    """

    bnf = 'NSE:NIFTY BANK'
    # bnf = 'NFO:BANKNIFTY'+expiry_date.fut_expiry()+'FUT'
    print(bnf)
    bnf_ltp = kite.ltp(bnf)
    print(bnf_ltp)
    currentStrike = ScalpSettings["BNFSTRDL"]['CurrentStrk']
    strike = round(int(bnf_ltp[bnf]['last_price']), -2)

    if currentStrike != 0:
        strike = str(currentStrike)
    ce_strike = pe_strike = str(strike)
    bnk_a = "BANKNIFTY"
    # bnk_b = expiry_date.exp_date()
    bnk_b = expiry_date.final_expiry()
    straddle_optionWklyPrefix = bnk_a + bnk_b[0]
    hedge_optionWklyPrefix = bnk_a + bnk_b[1]
    if bnk_b[2]:
        ce_strike = str(strike)
        pe_strike = str(strike)
    ceContract = straddle_optionWklyPrefix + ce_strike + str("CE")
    peContract = straddle_optionWklyPrefix + pe_strike + str("PE")

    ScalpSettings["BNFSTRDL"]['ceContract'] = straddle_optionWklyPrefix + ce_strike + str("CE")
    ScalpSettings["BNFSTRDL"]['peContract'] = straddle_optionWklyPrefix + pe_strike + str("PE")

    print(ceContract, peContract)

    df = pd.DataFrame(instruments)
    symbol = df[df['exchange'].str.match('NFO')]
    ce_dict_token = symbol[symbol['tradingsymbol'] == ceContract]
    ScalpSettings["BNFSTRDL"]['ceInstruToken'] = int(ce_dict_token['instrument_token'].to_string(index=False))
    pe_dict_token = symbol[symbol['tradingsymbol'] == peContract]
    ScalpSettings["BNFSTRDL"]['peInstruToken'] = int(pe_dict_token['instrument_token'].to_string(index=False))
    print(ScalpSettings["BNFSTRDL"]['ceInstruToken'])
    print(ScalpSettings["BNFSTRDL"]['peInstruToken'])


def triggerStraddle(strategy, alreadyEntered):
    global ScalpSettings
    print("^^^^^^^^^^^^^ sleeping 10 seconds, is trade on?", alreadyEntered)

    print(straddle_entry_time)
    if (alreadyEntered == False and ScalpSettings[strategy][
        'TradeOn'] == False and datetime.datetime.now().time() > straddle_entry_time and datetime.datetime.now().time() < straddle_entry_end_time):
        if (ScalpSettings[strategy]['ceInstruToken'] == 0):
            setTokens()
        time.sleep(4)

        Threads = []
        Accounts = ScalpSettings["Accounts"]
        for account in Accounts:
            status = 'Teststrtgy'
            if (ScalpSettings[account].get(status, False)):
                Threads.append(threading.Thread(target=triggerOrders, args=(account, strategy, "ZENTRY")))

        for thread in Threads:
            thread.start()

        for thread in Threads:
            thread.join()

        ScalpSettings[strategy]['TradeOn'] = True
        sendTradeAlert("@@@ ZENBNFV3 - Entry, ALERT", strategy, "9:15")


def findEntryPrices(CEorPE):
    global ScalpSettings
    # time.sleep(5)
    print("Inside find entry - already entered? ", ScalpSettings[CEorPE]['TradeOn'],
          ScalpSettings[CEorPE]['FirstTradeOn'])
    for _ in range(50):

        try:

            rsicerecords = kite.historical_data(ScalpSettings[CEorPE]['ceInstruToken'],
                                                datetime.datetime.now() - timedelta(days=6), datetime.datetime.now(),
                                                "3minute")
            rsiperecords = kite.historical_data(ScalpSettings[CEorPE]['peInstruToken'],
                                                datetime.datetime.now() - timedelta(days=6), datetime.datetime.now(),
                                                "3minute")
            # print("ce data size", len(cerecords))
            # print("pe data size", len(cerecords))
        except Exception as e:
            logging.info("Order placement failed: {}".format(e))
            time.sleep(30)
            sendErrorAlert("ZENBNFV3 -  Failed , Retrying", "N", "N")
            continue
        # no exception, continue remainder of code
        if len(rsicerecords) == 0 or len(rsiperecords) == 0:
            time.sleep(30)
            continue
        else:
            break

    # did not break the for loop, therefore all attempts failed
    else:
        sendErrorAlert("ZENBNFV3 -  Failed Fully, ALERT", "N", "N")

    rsicedf = pd.DataFrame(rsicerecords)
    rsipedf = pd.DataFrame(rsiperecords)
    rsidf = pd.concat([rsicedf, rsipedf]).groupby('date')[['open', 'high', 'low', 'close', 'volume']].apply(sum)
    # print(" Day ", df)

    rsidf['rsi'] = talib.RSI(rsidf['close'])

    rsi = rsidf['rsi']
    volume = df['volume']
    df = df.assign(vwap=((volume * close).cumsum() / volume.cumsum()).ffill())
    vwap = df['vwap']
    close = rsidf['close']
    ceClose = rsicedf['close']
    peClose = rsipedf['close']

    rsicedf['rsi'] = talib.RSI(rsicedf['close'])
    rsipedf['rsi'] = talib.RSI(rsipedf['close'])
    rsice = rsicedf['rsi']
    rsipe = rsipedf['rsi']

    print(" Find Entry ")
    # skipping last candle as it is not reliable from zerodha
    size = close.size - 1
    rsisize = rsi.size - 1
    print(" ^^^^^^^^^^^^^^^^^^^^^^^^ RSI ^^^^^^^^^^^^^^^^^^^^^^^^^ ", rsi[rsisize - 1])
    print(" ^^^^^^^^^^^^^^^^^^^^^^^^ ceClose  ^^^^^^^^^^^^^^^^^^^^^^^^^ ", ceClose[ceClose.size - 1])
    print(" ^^^^^^^^^^^^^^^^^^^^^^^^ peClose ^^^^^^^^^^^^^^^^^^^^^^^^^ ", peClose[peClose.size - 1])
    print(" ^^^^^^^^^^^^^^^^^^^^^^^^ ceRSI  ^^^^^^^^^^^^^^^^^^^^^^^^^ ", rsice[rsice.size - 1])
    print(" ^^^^^^^^^^^^^^^^^^^^^^^^ peRSI ^^^^^^^^^^^^^^^^^^^^^^^^^ ", rsipe[rsipe.size - 1])

    if ceClose[ceClose.size - 1] > peClose[peClose.size - 1] and ScalpSettings[CEorPE]['legBroken'] == False:
        ScalpSettings[CEorPE]['brokenLeg'] = "CE"
    elif ceClose[ceClose.size - 1] < peClose[peClose.size - 1] and ScalpSettings[CEorPE]['legBroken'] == False:
        ScalpSettings[CEorPE]['brokenLeg'] = "PE"

    if ScalpSettings[CEorPE]['TradeOn'] == False:
        ScalpSettings[CEorPE]['brokenLeg'] = "CEPE"

    if datetime.datetime.now().time() > datetime.time(15, 23) and ScalpSettings[CEorPE]['TradeOn'] == True:
        print("Exiting Straddle")
        # if(ScalpSettings[CEorPE]['brokenLeg']== "CEPE" or ScalpSettings[CEorPE]['legBroken']==False):
        # ScalpSettings[CEorPE]['brokenLeg'] = "CE"
        # Threads = []
        # Accounts = ScalpSettings["Accounts"]
        # for account in Accounts:
        # status = 'Teststrtgy'
        # if (ScalpSettings[account].get(status, False)):
        # Threads.append(threading.Thread(target=exitOnTrigger, args=(account,CEorPE,"ZEXIT")))

        # for thread in Threads:
        # thread.start()

        # for thread in Threads:
        # thread.join()

        # ScalpSettings[CEorPE]['brokenLeg'] = "PE"
        # Threads = []
        # Accounts = ScalpSettings["Accounts"]
        # for account in Accounts:
        # status = 'Teststrtgy'
        # if (ScalpSettings[account].get(status, False)):
        # Threads.append(threading.Thread(target=exitOnTrigger, args=(account,CEorPE,"ZEXIT")))

        # for thread in Threads:
        # thread.start()

        # for thread in Threads:
        # thread.join()
        # os._exit(1)

        # if (ScalpSettings[CEorPE]['brokenLeg'] == "CE"):

        # ScalpSettings[CEorPE]['brokenLeg'] = "PE"
        # Threads = []
        # Accounts = ScalpSettings["Accounts"]
        # for account in Accounts:
        # status = 'Teststrtgy'
        # if (ScalpSettings[account].get(status, False)):
        # Threads.append(threading.Thread(target=exitOnTrigger, args=(account,CEorPE,"ZEXIT")))

        # for thread in Threads:
        # thread.start()

        # for thread in Threads:
        # thread.join()
        # os._exit(1)

        # if (ScalpSettings[CEorPE]['brokenLeg'] == "PE"):

        # ScalpSettings[CEorPE]['brokenLeg'] = "CE"
        # Threads = []
        # Accounts = ScalpSettings["Accounts"]
        # for account in Accounts:
        # status = 'Teststrtgy'
        # if (ScalpSettings[account].get(status, False)):
        # Threads.append(threading.Thread(target=exitOnTrigger, args=(account,CEorPE,"ZEXIT")))

        # for thread in Threads:
        # thread.start()

        # for thread in Threads:
        # thread.join()
        os._exit(1)

    print(" ^^^^^^^^^^^^^^^^^^^^^^^^ legbroken ^^^^^^^^^^^^^^^^^^^^^^^^^ ", ScalpSettings[CEorPE]['legBroken'])
    print(" ^^^^^^^^^^^^^^^^^^^^^^^^ TradeOn ^^^^^^^^^^^^^^^^^^^^^^^^^ ", ScalpSettings[CEorPE]['TradeOn'])
    print(" ^^^^^^^^^^^^^^^^^^^^^^^^ brokenLeg ^^^^^^^^^^^^^^^^^^^^^^^^^ ", ScalpSettings[CEorPE]['brokenLeg'])

    print(" ^^^^^^^^^^^^^^^^^^^^^^^^ RSI Check ^^^^^^^^^^^^^^^^^^^^^^^^^ ",
          rsi[rsisize - 1] < ScalpSettings[CEorPE]['entryRSI'])
    print(" ^^^^^^^^^^^^^^^^^^^^^^^^ VWAP check ^^^^^^^^^^^^^^^^^^^^^^^^^ ", close[size - 1] < vwap[size - 1])

    if (rsi[rsisize - 1] < ScalpSettings[CEorPE]['entryRSI'] and ScalpSettings[CEorPE]['TradeOn'] == False and close[
        size - 1] < vwap[size - 1]):
        print(" Sell ENtry ", close[size - 1])

        Threads = []
        Accounts = ScalpSettings["Accounts"]
        for account in Accounts:
            status = 'Teststrtgy'
            if (ScalpSettings[account].get(status, False)):
                Threads.append(threading.Thread(target=triggerOrders, args=(account, CEorPE, "ZENTRY")))

        for thread in Threads:
            thread.start()

        for thread in Threads:
            thread.join()

        ScalpSettings[CEorPE]['TradeOn'] = True
        sendTradeAlert("@@@ ZENBNFV3 - Entry, ALERT", CEorPE, close[size - 1])

    if (rsi[rsisize - 1] < ScalpSettings[CEorPE]['entryRSI'] and ScalpSettings[CEorPE]['legBroken'] == True and close[
        size - 1] < vwap[size - 1]):
        print(" reEnterBrokenLeg ", close[size - 1])
        Threads = []
        Accounts = ScalpSettings["Accounts"]
        for account in Accounts:
            status = 'Teststrtgy'
            if (ScalpSettings[account].get(status, False)):
                Threads.append(threading.Thread(target=reEnterBrokenLeg, args=(account, CEorPE, "ZENTRY")))

        for thread in Threads:
            thread.start()

        for thread in Threads:
            thread.join()

        ScalpSettings[CEorPE]['brokenLeg'] = "CEPE"
        ScalpSettings[CEorPE]['TradeOn'] = True
        ScalpSettings[CEorPE]['legBroken'] = False
        sendTradeAlert("@@@ ZENBNFV3 - Re Entry, ALERT", CEorPE, close[size - 1])

    if (datetime.datetime.now().time() > datetime.time(9, 17) and rsi[rsisize - 1] > ScalpSettings[CEorPE][
        'exitRSI'] and ScalpSettings[CEorPE]['TradeOn'] and ScalpSettings[CEorPE]['legBroken'] == False and close[
        size - 1] > vwap[size - 1]):
        print(" Exit ENtry ", close[size - 1])

        Threads = []
        Accounts = ScalpSettings["Accounts"]
        for account in Accounts:
            status = 'Teststrtgy'
            if (ScalpSettings[account].get(status, False)):
                Threads.append(threading.Thread(target=exitOnTrigger, args=(account, CEorPE, "ZEXIT")))

        for thread in Threads:
            thread.start()

        for thread in Threads:
            thread.join()

        ScalpSettings[CEorPE]['legBroken'] = True
        sendTradeAlert("@@@ ZENBNFV3 - Leg Exit, ALERT", CEorPE, close[size - 1])
    # pickleWrite()


def triggerOrders(account, CEorPE, tag):
    print("Placing Order for Account ", account)
    kiteobj = KiteConnect(api_key=ScalpSettings[account]['api_key'])
    kiteobj.set_access_token(ScalpSettings[account]['access_code'])

    numberofLots = ScalpSettings[account]['Test_lot_size']
    tradeEnabled = ScalpSettings[account]['Teststrtgy']

    print("number lots ", numberofLots)
    print("Trade Enabled  ", tradeEnabled)
    print("Trade ceContract  ", ScalpSettings[CEorPE]['ceContract'])
    print("Trade peContract  ", ScalpSettings[CEorPE]['peContract'])
    if (ScalpSettings[CEorPE]['TradeOn'] == False and tradeEnabled and "CE" in ScalpSettings[CEorPE]['brokenLeg']):
        executemarketOrder(kiteobj, ScalpSettings[CEorPE]['ceContract'], kite.TRANSACTION_TYPE_SELL,
                           kite.ORDER_TYPE_MARKET, ScalpSettings[account]['Test_lot_size'], tag)

    if (ScalpSettings[CEorPE]['TradeOn'] == False and tradeEnabled and "PE" in ScalpSettings[CEorPE]['brokenLeg']):
        executemarketOrder(kiteobj, ScalpSettings[CEorPE]['peContract'], kite.TRANSACTION_TYPE_SELL,
                           kite.ORDER_TYPE_MARKET, ScalpSettings[account]['Test_lot_size'], tag)


def reEnterBrokenLeg(account, CEorPE, tag):
    print("Placing Order for Account ", account)
    kiteobj = KiteConnect(api_key=ScalpSettings[account]['api_key'])
    kiteobj.set_access_token(ScalpSettings[account]['access_code'])

    numberofLots = ScalpSettings[account]['Test_lot_size']
    tradeEnabled = ScalpSettings[account]['Teststrtgy']
    ceContract = "NFCE"
    peContract = "NFPE"

    print("number lots ", numberofLots)
    print("Trade Enabled  ", tradeEnabled)
    print("Trade ceContract  ", ScalpSettings[CEorPE]['ceContract'])
    print("Trade peContract  ", ScalpSettings[CEorPE]['peContract'])
    if ScalpSettings[CEorPE]['TradeOn'] == True and tradeEnabled and "CE" in ScalpSettings[CEorPE]['brokenLeg']:
        executemarketOrder(kiteobj, ScalpSettings[CEorPE]['ceContract'], kite.TRANSACTION_TYPE_SELL,
                           kite.ORDER_TYPE_MARKET, ScalpSettings[account]['Test_lot_size'], tag)

    if ScalpSettings[CEorPE]['TradeOn'] == True and tradeEnabled and "PE" in ScalpSettings[CEorPE]['brokenLeg']:
        executemarketOrder(kiteobj, ScalpSettings[CEorPE]['peContract'], kite.TRANSACTION_TYPE_SELL,
                           kite.ORDER_TYPE_MARKET, ScalpSettings[account]['Test_lot_size'], tag)


def exitOnTrigger(account, CEorPE, tag):
    print("Placing Order for Account ", account)
    kiteobj = KiteConnect(api_key=ScalpSettings[account]['api_key'])
    kiteobj.set_access_token(ScalpSettings[account]['access_code'])

    numberofLots = ScalpSettings[account]['Test_lot_size']
    tradeEnabled = ScalpSettings[account]['Teststrtgy']

    print("number lots ", numberofLots)
    if (tradeEnabled and "CE" in ScalpSettings[CEorPE]['brokenLeg']):
        executemarketOrder(kiteobj, ScalpSettings[CEorPE]['ceContract'], kite.TRANSACTION_TYPE_BUY,
                           kite.ORDER_TYPE_MARKET, ScalpSettings[account]['Test_lot_size'], tag)

    if (tradeEnabled and "PE" in ScalpSettings[CEorPE]['brokenLeg']):
        executemarketOrder(kiteobj, ScalpSettings[CEorPE]['peContract'], kite.TRANSACTION_TYPE_BUY,
                           kite.ORDER_TYPE_MARKET, ScalpSettings[account]['Test_lot_size'], tag)


setToken = False
# checkVIX()
todayVIX = algoUtils.getVIX()
print(" &&&&& VIX Today : ", todayVIX)
ScalpSettings["BNFSTRDL"]['VIX'] = todayVIX
if todayVIX > ScalpSettings["BNFSTRDL"]['VIXcutoff']:
    print("High VIX Day, no ZEN Straddle strategy, exiting")
    os._exit(1)
time_now = datetime.datetime.now()  # Or .now() for local time
print(time_now)
prev_minute = time_now.minute - (time_now.minute % 3)
time_rounded = time_now.replace(minute=prev_minute, second=0, microsecond=0)

print(ScalpSettings)


def main():
    """

    :return:
    """

    send_alert('ZENBNFV3 Algo Started', "", "")
    loadAccessCodes()

    access_code_file = open("../setup/ZU9940.txt", "r")
    today_access_token = access_code_file.read()
    print(" Access Token", today_access_token)
    straddle_entry_time = datetime.time(9, 15)
    straddle_entry_end_time = datetime.time(9, 30)

    kite = KiteConnect(api_key=ScalpSettings['ZU9940']['api_key'])
    kite.set_access_token(ScalpSettings['ZU9940']['access_code'])

    global instruments
    instruments = getInstrumentsList(kite)


while True:
    current_time = datetime.datetime.now().time()
    script_exit_time = datetime.time(15, 23)
    # Wait until next 3 minute time
    time_rounded += timedelta(minutes=3)
    time_to_wait = (time_rounded - datetime.datetime.now()).total_seconds()
    print(" Waiting for :", time_to_wait)
    time.sleep(abs(time_to_wait))
    # letting zerodha gather itself for 2 secs
    time.sleep(4)
    # 5 min interval trigger...now execute strategy
    print("Test ", datetime.datetime.now())
    # get o=hlc for 5 min interval

    # first entry straddle at 9 15
    triggerStraddle("BNFSTRDL", ScalpSettings["BNFSTRDL"]['FirstTradeOn'])

    if ScalpSettings["BNFSTRDL"]['ceInstruToken'] == 0:
        setTokens()

    findEntryPrices("BNFSTRDL")

    # Send Telegram Message
    send_alert("A. ZENBNFV3 : Running Fine : ", datetime.datetime.now().hour, datetime.datetime.now().minute)

    if current_time >= script_exit_time:
        sys.exit(1)

if __name__ == '__main__':
    main()
