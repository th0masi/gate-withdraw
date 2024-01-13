import ccxt
import random
import time
from sys import stderr

import config
from loguru import logger

logger.remove()
logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                          ' | <level>{level: <8}</level>'
                          ' | <cyan>{line}</cyan>'
                          ' - <white>{message}</white>')
logger.add(
    "logfile.log",
    rotation="3 days",
    format="<green>{time}</green> | "
           "<level>{level}</level> | "
           "<cyan>{name}</cyan>:"
           "<cyan>{function}</cyan>:"
           "<cyan>{line}</cyan> - "
           "<level>{message}</level>"
)

token_code = 'MEME'
network = 'ETH'


def control_fee():
    while True:
        try:
            fees = exchange.fetch_deposit_withdraw_fees()

            if token_code in fees:
                meme_eth_info = fees[token_code]
                max = config.MAX_FEE_MEME_GAS
                fee = meme_eth_info.get('networks').get('ETH').get('withdraw').get('fee')
                fee_1 = meme_eth_info.get('withdraw').get('fee')
                fee_2 = meme_eth_info.get('info').get('withdraw_fix_on_chains').get('ETH')

                if int(fee) <= max and int(fee_1) <= max and int(fee_2) <= max:
                    logger.success(f'Current fee: {fee} ${token_code}, go withdraw!')
                    return int(fee)
                else:
                    logger.info(f'Current fee: {fee} ${token_code}, wait'
                                f' for {max} ${token_code}')

        except Exception as e:
            logger.error(f'Cant get current fee, error:  {e}')
            continue

        logger.info(f'Sleep 120 sec...')
        time.sleep(120)


if __name__ == '__main__':
    with open('wallets.txt', 'r') as file:
        wallet_addresses = [line.strip() for line in file]

    exchange = ccxt.gateio({
        'apiKey': config.API_KEY,
        'secret': config.API_SECRET,
    })

    for address in wallet_addresses:
        fee = control_fee()
        amount = random.uniform(*config.AMOUNT)
        amount_with_fee = round(fee + amount, 2)
        delay = random.randint(*config.DELAY)

        try:
            logger.info(f" {address} | Try to withdraw {amount_with_fee} ${token_code}...")
            response = exchange.withdraw(token_code, amount_with_fee, address, params={
                'network': network,
            })
            withdrawal_id = response.get('id', None)

            if withdrawal_id:
                logger.success(f" {address} | Success withdraw [ID: {withdrawal_id}]")
                time.sleep(delay)

        except ccxt.BaseError as error:
            error_message = str(error)

            if "INVALID_PARAM_VALUE" in error_message:
                logger.error(f" {address} | Account not in whitelist: {error}")

            elif "Invalid key provided" in error_message:
                logger.error(f" {address} | Invalid API key")
                exit()

            elif "Signature mismatch" in error_message:
                logger.error(f" {address} | Invalid API secret")
                exit()

            else:
                logger.error(f" {address} | Unexpected error: {error}")

    logger.success(f"All tasks done!")
