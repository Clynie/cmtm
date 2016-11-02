
import numpy as np
import scipy
import matcompat

# if available import pylab (from matlibplot)
try:
    import matplotlib.pylab as plt
except ImportError:
    pass

#%function  [s, c, ph, ci, phi] = cmtm(x,y,dt,NW,qbias,confn,qplot);
#%
#%Multi-taper method coherence using adaptive weighting and correcting 
#%for the bias inherent to coherence estimates.  The 95% coherence
#%confidence level is computed by cohconf.m.  In addition, a built-in
#%Monte Carlo estimation procedure is available to estimate phase 95%
#%confidence limits. 
#%
#% Inputs:
#%         x     - Input data vector 1.  
#%         y     - Input data vector 2.  
#%         dt    - Sampling interval (default 1) 
#%         NW    - Number of windows to use (default 8) 
#%         qbias - Correct coherence estimate for bias (yes, 1)  (no, 0, default).
#%         confn - Number of iterations to use in estimating phase uncertainty using a Monte Carlo
#%                 method. (default 0)
#%         qplot - Plot the results, (yes, 1), (No, 0, default).  The upper tickmarks indicate the
#%                 bandwidth of the coherence and phase estimates.  
#%
#% Outputs:
#%         s       - frequency
#%         c       - coherence
#%         ph      - phase
#%         ci      - 95% coherence confidence level
#%         phi     - 95% phase confidence interval, bias corrected
#%                   (add and subtract phi from ph).
#%
#%
#%required files: cohconf.m, cohbias.m, cohbias.mat, Matlab signal processing toolbox.
#%
#%Peter Huybers
#%MIT, 2003
#%phuyber@mit.edu
def cmtm(x, y, dt, NW, qbias, confn, qplot):

    # Local Variables: ci, fx, cb, qplot, Pk, E, qbias, vari, ys, phut, Fx, Fy, phl, ds, fkx, fky, tol, Ptemp, ph, phlt, pl, NW, phi, P1, pls, xs, i1, fy, wk, N, P, V, dt, confn, phu, a, c, b, Cxy, Pkx, Pky, iter, col, s, w, v, y, x, h, k
    # Function calls: disp, cmtm, dpss, cohconf, conv, fill, fft, set, conj, repmat, find, size, plot, angle, figure, cohbias, min, axis, sum, si, sqrt, abs, zeros, rem, xlabel, pi, ciph, real, max, ylabel, sort, nargin, ones, randn, subplot, ifft, clf, gcf, fliplr, length, num2str, title, round, mean
    #%check input
    if nargin<2.:
        help(cmtm)
        return []
    
    
    if nargin<7.:
        qplot = 0.
    
    
    if nargin<6.:
        confn = 0.
    
    
    if nargin<5.:
        qbias = 0.
    
    
    if nargin<4.:
        NW = 8.
    
    
    if length(NW) == 0.:
        NW = 8.
    
    
    if nargin<3.:
        dt = 1.
    
    
    if length(dt) == 0.:
        dt = 1.
    
    
    if NW<1.5:
        np.disp('Warning: NW must be greater or equal to 1.5')
        return []
    
    
    if nargin > 4.:
        np.disp('-------------------------')
        np.disp(np.array(np.hstack(('Number of windows: ', num2str(NW)))))
        if qbias == 1.:
            np.disp('Bias correction:   On')
        else:
            np.disp('Bias correction:   Off')
            
        
        np.disp(np.array(np.hstack(('Confidence Itera.: ', num2str(confn)))))
        if qplot == 1.:
            np.disp('Plotting:          On')
        else:
            np.disp('Plotting:          Off')
            
        
        np.disp('-------------------------')
    
    
    x = x.flatten(1)-np.mean(x)
    y = y.flatten(1)-np.mean(y)
    if length(x) != length(y):
        np.disp('Warning: the lengths of x and y must be equal.')
        return []
    
    
    #%define some parameters
    N = length(x)
    k = matcompat.max(np.round((2.*NW)), N)
    k = matcompat.max((k-1.), 1.)
    s = np.arange(0., (1./dt-1./np.dot(N, dt))+(1./np.dot(N, dt)), 1./np.dot(N, dt)).conj().T
    pls = np.arange(2., ((N+1.)/2.+1.)+1)
    v = 2.*NW-1.
    #%approximate degrees of freedom
    if plt.rem(length(y), 2.) == 1.:
        pls = pls[0:0-1.]
    
    
    #%Compute the discrete prolate spheroidal sequences, requires the spectral analysis toolbox.
    [E, V] = dpss(N, NW, k)
    #%Compute the windowed DFTs.
    fkx = np.fft((E[:,0:k]*x[:,int(np.ones(1., k))-1]), N)
    fky = np.fft((E[:,0:k]*y[:,int(np.ones(1., k))-1]), N)
    Pkx = np.abs(fkx)**2.
    Pky = np.abs(fky)**2.
    #%Itteration to determine adaptive weights:    
    for i1 in np.arange(1., 3.0):
        if i1 == 1.:
            vari = matdiv(np.dot(x.conj().T, x), N)
            Pk = Pkx
        
        
        if i1 == 2.:
            vari = matdiv(np.dot(y.conj().T, y), N)
            Pk = Pky
        
        
        P = (Pk[:,0]+Pk[:,1])/2.
        #% initial spectrum estimate
        Ptemp = np.zeros(N, 1.)
        P1 = np.zeros(N, 1.)
        tol = matdiv(np.dot(.0005, vari), N)
        #% usually within 'tol'erance in about three iterations, see equations from [2] (P&W pp 368-370).   
        a = np.dot(vari, 1.-V)
        while np.sum(matdiv(np.abs((P-P1)), N)) > tol:
            b = np.dot(P, np.ones(1., k))/(np.dot(P, V.conj().T)+np.dot(np.ones(N, 1.), a.conj().T))
            #% weights
            wk = b**2.*np.dot(np.ones(N, 1.), V.conj().T)
            #% new spectral estimate
            P1 = (np.sum((wk.conj().T*Pk.conj().T))/np.sum(wk.conj().T)).conj().T
            Ptemp = P1
            P1 = P
            P = Ptemp
            #% swap P and P1
            
        if i1 == 1.:
            fkx = np.dot(np.sqrt(k), np.sqrt(wk))*fkx/matcompat.repmat(np.sum(np.sqrt(wk.conj().T)).conj().T, 1., k)
            Fx = P
            #%Power density spectral estimate of x
        
        
        if i1 == 2.:
            fky = np.dot(np.sqrt(k), np.sqrt(wk))*fky/matcompat.repmat(np.sum(np.sqrt(wk.conj().T)).conj().T, 1., k)
            Fy = P
            #%Power density spectral estimate of y
        
        
        
    #%As a check, the quantity sum(abs(fkx(pls,:))'.^2) is the same as Fx and
    #%the spectral estimate from pmtmPH.
    #%Compute coherence
    Cxy = np.sum(np.array(np.hstack((fkx*np.conj(fky)))).conj().T)
    ph = matdiv(np.angle(Cxy)*180., np.pi)
    c = np.abs(Cxy)/np.sqrt((np.sum((np.abs(fkx.conj().T)**2.))*np.sum((np.abs(fky.conj().T)**2.))))
    #%correct for the bias of the estimate
    if qbias == 1.:
        c = cohbias(v, c).conj().T
    
    
    #%Phase uncertainty estimates via Monte Carlo analysis. 
    if confn > 1.:
        cb = cohbias(v, c).conj().T
        for iter in np.arange(1., (confn)+1):
            if plt.rem(iter, 10.) == 0.:
                np.disp(np.array(np.hstack(('phase confidence iteration: ', num2str(iter)))))
            
            
            fx = np.fft((plt.randn(matcompat.size(x))+1.))
            fx = matdiv(fx, np.sum(np.abs(fx)))
            fy = np.fft((plt.randn(matcompat.size(y))+1.))
            fy = matdiv(fy, np.sum(np.abs(fy)))
            ys = np.real(plt.ifft((fy*np.sqrt((1.-cb.conj().T**2.)))))
            ys = ys+np.real(plt.ifft((fx*cb.conj().T)))
            xs = np.real(plt.ifft(fx))
         # matlab  code     [si, ciph(iter,:), phi(iter,:)]=cmtm(xs,ys,dt,NW);

        pl = np.round(np.dot(.975, iter))
        #%sorting and averaging to determine confidence levels.
        phi = np.sort(phi)
        phi = np.array(np.vstack((np.hstack((phi[int(pl)-1,:])), np.hstack((-phi[int((iter-pl+1.))-1,:])))))
        phi = np.mean(phi)
        phi = plt.conv(phi[0:], (np.array(np.hstack((1., 1., 1.)))/3.))
        phi = phi[1:0-1.]
    else:
        phi = np.zeros(matcompat.size(pls))
        
    
    #%Cut to one-sided funtions
    c = c[int(pls)-1]
    s = s[int(pls)-1].conj().T
    ph = ph[int(pls)-1]
    phl = ph-phi
    phu = ph+phi
    #%Coherence confidence level
    ci = cohconf(v, .95)
    #%not corrected for bias, this is conservative.
    ci = np.dot(ci, np.ones(matcompat.size(c)))
    #%plotting
    if qplot == 1.:
        #%coherence
    plt.figure(plt.gcf)
    plt.clf
    plt.subplot(211.)
    plt.hold(on)
    plt.plot(s, c)
    h = plt.ylabel('coherence')
    h = plt.xlabel('frequency')
    plt.plot(s, ci, 'k--')
    pl = nonzero((c > ci[0]))
    plt.title(np.array(np.hstack(('mean is ', num2str(np.mean(c), 2.), '   ', num2str(matdiv(100.*length(pl), length(c)), 2.), '% of estimates above 95% confidence level'))))
    plt.axis(tight)
    h = plt.axis
    plt.axis(np.array(np.hstack((h[0:2.], 0., 1.025))))
    w = matdiv(NW, np.dot(dt, N))
    #%half-bandwidth of the dpss
    plt.plot(np.array(np.hstack((s[0], h[1]))), np.array(np.hstack((1.02, 1.02))), 'k')
    for ds in np.arange(matcompat.max(s), (matcompat.max(s))+(2.*w), 2.*w):
        plt.plot(np.array(np.hstack((ds, ds))), np.array(np.hstack((.98, 1.02))), 'k')
        
    #%phase
    plt.subplot(212.)
    plt.hold(on)
    plt.plot(s, ph)
    if confn > 0.:
        col = np.array(np.hstack((.9, .9, .9)))
        h = plt.fill(np.array(np.hstack((s[0], s[0:], np.fliplr(np.array(np.hstack((s[0:], s[int(0)-1]))))))), np.array(np.hstack((phu[0], phl, np.fliplr(np.array(np.hstack((phu, phl[int(0)-1]))))))), col)
        set(h, 'edgecolor', col)
        pl = nonzero((phu<=180.))
        phu[int(pl)-1] = -180.
        pl = nonzero((phu > 180.))
        phu[int(pl)-1] = phu[int(pl)-1]-360.
        phlt = np.dot(-180., np.ones(matcompat.size(phl)))
        h = plt.fill(np.array(np.hstack((s[0], s[0:], np.fliplr(np.array(np.hstack((s[0:], s[int(0)-1]))))))), np.array(np.hstack((phu[0], phlt, np.fliplr(np.array(np.hstack((phu, phlt[int(0)-1]))))))), col)
        set(h, 'edgecolor', col)
        pl = nonzero((phl >= -180.))
        phl[int(pl)-1] = 180.
        pl = nonzero((phl<-180.))
        phl[int(pl)-1] = phl[int(pl)-1]+360.
        phut = 180.*np.ones(matcompat.size(phl))
        h = plt.fill(np.array(np.hstack((s[0], s[0:], np.fliplr(np.array(np.hstack((s[0:], s[int(0)-1]))))))), np.array(np.hstack((phut[0], phl, np.fliplr(np.array(np.hstack((phut, phl[int(0)-1]))))))), col)
        set(h, 'edgecolor', col)
    
    
    h = plt.plot(s, ph)
    plt.plot(s, np.zeros(matcompat.size(s)), 'k--')
    plt.axis(tight)
    h = plt.axis
    plt.axis(np.array(np.hstack((h[0:2.], -180., 180.))))
    h = plt.xlabel('frequency')
    h = plt.ylabel('phase')
    
    return [s, c, ph, ci, phi]