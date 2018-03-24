import os
import time
from slackclient import SlackClient
import json
import socket
import csv

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND_GOT = "camelateforstanduptoday"
EXAMPLE_COMMAND_GAVE = "gavechocolates"
EXAMPLE_COMMAND_EXCUSED = "goeasyon"
EXAMPLE_COMMAND_NOTEXCUSED = "immunityoverfor"
EXAMPLE_PUNISHMENT = "havenotyetbroughtchocolates"
# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

count = dict()
isExcused = dict()
def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    names = [word for word in command.split() if word.startswith('<@')]
    name_list=[]
    for name in names:
        ans = slack_client.api_call("users.info",user = name.strip('<').strip('>').strip('@').upper())
        print ans
        name_list.append(ans['user']['profile']['first_name']+' '+ans['user']['profile']['last_name'])

    command = command.replace(" ", "")

    result = ""
    response = "Sorry. I do not understand..!!"
    command = command.lower()
    print len(command)
    if(len(command) == 0):
        response = "Just a reminder...\n"
        for name in count:
            result = result + name + " " +'`' + str(count[name])  +'`' + " "+ '\n'
        for name in isExcused:
            response += "\nImmunity for ";
            for name in isExcused:
                response += (name + " ")
            response = response + '\n'
    if command.startswith(EXAMPLE_COMMAND_EXCUSED):
        response = "Yes sir, I will"
        slack_client.api_call("chat.postMessage", channel=channel,text=response, as_user=True)
        for name in name_list:
            isExcused[name] = True;
        return;
    if command.endswith(EXAMPLE_COMMAND_EXCUSED):
        response = "Haha..!! Let's double their count.."
        slack_client.api_call("chat.postMessage", channel=channel,text=response, as_user=True)
        for name in name_list:
            if name in count:
                count[name] = count[name] * 2;
        return;
    if command.startswith(EXAMPLE_COMMAND_NOTEXCUSED):
        response = "Your immunity is over!"
        slack_client.api_call("chat.postMessage", channel=channel,text=response, as_user=True)
        for name in name_list:
            del isExcused[name]
        return;
    
    if command.endswith(EXAMPLE_COMMAND_GOT):
        print name_list
        for name in name_list:
            if name in isExcused:
                continue
            if name in count:
                count[name] = count[name] + 1
            else:
                count[name] = 1
        response = ' '.join(name_list)
        response += ( " .....Be early next time!")
        
        for name in count:
            result = result + name + " " +'`' + str(count[name])  +'`' + " "+ '\n'
        for name in isExcused:
            response += "\nImmunity for ";
            for name in isExcused:
                response += (name + " ")
            response = response + '\n'
    else:
        if command.endswith(EXAMPLE_COMMAND_GAVE):
            for name in name_list:
                count[name] = 0
            response = ' '.join(name_list)
            response += ( " Those chocolates were delicious. Thanks..!")
            for name in count:
                result = result + name + " " +'`' + str(count[name])  +'`' + " "+ '\n'

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)
    if len(result):
        slack_client.api_call("chat.postMessage", channel=channel,text=result, as_user=True)
    with open('chocolate_counter.csv', 'wb') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in count.items():
            writer.writerow([key, value])

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000.
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:

            # Read from csv to dictionary
            with open('chocolate_counter.csv', 'rb') as f:
                reader = csv.reader(f)
                for row in reader:
                    count[row[0]] = row[1]

            command, channel = parse_slack_output(slack_client.rtm_read())
            if channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
