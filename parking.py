from datetime import datetime
from pathlib import Path


PARKING_FILE = Path(__file__).resolve().parent.parent / "parking.txt"


def Машин_оруулах():
    номер = input("Улсын дугаар: ")
    цаг = datetime.now().strftime("%H:%M")
    
    with open(PARKING_FILE, "a", encoding="utf-8") as file:
        file.write(f'{номер} - {цаг}\n')
        
        return "<<Амжилттай нэвтэрлээ>>"

def Машин_гарах():
    номер = input("Улсын дугаар: ")
    гарсан_цаг = input("Гарсан цаг: ")
    found = False
    
    Жагсаалт = []
    
                 
    with open(PARKING_FILE, "r", encoding="utf-8") as file:
        for номерцаг in file:
            if номер in номерцаг:
                parts = номерцаг.strip().split(" - ")
                орсон_цаг = parts[1]
                
                орсон_parts = орсон_цаг.split(":")
                орсон_цагийн_тоо = int(орсон_parts[0])
                орсон_минут = int(орсон_parts[1])
                
                гарсан_parts = гарсан_цаг.split(":")
                гарсан_цагийн_тоо = int(гарсан_parts[0])
                гарсан_минут = int(гарсан_parts[1])
                
                
                орсон_нийт_минут = орсон_цагийн_тоо * 60 + орсон_минут
                гарсан_нийт_минут = гарсан_цагийн_тоо * 60 + гарсан_минут
                
                зогссон_минут = гарсан_нийт_минут - орсон_нийт_минут
                
                зогссон_цаг = зогссон_минут // 60
                үлдсэн_минут = зогссон_минут % 60  
                         
                print("Орсон цаг:", орсон_цаг)
                print(f"Зогссон хугацаа: {зогссон_цаг} цаг {үлдсэн_минут} минут")
                print("===== Машин олдлоо:", номерцаг)
                found = True
                
            else:
                Жагсаалт.append(номерцаг) 
                
    with open(PARKING_FILE, "w", encoding="utf-8") as file:
        for номерцаг in  Жагсаалт:
            file.write(номерцаг)      
                              
    if found == False:
        print("===== Машин олдсонгүй")            
        
        


def Машин_устгах():
    Жагсаалт = []
    номер = input("Улсын дугаар: ")
    
    with open(PARKING_FILE, "r", encoding="utf-8") as file:
        for номерцаг in file:
            if номер not in номерцаг:
                Жагсаалт.append(номерцаг)  
                
    with open(PARKING_FILE, "w", encoding="utf-8") as file:
        for номерцаг in Жагсаалт:
            file.write(номерцаг)
                   
    return ("===== Машин устлаа")     
        
def Машинууд_харах():
    одоо = datetime.now()
    одоогийн_нийт_минут = одоо.hour * 60 + одоо.minute
    машинууд = []

    with open(PARKING_FILE, "r", encoding="utf-8") as file:
        for мөр in file:
            номер, орсон_цаг = мөр.strip().split(" - ")
            орсон_цагийн_тоо, орсон_минут = map(int, орсон_цаг.split(":"))
            орсон_нийт_минут = орсон_цагийн_тоо * 60 + орсон_минут
            зогссон_минут = одоогийн_нийт_минут - орсон_нийт_минут

            if зогссон_минут < 0:
                зогссон_минут += 24 * 60

            зогссон_цаг = зогссон_минут // 60
            үлдсэн_минут = зогссон_минут % 60
            машинууд.append(
                f"{номер} - Орсон: {орсон_цаг} - Зогссон: "
                f"{зогссон_цаг} цаг {үлдсэн_минут} минут"
            )

    return "\n".join(машинууд)
      
def Нийт_машин():
    машинууд = []
    
    with open(PARKING_FILE, "r", encoding="utf-8") as file:
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
        Машин_гарах()
        
    elif choice == "3":
            print(Машин_устгах())
            
    elif choice == "4":
            print(Машинууд_харах())  
            
    elif choice == "5":
            print(Нийт_машин())     

    elif choice == "6":
        break
