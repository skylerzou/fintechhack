#proof of concept 
#handcoded by skyler

approval = []
curr = 0
estworking = curr
cont = True
totalapproved = 0
totalreim = 0
#index vals in approvals
indexnum = 0
reqamount = 1
apprstatus = 2
reimamount = 3
reimstatus = 4


#technically bad practice
#could instead pass in the approval array -> do the summing -> return estworking
#but dont want to do that ngl

def recalc ():
    global totalreim, totalapproved, estworking 
    totalreim = sum(item[reimamount] for item in approval if not item[reimstatus]) #sum of outstanding reimbursement
    totalapproved = sum(item[reqamount] for item in approval if item[apprstatus] and not item[reimstatus] and item[reimamount] == 0) #sum of approved items but NOT 
    estworking = curr - totalapproved-totalreim #updating
    
while cont: #kinda excessive but its a little better than a bare while loop

    #prints out your stats and the keybinds
    print(f"\nCurr: {curr}")
    print(f"Working: {estworking}")
    print(f"Commited: {totalapproved+totalreim}\n")
    print("a to add")
    print("q to quit")
    print("v to view/accept requests and pending reimbursement")
    print("p to request reimbursement")
    print("r to request")

    val = input("Enter: ")

    #QUIT CASE
    if val == "q":
        cont = False
        break

    #ADDING CASE
    elif val == "a":
        amount = int(input("Enter amount: "))
        curr += abs(amount)
        estworking = curr - totalapproved-totalreim
        continue

    #REQUESTING CASE
    elif val == "r":
        requested = int(input("Enter amount requested: "))
        #format (index, requested amount, approved status, reimbursement amount, completion status)
        approval.append([len(approval), requested, False, 0, False])
        continue

    #VIEWING/ACCEPTING CASE
    elif val == "v":
        #viewing part
        for i in range(len(approval)):
            print(f"{approval[i]} \n")

        #quit out or acceptance/completion
        print(f"q to exit \n")
        print(f"a to accept \n")
        print(f"c to complete \n")
        viewing = input("Enter: ")

        if viewing == "q":
            continue

        elif viewing == "a":
            num = int(input(f"Approval number: "))
            if approval[num][apprstatus] == True:
                print(f"Already accepted")
                continue
            approval[num][apprstatus] = True
            recalc()
            continue

        elif viewing == "c":
            num = int(input(f"Completed number: "))
            if approval[num][reimstatus] == True:
                print(f"Already completed")
                continue
            if approval[num][apprstatus] == False:
                print(f"You have not been approved")
            approval[num][reimstatus] = True
            curr -= approval[num][reimamount] #removing the reimbursed
            recalc()
            continue

    #requesting reimbursement case
    elif val == "p":
        num = int(input("Approval number: "))
        if num >= len(approval) or num < 0:
            print(f"Invalid number")
            continue
        elif approval[num][apprstatus] == False:
            print(f"You have not been approved")
            continue
        elif approval[num][apprstatus] == True and approval[num][reimstatus] == True:
            print(f"You have been paid back")
            continue
        elif approval[num][apprstatus] == True and approval[num][reimstatus] == False:
            reim = int(input("Reimbursement amount: "))
            approval[num][reimamount] = reim
            recalc()
            continue
    else:
        print(f"Invalid input")

#note: using sum for updating curr and working so i don't need to worry about desyncing and at small scale is still pretty quick
#once an item gets a reimbursement request we no longer want to count that item in total approved