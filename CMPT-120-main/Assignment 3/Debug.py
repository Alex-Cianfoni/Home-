def main():
    
    #Can you print out "Hello" 8 times? I gave you a tiny hint to start...
    name = "Hello"
    for x in range(8):
        print(name)

    #What about as a while loop?
    i = 0
    while (i < 8):
        print("alex")
        i += 1

    #The loop iterations are one behind in a non-programming counting way... how can we fix this?
    count = 0
    while (count < 4):
        print("While loop iteration", count)
        count = count + 1
        
    #Same deal here!
    for x in range(4):
        print("For loop iteration:", x)
     
    #Uh oh I messed up and made an infinite loop... so silly of me!   
    endless = 4    
    while (endless < 5):
        print("I'm stuck in this loop!!!!")
        endless += 1
    
    
    
main()
