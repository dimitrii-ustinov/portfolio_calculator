"""
Project name: Financial advisor and investment portfolio

The program creates financial recommendations and maintains portfolio 
according to your market activity.

Author: Dimitrii Ustinov

Date: 2023-10-23
"""

import yfinance as yf
import matplotlib.pyplot as plt
import chat_gpt_api as gpt
import textwrap
import pandas as pd
import json
import os.path
import time
import webbrowser
from pytickersymbols import PyTickerSymbols #taken from https://github.com/portfolioplus/pytickersymbols


#The function filters out the stocks in the NASDAQ 100 list, removing irrelevant stock tickers    
def get_stock_list():
    """The function gets the stock list from pytickersymbols and filters out 
    the tickers that are invalid returning a new list"""
    stock_data = PyTickerSymbols()
     # the naming conversation is get_{index_name}_{exchange_city}_{yahoo or google}_tickers
    nasdaq_100_list = stock_data.get_nasdaq_100_nyc_yahoo_tickers()
    filtered_nasdaq_100 = []
    for stock in nasdaq_100_list:
        if len(stock) < 6:
            filtered_nasdaq_100.append(stock)
    return filtered_nasdaq_100    

#The function checks if the symbol is in the NASDAQ 100 list
def stock_filter():
    """Check if the chosen stock is in the NASDAQ-100 list and return an error if the 
    chosen stock doesn't belong to NASDAQ 100"""
    stock_list = get_stock_list()
    prompt = str(input("Type a stock symbol you want to analyse from NASDAQ 100: ")).upper()
    while prompt not in stock_list:
        
        print(textwrap.fill(str(stock_list),width = 70))
        prompt = str(input("Remember, it has to be in NASDAQ 100.\nLook at the list above.\nType a stock symbol you want to analyse from NASDAQ 100: ")).upper()
        
    return prompt
        

#The function provides graphical insights into the stock price and  price changes
def analyze_stock(symbol, start_date, end_date):
    """The functions creates 2 plots with daily closing prices and price changes """
    stock_data = yf.download(symbol, start=start_date, end=end_date)     # Fetch the stock data from Yahoo Finance
    stock_data['Daily Return'] = stock_data['Close'].pct_change()        # Calculate the daily returns
     
     # Plot the closing price and daily returns
    plt.figure(figsize=(10, 5))
    plt.subplot(2, 1, 1)
    plt.plot(stock_data['Close'])
    plt.title('Stock Price')
    plt.ylabel('Price')
    plt.subplot(2, 1, 2)
    plt.plot(stock_data['Daily Return'])
    plt.title('Daily Returns')
    plt.ylabel('Return')
    plt.tight_layout()
    plt.show()
    
#The function fetches the information from Yahoo Finance about the company
def get_info(symbol):
    """Get the information about the company"""
    ticker = yf.Ticker(f"{symbol}")
    company_info = ticker.info['longBusinessSummary']
    print(textwrap.fill(company_info,width = 100))    


#Generate the ChatGPT financial recommendation
def generate_text(symbol):
    """Prompt a user for an input and feed to GPT. Return a response"""
    start_time = time.time()
    framed_response = f"Write an investment recommendation of the company under the ticker {symbol}. Do not format it as a letter"
     #Get the text generated using chat GPT
    output = gpt.basic_generation(framed_response)
    print(textwrap.fill(output,width = 100))
    end_time = time.time()
    print(f"The time it took to generate the text is {(end_time - start_time):.2f} seconds")    

#The function generates a new Portfolio where a budget is set by the user
def stock_dict():
        """Make a dictionary with zeros for each stock and current available budget"""
        budget = int(input("What is the budget of your portfolio?(Type an int): "))  #Get the budget
        with open('portfolio.json', 'w') as json_file:                               #Write the dictionary into the json file
                stock_dictionary = {'MY_BUDGET:': [budget]}
                stock_list = get_stock_list()
                for stock in stock_list:
                        stock_dictionary[stock] = [0,0,0,0]
                        #Save it into json file
                json.dump(stock_dictionary, json_file)                

#Supplementary to buy_sell(). 
def stocks_purchased_dict(current_portfolio):
        """Returns the new dictionary with stocks purchased.
        Supplimentary function to buy_sell()"""
        stocks_purchased_dict = {}
        for stock, value in current_portfolio.items():
                if value[0] > 0 and stock != 'MY_BUDGET:':
                        stocks_purchased_dict[stock] = value[0] 
        return stocks_purchased_dict

#Supplementary to buy_sell(). 
def current_portfolio_changer(amount, my_budget, invested, symbol, current_portfolio, price):
        """Function changes current portfolio according to the user input
        Supplimentary to buy_sell()"""
        if amount != 0:                                                   #Check if the amount of stocks in the portfolio is = 0
                ave_price = invested / amount
        else:
                ave_price = 0
                price = 0
                invested = 0
        current_portfolio[symbol] = [amount,price,ave_price,invested]                #Add values to the dictionary
        current_portfolio['MY_BUDGET:'] = [my_budget]                                #Changes the budget available
        return current_portfolio 
               
#The function executing purchases, sales and budget changes
def buy_sell(symbol, current_portfolio):
        """Prompt user to buy or sell and ask for the amount of stocks needed. 
        Return a revised dictionary"""       
        stock = yf.Ticker(symbol)                        
        price = stock.info['currentPrice']                                          #Save the last market price
        buy_or_sell = str(input(f"Do you want to buy/sell {symbol}?(Type YES or anything else to quit): "))
        if buy_or_sell == 'YES':    
                
                try:                                                                #Check if the input is an integer
                        print(f"This program does not allow shorting. Your maximal purchase of {symbol} is {int(current_portfolio['MY_BUDGET:'][0]//price)}.\nYou can also sell {stocks_purchased_dict(current_portfolio)}")
                        amount_prompt = int(input(f"How many shares of {symbol} do you want to buy(+) or sell(-)?(Type an int): "))
                
                except ValueError:
                        print("Type an integer. Run the program again to proceed")
                
                else:
                        amount = current_portfolio[symbol][0] + amount_prompt
                        invested = round(current_portfolio[symbol][3] + amount_prompt*price, 2)
                        my_budget = round(current_portfolio['MY_BUDGET:'][0] - amount_prompt*price)
                          #Check that the budget is not negative and that it is not a short sell
                        if amount >= 0 and my_budget >= 0:   
                                current_portfolio = current_portfolio_changer(amount, my_budget, invested, symbol, current_portfolio, price) 
                                return current_portfolio
                        else:
                                print("This trade is outside of your portfolio limit")
        return current_portfolio

def main():
    """Prints the plots and the generated text, reads and writes the Portfolio"""
    
    symbol = stock_filter()                                               #Checks if the stock is part of NASDAQ list
    
    start_date = str(input("Type a start date in a format yyyy-mm-dd: ")) # Start date of the analysis
    end_date = str(input("Type an end date in a format yyyy-mm-dd: "))    # End date of the analysis
    get_info(symbol)                                                      # Prints information from yfinance about the company
    analyze_stock(symbol, start_date, end_date)                           # Prints the plots
    #generate_text(symbol)                                                 #Prints ChatGPT financial advice
    
    if not os.path.exists('portfolio.json'):                              #Creates Portfolio if it run the first time
            stock_dict()
            
    with open('portfolio.json', 'r') as json_file:                        #Opens saved Portfolio file
            current_portfolio = dict(json.load(json_file))
    portfolio = buy_sell(symbol, current_portfolio)
    
    with open('portfolio.json', 'w') as json_file:                        #Records changes in the Portfolio
            json.dump(portfolio, json_file)   
    new = 2                                                               # open in a new tab
    webbrowser.open('file://' + os.path.realpath('portfolio.json'),new=new)    


main() 

