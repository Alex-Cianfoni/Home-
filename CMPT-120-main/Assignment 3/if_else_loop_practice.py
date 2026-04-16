#first of all, breathe
#don't let this intimidate you. break it down a part at a time. You've done all of these separately and now we're just combining them.
'''
Instructions: Create a list with at least 8 numbers, and make sure you have a raandom dispersement between 0-50
Create a loop (which loop would be best given we know how long we're going [the length of the list]?) that runs through the entire list
Inside of your loop, have an if/elif/else that checks AT EACH INDEX OF THE LIST:
if the number is greater than 35: print ("greater than 35")
elif the number is between 20-35: print ("between 20-35")
elif the number is between 5-20: print ("between 5 and 20")
else (the number is less than 5)
'''

def main():
number = [21, 25, 44, 16, 14, 9, 14, 5, 37]
#if the number is greater then 20 and less then 35 then print between 20 and 35
if number >20 and number < 35:
    print("between 20 and 35")
    #if the number is larger then 5 but less then 20 print between 5 and 20
if number >5 and number < 20:
    print("between 5 and 20")
    # if the number is bigger then 25 print greater then 35 duh
if number <35:
    print("greater then 35 duh")
else number >5:
 #if else print less then 5 

    
main()
