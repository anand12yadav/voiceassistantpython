# google calendar api imports
from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import os
import time
import playsound
import speech_recognition as sr
import pyttsx3
import pytz
import subprocess



SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

DAYS=["monday","tuesday","wednesday","friday","saturday","sunday"]
MONTHS=['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']
DAY_EXTENTIONS=["rd",'th','st','nd']

def speak(text):
    engine=pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

#this was using google gTTS wich was bit slow so we oved to use pyttsx3 (refer above code)
'''
#this function takes text and convert it to speech using gTTS and will store the text to voice in mp3 format in filename variable.
# we will use playsound to let the laptop speaker give the output using speakers
# we have given "Hello" as text input it is converted to mp3 and gives the output hello in human voice.
def speak(text):
    tts=gTTS(text=text,lang="en")
    filename="voice.mp3"
    tts.save(filename)
    playsound.playsound(filename)
'''
def get_audio():
    r=sr.Recognizer()
    with sr.Microphone() as source:
        audio=r.listen(source)
        said=""

        try:
            said=r.recognize_google(audio)
            print(said)
        except Exception as e:
            print("Exception " + str(e))
    return said.lower()
'''
speak("Hello")
get_audio()

text= get_audio()
if "hello" in text:
    speak("hello, how are you ?")

if "What is your name" in text:
    speak("My name is helping bot ?")
'''

# this method helps to validate you from the credentails present in credentials.json so that we dont have to signin 
# again and again for the google calendar api.
# it will create a pickle file and store all the credentials so we dont have to signin again.

def authenticate_google():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            

    service = build('calendar', 'v3', credentials=creds)
    return service


# Call the Calendar API
# n is the number of events we want from the calendar , service is whhat we get from autheticate_google function
# changing n to day (making a custom function accordinr to  our need)
def get_events(day,service):
    date=datetime.datetime.combine(day,datetime.datetime.min.time()) # taking the minimum time of a day i.e monday ->12.01 am
    end_date=datetime.datetime.combine(day,datetime.datetime.max.time()) # taking maximum time of the day i.e monday-> 11.59 pm
    utc=pytz.UTC #helps to give current utc time zone
    date=date.astimezone(utc)
    end_date=date.astimezone(utc)


    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(),timeMax=end_date.isoformat(), singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('No upcoming events found.')
    else:
        speak(f"you have {len(events)} events on this day")

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary']) #2019-11-05T10:00:00-05:00
            start_time=str(start.split("T")[1].spit("-")[0]) #2019-11-05T10:00:00-05:00 its splitted based on "T" and then "-"
            if int(start_time.split(":")[0])<12:
                start_time=start_time + "am"
            else:
                start_time=str(int(start.spit(":")[0])-12) + start_time.split(":")[1]
                start_time=start_time + "pm"
            
            speak(event["summary"]+ "at" + start_time)


# getting the current date so that we can ask the bot about future date events based on current date
def get_date(text):
    text=text.lower()
    today=datetime.date.today()

    # if the input text is "today" we will return today's date

    if text.count("today")>0: # 0 means theres no word "today" in the text
        return today
    
    # -1 means not present or not defined in the line when the user ask for the events through speech "whats tommorrow" so here there is no day,week ,month so it will be -1
    day=-1
    day_of_week=-1
    month=-1
    year=today.year

    for word in text.split():
        if word in MONTHS:
            month=MONTHS.index(word)+1  # suppose if the text is "whats planned on september 9th", so here we will take september from the text line and find in MONTHS list as the index is 8 for sep in list but sep is 9th month in real we add +1 
        elif word in DAYS:
            day_of_week=DAYS.index(word)
        elif word.isdigit():
            day=int(word)
        else:
            for ext in DAY_EXTENTIONS:
                found=word.find(ext)
                if found >0:
                    try:
                        day=int(word[:found]) # if its is 9th -> 9,th 9 at 0 index and th at 1 index
                    except:
                        pass
    
    # here if the user asks abou the events from next year and our calendar is of current year then we will have to move to next year 
    # "what is on september 9th" but current month is october so it means it is asking about next year's september
    if month < today.month and month != -1:
        year=year+1

    # suppose today is 6th but the user is asking "what is on 1st" which means he might be asking about next month's 1st date
    # as in the text the month is not defined so we have taken -1 in the if condition
    if day<today.day and month==-1 and day!=-1:
        month=month+1

    # suppose the user ask as "what is on momday",here there is no month and no day defined so in if condition it is -1
    # now we will find the exact day through the day_of_week
    if month==-1 and day==-1 and day_of_week!=-1:
        current_day_of_week=today.weekday() #0->monday --- 6->sunday
        dif=day_of_week-current_day_of_week # will provide the diff between the day asked by the user to the current day 

        if dif<0:
            dif += 7
            if text.count("next")>=1:
                dif +=7
    
        return today+ datetime.timedelta(dif) # delta will help to figure it out whether we have to go to next week using dif
    if month ==-1 or day==-1:
        return None
    return datetime.datetime(month=month,day=day,year=year)

def note(text):
    date=datetime.datetime.now()
    file_name=str(date).replace(":","-")+ "-note.txt"
    with open(file_name,"w") as f:
        f.write(text)
    subprocess.Popen(["notepad.exe",file_name])

#note("hey there")

'''
service=authenticate_google()
get_events(2,service)
'''
WAKE = "hey anand"
SERVICE=authenticate_google()
#text=get_audio()

# putting everything in while loop so that it keeps running in background and perform a task after saying "hey anand" just like hey google

while True:
    print("Listening..")
    text=get_audio()
    if text.count(WAKE)>0:
        speak("I am ready")
        text=get_audio()
        # these are few keywords if present in speech then only we will call our get_events method (you can add as many you want in the list i have added few)
        CALENDAR_STRS=["what do i have","do i have plans","am i busy"]
        for phrase in CALENDAR_STRS:
            if phrase in text:
                date=get_date(text)
                if date:
                    get_events(date,SERVICE)
                else:
                    speak("Sorry I dont understand")

        NOTE_STRS=["make a note","write this down","remember this"]
        for phrase in NOTE_STRS:
            if phrase in text:
                speak("What would you like me to write down ?")
                note_text=get_audio()
                note(note_text)
                speak("I've made a note of that.")
