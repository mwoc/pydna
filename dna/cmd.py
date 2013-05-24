import sys
import getopt

cond = {}
if len(sys.argv) > 1:
    _args = sys.argv.copy()
    _args.pop(0)
    optlist, args = getopt.getopt(_args, '', ['pressure=', 'y-rcvr=', 'y-stor='])

    for i, opt in enumerate(optlist):

        print(opt)
        if opt[0] == '--pressure':
            cond['p_hi'] = float(opt[1])
        elif opt[0] == '--y-rcvr':
            cond['molefrac_rcvr'] = float(opt[1])
        elif opt[0] == '--y-stor':
            cond['molefrac_stor'] = float(opt[1])

print(cond)