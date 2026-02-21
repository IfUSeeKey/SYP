struct Tdate {
	int day;
	int month;
	int year;
};

struct Tfio {
	string surname;
	string name;
	string patronymic;
};

struct TUzel {
	Tdate date;
	Tfio fio;
	int index;
	listNode* puzel;
	listNode* suzel;
};

struct Address {
    string street;
    string city;
    string zipCode;
};

struct Employee_info {
    string name;
    string position;
    double salary;
    Address address;
};

struct Person_info {
    Tfio fio;
    int age;
    double height;
    Address address;
    Tdate birthDate;
    string birthplace;
};

struct Point_on_map {
    double x;
    double y;
};

struct Student_charact {
    int id;
    string firstName;
    string lastName;
    double averageGrade;
};
