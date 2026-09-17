def Машин_оруулах():
    номер = input("Улсын дугаар: ")
    цаг = input("Орсон цаг: ")
    
    with open("parking.txt", "a", encoding="utf-8") as file:
        file.write(f'{номер} - {цаг}\n')
        
        return "<<Амжилттай нэвтэрлээ>>"

def Машин_гарах():
    номер = input("Улсын дугаар: ")
    found = False
    
    with open("parking.txt", "r", encoding="utf-8") as file:
        for номерцаг in file:
            if номер in номерцаг:
                print("===== Машин олдлоо:", номерцаг)
                found = True
                    
    if found == False:
        print("===== Машин олдсонгүй")            
        
def Машин_устгах():
    Жагсаалт = []
    номер = input("Улсын дугаар: ")
    
    with open("parking.txt", "r", encoding="utf-8") as file:
        for номерцаг in file:
            if номер not in номерцаг:
                Жагсаалт.append(номерцаг)  
                
    with open("parking.txt", "w", encoding="utf-8") as file:
        for номерцаг in Жагсаалт:
            file.write(номерцаг)
                   
    return ("===== Машин устлаа")     
        
def Машинууд_харах():
    
    with open("parking.txt", "r", encoding="utf-8") as file:
        агуулга = file.read()
        
    return агуулга
      
def Нийт_машин():
    машинууд = []
    
    with open("parking.txt", "r", encoding="utf-8") as file:
        for номерцаг in file:
            машинууд.append(номерцаг)
    
    return len(машинууд) 
       
       
        
while True:
    print("\n1. Машин_оруулах")
    print("2. Машин_гарах")
    print("3. Машин_устгах")
    print("4. Машинууд_харах")
    print("5. Нийт_машин")
    print("6. Exit")
    
    choice = input("Сонголт: ")
    
    if choice == "1":
        print(Машин_оруулах())
        
    elif choice == "2":
         print(Машин_гарах())
        
    elif choice == "3":
            print(Машин_устгах())
            
    elif choice == "4":
            print(Машинууд_харах())  
            
    elif choice == "5":
            print(Нийт_машин())     

    elif choice == "6":
        break