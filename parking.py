from datetime import datetime
from pathlib import Path


PARKING_FILE = Path(__file__).resolve().parent / "parking.txt"

ЦАГИЙН_ТӨЛБӨР = 1000
ЦАГИЙН_ФОРМАТ = "%Y-%m-%d %H:%M"


def Төлбөр_тооцох(минут):
    цаг = max((минут + 59) // 60, 1)
    return цаг * ЦАГИЙН_ТӨЛБӨР


def _цаг_унших(текст):
    return datetime.strptime(текст.strip(), ЦАГИЙН_ФОРМАТ)


def _зогссон_минут(орсон, гарсан):
    return int((гарсан - орсон).total_seconds() // 60)


def Машин_оруулах():
    номер = input("Улсын дугаар: ")
    цаг = datetime.now().strftime(ЦАГИЙН_ФОРМАТ)
    
    with open(PARKING_FILE, "a", encoding="utf-8") as file:
        file.write(f'{номер} - {цаг}\n')
        
        return "<<Амжилттай нэвтэрлээ>>"

def Машин_гарах():
    номер = input("Улсын дугаар: ")
    гарсан_цаг = datetime.now()
    found = False
    
    Жагсаалт = []
    
                 
    with open(PARKING_FILE, "r", encoding="utf-8") as file:
        for номерцаг in file:
            if номер in номерцаг:
                parts = номерцаг.strip().split(" - ")
                орсон_цаг = parts[1]

                зогссон_минут = _зогссон_минут(
                    _цаг_унших(орсон_цаг), гарсан_цаг
                )

                if зогссон_минут < 0:
                    print("===== Гарсан цаг орсон цагаас өмнө байна:", орсон_цаг)
                    Жагсаалт.append(номерцаг)
                    found = True
                    continue

                зогссон_цаг = зогссон_минут // 60
                үлдсэн_минут = зогссон_минут % 60
                төлбөр = Төлбөр_тооцох(зогссон_минут)

                print("Орсон цаг:", орсон_цаг)
                print(f"Зогссон хугацаа: {зогссон_цаг} цаг {үлдсэн_минут} минут")
                print(f"Төлбөр: {төлбөр}₮")
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
    машинууд = []

    with open(PARKING_FILE, "r", encoding="utf-8") as file:
        for мөр in file:
            номер, орсон_цаг = мөр.strip().split(" - ")
            зогссон_минут = max(_зогссон_минут(_цаг_унших(орсон_цаг), одоо), 0)

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
       
       
        
if __name__ == "__main__":
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
