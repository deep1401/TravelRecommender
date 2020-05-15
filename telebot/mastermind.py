def get_response(msg):
    msg = msg.lower()
    if 'location' and 'days' not in msg:
        return 'Please enter your desired destination and number of days in the following format: \n ' \
               'location:<location> days:<number of days>'
    else:
        start = msg.find("location:") + len("location:")
        end = msg.find("days")
        substring = msg[start:end]
        start1 = msg.find("days:") + len("days:")
        substring1 = msg[start1:]
        return {'location': substring.strip(), 'days': substring1.strip()}
