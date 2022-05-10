def svr_param(df,param,args={}):
    pit = 50
    if param=='C':
        arvot = np.geomspace(0.1, 16000, pit) #C
    elif param=='gamma':
        arvot = np.linspace(0.01, 8, pit) #gamma
    elif param=='epsilon':
        arvot = np.linspace(0.1, 3, pit) #epsilon
    else:
        print('tuntematon parametri')
        exit(1)
    nsum_data = np.sum((df.vuo-np.mean(df.vuo))**2)
    pisteet = np.zeros(pit)
    print('')
    for i,c in enumerate(arvot):
        print("\033[F%i/%i\033[K" %(i+1,pit))
        args.update({param:c}) #gamma=2.58, epsilon=1.3
        a,b = ristivalidoi(df, svm.SVR(tol=0.005, **args), 5)
        pisteet[i] = 1-a/nsum_data
    return arvot, pisteet

def svr_param_kaikki(df,args={}):
    if True:
        a,p = svr_param(df,'C',args)
        ind = np.argmax(p)
        m = a[ind]
        print('C = %.0f\t R2 = %.3f' %(m,p[ind]))
        args.update({'C':m})
        plt.plot(a,p)
        plt.gca().set_xscale('log')
        plt.show()
    elif 'C' not in args:
        args.update({'C':4570})

    if False:
        a,p = svr_param(df,'epsilon',args)
        ind = np.argmax(p)
        m = a[ind]
        print('epsilon = %.3f\t R2 = %.3f' %(m,p[ind]))
        args.update({'epsilon':m})
        plt.plot(a,p)
        plt.gca().set_xscale('log')
        plt.show()
    elif 'epsilon' not in args:
        args.update({'epsilon':1.224})

    if False:
        a,p = svr_param(df,'gamma',args)
        ind = np.argmax(p)
        m = a[ind]
        print('gamma = %.3f\t R2 = %.3f' %(m,p[ind]))
        args.update({'gamma':m})
        plt.plot(a,p)
        plt.gca().set_xscale('log')
        plt.show()
    elif 'gamma' not in args:
        args.update({'gamma':5.717})
    return args

def main_tutki_svr():
    np.random.seed(12345)
    prf_ind = 0
    df = tee_data(prf_ind)
    df.vuo = df.vuo*1e9 #pienet luvut sotkevat menetelmiä
    args = {'C': 900, 'epsilon': 1.5204081632653061, 'gamma': 5.391020408163265} #jäätymiskausi C=17700, mutta hidas
    args = {'C': 500, 'epsilon': 1.4612244897959183, 'gamma': 0.4991836734693878} #jäätymiskausi sis prf ja lat
    args = svr_param_kaikki(df,args)
    print(args)
    return 0


def ortogonaali_regressio(dtx,dty):
    n11 = 1/(dtx.shape[0]-1)
    dtym = np.mean(dty)
    dtxm = np.mean(dtx)
    sxx = n11*np.sum((dtx-dtxm)**2)
    syy = n11*np.sum((dty-dtym)**2)
    sxy = n11*(np.sum((dty-dtym)*(dtx-dtxm)))
    a1 = (syy-sxx+np.sqrt((syy-sxx)**2 + 4*sxy**2)) / (2*sxy)
    a0 = dtym - a1*dtxm
    return [a0,a1]

def piirra_ortog(t_ind, piirtox, dtx, nimet):
    datax = dtx[:,[t_ind+1]]
    wetl = dtx[:,[-1]]
    maski = (datax>=0.03).flatten()
    a0,a1 = ortogonaali_regressio(datax[maski],wetl[maski])
    tausta, = plot(datax[maski,:],wetl[maski,:],'.',color='b')
    tausta, = plot(datax[~maski,:],wetl[~maski,:],'.',color='r')
    piirtoy = piirtox[:,1]*a1 + a0
    print(a0,a1)
    sovit, = plot(piirtox[:,1],piirtoy)
    xlabel(nimet[t_ind])
    ylabel('wetland')
    show()

class Ortog():
    def __init__(self,suure=0):
        self.suure = suure
        return
    def fit(self,x,y):
        self.a0,self.a1 = ortogonaali_regressio(x[:,self.suure],y)
    def predict(self,x):
        return x[:,self.suure]*self.a1 + self.a0
    def get_params(self,deep):
        return {'suure':self.suure}
    def set_params(self,**kwargs):
        for k in kwargs.keys():
            if k == 'suure':
                self.suure = kwargs[k]
                
class OmaRandomForest():
    def __init__(self, n_estimators=100, samp_kwargs={'frac':0.025}, tree_kwargs={}):
        self.n_estimators = n_estimators
        self.samp_kwargs = samp_kwargs
        self.tree_kwargs = tree_kwargs
    def fit(self,x,y):
        df = pd.concat([x,y],axis=1)
        self.puut = np.empty(self.n_estimators, object)
        for i,dt in enumerate(RandomSubspace(df, self.n_estimators, samp_kwargs=self.samp_kwargs)):
            self.puut[i] = tree.DecisionTreeRegressor(**self.tree_kwargs).fit(dt.drop(y.name,axis=1), dt[y.name])
        return self
    def predict(self, x, palauta=True):
        self.yhatut = np.empty([x.shape[0], len(self.puut)])
        for i,puu in enumerate(self.puut):
            self.yhatut[:,i] = puu.predict(x)
        return np.mean(self.yhatut, axis=1) if palauta else None
    def confidence(arvo,x=None):
        if not x is None:
            self.predict(x, palauta=False)
        return (np.percentile(self.yhatut, arvo, axis=1), np.percentile(self.yhatut, 1-arvo, axis=1))

def main_random_forest():
    np.random.seed(12345)
    prf_ind = 0
    df = tee_data(prf_ind).drop('yksi',axis=1)
    df.vuo = df.vuo*1e9
    npist = len(df)
    nsum_data = np.sum((df.vuo-np.mean(df.vuo))**2)

    #malli = ensemble.RandomForestRegressor(n_estimators=100)
    malli = OmaRandomForest(n_estimators=100, samp_kwargs={'frac':0.5})
    nsum_sovit, aika = ristivalidoi(df, malli, 15)
    print(np.sqrt(nsum_sovit/npist), 1-nsum_sovit/nsum_data, aika)

