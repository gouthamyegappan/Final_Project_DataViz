#!/usr/bin/env python
# coding: utf-8

# In[65]:


from dash import html
from dash import Dash, dcc, html
from dash import Dash, dcc, html, Input, Output
import pandas as pd

import plotly.graph_objects as go
import plotly.express as px

from jupyter_dash import JupyterDash
import collections

import regex as re

import datetime
import gunicorn
import dns


# In[14]:


data = pd.read_csv('Final Project/final_data.csv').drop('Unnamed: 0', axis = 1)


# In[31]:


data = data.dropna(subset = ['title'])


# In[34]:


vals = [v.lower() for v in data['title']]
vals = [re.sub(r'[: | \ | / | -]',' ',v) for v in vals]

vals = [list(set(v.split())) for v in vals]
data_words = vals


# In[35]:


def wanted_search(title):
    youtube = [tit for tit in data['title'] if title in tit]

    # split values
    all_youtube = ' '.join([' '.join(t) for t in [v.split()[:-2] for v in youtube]]).lower()
    youtube_counts = collections.Counter(all_youtube.split())
    counts = pd.DataFrame.from_dict(youtube_counts, orient='index')
    counts = counts.loc[[idx for idx in counts.index if len(idx) > 2]]

    not_words = ['the', 'and', 'for', '(1)']
    counts = counts.loc[[idx for idx in counts.index if idx not in not_words]]

    return counts


# In[40]:


vals = wanted_search('- YouTube')
# wanted_search('TikTok')
vals = vals.sort_values(by = 0)[-15:]
vals = vals.iloc[::-1]

fig_youtube = px.bar(x = vals.index, y = vals[0], title='Most Watched Youtube Videos', width=700, height = 500, 
                   labels= {"y": 'Total Views',
                            'x': 'Tag Name'}).update_layout(yaxis_title = 'Total Views')

fig_youtube.update_xaxes(tickfont_size=11)


# In[41]:


tiktok_data = data[[True if 'TikTok' in t else False for t in data['title']]]
all_matches = [re.findall(r'\((.*?)\)', s) for s in tiktok_data['title']]
people = [m[0] for m in all_matches  if len(m) > 0]
vals2 = pd.Series(people).value_counts()[:15]

fig_tiktok = px.bar(x = vals2.index, y = vals2.values, title='Most Watched TikTok Creators', width=700, height = 500, 
                   labels= {"y": 'Total Views',
                            'x': 'Username'}).update_layout(yaxis_title = 'Total Views')

fig_tiktok.update_xaxes(tickfont_size=8)


# In[48]:


def days_passed():
    end = datetime.datetime.fromtimestamp(int(str(data['time_usec'].iloc[0])[:10]))
    begin = datetime.datetime.fromtimestamp(int(str(data['time_usec'].iloc[-1])[:10]))
    return (end - begin).days

day_pass = days_passed()

# Act like its even 7 weeks
day_pass += 1
week_pass = day_pass/7


# In[55]:


num_to_day = {0: 'Sunday', 1:'Monday', 2:'Tuesday', 3:'Wednesday', 4:'Thursday', 5:'Friday', 6: 'Saturday'}
def get_week_data(df):
    week_of_day_data = df['weekday'].value_counts()/week_pass
    week_of_day_data.sort_index(inplace = True)
    week_of_day_data.rename(index = num_to_day, inplace = True)
    return week_of_day_data


# In[59]:


# Load Data
df = px.data.tips()

# Build App
app = JupyterDash(__name__)
server = app.server
app.layout = html.Div([
    html.H1("Time Waster Analysis"),
    html.P('Use the tool below to identify the types of internet usage that you consider to be wasteful. Once you hover over a group, the terms that \
            make that group will appear on the right. Groups that are closer together are more similar. Each axis represents a certain type of internet usage.'),
    html.Iframe(src= 'assets/lda.html', style={"height": "870px", "width": "100%"}),
    

    html.H1('Select The Groups That You Consider A Waste of Time'),
    html.P('Input all groups you find to be wasteful in the dropdown below.'),
    
    html.Label([
                dcc.Dropdown(options = list(range(1,11)),
                id="time_waster_id",
                value = [19],
                multi=True
    )]),

        
    html.Div(children = [
        dcc.Graph(id = 'graph', style={'display': 'inline-block'}),
        dcc.Graph(id = 'week', style={'display': 'inline-block'})
    ]),
    

    html.Img(src='assets/wc_image4.png', style = {'width':'95%', "border":"2px black solid"}),     
    
    html.H1('Breakdown of Most Consumed'),
    html.P('These are the 10 most watched Youtube and Tiktok creators and tags'),

    html.Div(children = [
        dcc.Graph(id = 'youtube', figure = fig_youtube, style={'display': 'inline-block'}),
        dcc.Graph(id = 'tiktok', figure = fig_tiktok, style={'display': 'inline-block'}),
    ]),
    
    html.H1('What You Can Do Today?'),
    html.P('By using this tool you can identify times in which your wasteful usage increases and implement strategies to fill that time with some \
    other activity. In addition by knowing the searches that you waste your time with most, you can increase your awareness every time you find yourself \
    searching for that.'),
    html.P('Here are some helpful websites for further information.'),
    html.P('1. https://www.marksdailyapple.com/13-ways-to-spend-less-time-online-and-reclaim-your-real-life'),
    html.P('2. https://www.breobox.com/blogs/news/ways-spend-less-time-online'),
    html.P('3. https://bookriot.com/how-to-read-more-and-internet-less-when-you-have-no-self-control')

])

# Define callback to update graph
@app.callback(
    Output('graph', 'figure'),
    [Input("time_waster_id", "value")]
)

def update_figure(waste_idx):
    waste_idx = [w - 1 for w in waste_idx]
    data['date_hour'] = data['date_hour'].astype(int)
    dta_by_hour_total = pd.DataFrame(round(data.groupby('date_hour').count()['url']/day_pass, 1))

    df_by_waste = data[data['groups'].isin(waste_idx)]
    dta_by_hour_waste = pd.DataFrame(round(df_by_waste.groupby('date_hour').count()['url']/day_pass, 1))

    fig = px.bar(dta_by_hour_total, x = dta_by_hour_total.index, y = 'url',
                       title="Average Internet Usage Throughout The Day <br><sup> Usage Peaks Around Noon</sup>",
                       labels= {"date_hour": 'Time of Day',
                                'url': 'Average Websites Visited'}).update_layout(yaxis_title = 'Average Websites Visited')

    fig.add_trace(go.Bar(x = dta_by_hour_waste.index, y = dta_by_hour_waste['url']))
    fig.update_layout(
        barmode="overlay",
        bargap=0.1,
        xaxis = dict(tickmode = 'array',
                     tickvals = [0, 5, 10, 15, 20],
                     ticktext = ['0:00', '5:00', '10:00', '15:00', '20:00']
                    )
    )

    fig.update_xaxes(tickangle = 45)

    fig.for_each_trace(lambda t: t.update(name = 'Time Wasted',
                                         )
                      )
    
    return fig

@app.callback(
    Output('week', 'figure'),
    [Input("time_waster_id", "value")]
)

def update_week_figure(waste_idx):
    waste_idx = [w - 1 for w in waste_idx]
    data['date_hour'] = data['date_hour'].astype(int)
    df_by_waste = data[data['groups'].isin(waste_idx)]
    
    week_of_day_data = get_week_data(data)
    waste_data = get_week_data(df_by_waste)
    
    week_graph = px.line(week_of_day_data, x = week_of_day_data.index, y = week_of_day_data.values,
                       title="Internet Usage By Day of the Week <br><sup> Usage Peaks on Tuesday</sup>",
                       labels= {"index": 'Day',
                                'y': 'Average Websites Visited'}).update_layout(yaxis_title = 'Average Websites Visited')

    week_graph.add_scatter(x = waste_data.index, y = waste_data.values)
    week_graph.for_each_trace(lambda t: t.update(name = 'Time Wasted',
                                     )
                  )
    return week_graph
    
# Run app and display result inline in the notebook
app.run_server(port=9100)

