import sys

from kucoin.client import Client
from kucoin.exceptions import KucoinAPIException
from kucoin.exceptions import KucoinRequestException
from notifypy import Notify
from rich.console import Console
from PyInquirer import (Token, ValidationError, Validator, prompt,
                        style_from_dict)
import time
import math

########################################################################################
############################## YOUR STUFF GOES HERE ####################################

api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"
api_passphrase = "API_PASSPHRASE"

########################################################################################


class FloatValidator(Validator):
    """
    Checks if the input is a number
    """

    def validate(self, document):
        try:
            float(document.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number',
                cursor_position=len(document.text))


questions = [
    {
        'type': 'input',
        'name': 'ticker1',
        'message': 'What is the ticker of the asset you wish to sell?'
    },
    {
        'type': 'input',
        'name': 'ticker2',
        'message': 'What would you like to sell it for?'
    },
    {
        'type': 'input',
        'name': 'sl_percentage',
        'message': 'What stop-loss percentage would you like to work with?',
        'validate': FloatValidator
    },
    {
        'type': 'input',
        'name': 'enter_price',
        'message': 'At what price did you buy your assets?',
        'validate': FloatValidator
    }
]


# questions styling
style = style_from_dict({
    Token.QuestionMark: '#ff7f50 bold',
    Token.Answer: '#ff7f50 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})

# initialize stuff
notify = Notify()
console = Console()

global client
global accounts
global this_tick_stoploss


def tick(currency, pair, sl_percentage, enter_price):
    amount_owned = math.trunc(float(find_holding(currency)) * 10_000) / 10_000
    price_offset = enter_price * (sl_percentage / 100.0)
    first_stoploss = enter_price - price_offset
    previous_stoploss = first_stoploss
    console.log("[yellow]Set initial stop-loss price at: " + str(first_stoploss))
    while True:
        previous_stoploss = do_tick(pair, price_offset, amount_owned, previous_stoploss, first_stoploss)
        time.sleep(10)


def find_holding(currency):
    for i in range(len(accounts)):
        asset = accounts[i]
        if asset['currency'] == currency and asset['type'] == "trade" and not asset['balance'] == 0:
            holding = asset['balance']
            console.log("[yellow]Currently holding " + str(holding) + " " + str(currency))
            return holding


def do_tick(pair, price_offset, amount_owned, previous_stoploss, first_stoploss):
    global this_tick_stoploss
    current_price = float(client.get_ticker(pair)['price'])
    this_tick_stoploss = current_price - price_offset
    if current_price < previous_stoploss:
        console.log("[yellow]Triggered stop-loss. Proceeding to sell..")
        notify.title = "Triggered latest stop-loss!"
        notify.message = "Selling for the best market price."
        notify.send()
        sell(pair, amount_owned)
    elif this_tick_stoploss > previous_stoploss:
        console.log("[yellow]Higher price: stop-loss lifted from {} to {}".format(
            str(round(previous_stoploss, 2)),
            str(round(this_tick_stoploss, 2))
        ))
        return this_tick_stoploss
    else:
        console.log("[yellow]No significant price change")
        return previous_stoploss


def sell(pair, holding):
    order = client.create_market_order(pair, client.SIDE_SELL, size=holding)
    order_details = client.get_order(order["orderId"])
    price = float(order_details["dealFunds"]) / float(order_details["dealSize"])
    console.log("[yellow]Sold out @  " + str(price) + "")
    input()


def check_if_valid(pair):
    try:
        float(client.get_ticker(pair)['price'])
    except KucoinAPIException as e:
        print(e)
        sys.exit()


def open_connection():
    global client
    global accounts
    try:
        client = Client(api_key, api_secret, api_passphrase)
        accounts = client.get_accounts()
    except (KucoinAPIException, KucoinRequestException) as e:
        console.log("[yellow]Something went wrong during the API initialization: \n{}".format(e))
        sys.exit()


def main():
    open_connection()
    console.log("[yellow]Welcome! Lets do this.")
    answers = prompt(questions, style=style)
    ticker1 = answers["ticker1"]
    ticker2 = answers["ticker2"]
    currency = ticker1
    pair = "{}-{}".format(ticker1, ticker2)
    sl_percentage = float(answers["sl_percentage"])
    enter_price = float(answers["enter_price"])
    check_if_valid(pair)
    tick(currency, pair, sl_percentage, enter_price)


if __name__ == "__main__":
    main()

