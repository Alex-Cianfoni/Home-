class Dog:
  def __init__(self, name, age):
    self.name = name
    self.age = age

class Employee:
    def __init__(self, name, idNumber, department):
        self.name = name
        self.idNumber = idNumber
        self.department = department
        
class Cake:
   def __init__(self, flavor, frosting):
        self.flavor = flavor
        self.frosting = frosting


def main():
    #fill this one out with a dog's name and age.. can be your dog, friend's dog, etc
    newDog = Dog("sandy",13)
    print(newDog.name, newDog.age)
    
    #and what about a new employee
    newEmployee =Employee("tyler",2313213,23)
    #how would we print out each of the variables from newEmployee?
    print(newEmployee.name,newEmployee.idNumber,newEmployee.department)
    
    #now create and print out a cake you make
    newCake= Cake("choc","can")
    print(newCake.flavor,newCake.frosting)

    
    #and now create another cake and print it out
    newCake1= Cake("choc","marker")
    print(newCake1.flavor,newCake1.frosting)
main()
