
import time
import _mysql
from yahoo_historical import Fetcher

# Constants for pulling data
start_date = [2016, 11, 1]
end_date = [2017, 11, 1]

# Establish database connection
db = _mysql.connect(host="localhost", user="dbdesign", passwd="dbdesign", db="project")

# Query the list of symbols from the database
db.query("SELECT ticker FROM companies")
ticker_list_result = db.store_result()
num_tickers = ticker_list_result.num_rows()

# Keep track of failed tickers?
failed_tickers = []

# Loop of the retrieved symbols
for i in range(1, num_tickers):
    ticker = ticker_list_result.fetch_row()[0][0]

    # TODO Small delay to avoid API throttling?
    # time.sleep(2)

    # Get the historical data for the current symbol
    # (Try in loop for when the API fails due to too many requests/retries)
    skip = False
    while True:
        try:
            print("Getting data for:\t" + ticker + "\t\t" + str(i) + "/" + str(num_tickers))
            data = Fetcher(ticker, start_date, end_date)
            historical = data.getHistorical()
        except Exception as e:
            print("===Error===")
            print(e)
            if "name='B', domain=None, path=None" in e:
                skip = True
                break
            print("Fetching [" + ticker + "] failed. Trying again after 30s delay...")
            time.sleep(30)
            continue
        break

    # Skip the ticker if there is an issue with the API
    if skip:
        print("API ERROR. SKIPPING " + ticker)
        failed_tickers.append(ticker)
        continue

    # Loop over each day and insert into Daily for the given symbol-date pair
    # Date       Open       High        Low      Close  Adj Close   Volume
    for row in historical.itertuples():
        # Extract each part of the data for the day
        date = row.__getattribute__("Date")
        d_open = row.__getattribute__("Open")
        d_close = row.__getattribute__("Close")
        d_high = row.__getattribute__("High")
        d_low = row.__getattribute__("Low")
        d_volume = row.__getattribute__("Volume")

        # Delete the entry if it already exists
        db.query("DELETE FROM daily WHERE ticker = '" + ticker + "' AND date = '" + date + "'")

        # Insert the data into the database
        query = "INSERT INTO daily values ('" \
                 + ticker + "', '" \
                 + date + "', " \
                 + str(d_high) + ", " \
                 + str(d_low) + ", " \
                 + str(d_open) + ", " \
                 + str(d_close) + ", " \
                 + str(d_volume) + ")"

        db.query(query)

# Print any tickers that were skipped due to API errors
print("\nTickers where API failed:")
print(failed_tickers)
