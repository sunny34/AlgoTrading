import requests
from src.strategy_code_base import logger


def send_alert(message: str, arg1: str, arg2: str) -> None:
    """
    function which sends alert to the telegram

    :param message:
    :param arg1:
    :param arg2:
    :return:
    """
    send_url = f'https://api.telegram.org/bot158033:AAGQxfY3jqgaABA-fCwUgE/sendmessage?chat_id=-362269073&text=' \
               f'"{message} : {arg1} : {arg2}"'
    try:
        requests.get(send_url)
    except Exception as e:
        logger.info("telegram alert failed: {}".format(e))


def send_trade_alert(message: str, arg1: str, arg2: str) -> None:
    """
    function which send trade alert

    :param message:
    :param arg1:
    :param arg2:
    :return:
    """
    send_url = f'https://api.telegram.org/bot154:AAahqp91IVWaENg/sendmessage?chat_id=-406660920&text="' \
               f'{message} : {arg1} : {arg2}" '
    try:
        requests.get(send_url)
    except Exception as e:
        logger.info("telegram alert failed: {}".format(e))


def send_error_alert(message: str, arg1: str, arg2: str) -> None:
    """
    Function which send error alert to telegram

    :param message:
    :param arg1:
    :param arg2:
    :return:
    """
    send_url = f'https://api.telegram.org/bot354:AAIVWaENg/sendmessage?chat_id=-406660920&text=' \
               f'"{message} : {arg1} : {arg2}"'
    try:
        requests.get(send_url)
    except Exception as e:
        logger.info("telegram alert failed: {}".format(e))
