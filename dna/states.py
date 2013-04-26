import refprop as rp



def getPsat(Tsat,y):
    rp.setup('def', 'ammonia', 'water')
    x = [y, 1-y]
    rp.setref(hrf='NBP',ixflag=2, x0=x)
    prop = rp.flsh('tq', (Tsat + 273.15), 0, x,2)

    return prop

for i in range(1, 19):
    print('*' * 10)
    print('NH3 mass fraction: ',i/20)

    try:
        prop = getPsat(30,i/20)
    except:
        print('failed')
        pass
    else:
        print('P_sat: ',prop['p']/100)
        #print(prop)

