class Dog:
    def __init__(self):
        self.name = ""
        self.nickname   = ""
        self.age    = ""
        self.liggeliste = []
        
    def give_attributes(self, name, nickname, age):
        self.name = name
        self.nickname   = nickname
        self.age    = age
        
    def change_name(self, newName):
        self.name = newName 
    
    def change_nickname(self, newNickname):
        self.nickname = newNickname 
        
    def birthday(self):
        self.age = self.age+1
        
    def cavasondag(self):
        self.liggeliste = [[1]*7]*3
