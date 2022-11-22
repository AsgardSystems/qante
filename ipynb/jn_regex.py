MONTHS = ['january','february','march','april', 'may', 'june','july','august',\
         'september','october','november','december']
MONTHS_ABR = [m[:3] for m in MONTHS]
DAYS =['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
DAYS_ABR = [d[:3] for d in DAYS]

YEAR = '((19)|(20))?\d{2}'
DAY = '[0-3]?\d'
MONTHn = '(0|1)?\d'
MONTHa = '(('+')|('.join(MONTHS)+')'+'|('+')|('.join(MONTHS_ABR)+'))'
DOW = '(('+')|('.join(DAYS)+')'+'|('+')|('.join(DAYS_ABR)+'))'
DATEnum = '({}[/\-]{}[/\-]{})|({}[/\-]{}[/\-]{})'.format(MONTHn,DAY,YEAR,DAY,MONTHn,YEAR)
DATEalpha = DOW+',? +'+MONTHa+' +'+DAY+',? +'+YEAR
DATE = '({}|{})'.format(DATEnum, DATEalpha)

HR = '[0-2]?\d'
MINSEC = '[0-5]?\d'
GMT = '\(?gmt[-+]{}:{}\)?'.format(HR,MINSEC)
TIME = '{}:{}(:{})? *((am)|(pm))? *({})?'.format( HR, MINSEC, MINSEC, GMT )

EMAIL = '([A-Za-z0-9._%+=-]+@[A-Za-z0-9.-]+(\.[A-Za-z]{2,4}){1,2})'

TXT_FILE = 'bill.txt'
TXT_PATH='./txt/'
PKL_FILE = 'sdge.pkl'
PKL_PATH='./pkl/'
EML_FILE = 'email.txt'
