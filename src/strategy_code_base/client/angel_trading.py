# package import statement
from smartapi import SmartConnect  # or from smartapi.smartConnect import SmartConnect
from src.strategy_code_base.adhoc.backtester import logger
import asyncio


# import smartapi.smartExceptions(for smartExceptions)

# create object of call
async def create_connection(client_username: str, client_password: str):
    result = dict()
    obj = SmartConnect(api_key="B7H7umuQ")

    # login api call

    data = obj.generateSession(client_username, client_password)
    refresh_token = data['data']['refreshToken']

    # fetch the feedtoken
    feed_token = obj.getfeedToken()

    # fetch User Profile
    user_profile = obj.getProfile(refresh_token)

    result[client_username] = dict(connection=obj, feed_token=feed_token, user_profile=user_profile)

    return result


# place order

async def place_order(obj, symbol, symbol_token, transaction_type, order_type, exchange):
    logger.info(f"Placing {transaction_type} order for {symbol} token symbol {symbol_token} on exchange {exchange}")
    try:
        order_params = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": symbol_token,
            "transactiontype": "BUY",
            "exchange": exchange,
            "ordertype": order_type,
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "530.25",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": "1"
        }
        order_id = obj.placeOrder(order_params)
        order_book = obj.orderBook()
        print(order_book)

        print("The order id is: {}".format(order_id))
    except Exception as e:
        print("Order placement failed: {}".format(str(e)))


async def get_trade_book(obj):
    res = obj.tradeBook()
    print(res)


async def close_connection(obj, client_id: str):
    # logout
    try:
        logger.info(f"Logging out session for client {client_id}")
        logout = obj.terminateSession(client_id)
        logger.info(f"logout response is {logout}")
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")


async def main():
    obj = await create_connection()
    await place_order(obj)
    await get_trade_book(obj)


if __name__ == '__main__':
    main()
