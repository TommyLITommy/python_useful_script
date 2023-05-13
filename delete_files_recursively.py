import os
def delete(cwd, file_extension):
    os.chdir(cwd)
    os.getcwd()
    list1 = os.listdir()
    if not list1:
        return
    else:
        for i in list1:
            if os.path.isdir(i):
                delete(i, file_extension)
            else:
                if i.endswith(file_extension):
                    print(i)
                    try:
                        os.remove(i) #iterate subdirectory!
                    except:
                        print("remove fial")
        os.chdir('../')


delete(".", ".xlsx")
