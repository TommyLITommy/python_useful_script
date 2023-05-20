import os

def delete_folder(cwd):
    os.chdir(cwd)
    cur_cwd = os.getcwd()
    f_list = os.listdir()
    if f_list:
        for i in f_list:
            if os.path.isdir(i):
                delete_folder(i)
                folder_full_path = os.path.join(cur_cwd, i)
                os.rmdir(folder_full_path)
            else:
                try:
                    os.remove(i)
                except:
                    print("delte {} failed".format(i))
    os.chdir("../")

def delete_folder_recursively(cwd, folder_name):
    os.chdir(cwd)
    cur_cwd = os.getcwd()
    f_list = os.listdir()
    if f_list:    
        for i in f_list:
            if os.path.isdir(i):
                if i == folder_name:
                    delete_folder(i)
                    folder_full_path = os.path.join(cur_cwd, i)
                    os.rmdir(folder_full_path)
                else:
                    delete_folder_recursively(i, folder_name)
    os.chdir("../")

delete_folder_recursively("./", "output")


