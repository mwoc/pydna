import os
import csv

root = os.getcwd()

for f in sorted(os.listdir(root)):
    if os.path.isfile(f) and os.path.splitext(f)[1] == '.csv':
        with open(os.path.join(root, f), 'r') as csvfile:

            print('File: {}'.format(f))
            reader = csv.reader(csvfile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)

            result = {}
            for row in reader:

                if len(row) > 0:
                    if row[0] == '18.1':
                        result['mdot_rcvr'] = float(row[5])
                        result['y_rcvr'] = float(row[4])
                        result['p_hi'] = float(row[8])
                    elif row[0] == '47.1':
                        result['y_stor'] = float(row[4])
                    elif row[0] == 'Eff.:':
                        result['eff'] = float(row[1])

            print(result)
