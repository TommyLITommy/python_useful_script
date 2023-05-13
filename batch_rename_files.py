import os

folder = r'C:\Study\Python\useful_script_backup\automatic_test_for_360D_mutlipath_test\output\A3_YES_TV_NEW_PARA_#1\\'

for file_name in os.listdir(folder):
    if not file_name.endswith('.txt'):
        continue
    # Construct old file name
    source = folder + file_name

    file_name = file_name.replace("#2", "#1")
    destination = folder + file_name

    # Renaming the file
    os.rename(source, destination)
    
print('All Files Renamed')
print('New Names are')
# verify the result
res = os.listdir(folder)
print(res)