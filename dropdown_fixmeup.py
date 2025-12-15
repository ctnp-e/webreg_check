with open("things_output.txt", "r") as f:
    with open("dictlist.txt", "r") as fo:
        with open("final.txt", "w") as final:
            for line in fo:
                first = line.strip()
                
                # lowk forgot how to do readline again. im not very smart
                total = first + " \t\t\t " + f.readline()
                final.write(total)


