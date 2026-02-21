# -1 - less, 1 - more, 0 - equal
def compareDates(date1, date2):
    if date1.year < date2.year:
        return -1
    elif date1.year > date2.year:
        return 1
    elif date1.month < date2.month:
        return -1
    elif date1.month > date2.month:
        return 1
    elif date1.day < date2.day:
        return -1
    elif date1.day > date2.day:
        return 1
    else:
        return 0

# -1 - less, 1 - more, 0 - equal
def compareFio(fio1, fio2):
    if fio1.surname < fio2.surname:
        return -1
    elif fio1.surname > fio2.surname:
        return 1
    elif fio1.name < fio2.name:
        return -1
    elif fio1.name > fio2.name:
        return 1
    elif fio1.patronymic < fio2.patronymic:
        return -1
    elif fio1.patronymic > fio2.patronymic:
        return 1
    else:
        return 0

def changePlaces(p1, p2):
    if p1 != p2:
        tempDate = p1.date
        tempFio = p1.fio
        tempIndex = p1.index
        p1.date = p2.date
        p1.fio = p2.fio
        p1.index = p2.index
        p2.date = tempDate
        p2.fio = tempFio
        p2.index = tempIndex

def isEven(num):
    if num % 2 == 0:
        return True
    else:
        return False
