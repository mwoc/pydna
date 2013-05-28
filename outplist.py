import os, sys, getopt
import csv

root = os.getcwd()

if len(sys.argv) > 1:
    print(sys.argv)
    _args = sys.argv.copy()
    _args.pop(0)
    optlist, args = getopt.getopt(_args, '', ['path='])

    for i, opt in enumerate(optlist):

        if opt[0] == '--path':
            root = os.path.join(root, str(opt[1]))

for f in sorted(os.listdir(root)):
    fullpath = os.path.join(root, f)
    if os.path.isfile(fullpath) and os.path.splitext(fullpath)[1] == '.csv':
        with open(fullpath, 'r') as csvfile:

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
