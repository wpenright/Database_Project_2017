
# Main user application
# Prompt for search specification input
# Construct query based on specification
# Get response from database
# Return data to terminal or render some visualization to file

# TODO:
# - Add handling for incorrect inputs?
# - Add support for multiple filters at once
# - Make sure all identified functionality is present
# - Update prompts to better reflect requested data

import _mysql
import plotly
from plotly.graph_objs import Scatter, Layout

# Option and prompt data
metrics = {1: ("Open", "DailyPositions", "open"),
           2: ("Close", "DailyPositions", "close"),
           3: ("High", "DailyPositions", "high"),
           4: ("Low", "DailyPositions", "low"),
           5: ("Volume", "DailyPositions", "vol"),
           8: ("PPE", "FinancialData", "PPE"),
           9: ("EPS", "FinancialData", "EPS")}

# Latest value vs high/low/average over timeframe

measures = {1: "Individual",
            2: "Net Change",
            3: "Average"}

filters = {1: ("Greater Than Value", ">"),
           2: ("Less Than Value", "<")}

start_date_prompt = "Enter start date [YYYY-MM-DD]: "
end_date_prompt = "Enter end date [YYYY-MM-DD]: "


# Establish DB connection
try:
    db = _mysql.connect(host="localhost", user="dbdesign", passwd="dbdesign", db="financialdata")
except Exception as e:
    print(e)
    print("FAILED TO CONNECT TO DATABASE. EXITING...")
    exit(1)

# Welcome message
print("Welcome to our stock analyzer application!")
print("Search the S&P 500 and graph relations between metrics.")


# Quit the app
def quit_app():
    print("\nGoodbye!\n")
    exit(0)


# Perform a search query from the database
def do_search():

    # Prompt user for metric option
    metric_choices = []
    prompt = "Select the type of data to search by: \n[0 to quit]\n"
    for m_key in metrics.keys():
        prompt += "\t[" + str(m_key) + "]\t" + metrics[m_key][0] + "\n"
    metric = int(raw_input(prompt))

    # Handle if user decides to quit
    if metric == 0:
        quit_app()

    # Prompt user for measure type
    prompt = "Select how to measure the selected metric: \n"
    for m_key in measures.keys():
        prompt += "\t[" + str(m_key) + "]\t" + measures[m_key] + "\n"
    measure = int(raw_input(prompt))

    # Prompt user for filter type
    filter_choices = []
    prompt = "Select how to filter on the selected data: \n"
    for f_key in filters.keys():
        prompt += "\t[" + str(f_key) + "]\t" + filters[f_key][0] + "\n"
    filter = int(raw_input(prompt))

    # Prompt user for value
    value = raw_input("Enter the value to filter on: ")

    # Prompt user for start and end dates
    start_date = raw_input(start_date_prompt)
    end_date = raw_input(end_date_prompt)

    q_metric = metrics[metric][0]           # The metric to filter on
    q_table = metrics[metric][1]            # The table to search in
    q_comparison = filters[filter][1]
    q_items = "ticker as t"                 # The data to retrieve
    q_date_filter = "date < '" + end_date + "' AND date > '" + start_date + "'"
    q_where = " WHERE " + q_metric + " " + q_comparison + " " + value + " AND " + q_date_filter
    q_having = ""

    # Make changes to the query structure for just net change queries
    if measures[measure] == "Net Change":
        q_items += ", (SELECT " + q_metric + " FROM " + q_table + " WHERE ticker = t AND " + q_date_filter + " ORDER BY date DESC limit 1) - "
        q_items += "(SELECT " + q_metric + " FROM " + q_table + " WHERE ticker = t AND " + q_date_filter + " ORDER BY date ASC limit 1) as diff"

        q_where = ""
        q_having += " HAVING diff " + q_comparison + " " + value

        q_table = "SecuritiesMaster"

    # Adjust the query for averages
    if measures[measure] == "Average":
        q_items += ", avg(" + q_metric + ") as avg"
        q_where = " WHERE " + q_date_filter
        q_having += " HAVING avg " + q_comparison + " " + value

    # Construct the final query
    search_query = "SELECT " + q_items
    search_query += " FROM " + q_table
    search_query += q_where
    search_query += " GROUP BY t" + q_having

    # Query the database
    #print(search_query)
    db.query(search_query)
    data_result = db.store_result()

    # Print out the data nicely
    print("\nStocks matching your selection:")
    for i in range(0, data_result.num_rows()):
        row = data_result.fetch_row()[0]
        for element in row:
            print element,
            print "\t",
        print


# Graph a relation between stock metrics (or graph activity of a single stock)
def do_graph():
    print("TO BE IMPLEMENTED")

    db.query("SELECT date, close FROM dailypositions WHERE ticker = 'AAPL'")
    data_result = db.store_result()
    num_rows = data_result.num_rows()
    data_x = [] # Date
    data_y = [] # Price
    for i in range(0, num_rows):
        pair = data_result.fetch_row()[0]
        data_x.append(pair[0])
        data_y.append(pair[1])

    plot_data = Scatter(x=data_x, y=data_y, mode='markers+lines', text='AAPL')
    plotly.offline.plot({"data": [plot_data], "layout": Layout(title="AAPL History")})

# Retrieve and print all watchlist data
# (Get for specific stock?)
def view_watchlist():

    # Get all the rows from the watchlist table
    db.query("SELECT ticker, notes FROM watchlist")
    data_result = db.store_result()
    num_rows = data_result.num_rows()

    # Print a header for easier parsing
    print("----------------------------------------")
    print("SYMBOL\t\tNOTES")
    print("----------------------------------------")

    # Walk over each of the items in the watchlist
    for i in range(0, num_rows):
        pair = data_result.fetch_row()[0]
        ticker = pair[0]
        notes = pair[1]

        # Print out the current watchlist ticker and notes
        print(ticker + "\t\t" + notes)


# Add/edit/delete a watchlist entry
def edit_watchlist():

    # See if the user wants to update or delete a watchlist entry
    prompt = "Select what you want to do:\n[1]\tAdd/Update watchlist entry\n[2]\tDelete watchlist entry\n"
    action = int(raw_input(prompt))
    if action < 1 or action > 2:
        print("Invalid selection")
        return

    # Get the ticker the user wants to update
    prompt = "Enter the symbol of the watchlist entry:\n"
    ticker = raw_input(prompt)

    # If delete
    if action == 2:
        # DELETE FROM watchlist WHERE ticker = <ticker>
        query = "DELETE FROM watchlist WHERE ticker = '" + ticker + "'"
        db.query(query)
        return

    prompt = "Enter the note you want to store for this symbol in your watchlist:\n"
    notes = raw_input(prompt)

    # TODO: Display existing note information to help with editing?
    # TODO: Notify of symbols entered that are not in our list of the S&P500
    # TODO: Notify for successful deletes

    # If add/update
    if action == 1:
        # Insert watchlist data if new, or update existing record
        query = "INSERT INTO watchlist "
        query += "SELECT '" + ticker + "', '" + notes + "' FROM SecuritiesMaster WHERE ticker = '" + ticker + "' "
        query += "ON DUPLICATE KEY UPDATE notes = '" + notes + "'"
        db.query(query)
        return

activity_prompt = """Select what you want to do:
[0 to quit]
\t[1]\tSearch or Filter stocks by metric
\t[2]\tCompare and Graph stock data and metric relations
\t[3]\tView watchlist
\t[4]\tEdit watchlist\n"""

# Main loop to prompt user for input:
while True:
    print("\n============================================================\n")

    # Basic functions:
    #   Search stocks
    #   Compare/Graph stocks
    #   View watchlist
    #   Edit watchlist

    # Prompt user for top level option
    activity = int(raw_input(activity_prompt))
    # Quit
    if activity == 0:
        quit_app()
    # Search/Filter stocks
    elif activity == 1:
        do_search()
    # Compare/Graph stocks
    elif activity == 2:
        do_graph()
    # View watchlist and notes
    elif activity == 3:
        view_watchlist()
    # Add/edit/delete watchlist entries
    elif activity == 4:
        edit_watchlist()
