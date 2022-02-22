from dog import *

def main():
    katarina = Dog()
    print("An instance of the class Dog has been created.")
    print()
    katarina.give_attributes("Katarina", "Pho", 24)
    print("The dog %s is nicknamed %s." % (katarina.name,katarina.nickname))
    print()
    katarina.change_nickname("Katarushki")
    print("%s's nickname is now changed to %s" % (katarina.name, katarina.nickname))
    print()
    print("Her kommer opprinnelig liggeliste:")
    print(katarina.liggeliste)
    print()
    katarina.cavasondag()
    print("Her kommer liggelisten etter cavasondag:")
    print(katarina.liggeliste)
    

main()