# KuCoin Trailing Stop-Loss Script

**DISCLAIMER: I'm not in any way responsible for any input mistakes which result in trading losses**

This script connects to your API (created by you on your desktop within your kucoin account) and once you see an opportunity for a long position,
you can manually enter this by buying the asset. Just as you normally would.  

After you buy the asset, you fire up the script, which asks you which
asset you bought and on which pair. It then asks you for the stop-loss percentage you would like to use and at what price you got in. Using those 
numbers, an initial stop loss will be set. 

Every time the price climbs, the stop-loss is lifted as well. This will result in that, if the price
rises the with the percentage you filled in as the stop-loss percentage from your initial buy price, you will only be able to make profit. This is because the
stop-loss price is then at your initial buy-in price.

## Installation

1) Install [Python](https://www.python.org/downloads/), and make sure you check the box which says: "Add Python VERSION to PATH".  
  

2) In a command terminal / cmd window, navigate to the KucoinTrailingStopLoss folder and install the python packages using pip (keep the terminal open once finished):
```
pip install -r requirements.txt
```
or
```
pip3 install -r requirements.txt
```

3) Create a KuCoin API and make sure to enable "trade" access.  


4) Open tslk.py in a text-editor of you choice and fill in the API credentials where it says:  
   **YOUR STUFF GOES HERE**
   
## Using the actual script

In the same terminal window from before, while still in the KucoinTrailingStopLoss folder, you can run the script like so:

```
python tslk.py
```
or  
```
python3 tlsk.py
```

Follow the instructions. Please be careful about making typos while filling things out.

Enjoy.
