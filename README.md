# How to use
## create timesheet for the current whole year
1. fill the profile.yaml with your personal data
2. run the script like "python create_timesheet.py"

## create timesheet for another time range
1. fill the profile.yaml with your personal data
2. run the script with the start and end date as DD.MM.YYYY arguments like: "python create_timesheet.py 10.04.2021 22.10.2021"

## create timesheets for different coaches
1. create multiple .yaml files one for each coach
2. run the script for each of the estimated coaches .yaml file as argument like "python create_timesheet.py maxmustermann.yaml" and "python create_timesheet.py karlkaron.yaml"

## combine different coaches and time ranges
1. create multiple .yaml files one for each coach
2. run the script for each of the estimated coaches .yaml file and start, end date as argument like "python create_timesheet.py maxmustermann.yaml 10.04.2021 22.10.2021"