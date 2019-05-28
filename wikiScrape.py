#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 22 17:21:49 2019

@author: tk
"""
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from sportsreference.mlb.teams import Teams
from sportsreference.mlb.schedule import Schedule
import datetime
import json
import requests

def getTheWeather(code):
    if re.search('2\d\d',str(code)):
        return "T-Storms"
    elif re.search('5\d\d',str(code)):
        return "Rain"
    elif re.search('3\d\d',str(code)):
        return "Drizzle"
    elif re.search('6\d\d',str(code)):
        return "Snow"
    elif re.search('7\d\d',str(code)):
        if str(code)==781:
            return "Tornado Warning"
        else:
            return "Rain"
    elif re.search('8\d\d',str(code)):
        if str(code)==800:
            return "Clear skies"
        else:
            return "Partly Cloudy"

#the wiki tags for each city in string form
cTags=['New_York_City','Los_Angeles','Chicago','Houston','Philadelphia','Phoenix,_Arizona','San_Antonio','San_Diego','Dallas','San_Jose,_California','Austin,_Texas','Jacksonville,_Florida','Fort_Worth,_Texas','Columbus,_Ohio','San_Francisco','Charlotte,_North_Carolina','Indianapolis','Seattle','Denver','Washington,_D.C.']
#City Name, str
Names=[]

#City State, str
States=[]

#Population data, num as an str
Pops=[]

#Total city Area, str with numbers and units
Area=[]

#Demonyms i.e. New Yorker, Dallasite, Philadelphian, etc., str
Demonyms=[]
#Time zones, str
TZ=[]

#Latitudes and Longitudes
Lat=[]
Long=[]

#nested list of colleges featured on the wikipedia page
featColl=[]
collPattern="((University)\s(of)\s([A-Z]\w+\W)+)|(([A-Z](\w+)\s)+(University))|(([A-Z](\w+)\s)+(College))"

#nested list of nearby airports
airPort=[]

#nested list of MLB teams
baseBall=[]
whosePlaying=[]
weather=[]
mlbTeams=""
mlbAbbr={"Team":"Abbr"}

#check for mlb team, if you find a match, look at the schedule to see if there is a game td
td=datetime.datetime.now()

#Weekday, Mon date
wD=td.strftime("%A")
mon=td.strftime("%b")
d=td.strftime("%d") 
today=wD+", "+mon+" "+d


for n,team in enumerate(Teams()):
    if n==0:
        mlbTeams+="("+team.name+")"
    else:
        mlbTeams+="|("+team.name+")"
    mlbAbbr[team.name]=team.abbreviation

#loop through the wiki tags list and parse each wikipedia page for scraping
for count,cTag in enumerate(cTags):
    qpage="https://en.wikipedia.org/wiki/"+cTag
    print(qpage)
    page=urlopen(qpage)
    soup=BeautifulSoup(page, 'html.parser')
    #general info table for cities
    info=soup.find('table',{"class":"infobox geography vcard"})
    #main contents
    conts=soup.find('div',{"id":"mw-content-text"})
    pgs=conts.findAll('p')
    # Note: some names have tags to citations "Japan[1]" clean them up
    table_rows=info.findAll('tr')

    

    #loops through info table for information
    for i,tr in enumerate(table_rows):
        #if first row of table store the city name
        if i==0:
            name=re.split('\,',tr.text)
            Names.append(name[0])
            #The capitol doesnt have a state
            if tr.text=='Washington, D.C.':
                States.append(name[1])
        #if second row of the table (where its says "City"), skip
        elif i==1:
            continue
        #for the rest of the table:
        else:
            #checks for (label   Value) rows
            if tr.th in tr.contents:
                th=tr.th
                td=tr.td
                if re.search('\AState\Z',th.text): 
                    States.append(td.text.replace(u'\xa0', u' '))
                elif re.search('\APopulation',th.text):
                    popu=re.search('((\d+)\,)+(\d+)*',tr.next_sibling.td.text)
                    Pops.append(popu.group()) 
                elif re.search('^Area\[\d+\]$|^Area$',th.text):
                    Area.append(tr.next_sibling.td.text.replace(u'\xa0', u' '))
                #if the header is Demonym        
                elif re.search('Demonym',th.text):
                    demo=td.text
                    Demonyms.append(re.sub('\[\d\]','',demo))
                elif re.search('Time zone',th.text):
                    TZ.append(td.text)
            elif re.search('\ACoordinates',tr.td.text):
                la=tr.find('span',{"class":"latitude"})
                lo=tr.find('span',{"class":"longitude"})
                Lat.append(la.text)
                Long.append(lo.text)
    
    #finding all mentioned colleges in the wikipedia page
    collLinks=conts.findAll('a',string=re.compile(collPattern),limit=3)
    colleges=[]
    for link in collLinks:
        if re.search('(\d+)',link.text):
            continue
        else:
            colleges.append(link.text)
    #removing duplicates
    colleges=list(dict.fromkeys(colleges))
    featColl.append(colleges)
    
    #finding all mentioned airports
    apLinks=conts.findAll('a',title=re.compile("(Airport)"))
    airports=[]
    for apLink in apLinks:
        airports.append(apLink.text)
    #removing duplicates Note: The same airport can be called by different ways, havent been able to filter those out yet
    airports=list(dict.fromkeys(airports))
    airPort.append(airports)      

    #use open weather api to write "should I bring an umbrella" 
    genLat=re.findall('\d+',la.text)[0]
    genLon=re.findall('\d+',lo.text)[0]
    weatherURL='http://api.openweathermap.org/data/2.5/weather?lat='+genLat+'&lon='+genLon+'&appid=0348f0e49306d4b170d96f37631f3863'
    wPage=requests.get(weatherURL)
    wData=wPage.json()
    wCode=wData['weather'][0]['id']
    weather.append(getTheWeather(wCode))
    
    #use sportsreference api to list MLB teams and schedules for each city
    tLinks=conts.findAll('a',title=re.compile(mlbTeams))
    teams=[]
    isPlaying=[]
    sPattern1="^("+name[0]+")"
    if len(name)>1:
        sPattern2="^("+name[1]+")"
        for tLink in tLinks:
            tLinkText=tLink.text
            if re.search(sPattern1,tLinkText):
                teams.append(tLinkText)
            elif re.search(sPattern2,tLinkText):
                teams.append(tLinkText)
    else:
        for tLink in tLinks:
            tLinkText=tLink.text
            if re.search(sPattern1,tLinkText):
                teams.append(tLinkText)
        
    #removing duplicates
    teams=list(dict.fromkeys(teams))
    baseBall.append(teams)
   

    #loop through each baseball team, if any, and see if they are playing at home today
    if len(teams)>0:
        for team in teams:
            sch=Schedule(mlbAbbr[team])
            for game in sch:
                if game.date==today and game.location=='Home':
                    isPlaying.append(team)
    whosePlaying.append(isPlaying)
    
#creating the data frame
df=pd.DataFrame(list(zip(Names,States,Lat,Long,TZ,Pops,Area,Demonyms,featColl,baseBall,whosePlaying,weather)),columns=['City Name','State','Latitude','Longitude','Time Zone','Population','Area','Demonyms','Notable Educational Insitiutiions','Baseball Team(s)','What team is playing at home today','the weather'])

#creating the csv file
csv_file = df.to_csv ('WikiScraperProject.csv', index = None, header=True) 
        
    
   
    