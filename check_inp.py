# test file to see if i can make something tha tkidn of finds similar class
inp = input()

inp = inp.strip().lower()

# create dict
resulting_dict = dict()
with open("dropdown_final.txt", "r") as df:
    for line in df:
        dept = line.split("\t\t\t")[0].strip()
        select = line.split("\t\t\t")[1].strip()
        resulting_dict[dept] = select


for key in resulting_dict:
    print(key + " / " + resulting_dict[key])


def find_val(here):
    # checks if its typed directly
    # if not, removes special charcaters like & and space from my list of things?
    # basically make my own search function for htis
    here = here.lower()
    if (resulting_dict[here] != True):
        print ("go on...")


