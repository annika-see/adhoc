# importing tools
import pandas as pd
import json 
import matplotlib.pyplot as plt

df = pd.read_json('transaction-data-adhoc-analysis.json')

df

# transaction individual items computed manually:

price_list = {
'HealthyKid 3+,Gummy Vitamins' : 1500,
'Candy City,Gummy Worms' : 150,
'Exotic Extras,Beef Chicharon' : 1299,
'Candy City,Orange Beans' : 199,
'HealthyKid 3+,Nutrional Milk' : 1990,
'Exotic Extras,Kimchi and Seaweed' : 799,
'HealthyKid 3+,Yummy Vegetables' : 500,
}

# transforming data + organizing 

df['transaction_date'] = pd.to_datetime(df['transaction_date'])
df['transaction_id'] = df.index
#make the items into a list and clean the data                                                     
df['transaction_items'] = df['transaction_items'].apply(lambda x: x.split(';'))

#this splits the items into individual rows
df = df.explode('transaction_items')

def quantity_col(row):
    #if last char in string is ')' then the item has a quantity not 1
    if row['transaction_items'][-1] == ")":
        return row['transaction_items'][-2]
    else:
        return 1

df['quantity'] = df.apply(lambda row: quantity_col(row), axis=1)

def clean_transaction_items(row):
    #remove ('x'n) in transaction_items
    if row['transaction_items'][-1] == ")":
        return row['transaction_items'][:-5]
    else:
        return row['transaction_items']

df['transaction_items'] = df.apply(lambda row: clean_transaction_items(row), axis=1)

def update_transaction_value(row):
    #value = item_price * quantity
    return price_list[row['transaction_items']] * int(row['quantity'])

df['transaction_value'] = df.apply(lambda row: update_transaction_value(row), axis=1)

print("Start of Date Range: {}".format(df['transaction_date'].min()))
print("End of Date Range: {}".format(df['transaction_date'].max()))

# monthly breakdown

def breakdown_by_month(start, end):
    #start, end date inclusive
    
    filtered = df.loc[(df['transaction_date'] >= pd.to_datetime(start)) & (df['transaction_date'] <= pd.to_datetime(end))]

    def breakdown(dataframe):
        #count
        item_counter = {}
        for index, row in dataframe.iterrows():
            item = row['transaction_items']
            if item not in item_counter:
                item_counter[item] = 0
            item_counter[item] += int(row['quantity'])

        item_sales = pd.DataFrame(item_counter.items(), columns=['item', 'sold_count',])
        item_sales = item_sales.sort_values(by='item')

        def price_col(row):
            return price_list[row['item']]

        def value_col(row):
            return row['sold_count'] * price_list[row['item']]

        item_sales['price'] = item_sales.apply(lambda row: price_col(row), axis=1)
        item_sales['sale_value'] = item_sales.apply(lambda row: value_col(row), axis=1)
        item_sales = item_sales.reset_index(drop=True)
        item_sales = item_sales.set_index('item')
        
        print("Total Sold Count: {}".format(item_sales['sold_count'].sum()))
        print("Total Sale Value: {}".format(item_sales['sale_value'].sum()))
        
#         ax = item_sales.plot.barh(x='item', y='sale_value', figsize=(16,9))
#         ax
        item_sales.plot.pie(y='sale_value', figsize=(16,9), labels=None, fontsize=10, title='Item Sale Distribution:')
    
        return item_sales
    
    print("Date Range: {} - {}".format(start, end))
    print()
    print(breakdown(filtered))
    return 

breakdown_by_month('2022-01-01', '2022-01-31')

breakdown_by_month('2022-02-01', '2022-02-28')

def get_month_table(start, end):
    filtered = df.loc[(df['transaction_date'] >= pd.to_datetime(start)) & (df['transaction_date'] <= pd.to_datetime(end))]
    filtered = filtered.sort_values(by=['transaction_date', 'transaction_id'])
    return filtered

January2022 = get_month_table('2022-01-01', '2022-01-31')
February2022 = get_month_table('2022-02-01', '2022-02-28')
March2022 = get_month_table('2022-03-01', '2022-03-31')
April2022 = get_month_table('2022-04-01', '2022-04-30')
May2022 = get_month_table('2022-05-01', '2022-05-31')
June2022 = get_month_table('2022-06-01', '2022-06-30')

months = [0, January2022, February2022, March2022, April2022, May2022, June2022]

def top_users(month_num=None):
    if month_num is None:
        table = df
    else:
        table = months[month_num]
    table['name'].apply(lambda x: x.upper())
    names_list = {}
    transaction_ids = []
    for index, row in table.iterrows():
        name = row['name']
        if name not in names_list:
            names_list[name] = {'unique_transactions' :0, 'total_items_bought_count' :0, 'total_items_bought_value': 0, 
                                'latest_transaction':0,}
        if row['transaction_id'] not in transaction_ids:
            transaction_ids.append(row['transaction_id'])
            names_list[name]['unique_transactions'] += 1
        names_list[name]['total_items_bought_count'] += int(row['quantity'])
        names_list[name]['total_items_bought_value'] += int(row['transaction_value'])
        names_list[name]['latest_transaction'] = row['transaction_date']
        

    names, unique, count, value, latest = [],[],[],[],[]
    for k, v in names_list.items():
        names.append(k)
        unique.append(v['unique_transactions'])
        count.append(v['total_items_bought_count'])
        value.append(v['total_items_bought_value'])
        latest.append(v['latest_transaction'])
        
    data = pd.DataFrame(list(zip(names, unique, count, value, latest)), columns= ['name', 'unique_transactions', 'total_items_bought_count',
                                                                                 'total_items_bought_value', 'latest_transaction'])
    return data.sort_values(by='total_items_bought_value', ascending=False)

# top users jan to june 

top_users()

# top users jan only

january_top_users = top_users(1)
january_top_users.head(20).plot.bar(x='name', y='total_items_bought_value', figsize=(16,9))
january_top_users

# repeat users

def repeat_users(month_num):
    if month_num > 1:
        previous_month_names = months[month_num - 1]['name'].unique()
        current_month_names = months[month_num]['name'].unique()

        repeat_count = 0
        for name in current_month_names:
            if name in previous_month_names:
                repeat_count += 1
        output = ("Repeat users(purchased previous and current month): {}".format(repeat_count))
        return output
    else:
        return 0 


print("Jan: {}".format(repeat_users(1)))
print("Feb: {}".format(repeat_users(2)))
print("Mar: {}".format(repeat_users(3)))
print("Apr: {}".format(repeat_users(4)))
print("May: {}".format(repeat_users(5)))
print("June: {}".format(repeat_users(6)))

# inactive users 

def inactive_users(month_num):
    if month_num > 1:
        previous_month_names = months[month_num - 1]['name'].unique()
        current_month_names = months[month_num]['name'].unique()
        repeat_count = 0
        for name in previous_month_names:
            if name in current_month_names:
                repeat_count += 1
        output = ("Inactive users(purchased previous but not current month): {}".format(repeat_count))
    else:
        return 0
    
print("Jan: {}".format(inactive_users(1)))
print("Feb: {}".format(inactive_users(2)))
print("Mar: {}".format(inactive_users(3)))
print("Apr: {}".format(inactive_users(4)))
print("May: {}".format(inactive_users(5)))
print("June: {}".format(inactive_users(6)))

# engaged users 

def engaged_users():
    jan_users = months[1]['name'].unique()
    feb_users = months[2]['name'].unique()
    mar_users = months[3]['name'].unique()
    apr_users = months[4]['name'].unique()
    may_users = months[5]['name'].unique()
    jun_users = months[6]['name'].unique()
    
    engaged_list = []
    
    for name in jan_users:
        if name in feb_users and name in mar_users and name in apr_users and name in may_users and name in jun_users:
            engaged_list.append(name)
            
    print(len(engaged_list))
    return engaged_list

engaged_users_list = engaged_users()

# top engaged users 

def top_engaged_users():
    table = df[df['name'].isin(engaged_users_list)]
    names_list = {}
    transaction_ids = []
    for index, row in table.iterrows():
        name = row['name']
        if name not in names_list:
            names_list[name] = {'unique_transactions' :0, 'total_items_bought_count' :0, 'total_items_bought_value': 0, 
                                'latest_transaction':0,}
        if row['transaction_id'] not in transaction_ids:
            transaction_ids.append(row['transaction_id'])
            names_list[name]['unique_transactions'] += 1
        names_list[name]['total_items_bought_count'] += int(row['quantity'])
        names_list[name]['total_items_bought_value'] += int(row['transaction_value'])
        names_list[name]['latest_transaction'] = row['transaction_date']
    

    names, unique, count, value, latest = [],[],[],[],[]
    for k, v in names_list.items():
        names.append(k)
        unique.append(v['unique_transactions'])
        count.append(v['total_items_bought_count'])
        value.append(v['total_items_bought_value'])
        latest.append(v['latest_transaction'])
        
    data = pd.DataFrame(list(zip(names, unique, count, value, latest)), columns= ['name', 'unique_transactions', 'total_items_bought_count',
                                                                                 'total_items_bought_value', 'latest_transaction'])
    return data.sort_values(by='total_items_bought_value', ascending=False)

top_engaged_users().head(20)