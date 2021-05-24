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
                message='Please enter a digit',
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
        'message': 'What is the ticker of the asset you want to for?'
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
    },
    {
        'type': 'input',
        'name': 'percentage_to_sell',
        'message': 'What percentage of your holdings do you want to sell?',
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
global assets
global this_tick_stop_loss
interval_seconds = 10


def update_price_continuously(settings):
    """
    Takes the user settings and continuously loops and runs the do_tick
    function. That function performs logic based on the current retrieved price.
    Sleeps for 10 seconds after every loop.

    :param settings:
    :return:
    """
    # extract specific values from settings
    primary_asset = settings["ticker1"]
    pair = "{}-{}".format(settings["ticker1"], settings["ticker2"])
    sl_percentage = float(settings["sl_percentage"])
    enter_price = float(settings["enter_price"])
    percentage_to_sell = float(settings["percentage_to_sell"])

    # get the amount (of primary asset) that is owned by the user
    amount_owned = math.trunc(float(find_holding(primary_asset)) * 10_000) / 10_000

    # calculate the fixed stop-loss price offset
    price_offset = enter_price * (sl_percentage / 100.0)

    # determine the initial stop-loss value (based on the enter_price)
    first_stop_loss = enter_price - price_offset

    # keep a local value of the stop-loss of the previous iteration
    previous_stop_loss = first_stop_loss

    # report initial stop-loss price
    console.log("[yellow]Set initial stop-loss price at: " + str(first_stop_loss))

    # loop infinitely (with 10 second pauses) until stop-loss is hit and assets are sold
    while True:
        previous_stop_loss = do_tick(pair, price_offset, amount_owned, previous_stop_loss, percentage_to_sell)
        time.sleep(interval_seconds)


def find_holding(currency):
    """
    Loop through all assets ( either in the trading or main account ). If the
    assets ticker is equal to the user's primary ticker, the asset is in the
    trading account and the balance is not equal to zero, the amount that is
    held by the user is returned.

    :param currency:
    :return:
    """
    for i in range(len(assets)):
        asset = assets[i]
        if asset['currency'] == currency and asset['type'] == "trade":
            if float(asset['balance']) == 0:
                console.log("[yellow]There are {} funds in your trading account. Aborting..".format(str(currency)))
                sys.exit()
            else:
                holding = asset['balance']
                console.log("[yellow]Currently holding " + str(holding) + " " + str(currency))
                return holding


def do_tick(pair, price_offset, amount_owned, previous_stop_loss, percentage_to_sell):
    """
    Checks whether the stop-loss is hit, or if the current price has increased.
    Either sells the funds, lifts the stop-loss price or does nothing.

    :param pair:
    :param price_offset:
    :param amount_owned:
    :param previous_stop_loss:
    :param percentage_to_sell:
    :return:
    """
    global this_tick_stop_loss
    current_price = float(client.get_ticker(pair)['price'])
    this_tick_stop_loss = current_price - price_offset
    if current_price < previous_stop_loss:
        # stop-loss hit. selling..
        console.log("[yellow]Triggered stop-loss. Proceeding to sell..")
        notify.title = "Triggered latest stop-loss!"
        notify.message = "Selling for the best market price."
        notify.send()
        sell(pair, amount_owned, percentage_to_sell)
    elif this_tick_stop_loss > previous_stop_loss:
        # price increased, and lifting the stop-loss price.
        console.log("[yellow]Price increase detected: stop-loss lifted from {} to {}".format(
            str(previous_stop_loss),
            str(this_tick_stop_loss)
        ))
        return this_tick_stop_loss
    else:
        # stop-loss not hit, but also no price increase
        console.log("[yellow]No significant price change. Going again in {} seconds".format(interval_seconds))
        return previous_stop_loss


def sell(pair, amount_owned, percentage_to_sell):
    """
    Sell the funds that are in the trading account.

    :param pair:
    :param amount_owned:
    :param percentage_to_sell:
    :return:
    """
    amount_to_sell = amount_owned * (percentage_to_sell / 100.0)
    order = client.create_market_order(pair, client.SIDE_SELL, size=amount_to_sell)
    order_details = client.get_order(order["orderId"])
    price = float(order_details["dealFunds"]) / float(order_details["dealSize"])
    console.log("[yellow]Sold out @  " + str(price) + "")

    sys.exit()


def check_if_valid(settings):
    """
    Checks whether the given pair exists on kucoin.
    If not, the program is killed.

    :param settings:
    :return:
    """
    pair = "{}-{}".format(settings["ticker1"], settings["ticker2"])
    try:
        float(client.get_ticker(pair)['price'])
    except KucoinAPIException as e:
        print(e)
        sys.exit()


def open_connection():
    """
    Creates the API connection using the user's credentials.
    When this is unsuccessful, the program is killed.

    :return:
    """
    global client
    global assets
    try:
        client = Client(api_key, api_secret, api_passphrase)
        assets = client.get_accounts()
    except (KucoinAPIException, KucoinRequestException) as e:
        console.log("[yellow]Something went wrong during the API initialization: \n{}".format(e))
        sys.exit()


def main():
    """
    Main function which gets everything going.

    :return:
    """
    open_connection()
    console.log("[yellow]Welcome! Lets start.")
    settings = prompt(questions, style=style)
    check_if_valid(settings)
    update_price_continuously(settings)


# start of the script. calls the main function.
if __name__ == "__main__":
    main()

