import sys
import datetime
import datetimerange
import yaml
import json
import requests
from reportlab.pdfgen import canvas
import imghdr
from reportlab.lib.units import mm

profile_path = 'profile.yaml'
fileName = 'Uebungsleiterabrechung.pdf'
document_title = 'timesheet'
organisation_title = 'Sportgemeinschaft Aumund-Vegesack e.V.'
group_title = 'Abteilung Judo Ju-Jutsu Jiu-Jitsu'
sub_title = 'Abrechnung für Trainer, Übungsleiter und Ko-Trainer'
trainer_name = {'first_name': 'Max', 'family_name': 'Mustermann'}
trainer_adress = {'street': 'Hauptstraße 1',
                  'zip-code': '12345', 'city': 'Bremen'}
work_location = 'Turnhallenstr.'
trainer_bank = {'iban': 'DE012345678', 'bank_name': '',
                'bic': '', 'owner_name': 'Max Mustermann'}
hours_per_day = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
start_date = ''  # 'YYYY-MM-DDT00:00:00+0900' format
end_date = ''  # 'YYYY-MM-DDT00:00:00+0900' format
additional_entries = []


def importProfile():
    global organisation_title
    global group_title
    global sub_title
    global trainer_name
    global trainer_adress
    global work_location
    global trainer_bank
    global hours_per_day
    global fileName
    global additional_entries
    profile = None

    with open(profile_path, "r", encoding='utf8') as stream:
        try:
            profile = yaml.safe_load(stream)

            organisation_title = profile['organisation_title']
            group_title = profile['group_title']
            sub_title = profile['sub_title']
            trainer_name = {
                'first_name': profile['vorname'], 'family_name': profile['nachname']}
            trainer_adress = profile['trainer_adresse']
            work_location = profile['work_location']
            trainer_bank = profile['bank']
            hours_per_day = profile['trainingsstunden']
            fileName = str(trainer_name['family_name'])+'_'+fileName
            if 'additional_times' in profile:
                additional_entries = profile['additional_times']
        except yaml.YAMLError as exc:
            print(exc)

# returns holidays as list od date ranges
# hardcoded for school holidays + state holidaysin Bremen


def tryToGetHolidays():
    holidays = []  # list of ranges

    # access shool holidays
    # TODO hardoded for country hb
    response = requests.get(
        'https://ferien-api.de/api/v1/holidays/HB/'+str(start_date[:4]))
    if response.status_code == 200:
        cont = json.loads(response.content.decode('utf-8'))
        print('-------------- found following holidays: --------------')
        for d in cont:
            range = datetimerange.DateTimeRange(d['start'], d['end'])
            holidays.append(range)
            print(d['name'] + '\n' + str(range))
    else:
        raise ValueError(
            "Error could not access holiday data1. Make sure you have access to the internet")

    # access holidays
    response = requests.get(
        'https://get.api-feiertage.de/?years='+str(start_date[:4]))
    if response.status_code == 200:
        cont = json.loads(response.content.decode('utf-8'))
        if cont['status'] != 'success':
            raise ValueError(
                "Error something went wrong while access holidays2")
        for d in cont['feiertage']:
            if str(d['hb']) == '1':  # TODO hardoded for country hb
                range = datetimerange.DateTimeRange(dateFromStr(d['date']), dateFromStr(
                    d['date']))  # TODO checki f this works as expected
                holidays.append(range)
                print(d['fname'] + '\n' + str(range))
    else:
        raise ValueError(
            "Error could not access holiday data2. Make sure you have access to the internet")

    return holidays

# returns a list of days in given range which are are not the holidays


def cleanedDays(all_days_range):
    # TODO maybe we need to get Feiertage from anoper api?
    #all_days = datetime.datetime.today()
    cleaned_days = []
    holidays = tryToGetHolidays()

    current_day = all_days_range.start_datetime
    time_delta = datetime.timedelta(days=1)
    while current_day < all_days_range.end_datetime:
        add_current = True
        # check all holidays
        for h in holidays:
            if current_day.replace(tzinfo=datetime.timezone.utc) >= h.start_datetime.replace(tzinfo=datetime.timezone.utc) \
                and current_day.replace(tzinfo=datetime.timezone.utc) <= h.end_datetime.replace(tzinfo=datetime.timezone.utc):
                add_current = False
                break
        if add_current:
            cleaned_days.append(current_day)
        current_day += time_delta

    return cleaned_days


def allDaysRange():
    global start_date
    global end_date
    if start_date == '' or end_date == '':
        print('WARNING: using this complete year as date range')
        yyyy = str(datetime.datetime.today().year)
        return datetimerange.DateTimeRange(dateFromStr('01.01.'+yyyy), dateFromStr('30.12.'+yyyy))
    else:
        return datetimerange.DateTimeRange(start_date, end_date)


def dateStr(date):
    day = str(date.day) if len(str(date.day)) > 1 else '0'+str(date.day)
    month = str(date.month) if len(
        str(date.month)) > 1 else '0'+str(date.month)
    return day+'.'+month+'.'+str(date.year)

###
# converts strings like
### 'DD.MM.YYYY' or 'YYYY-MM-DD'
# to time object strings like 'YYYY-MM-DDT00:00:00+0900'
###
def dateFromStr(date_str):
    d = 'T00:00:00+0900'
    d_arr = date_str.split('.')
    if len(d_arr) == 3 and len(d_arr[0]) == 2 and len(d_arr[1]) == 2 and len(d_arr[2]) == 4:
        return d_arr[2]+'-'+d_arr[1]+'-'+d_arr[0]+d
    d_arr = date_str.split('-')
    if len(d_arr) == 3 and len(d_arr[0]) == 4 and len(d_arr[1]) == 2 or len(d_arr[2]) == 2:
        return d_arr[0]+'-'+d_arr[1]+'-'+d_arr[2]+d
    else:
        raise ValueError("Error could not read "+date_str +
                         ' make sure you wrote dates in DD.MM.YYYY or YYYY-MM-DD format')


###
# creates objects from global additional_entries
###
def additionalDays():
    global additional_entries
    date_format = '%Y-%m-%dT%H:%M:%S+0900'
    
    result = []
    
    for e in additional_entries:
        new_entry=[datetime.datetime.strptime(dateFromStr(e['date']), date_format), e['duration']]
        print('new entry:' + str(new_entry))
        result.append(new_entry)
        
    return result
     


# returns [training times, hours] (if >0 hours)
# this list should be ready to print
def trainingTimes():
    trainings = []
    all_days = allDaysRange()
    cleaned_days = cleanedDays(all_days)

    for d in cleaned_days:
        if hours_per_day[d.weekday()] > 0:
            trainings.append([d, hours_per_day[d.weekday()]])

    trainings = trainings + additionalDays()
    #print(trainings)

    return trainings


def drawHeader(pdf):
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(300, 770, organisation_title)
    pdf.drawCentredString(300, 750, group_title)

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(300, 730, sub_title)

    pdf.line(75, 720, 500, 720)


def drawInfos(pdf):
    pdf.setFont("Helvetica", 10)
    pdf.drawString(75, 700, "Name:")
    pdf.drawString(300, 700, " Vorname:")
    pdf.drawString(73, 685, " Adresse:")
    pdf.drawString(300, 685, " Turnhalle:")

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(130, 700, trainer_name['family_name'])
    pdf.drawString(370, 700, trainer_name['first_name'])

    pdf.drawString(130, 685, trainer_adress['street'])
    pdf.drawString(130, 670, trainer_adress['zip-code'])
    pdf.drawString(130, 655, trainer_adress['city'])
    pdf.drawString(370, 685, work_location)

# draws a rectangle to the pdf
# offset will be added to the positions


def rectangle(pdf, start_pos, end_pos, offset=[-2., -5.]):
    x_start, y_start = start_pos
    x_end, y_end = end_pos
    offset_x, offset_y = offset
    x_start += offset_x
    x_end += offset_x
    y_start += offset_y
    y_end += offset_y
    pdf.line(x_start, y_start, x_end, y_start)
    pdf.line(x_start, y_start, x_start, y_end)
    pdf.line(x_end, y_end, x_end, y_start)
    pdf.line(x_end, y_end, x_start, y_end)

# draws the data from training_times
# all the timestamps are drawn relative to the start x,y position


def drawTimes(pdf, training_times, start_x=75, start_y=600, row_dist=15, col_dist=90):
    no_max_rows = 25  # start new col after this
    x = 0
    y = 0

    pdf.setFont("Helvetica", 8)
    # pdf.drawCentredString(300, start_y+(2*row_dist),
    #                      'Abzurechnende Übungsstunden (1 Ü-Einheit = 60 Minuten)')

    # first head
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(start_x+x, start_y+row_dist, '    Tag')
    pdf.drawString(start_x+x+(0.7*col_dist), start_y+row_dist, 'Std.')
    rectangle(pdf, [start_x+x, start_y+2*row_dist],
              [start_x+x+(col_dist), start_y])

    for e in training_times:
        pdf.setFont("Helvetica", 10)
        #print(dateStr(e[0])+ ": " +str(e[1]))
        pdf.drawString(start_x+x, start_y-y, dateStr(e[0]))
        pdf.drawString(start_x+x+(0.7*col_dist), start_y-y, str(e[1]))
        rectangle(pdf, [start_x+x, start_y-y+(row_dist)],
                  [start_x+x+(col_dist), start_y-y])
        y += row_dist

        # new col
        if y >= row_dist*no_max_rows:
            x += col_dist
            y = 0
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(start_x+x, start_y+row_dist, '    Tag')
            pdf.drawString(start_x+x+(0.7*col_dist),
                           start_y+row_dist, 'Std.')
            rectangle(pdf, [start_x+x, start_y+2*row_dist],
                      [start_x+x+(col_dist), start_y])
    # draw sum
    s = sum([e for _, e in training_times])
    pdf.drawString(start_x+x, start_y-(row_dist*(no_max_rows+1)),
                   'Summe= '+str(s)+' Std.')


def drawPaymentInfo(pdf):
    # bank data
    pdf.setFont("Helvetica", 10)
    pdf.drawString(75, 165, 'BIC:')
    pdf.drawString(75, 150, 'Bankinstitut:')
    pdf.drawString(300, 165, 'IBAN:')
    pdf.drawString(300, 150, 'Kontoinhaber:')
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(145, 165, trainer_bank['bic'])
    pdf.drawString(145, 150, trainer_bank['bank_name'])
    pdf.drawString(375, 165, trainer_bank['iban'])
    pdf.drawString(375, 150, trainer_bank['owner_name'])
    # signature ül
    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        75, 110, trainer_adress['city'] + ', ' + dateStr(datetime.datetime.today()))
    pdf.line(75, 100, 280, 100)
    pdf.setFont("Helvetica", 5)
    pdf.drawString(235, 90, '(Übungsleiter)')
    # signature al
    pdf.setFont("Helvetica", 10)
    pdf.line(300, 100, 500, 100)
    pdf.setFont("Helvetica", 5)
    #pdf.drawString(450, 90, '(Abteilungsleitung)')


def drawSignature(pdf):
    signature = "./unterschrift.png"
    if is_valid_image(signature):
        pdf.drawImage(signature, 62*mm, -62*mm, width=120,
                      preserveAspectRatio=True, mask='auto')


def is_valid_image(filename):
    with open(filename, 'rb') as f:
        return bool(imghdr.what(f))


def main() -> int:
    global profile_path
    global fileName
    global start_date
    global end_date

    # handle parameters
    if len(sys.argv) > 3:
        profile_path = str(sys.argv[1])
        start_date = dateFromStr(sys.argv[2])
        end_date = dateFromStr(sys.argv[3])
    elif len(sys.argv) > 2:
        start_date = dateFromStr(sys.argv[1])
        end_date = dateFromStr(sys.argv[2])
    elif len(sys.argv) > 1:
        profile_path = str(sys.argv[1])

    importProfile()

    # calculation
    training_times = trainingTimes()

    # creating a pdf object
    pdf = canvas.Canvas(fileName)
    pdf.setTitle(document_title)

    drawHeader(pdf)
    drawInfos(pdf)
    drawTimes(pdf, training_times)
    drawPaymentInfo(pdf)
    drawSignature(pdf)

    pdf.save()
    return 0


if __name__ == '__main__':
    sys.exit(main())
