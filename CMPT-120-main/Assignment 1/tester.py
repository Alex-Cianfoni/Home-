class student:
    def __init__(self, name, studentid, year, major, gpa):
        self.name = name
        self.studentid = studentid
        self.year = year
        self.major = major
        self.gpa = gpa


def main():
    student1 = student("jake", 2028323, 2026, "cyber", 2.3)
    student2 = student("Reberto", 5213232, 2026, "cyber", 1.7)
    student3 = student("tyler", 232323, 2026, "cyber", 2.8)
    print(student2.name)
    print(student1.gpa)


main()
